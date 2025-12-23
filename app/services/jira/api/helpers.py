import logging
from datetime import datetime
from typing import Dict
import base64

logger = logging.getLogger(__name__)

def generate_upload_summary_txt(csv_filename: str, results: Dict, project_key: str) -> str:
    """Genera el contenido del archivo TXT con el resumen de la carga"""
    now = datetime.now()
    fecha_hora = now.strftime('%Y-%m-%d %H:%M:%S')
    
    lines = []
    lines.append(f"Procesado: {fecha_hora}")
    lines.append(f"Archivo: {csv_filename}")
    lines.append("--------------------------------------------------")
    
    for idx, created in enumerate(results.get('created', []), start=1):
        summary = created.get('summary', 'Sin resumen')
        key = created.get('key', 'N/A')
        lines.append(f"{idx}. [OK] {summary} --> {key}")
    
    if results.get('failed'):
        lines.append("")
        for failed in results.get('failed', []):
            row_num = failed.get('row', '?')
            error = failed.get('error', 'Error desconocido')
            summary = failed.get('summary', 'Sin resumen')
            lines.append(f"[ERROR] Fila {row_num}: {summary} --> Error: {error}")
    
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append(f"Resumen del procesamiento de {csv_filename}:")
    lines.append(f"  [OK] Exitos: {results.get('success_count', 0)}")
    lines.append(f"  [ERROR] Errores: {results.get('error_count', 0)}")
    lines.append(f"  [OK] Total de registros: {results.get('total', 0)}")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("Query para buscar en Jira")
    lines.append("")
    
    created_keys = [c.get('key') for c in results.get('created', []) if c.get('key')]
    if created_keys:
        sorted_keys = sorted(created_keys)
        first_key = sorted_keys[0]
        last_key = sorted_keys[-1]
        lines.append(f'PROJECT = {project_key} and key <= "{last_key}" and key >= "{first_key}"')
    else:
        lines.append(f'PROJECT = {project_key}')
    
    return '\n'.join(lines)

def generate_stories_upload_summary_txt(results: Dict, project_key: str, total_stories: int) -> str:
    """Genera resumen TXT para carga de historias"""
    now = datetime.now()
    lines = [
        f"Procesado: {now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Tipo: Carga de Historias de Usuario",
        "--------------------------------------------------",
    ]
    for idx, created in enumerate(results.get('created', []), start=1):
        lines.append(f"{idx}. [OK] {created.get('summary', 'Story')} --> {created.get('key', 'N/A')}")
    
    if results.get('failed'):
        lines.append("")
        for f in results.get('failed', []):
            lines.append(f"[ERROR] Story: {f.get('summary', 'Story')} --> Error: {f.get('error', 'N/A')}")
            
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append(f"Resumen:")
    lines.append(f"  [OK] Exitos: {results.get('success_count', 0)}")
    lines.append(f"  [ERROR] Errores: {results.get('error_count', 0)}")
    lines.append(f"  Total: {total_stories}")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("Query para buscar en Jira")
    lines.append("")
    
    created_keys = [c.get('key') for c in results.get('created', []) if c.get('key')]
    if created_keys:
        sorted_keys = sorted(created_keys)
        first_key = sorted_keys[0]
        last_key = sorted_keys[-1]
        lines.append(f'PROJECT = {project_key} and key <= "{last_key}" and key >= "{first_key}"')
    else:
        lines.append(f'PROJECT = {project_key}')
    
    return '\n'.join(lines)

def generate_test_cases_upload_summary_txt(results: Dict, project_key: str, total_cases: int) -> str:
    """Genera resumen TXT para carga de casos de prueba"""
    now = datetime.now()
    lines = [
        f"Procesado: {now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Tipo: Carga de Casos de Prueba",
        "--------------------------------------------------",
    ]
    for idx, created in enumerate(results.get('created', []), start=1):
        lines.append(f"{idx}. [OK] {created.get('summary', 'Test Case')} --> {created.get('key', 'N/A')}")
    
    if results.get('failed'):
        lines.append("")
        for f in results.get('failed', []):
            lines.append(f"[ERROR] Tipo: {f.get('summary', 'Test Case')} --> Error: {f.get('error', 'N/A')}")
            
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append(f"Resumen:")
    lines.append(f"  [OK] Exitos: {results.get('success_count', 0)}")
    lines.append(f"  [ERROR] Errores: {results.get('error_count', 0)}")
    lines.append(f"  Total: {total_cases}")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("Query para buscar en Jira")
    lines.append("")
    
    created_keys = [c.get('key') for c in results.get('created', []) if c.get('key')]
    if created_keys:
        sorted_keys = sorted(created_keys)
        first_key = sorted_keys[0]
        last_key = sorted_keys[-1]
        lines.append(f'PROJECT = {project_key} and key <= "{last_key}" and key >= "{first_key}"')
    else:
        lines.append(f'PROJECT = {project_key}')
    
    return '\n'.join(lines)
