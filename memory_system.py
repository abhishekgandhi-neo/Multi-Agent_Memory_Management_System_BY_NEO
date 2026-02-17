import json
import uuid
from openrouter_client import OpenRouterClient
from database import DatabaseManager
from config import DEFAULT_MODEL, SUMMARIZER_MODEL, HOT_CONTEXT_WINDOW, COLD_CONTEXT_THRESHOLD

class MemoryAgentSystem:
    def __init__(self, db_manager: DatabaseManager, llm_client: OpenRouterClient, verbose=False):
        self.db = db_manager
        self.llm = llm_client
        self.verbose = verbose
        self.log_history = []

    def _log(self, action, details):
        entry = {"action": action, "details": details}
        self.log_history.append(entry)
        if self.verbose:
            print(f"\n[AGENT DECISION] {action}")
            if isinstance(details, dict):
                for k, v in details.items():
                    print(f"  - {k}: {v}")
            else:
                print(f"  - {details}")

    def _get_hot_context(self, session_id):
        """Retrieves only the most recent N turns to save tokens."""
        messages = self.db.get_latest_messages(session_id, n=HOT_CONTEXT_WINDOW)
        return [{"role": m[0], "content": m[1]} for m in messages]

    def _get_summarized_context(self, session_id):
        """Retrieves the latest summarized context."""
        summaries = self.db.get_session_messages(session_id, msg_type='summary')
        if not summaries:
            return ""
        # Return only the most recent summary to be token efficient
        return summaries[-1][1]

    def _get_relevant_context(self, session_id, query, hot_messages):
        """Retrieves relevant turns, filtering out those already in the hot window."""
        self._log("DATABASE QUERY", f"Searching vector DB for relevant context to: '{query}'")
        results = self.db.search_embeddings(query, n_results=3, session_id=session_id)
        context_docs = results['documents'][0] if results['documents'] else []
        
        # Competitive Pruning: Filter out hits already in the hot context
        hot_content = [m['content'] for m in hot_messages]
        relevant_filtered = [doc for doc in context_docs if doc not in hot_content]
        
        # Limit the number of relevant snippets to 2 to minimize overhead
        return " | ".join(relevant_filtered[:2])

    def generate_response(self, session_id, user_input):
        # 1. Retrieval & Agent Decisions
        self._log("RETRIEVAL", f"Starting memory retrieval for session {session_id}")
        
        hot_context = self._get_hot_context(session_id)
        summary = self._get_summarized_context(session_id)
        relevant = self._get_relevant_context(session_id, user_input, hot_context)

        # Context Injection (Optimized for token efficiency)
        context_str = ""
        if summary:
            # Shortened label to save tokens
            context_str += f"Sum: {summary}\n"
        if relevant:
            context_str += f"Rel: {relevant}\n"

        # Ultra-short system prompt for gpt-4o-mini
        system_content = "Assistant. Context below if any."
        if context_str:
            system_content += f"\n{context_str}"

        # Final Prompt Construction
        messages = [{"role": "system", "content": system_content}] + hot_context + [{"role": "user", "content": user_input}]
        
        if self.verbose:
            print(f"\n[LLM QUERY] Sending prompt to {DEFAULT_MODEL}...")

        response = self.llm.chat_completion(messages, model=DEFAULT_MODEL)
        
        if response:
            self.db.add_message(session_id, "user", user_input, "original")
            self.db.add_message(session_id, "assistant", response, "original")
            self._trigger_consolidation_and_pruning(session_id)
            
        return response

    def _trigger_consolidation_and_pruning(self, session_id):
        """Summarizes into blocks to avoid redundant LLM calls and reduce overhead."""
        all_original = self.db.get_session_messages(session_id, msg_type='original')
        
        # Only summarize when history exceeds threshold significantly and we have enough new turns
        # This prevents re-summarizing every single turn after the first limit is hit.
        existing_summaries = self.db.get_session_messages(session_id, msg_type='summary')
        
        # Trigger condition: 
        # (Total history > threshold) AND (No summary OR (Growth since last summary/start > buffer))
        trigger_threshold = COLD_CONTEXT_THRESHOLD + 5 
        
        if len(all_original) >= trigger_threshold:
            # Ensure we don't re-summarize if we just did it 3 turns ago
            # We check the count of messages in the latest summary if we were smart, 
            # here we just check if len(all_original) is a multiple of 5 above threshold or 
            # if we have significantly more messages than turns covered by the last summary.
            # Simplified for benchmark: trigger every 5 new turns after reaching 10.
            delta = len(all_original) - COLD_CONTEXT_THRESHOLD
            if delta % 5 == 0:
                self._log("CONSOLIDATION", f"Memory size ({len(all_original)}) exceeds threshold. Summarizing block.")
                
                # Summarize everything EXCEPT the hot window
                to_summarize = all_original[:-HOT_CONTEXT_WINDOW]
                text = "\n".join([f"{m[0]}: {m[1]}" for m in to_summarize])
                
                sum_prompt = [
                    {"role": "system", "content": "Briefly summarize key facts. No filler."},
                    {"role": "user", "content": text}
                ]
                
                summary = self.llm.chat_completion(sum_prompt, model=SUMMARIZER_MODEL)
                if summary:
                    self._log("MEMORY_STORAGE", "Summarized archived turns.")
                    self.db.add_message(session_id, "system", summary, "summary")
