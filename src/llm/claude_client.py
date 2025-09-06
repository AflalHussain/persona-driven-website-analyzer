import time
import logging
import random
from typing import Dict
from langchain_anthropic import ChatAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

class RateLimitedLLM:
    def __init__(self, api_key: str, min_delay: float = 10.0, max_delay: float = 20.0):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-latest",
            temperature=0.7,
            anthropic_api_key=api_key
        )
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_call_time = 0
        self.retry_count = 0
        self.max_retries = 3

    def _wait_for_rate_limit(self):
        """Ensure minimum delay between API calls with exponential backoff"""
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        
        if self.retry_count > 0:
            delay = min(300, self.min_delay * (2 ** self.retry_count))
        else:
            delay = random.uniform(self.min_delay, self.max_delay)
            
        if elapsed < delay:
            sleep_time = delay - elapsed
            logging.info(f"Waiting {sleep_time:.2f} seconds before next API call")
            time.sleep(sleep_time)
            
        self.last_call_time = time.time()

    def invoke(self, message: Dict[str, str], max_attempts: int = 3) -> str:
        """Make API call with built-in retry logic"""
        self.retry_count = 0
        last_error = None
        
        while self.retry_count < max_attempts:
            try:
                self._wait_for_rate_limit()
                logging.info(f"Attempt {self.retry_count + 1} of {max_attempts}")
                
                response = self.llm.invoke(message)
                self.retry_count = 0
                return response.content
                
            except Exception as e:
                self.retry_count += 1
                last_error = e
                error_msg = str(e)
                
                if "rate_limit_error" in error_msg:
                    logging.warning(f"Rate limit hit on attempt {self.retry_count}")
                elif self.retry_count >= max_attempts:
                    logging.error(f"Max retries ({max_attempts}) reached")
                    raise
                else:
                    logging.warning(f"Error on attempt {self.retry_count}: {error_msg}")
                    time.sleep(2 ** self.retry_count)
        
        raise ValueError(f"Failed after {max_attempts} attempts. Last error: {str(last_error)}") 