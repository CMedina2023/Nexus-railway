"""
Rutas de Dashboard con filtrado por rol
Responsabilidad única: Endpoints para dashboard con permisos por rol (SRP)
"""
import logging
from flask import Blueprint, request, jsonify
from typing import Optional, Any

from app.auth.decorators import filter_by_role
from app.auth.dashboard_filter_service import DashboardFilterService
from app.database.repositories.user_story_repository import UserStoryRepository
from app.database.repositories.test_case_repository import TestCaseRepository
from app.database.repositories.jira_report_repository import JiraReportRepository
from app.database.repositories.bulk_upload_repository import BulkUploadRepository

logger = logging.getLogger(__name__)

# Crear Blueprint para dashboard
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/metrics', methods=['GET'])
@filter_by_role
def get_dashboard_metrics(user: Any):
    """
    Obtiene métricas complejas del dashboard (OCP)
    ✅ Admin: Ve métricas globales
    ✅ Usuario: Ve métricas personales
    """
    try:
        repos = {
            'story': UserStoryRepository(),
            'test_case': TestCaseRepository(),
            'report': JiraReportRepository(),
            'upload': BulkUploadRepository()
        }
        
        metrics_data = DashboardFilterService.get_complex_metrics(user, repos)
        return jsonify(metrics_data), 200
        
    except Exception as e:
        logger.error(f"Error al obtener métricas del dashboard: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener métricas"}), 500


@dashboard_bp.route('/stories', methods=['GET'])
@filter_by_role
def get_user_stories(user: Any):
    """
    Obtiene historias generadas según el rol del usuario (OCP)
    """
    try:
        limit = request.args.get('limit', type=int)
        story_repo = UserStoryRepository()
        
        stories = DashboardFilterService.get_filtered_items(user, story_repo, limit=limit)
        
        return jsonify({
            "success": True,
            "stories": [story.to_dict() for story in stories],
            "total": len(stories)
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener historias: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener historias"}), 500


@dashboard_bp.route('/test-cases', methods=['GET'])
@filter_by_role
def get_user_test_cases(user: Any):
    """
    Obtiene casos de prueba generados según el rol del usuario (OCP)
    """
    try:
        limit = request.args.get('limit', type=int)
        test_case_repo = TestCaseRepository()
        
        test_cases = DashboardFilterService.get_filtered_items(user, test_case_repo, limit=limit)
        
        return jsonify({
            "success": True,
            "test_cases": [tc.to_dict() for tc in test_cases],
            "total": len(test_cases)
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener casos de prueba: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener casos de prueba"}), 500


@dashboard_bp.route('/reports', methods=['GET'])
@filter_by_role
def get_user_reports(user: Any):
    """
    Obtiene reportes creados en Jira según el rol del usuario (OCP)
    """
    try:
        limit = request.args.get('limit', type=int)
        report_repo = JiraReportRepository()
        
        reports = DashboardFilterService.get_filtered_items(user, report_repo, limit=limit)
        
        return jsonify({
            "success": True,
            "reports": [report.to_dict() for report in reports],
            "total": len(reports)
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener reportes: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener reportes"}), 500


@dashboard_bp.route('/bulk-uploads', methods=['GET'])
@filter_by_role
def get_user_bulk_uploads(user: Any):
    """
    Obtiene cargas masivas realizadas según el rol del usuario (OCP)
    """
    try:
        limit = request.args.get('limit', type=int)
        upload_repo = BulkUploadRepository()
        
        uploads = DashboardFilterService.get_filtered_items(user, upload_repo, limit=limit)
        
        return jsonify({
            "success": True,
            "bulk_uploads": [upload.to_dict() for upload in uploads],
            "total": len(uploads)
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener cargas masivas: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener cargas masivas"}), 500


@dashboard_bp.route('/activity-metrics', methods=['GET'])
@filter_by_role
def get_activity_metrics(user: Any):
    """
    Obtiene métricas de actividad del usuario según su rol (SRP)
    """
    try:
        repos = {
            'story': UserStoryRepository(),
            'test_case': TestCaseRepository(),
            'report': JiraReportRepository(),
            'upload': BulkUploadRepository()
        }
        
        metrics = DashboardFilterService.get_activity_metrics(user, repos)
        
        return jsonify({
            "success": True,
            "metrics": metrics,
            "user_role": user.role
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener métricas de actividad: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener métricas de actividad"}), 500


@dashboard_bp.route('/summary', methods=['GET'])
@filter_by_role
def get_dashboard_summary(user: Any):
    """
    Obtiene resumen completo del dashboard según el rol del usuario (SRP)
    """
    try:
        repos = {
            'story': UserStoryRepository(),
            'test_case': TestCaseRepository(),
            'report': JiraReportRepository(),
            'upload': BulkUploadRepository()
        }
        
        summary = DashboardFilterService.get_dashboard_summary(user, repos)
        
        return jsonify({
            "success": True,
            "summary": summary,
            "user_role": user.role
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener resumen del dashboard: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener resumen del dashboard"}), 500


@dashboard_bp.route('/clear-metrics', methods=['DELETE'])
@filter_by_role
def clear_all_metrics(user: Any):
    """
    Limpia todas las métricas del dashboard (Solo Admin)
    """
    try:
        # Verificar que sea admin
        if user.role != 'admin':
            logger.warning(f"Intento no autorizado de limpiar métricas por usuario {user.email} (rol: {user.role})")
            return jsonify({"error": "No autorizado. Solo Admin puede limpiar métricas"}), 403
        
        story_repo = UserStoryRepository()
        test_case_repo = TestCaseRepository()
        report_repo = JiraReportRepository()
        upload_repo = BulkUploadRepository()
        
        # Contar antes de limpiar para el log
        counts = {
            "stories": story_repo.count_all(),
            "test_cases": test_case_repo.count_all(),
            "reports": report_repo.count_all(),
            "uploads": upload_repo.count_all()
        }
        
        # Limpiar todas las tablas
        story_repo.delete_all()
        test_case_repo.delete_all()
        report_repo.delete_all()
        upload_repo.delete_all()
        
        logger.info(f"Admin {user.email} limpió todas las métricas: {counts}")
        
        return jsonify({
            "success": True,
            "message": "Todas las métricas han sido limpiadas exitosamente",
            "deleted": counts
        }), 200
    
    except Exception as e:
        logger.error(f"Error al limpiar métricas: {e}", exc_info=True)
        return jsonify({"error": "Error al limpiar métricas"}), 500



