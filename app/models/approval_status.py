"""
Enum para los estados de aprobación del workflow
Responsabilidad única: Definir los estados válidos de un artefacto
"""
from enum import Enum

class ApprovalStatus(str, Enum):
    """
    Estados posibles en el flujo de aprobación
    """
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    REJECTED = "REJECTED"
    SYNCED = "SYNCED"
