"""
Excepciones relacionadas con el workflow de aprobación
Responsabilidad única: Definir errores específicos de lógica de negocio de workflows
"""
from app.utils.exceptions import NexusAIException

class WorkflowError(NexusAIException):
    """Error base para workflows"""
    pass

class InvalidTransitionError(WorkflowError):
    """La transición de estado solicitada no es válida"""
    pass

class WorkflowPermissionError(WorkflowError):
    """El usuario no tiene permisos para ejecutar la acción en el workflow"""
    pass

class ArtifactNotFoundError(WorkflowError):
    """El artefacto asociado al workflow no existe"""
    pass
