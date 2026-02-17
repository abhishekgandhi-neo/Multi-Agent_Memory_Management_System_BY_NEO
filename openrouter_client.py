import requests
import json
import time
import logging
import os
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenRouterClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or OPENROUTER_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "LLM Memory Manager",
        }
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        self.default_model = "openai/gpt-4o-mini"

    def chat_completion(self, messages, model=None, stream=False):
        model = model or self.default_model
        if self.api_key == "YOUR_OPENROUTER_API_KEY" or not self.api_key or "dummy" in self.api_key:
            # Enhanced mock mode for realistic benchmarking
            last_user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "Hello")
            mock_content = f"I understand you are talking about: {last_user_msg[:50]}. How can I help further?"
            
            # Simple heuristic: 1 token per 4 chars
            prompt_text = json.dumps(messages)
            prompt_tokens = len(prompt_text) // 4
            completion_tokens = len(mock_content) // 4
            
            self._update_usage({
                "prompt_tokens": prompt_tokens, 
                "completion_tokens": completion_tokens, 
                "total_tokens": prompt_tokens + completion_tokens
            })
            return mock_content

        payload = {
            "model": model,
            "messages": messages,
        }
        
        try:
            response = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                usage = data.get("usage", {})
                self._update_usage(usage)
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"Invalid response: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling OpenRouter: {e}")
            return None

    def _update_usage(self, usage):
        self.token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
        self.token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
        self.token_usage["total_tokens"] += usage.get("total_tokens", 0)

    def get_token_usage(self):
        return self.token_usage
