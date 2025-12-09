"""
Rutas de Dashboard con filtrado por rol
Responsabilidad única: Endpoints para dashboard con permisos por rol (SRP)
"""
import logging
from flask import Blueprint, request, jsonify
from typing import Optional

from app.auth.decorators import login_required, get_current_user_id
from app.auth.user_service import UserService
from app.database.repositories.user_story_repository import UserStoryRepository
from app.database.repositories.test_case_repository import TestCaseRepository
from app.database.repositories.jira_report_repository import JiraReportRepository
from app.database.repositories.bulk_upload_repository import BulkUploadRepository

logger = logging.getLogger(__name__)

# Crear Blueprint para dashboard
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/stories', methods=['GET'])
@login_required
def get_user_stories():
    """
    Obtiene historias generadas según el rol del usuario
    
    Query params:
        - limit: Límite de resultados (opcional)
    
    ✅ Admin: Ve todas las historias
    ✅ Analista QA y Usuario: Solo ven sus propias historias
    """
    try:
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        limit = request.args.get('limit', type=int)
        story_repo = UserStoryRepository()
        
        if user.role == 'admin':
            # Admin ve todas las historias
            stories = story_repo.get_all(limit=limit)
            logger.info(f"Admin {user.email} consultó todas las historias ({len(stories)} resultados)")
        else:
            # Analista QA y Usuario solo ven sus propias historias
            stories = story_repo.get_by_user_id(user.id, limit=limit)
            logger.info(f"Usuario {user.email} (rol: {user.role}) consultó sus historias ({len(stories)} resultados)")
        
        return jsonify({
            "success": True,
            "stories": [story.to_dict() for story in stories],
            "total": len(stories)
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener historias: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener historias"}), 500


@dashboard_bp.route('/test-cases', methods=['GET'])
@login_required
def get_user_test_cases():
    """
    Obtiene casos de prueba generados según el rol del usuario
    
    Query params:
        - limit: Límite de resultados (opcional)
    
    ✅ Admin: Ve todos los casos de prueba
    ✅ Analista QA y Usuario: Solo ven sus propios casos
    """
    try:
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        limit = request.args.get('limit', type=int)
        test_case_repo = TestCaseRepository()
        
        if user.role == 'admin':
            # Admin ve todos los casos
            test_cases = test_case_repo.get_all(limit=limit)
            logger.info(f"Admin {user.email} consultó todos los casos de prueba ({len(test_cases)} resultados)")
        else:
            # Analista QA y Usuario solo ven sus propios casos
            test_cases = test_case_repo.get_by_user_id(user.id, limit=limit)
            logger.info(f"Usuario {user.email} (rol: {user.role}) consultó sus casos de prueba ({len(test_cases)} resultados)")
        
        return jsonify({
            "success": True,
            "test_cases": [tc.to_dict() for tc in test_cases],
            "total": len(test_cases)
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener casos de prueba: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener casos de prueba"}), 500


@dashboard_bp.route('/reports', methods=['GET'])
@login_required
def get_user_reports():
    """
    Obtiene reportes creados en Jira según el rol del usuario
    
    Query params:
        - limit: Límite de resultados (opcional)
        - report_type: Tipo de reporte para filtrar (opcional)
    
    ✅ Admin: Ve todos los reportes
    ✅ Analista QA y Usuario: Solo ven sus propios reportes
    """
    try:
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        limit = request.args.get('limit', type=int)
        report_repo = JiraReportRepository()
        
        if user.role == 'admin':
            # Admin ve todos los reportes
            reports = report_repo.get_all(limit=limit)
            logger.info(f"Admin {user.email} consultó todos los reportes ({len(reports)} resultados)")
        else:
            # Analista QA y Usuario solo ven sus propios reportes
            reports = report_repo.get_by_user_id(user.id, limit=limit)
            logger.info(f"Usuario {user.email} (rol: {user.role}) consultó sus reportes ({len(reports)} resultados)")
        
        return jsonify({
            "success": True,
            "reports": [report.to_dict() for report in reports],
            "total": len(reports)
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener reportes: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener reportes"}), 500


@dashboard_bp.route('/bulk-uploads', methods=['GET'])
@login_required
def get_user_bulk_uploads():
    """
    Obtiene cargas masivas realizadas según el rol del usuario
    
    Query params:
        - limit: Límite de resultados (opcional)
        - upload_type: Tipo de carga para filtrar (opcional)
    
    ✅ Admin: Ve todas las cargas masivas
    ✅ Analista QA y Usuario: Solo ven sus propias cargas
    """
    try:
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        limit = request.args.get('limit', type=int)
        upload_repo = BulkUploadRepository()
        
        if user.role == 'admin':
            # Admin ve todas las cargas
            uploads = upload_repo.get_all(limit=limit)
            logger.info(f"Admin {user.email} consultó todas las cargas masivas ({len(uploads)} resultados)")
        else:
            # Analista QA y Usuario solo ven sus propias cargas
            uploads = upload_repo.get_by_user_id(user.id, limit=limit)
            logger.info(f"Usuario {user.email} (rol: {user.role}) consultó sus cargas masivas ({len(uploads)} resultados)")
        
        return jsonify({
            "success": True,
            "bulk_uploads": [upload.to_dict() for upload in uploads],
            "total": len(uploads)
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener cargas masivas: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener cargas masivas"}), 500


@dashboard_bp.route('/activity-metrics', methods=['GET'])
@login_required
def get_activity_metrics():
    """
    Obtiene métricas de actividad del usuario según su rol
    
    ✅ Admin: Métricas globales de todos los usuarios
    ✅ Analista QA y Usuario: Solo sus propias métricas
    """
    try:
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        story_repo = UserStoryRepository()
        test_case_repo = TestCaseRepository()
        report_repo = JiraReportRepository()
        upload_repo = BulkUploadRepository()
        
        if user.role == 'admin':
            # Métricas globales para admin
            metrics = {
                "stories_generated": story_repo.count_all(),
                "test_cases_generated": test_case_repo.count_all(),
                "reports_created": report_repo.count_all(),
                "bulk_uploads_performed": upload_repo.count_all(),
                "view_type": "global"
            }
            logger.info(f"Admin {user.email} consultó métricas globales")
        else:
            # Métricas personales para analista_qa y usuario
            metrics = {
                "stories_generated": story_repo.count_by_user(user.id),
                "test_cases_generated": test_case_repo.count_by_user(user.id),
                "reports_created": report_repo.count_by_user(user.id),
                "bulk_uploads_performed": upload_repo.count_by_user(user.id),
                "view_type": "personal"
            }
            logger.info(f"Usuario {user.email} (rol: {user.role}) consultó sus métricas personales")
        
        return jsonify({
            "success": True,
            "metrics": metrics,
            "user_role": user.role
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener métricas de actividad: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener métricas de actividad"}), 500


@dashboard_bp.route('/summary', methods=['GET'])
@login_required
def get_dashboard_summary():
    """
    Obtiene resumen completo del dashboard según el rol del usuario
    
    ✅ Admin: Resumen global de todos los usuarios
    ✅ Analista QA y Usuario: Solo su propio resumen
    """
    try:
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        story_repo = UserStoryRepository()
        test_case_repo = TestCaseRepository()
        report_repo = JiraReportRepository()
        upload_repo = BulkUploadRepository()
        
        if user.role == 'admin':
            # Resumen global para admin
            summary = {
                "total_stories": story_repo.count_all(),
                "total_test_cases": test_case_repo.count_all(),
                "total_reports": report_repo.count_all(),
                "total_bulk_uploads": upload_repo.count_all(),
                "recent_stories": [s.to_dict() for s in story_repo.get_all(limit=5)],
                "recent_test_cases": [tc.to_dict() for tc in test_case_repo.get_all(limit=5)],
                "recent_reports": [r.to_dict() for r in report_repo.get_all(limit=5)],
                "recent_bulk_uploads": [u.to_dict() for u in upload_repo.get_all(limit=5)],
                "view_type": "global"
            }
            logger.info(f"Admin {user.email} consultó resumen global del dashboard")
        else:
            # Resumen personal para analista_qa y usuario
            summary = {
                "total_stories": story_repo.count_by_user(user.id),
                "total_test_cases": test_case_repo.count_by_user(user.id),
                "total_reports": report_repo.count_by_user(user.id),
                "total_bulk_uploads": upload_repo.count_by_user(user.id),
                "recent_stories": [s.to_dict() for s in story_repo.get_by_user_id(user.id, limit=5)],
                "recent_test_cases": [tc.to_dict() for tc in test_case_repo.get_by_user_id(user.id, limit=5)],
                "recent_reports": [r.to_dict() for r in report_repo.get_by_user_id(user.id, limit=5)],
                "recent_bulk_uploads": [u.to_dict() for u in upload_repo.get_by_user_id(user.id, limit=5)],
                "view_type": "personal"
            }
            logger.info(f"Usuario {user.email} (rol: {user.role}) consultó su resumen personal del dashboard")
        
        return jsonify({
            "success": True,
            "summary": summary,
            "user_role": user.role
        }), 200
    
    except Exception as e:
        logger.error(f"Error al obtener resumen del dashboard: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener resumen del dashboard"}), 500


@dashboard_bp.route('/clear-metrics', methods=['DELETE'])
@login_required
def clear_all_metrics():
    """
    Limpia todas las métricas del dashboard (historias, casos de prueba, reportes y cargas masivas)
    
    ✅ Solo Admin puede ejecutar esta acción
    ❌ Analista QA y Usuario NO tienen acceso
    """
    try:
        user_id = get_current_user_id()
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        # Verificar que sea admin
        if user.role != 'admin':
            logger.warning(f"Intento no autorizado de limpiar métricas por usuario {user.email} (rol: {user.role})")
            return jsonify({"error": "No autorizado. Solo Admin puede limpiar métricas"}), 403
        
        # Limpiar todas las tablas de métricas
        story_repo = UserStoryRepository()
        test_case_repo = TestCaseRepository()
        report_repo = JiraReportRepository()
        upload_repo = BulkUploadRepository()
        
        # Contar antes de limpiar para el log
        stories_count = story_repo.count_all()
        test_cases_count = test_case_repo.count_all()
        reports_count = report_repo.count_all()
        uploads_count = upload_repo.count_all()
        
        # Limpiar todas las tablas
        story_repo.delete_all()
        test_case_repo.delete_all()
        report_repo.delete_all()
        upload_repo.delete_all()
        
        logger.info(f"Admin {user.email} limpió todas las métricas: {stories_count} historias, {test_cases_count} casos de prueba, {reports_count} reportes, {uploads_count} cargas masivas")
        
        return jsonify({
            "success": True,
            "message": "Todas las métricas han sido limpiadas exitosamente",
            "deleted": {
                "stories": stories_count,
                "test_cases": test_cases_count,
                "reports": reports_count,
                "bulk_uploads": uploads_count
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error al limpiar métricas: {e}", exc_info=True)
        return jsonify({"error": "Error al limpiar métricas"}), 500



