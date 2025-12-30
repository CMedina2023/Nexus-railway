"""
Módulo para el manejo del progreso de obtención de datos mediante hilos y colas.
"""
import logging
from queue import Queue, Empty
from threading import Thread
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

class ProgressTracker:
    """
    Gestiona la ejecución de una tarea en segundo plano y rastrea su progreso
    mediante una cola sincronizada.
    """

    def __init__(self, connection: Any, jql: str):
        """
        Inicializa el rastreador de progreso.
        
        Args:
            connection: Conexión a la API (ej. JiraConnection)
            jql: Consulta JQL para obtener los issues
        """
        self.connection = connection
        self.jql = jql
        self.queue = Queue()
        self.all_issues: List[Dict] = []
        self.error: Optional[Exception] = None
        self._thread: Optional[Thread] = None

    def start(self) -> None:
        """Inicia el hilo de obtención de issues."""
        def _fetch_task():
            try:
                from app.auth.fetchers.parallel_issue_fetcher import MetricsIssueFetcher
                fetcher = MetricsIssueFetcher(self.connection)
                self.all_issues = fetcher.fetch_with_progress_queue(self.jql, self.queue)
                self.queue.put({'done': True})
            except Exception as e:
                logger.error(f"Error en ProgressTracker thread: {e}", exc_info=True)
                self.error = e
                self.queue.put({'error': str(e)})

        self._thread = Thread(target=_fetch_task, daemon=True)
        self._thread.start()

    def get_events(self, timeout: float = 1.0):
        """
        Generador que consume eventos de la cola de progreso.
        
        Args:
            timeout: Tiempo máximo de espera para nuevos datos
            
        Yields:
            Dict con información de progreso o señal de finalización
        """
        while True:
            try:
                data = self.queue.get(timeout=timeout)
                
                if 'error' in data:
                    self.error = Exception(data['error'])
                    break
                
                if data.get('done'):
                    break
                
                yield data
            except Empty:
                if self._thread and not self._thread.is_alive():
                    break
                continue

    def join(self, timeout: float = 10.0) -> None:
        """
        Espera a que el hilo de ejecución termine.
        
        Args:
            timeout: Tiempo máximo de espera
        """
        if self._thread:
            self._thread.join(timeout=timeout)

    @property
    def is_alive(self) -> bool:
        """Verifica si el hilo de ejecución sigue activo."""
        return self._thread.is_alive() if self._thread else False
