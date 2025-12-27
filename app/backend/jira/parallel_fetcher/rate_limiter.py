import time
from threading import Lock
from app.core.config import Config

class RateLimiter:
    """Thread-safe rate limiter for Jira API requests"""
    
    def __init__(self, rate_limit_sleep: float = None):
        self._rate_limit_sleep = rate_limit_sleep or Config.JIRA_PARALLEL_RATE_LIMIT_SLEEP
        self._rate_limit_lock = Lock()
        self._last_request_time = 0.0
        
    def wait(self) -> None:
        """
        Espera el tiempo necesario para respetar el rate limiting
        """
        with self._rate_limit_lock:
            current_time = time.time()
            time_since_last_request = current_time - self._last_request_time
            
            if time_since_last_request < self._rate_limit_sleep:
                sleep_time = self._rate_limit_sleep - time_since_last_request
                time.sleep(sleep_time)
            
            self._last_request_time = time.time()
