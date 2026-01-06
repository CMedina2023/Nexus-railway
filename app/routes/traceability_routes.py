"""
Rutas de API para Trazabilidad
Responsabilidad única: Definir endpoints para Requerimientos y Trazabilidad (SRP)
"""
from flask import Blueprint, request, jsonify
from app.auth.decorators import login_required
from app.database.repositories.requirement_repository import RequirementRepository
from app.database.repositories.coverage_repository import CoverageRepository
from app.models.requirement import Requirement, RequirementType, RequirementPriority, RequirementStatus
from app.models.traceability_link import TraceabilityLink, TraceabilityLinkType, ArtifactType
from app.models.requirement_coverage import RequirementCoverage, CoverageStatus

traceability_bp = Blueprint('traceability', __name__, url_prefix='/api/traceability')

requirement_repo = RequirementRepository()
coverage_repo = CoverageRepository()

@traceability_bp.route('/requirements', methods=['POST'])
@login_required
def create_requirement():
    """Crea un nuevo requerimiento"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required_fields = ['project_id', 'code', 'title', 'description', 'type', 'priority']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        requirement = Requirement(
            project_id=data['project_id'],
            code=data['code'],
            title=data['title'],
            description=data['description'],
            type=RequirementType(data['type']),
            priority=RequirementPriority(data['priority']),
            status=RequirementStatus(data.get('status', 'DRAFT')),
            source_document_id=data.get('source_document_id')
        )
        
        created_req = requirement_repo.create(requirement)
        
        # Inicializar cobertura vacía
        initial_coverage = RequirementCoverage(requirement_id=created_req.id)
        coverage_repo.upsert_coverage(initial_coverage)
        
        return jsonify(created_req.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@traceability_bp.route('/requirements/<req_id>/coverage', methods=['GET'])
@login_required
def get_requirement_coverage(req_id):
    """Obtiene el estado de cobertura de un requerimiento"""
    try:
        coverage = coverage_repo.get_coverage(req_id)
        if not coverage:
            return jsonify({'error': 'Coverage not found'}), 404
        return jsonify(coverage.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@traceability_bp.route('/link', methods=['POST'])
@login_required
def create_traceability_link():
    """Crea un enlace de trazabilidad entre dos artefactos"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required_fields = ['source_id', 'source_type', 'target_id', 'target_type', 'link_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        link = TraceabilityLink(
            source_id=data['source_id'],
            source_type=ArtifactType(data['source_type']),
            target_id=data['target_id'],
            target_type=ArtifactType(data['target_type']),
            link_type=TraceabilityLinkType(data['link_type']),
            created_by=None, # TODO: Get from session if possible
            meta=data.get('meta', {})
        )
        
        created_link = coverage_repo.create_link(link)
        
        # TODO: Trigger coverage recalculation task/service here
        
        return jsonify(created_link.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@traceability_bp.route('/matrix/<project_id>', methods=['GET'])
@login_required
def get_traceability_matrix(project_id):
    """Obtiene la matriz de trazabilidad para un proyecto"""
    try:
        requirements = requirement_repo.get_by_project(project_id)
        matrix = []
        
        for req in requirements:
            links = coverage_repo.get_links_for_artifact(req.id, ArtifactType.REQUIREMENT)
            coverage = coverage_repo.get_coverage(req.id)
            
            matrix.append({
                'requirement': req.to_dict(),
                'links': [link.to_dict() for link in links],
                'coverage': coverage.to_dict() if coverage else None
            })
            
        return jsonify({
            'project_id': project_id,
            'matrix': matrix
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
