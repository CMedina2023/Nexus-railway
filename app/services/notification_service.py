"""
Servicio de Notificaciones
Responsabilidad única: Gestionar el envío de notificaciones (Email, In-App) para eventos del sistema
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Servicio para envío de notificaciones
    Idealmente se conecta con un proveedor de Email (SMTP/SendGrid) o sistema de colas.
    En esta fase, simulamos el envío con Logs estructurados.
    """
    
    def __init__(self):
        # Aquí se inicializarían clientes de email, slack, etc.
        pass

    def notify_status_change(self, 
                           recipient_id: int, 
                           artifact_type: str, 
                           artifact_id: int, 
                           new_status: str,
                           actor_id: int,
                           comments: Optional[str] = None):
        """
        Notifica a un usuario sobre un cambio de estado en un artefacto
        """
        # TODO: Lookup user email from recipient_id via UserRepository
        
        subject = f"Nexus AI: {artifact_type} #{artifact_id} changed to {new_status}"
        body = f"""
        El estado del artefacto {artifact_type}:{artifact_id} ha cambiado a {new_status}.
        
        Acción realizada por Usuario ID: {actor_id}
        """
        
        if comments:
            body += f"\nComentarios: {comments}"
            
        self._send_email_mock(recipient_id, subject, body)
        self._create_in_app_notification(recipient_id, subject, body)

    def notify_review_request(self, 
                            potential_reviewers: List[int], 
                            artifact_type: str, 
                            artifact_id: int,
                            requester_id: int):
        """
        Notifica a los revisores que hay un nuevo ítem pendiente
        """
        subject = f"Nexus AI: Review Requested for {artifact_type} #{artifact_id}"
        body = f"Usuario {requester_id} ha solicitado revisión para {artifact_type}:{artifact_id}."
        
        for reviewer_id in potential_reviewers:
            self._send_email_mock(reviewer_id, subject, body)

    def _send_email_mock(self, user_id: int, subject: str, body: str):
        """Simula envío de email"""
        logger.info(f"[EMAIL MOCK] To: User({user_id}) | Subject: {subject} | Body: {body[:50]}...")

    def _create_in_app_notification(self, user_id: int, title: str, message: str):
        """
        Crea notificación en base de datos para mostrar en la UI
        TODO: Implementar modelo Notification y repositorio
        """
        logger.info(f"[IN-APP MOCK] User: {user_id} | Title: {title}")
