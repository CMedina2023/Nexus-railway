"""
Servicio para el formateo de respuestas de métricas.
"""
from typing import Dict, Any

class MetricsFormatter:
    """
    Clase encargada de dar formato a las respuestas de las APIs de métricas.
    """

    @staticmethod
    def format_project_metrics(
        project_key: str,
        view_type: str,
        metrics_result: Dict[str, Any],
        from_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Formatea el resultado de las métricas para la respuesta JSON.

        Args:
            project_key: Clave del proyecto.
            view_type: Tipo de vista (general/personal).
            metrics_result: Resultado del cálculo de métricas.
            from_cache: Si los datos provienen de la caché.

        Returns:
            Dict[str, Any]: Diccionario formateado para la respuesta.
        """
        return {
            "project_key": project_key,
            "view_type": view_type,
            "test_cases": metrics_result.get('test_cases', []),
            "bugs": metrics_result.get('bugs', []),
            "general_report": metrics_result.get('general_report', {}),
            "total_issues": metrics_result.get('total_issues', 0),
            "from_cache": from_cache
        }
