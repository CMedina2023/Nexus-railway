from flask import Blueprint, request, jsonify
from app.auth.decorators import login_required, role_required
from app.services.knowledge.document_ingestion_service import DocumentIngestionService
from app.models.project_document import ProjectDocument
from app.database.db import get_db

knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/api/knowledge')

# TODO: Use dependency injection properly
ingestion_service = DocumentIngestionService()

@knowledge_bp.route('/upload', methods=['POST'])
@login_required
def upload_documents():
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files[]')
        project_key = request.form.get('project_key')
        
        if not project_key:
            return jsonify({'error': 'Project Key is required'}), 400

        # Procesar archivos
        processed_docs, errors = ingestion_service.ingest_files(files, project_key)
        
        # Trigger context fusion (async in future)
        if processed_docs:
            ingestion_service.trigger_context_update(project_key, processed_docs)
            
        return jsonify({
            'status': 'success',
            'processed_count': len(processed_docs),
            'documents': [doc.to_dict() for doc in processed_docs],
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/documents/<project_key>', methods=['GET'])
@login_required
def list_documents(project_key):
    # TODO: Move to Repository
    db = get_db()
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM project_documents WHERE project_key = %s ORDER BY upload_date DESC", (project_key,))
        rows = cursor.fetchall()
        
    documents = []
    for row in rows:
        # Simple dict mapping
        doc = dict(row)
        documents.append(doc)
        
    return jsonify(documents)

@knowledge_bp.route('/context/<project_key>', methods=['GET'])
@login_required
def get_context(project_key):
    # TODO: Move to Repository
    db = get_db()
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM project_contexts WHERE project_key = %s ORDER BY version DESC LIMIT 1", (project_key,))
        row = cursor.fetchone()
        
    if row:
        ctx = dict(row)
        # Parse JSON fields if they are strings (SQLite)
        import json
        for field in ['glossary', 'business_rules', 'tech_constraints']:
            if ctx.get(field) and isinstance(ctx[field], str):
                try:
                    ctx[field] = json.loads(ctx[field])
                except:
                    pass
        return jsonify(ctx)
    else:
        return jsonify({'summary': '', 'glossary': {}, 'business_rules': [], 'tech_constraints': []})
