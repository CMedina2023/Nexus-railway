from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Callable
from app.backend.jira.parallel_fetcher.worker import Worker

class PaginationStrategy(ABC):
    """Interfaz base para estrategias de paginación"""
    
    def __init__(self, worker: Worker, max_workers: int, max_results_per_page: int):
        self.worker = worker
        self.max_workers = max_workers
        self.max_results_per_page = max_results_per_page

    @abstractmethod
    def fetch_all(
        self,
        jql: str,
        total: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        fields: Optional[str] = None,
        **kwargs
    ) -> List[Dict]:
        """
        Ejecuta la estrategia de paginación para obtener todas las issues
        """
        pass
