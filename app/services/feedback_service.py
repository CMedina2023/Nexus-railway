"""
Servicio para gestionar el feedback de usuarios
Responsabilidad única: Procesar y enviar feedback a Jira
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.backend.jira.connection import JiraConnection
from app.backend.jira.issue_service import IssueService
from app.backend.jira.project_service import ProjectService
from app.utils.exceptions import ValidationError
from app.core.config import Config

logger = logging.getLogger(__name__)


class FeedbackService:
    """
    Servicio para gestionar feedback de usuarios
    Crea issues (Bug/Task) en Jira con el feedback proporcionado
    """
    
    # Proyecto permitido para feedback
    ALLOWED_PROJECT_KEY = "NA"  # Nexus AI en Jira
    
    def __init__(
        self, 
        jira_connection: JiraConnection,
        project_service: ProjectService,
        issue_service: IssueService
    ):
        """
        Inicializa el servicio de feedback
        
        Args:
            jira_connection: Conexión a Jira
            project_service: Servicio de proyectos (DIP)
            issue_service: Servicio de issues (DIP)
        """
        self._connection = jira_connection
        self._project_service = project_service
        self._issue_service = issue_service
        logger.info("FeedbackService inicializado")
    
    def validate_project(self, project_key: str) -> bool:
        """
        Valida que el proyecto sea el permitido para feedback
        
        Args:
            project_key: Clave del proyecto (ej: "NEXUS")
            
        Returns:
            True si el proyecto es válido
            
        Raises:
            ValidationError: Si el proyecto no es válido
        """
        if not project_key:
            raise ValidationError("Debe seleccionar un proyecto")
        
        # Normalizar a mayúsculas
        project_key = project_key.upper().strip()
        
        if project_key != self.ALLOWED_PROJECT_KEY:
            raise ValidationError(
                f"Solo se permite enviar feedback al proyecto '{self.ALLOWED_PROJECT_KEY}'"
            )
        
        # Verificar que el proyecto existe en Jira
        try:
            projects = self._project_service.get_projects()
            project_exists = any(p.get('key') == project_key for p in projects)
            if not project_exists:
                raise ValidationError(f"El proyecto '{project_key}' no existe en Jira")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error verificando proyecto: {e}")
            raise ValidationError(f"Error al verificar el proyecto: {str(e)}")
        
        logger.info(f"Proyecto validado: {project_key}")
        return True
    
    def validate_feedback_data(
        self,
        issue_type: str,
        summary: str,
        description: str
    ) -> None:
        """
        Valida los datos del feedback
        
        Args:
            issue_type: Tipo de issue ("Bug" o "Task")
            summary: Resumen del feedback
            description: Descripción detallada
            
        Raises:
            ValidationError: Si los datos no son válidos
        """
        # Validar tipo de issue
        valid_types = ["Bug", "Task"]
        if issue_type not in valid_types:
            raise ValidationError(
                f"Tipo de issue inválido. Debe ser uno de: {', '.join(valid_types)}"
            )
        
        # Validar summary
        if not summary or not summary.strip():
            raise ValidationError("El resumen (summary) es obligatorio")
        
        if len(summary) > 255:
            raise ValidationError("El resumen no puede exceder 255 caracteres")
        
        # Validar description
        if not description or not description.strip():
            raise ValidationError("La descripción es obligatoria")
        
        logger.debug("Datos de feedback validados correctamente")
    
    def create_feedback_issue(
        self,
        project_key: str,
        issue_type: str,
        summary: str,
        description: str,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un issue de feedback en Jira
        
        Args:
            project_key: Clave del proyecto (debe ser NEXUS)
            issue_type: Tipo de issue ("Bug" o "Task")
            summary: Resumen del feedback
            description: Descripción detallada (puede incluir HTML)
            user_email: Email del usuario que envía el feedback (opcional)
            
        Returns:
            Dict con información del issue creado:
            {
                'success': True,
                'issue_key': 'NEXUS-123',
                'issue_id': '12345',
                'issue_url': 'https://...',
                'message': 'Feedback enviado exitosamente'
            }
            
        Raises:
            ValidationError: Si los datos no son válidos
            Exception: Si hay error al crear el issue
        """
        try:
            # Validar proyecto
            self.validate_project(project_key)
            
            # Validar datos
            self.validate_feedback_data(issue_type, summary, description)
            
            # Preparar descripción con información del usuario
            full_description = self._prepare_description(
                description, user_email
            )
            
            # Crear issue en Jira
            logger.info(
                f"Creando issue de feedback: {issue_type} - {summary[:50]}..."
            )
            
            # Usar IssueService para crear el issue
            result = self._issue_service.create_issue(
                project_key=project_key.upper(),
                issue_type=issue_type,
                summary=summary.strip(),
                description=full_description
            )
            
            # El resultado puede tener diferentes formatos
            if not result:
                raise Exception("Error al crear el issue en Jira")
            
            # Verificar si fue exitoso
            if isinstance(result, dict):
                if result.get('success') == False:
                    raise Exception(result.get('error', 'Error desconocido al crear issue'))
                
                issue_key = result.get('key')
                issue_id = result.get('id', '')
            else:
                raise Exception("Respuesta inesperada al crear issue")
            
            # Construir URL del issue
            base_url = Config.JIRA_BASE_URL.rstrip('/')
            issue_url = f"{base_url}/browse/{issue_key}"
            
            logger.info(f"Feedback creado exitosamente: {issue_key}")
            
            return {
                'success': True,
                'issue_key': issue_key,
                'issue_id': issue_id,
                'issue_url': issue_url,
                'message': f'Feedback enviado exitosamente como {issue_key}'
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creando feedback: {e}", exc_info=True)
            raise Exception(f"Error al crear el feedback en Jira: {str(e)}")
    
    def _prepare_description(
        self,
        description: str,
        user_email: Optional[str] = None
    ) -> str:
        """
        Prepara la descripción del issue agregando metadata
        
        Args:
            description: Descripción original
            user_email: Email del usuario (opcional)
            
        Returns:
            Descripción formateada con metadata
        """
        # Agregar información del usuario y timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        metadata_lines = [
            "--- INFORMACIÓN DEL FEEDBACK ---",
            f"Fecha: {timestamp}",
        ]
        
        if user_email:
            metadata_lines.append(f"Usuario: {user_email}")
        
        metadata_lines.append("--- DESCRIPCIÓN ---")
        metadata_lines.append("")
        
        metadata = "\n".join(metadata_lines)
        
        # Combinar metadata con descripción
        # Si la descripción tiene HTML, convertir a texto plano básico
        clean_description = self._html_to_jira_markup(description)
        
        return f"{metadata}{clean_description}"
    
    def _html_to_jira_markup(self, html_content: str) -> str:
        """
        Convierte HTML básico a markup de Jira
        
        Args:
            html_content: Contenido HTML
            
        Returns:
            Contenido en formato Jira markup
        """
        # Conversiones básicas de HTML a Jira markup
        content = html_content
        
        # Negrita
        content = content.replace('<strong>', '*').replace('</strong>', '*')
        content = content.replace('<b>', '*').replace('</b>', '*')
        
        # Cursiva
        content = content.replace('<em>', '_').replace('</em>', '_')
        content = content.replace('<i>', '_').replace('</i>', '_')
        
        # Subrayado
        content = content.replace('<u>', '+').replace('</u>', '+')
        
        # Listas
        content = content.replace('<ul>', '').replace('</ul>', '')
        content = content.replace('<ol>', '').replace('</ol>', '')
        content = content.replace('<li>', '* ').replace('</li>', '\n')
        
        # Párrafos y saltos de línea
        content = content.replace('<p>', '').replace('</p>', '\n\n')
        content = content.replace('<br>', '\n').replace('<br/>', '\n')
        content = content.replace('<div>', '').replace('</div>', '\n')
        
        # Enlaces
        import re
        # Convertir <a href="url">texto</a> a [texto|url]
        content = re.sub(
            r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
            r'[\2|\1]',
            content
        )
        
        # Imágenes (mantener como referencia)
        content = re.sub(
            r'<img[^>]*src=["\']([^"\']*)["\'][^>]*>',
            r'![\1]!',
            content
        )
        
        # Limpiar tags HTML restantes
        content = re.sub(r'<[^>]+>', '', content)
        
        # Limpiar espacios múltiples
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content.strip()
    

