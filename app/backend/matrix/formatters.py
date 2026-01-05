"""
Módulo de formateo para Matrix Backend.
Contiene utilidades para exportar matrices a HTML usando Jinja2.
"""
import os
import logging
from datetime import datetime
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

# Configuración de templates
# Se asume que templates está en la raiz del proyecto: root/templates
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
TEMPLATE_DIR = os.path.join(ROOT_DIR, 'templates')

def _prepare_test_case_data(test_case: Dict[str, Any], case_num: int) -> Dict[str, Any]:
    """
    Normaliza y prepara los datos de un caso de prueba para la plantilla.
    
    Args:
        test_case: Diccionario con datos crudos del caso de prueba
        case_num: Número secuencial del caso de prueba
        
    Returns:
        Diccionario normalizado para uso en template
    """
    # Título - Lógica de fallback
    titulo = test_case.get('titulo_caso_prueba', test_case.get('titulo', ''))
    if not titulo or str(titulo).strip() == '' or 'por definir' in str(titulo).lower():
        case_id = test_case.get('id_caso_prueba', test_case.get('id', f'TC{case_num:03d}'))
        titulo = f'Caso de Prueba {case_id}'
    
    # ID
    id_caso = test_case.get('id_caso_prueba', test_case.get('id', f'TC{case_num:03d}'))

    # Pasos (normalizar a lista y filtrar vacíos)
    pasos = test_case.get('pasos', test_case.get('Pasos', []))
    if isinstance(pasos, str):
        pasos = [pasos]
    if isinstance(pasos, list):
        pasos = [p for p in pasos if p]
    else:
        pasos = []

    # Resultado esperado (normalizar a lista y filtrar vacíos)
    resultado_esperado = test_case.get('resultado_esperado', test_case.get('Resultado_esperado', []))
    if isinstance(resultado_esperado, str):
        resultado_esperado = [resultado_esperado]
    if isinstance(resultado_esperado, list):
        resultado_esperado = [r for r in resultado_esperado if r]
    else:
        resultado_esperado = []

    return {
        'titulo': titulo,
        'id': id_caso,
        'descripcion': test_case.get('descripcion', test_case.get('Descripcion', '')),
        'precondiciones': test_case.get('precondiciones', test_case.get('Precondiciones', '')),
        'tipo_prueba': test_case.get('tipo_de_prueba', test_case.get('Tipo_de_prueba', 'Funcional')),
        'categoria': test_case.get('categoria', test_case.get('Categoria', '')),
        'pasos': pasos,
        'resultado_esperado': resultado_esperado,
        'prioridad': test_case.get('prioridad', test_case.get('Prioridad', 'Medium')),
        'historia': test_case.get('historia_de_usuario', test_case.get('historia', ''))
    }

def generate_test_cases_html_document(test_cases: List[dict], project_name="Sistema de Gestión de Proyectos", client_name="Cliente") -> str:
    """
    Genera un documento HTML para casos de prueba usando template Jinja2.
    
    Args:
        test_cases: Lista de casos de prueba
        project_name: Nombre del proyecto
        client_name: Nombre del cliente
        
    Returns:
        str: Contenido HTML del documento
    """
    try:
        if not os.path.exists(TEMPLATE_DIR):
            logger.error(f"Directorio de templates no encontrado: {TEMPLATE_DIR}")
            return "<html><body><h1>Error: Directorio de templates no encontrado</h1></body></html>"

        # Configurar entorno Jinja2
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        template = env.get_template('matrix/test_cases_document.html')
        
        # Preparar datos
        prepared_cases = [
            _prepare_test_case_data(case, i) 
            for i, case in enumerate(test_cases, 1)
        ]
        
        # Renderizar
        return template.render(
            test_cases=prepared_cases,
            project_name=project_name,
            client_name=client_name,
            current_year=datetime.now().year
        )
        
    except Exception as e:
        logger.error(f"Error generando documento HTML: {e}")
        return f"<html><body><h1>Error generando documento</h1><p>{str(e)}</p></body></html>"

