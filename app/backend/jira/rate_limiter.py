import logging
import time
from app.core.config import Config

logger = logging.getLogger(__name__)

class IssueCreationRateLimiter:
    """
    Rate limiter con backoff exponencial para creación de issues
    Previene throttling de Jira API
    """
    
    def __init__(self, base_delay: float = None, backoff_multiplier: float = None, max_delay: float = None):
        """
        Inicializa el limitador de velocidad.
        
        Args:
            base_delay: Retraso base entre peticiones.
            backoff_multiplier: Multiplicador para crecimiento exponencial.
            max_delay: Retraso máximo permitido.
        """
        self._base_delay = base_delay or Config.JIRA_CREATE_ISSUE_DELAY_SECONDS
        self._backoff_multiplier = backoff_multiplier or Config.JIRA_CREATE_ISSUE_BACKOFF_MULTIPLIER
        self._max_delay = max_delay or Config.JIRA_CREATE_ISSUE_MAX_DELAY_SECONDS
        self._current_delay = self._base_delay
        self._consecutive_errors = 0
        self._last_request_time = None
        logger.info(f"RateLimiter inicializado: base_delay={self._base_delay}s, backoff={self._backoff_multiplier}x, max={self._max_delay}s")
    
    def wait(self) -> None:
        """Espera si es necesario según el rate limit."""
        if self._last_request_time is None:
            self._last_request_time = time.time()
            return
        
        elapsed = time.time() - self._last_request_time
        required_delay = self._current_delay
        
        if elapsed < required_delay:
            wait_time = required_delay - elapsed
            logger.debug(f"Rate limiting: esperando {wait_time:.2f}s (delay actual: {self._current_delay:.2f}s)")
            time.sleep(wait_time)
        
        self._last_request_time = time.time()
    
    def report_success(self) -> None:
        """Reporta un éxito para resetear el backoff."""
        if self._consecutive_errors > 0:
            logger.info(f"Request exitoso después de {self._consecutive_errors} errores, reseteando backoff")
        self._consecutive_errors = 0
        self._current_delay = self._base_delay
    
    def report_error(self) -> None:
        """Reporta un error para incrementar el backoff."""
        self._consecutive_errors += 1
        old_delay = self._current_delay
        self._current_delay = min(
            self._current_delay * self._backoff_multiplier,
            self._max_delay
        )
        logger.warning(
            f"Error #{self._consecutive_errors} detectado, "
            f"incrementando delay: {old_delay:.2f}s → {self._current_delay:.2f}s"
        )
