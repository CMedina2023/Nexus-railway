"""
Módulo de formateo para Matrix Backend.
Contiene utilidades para exportar matrices a HTML.
"""
import os
import re
import logging
import html  # AÑADIDO: Para escapar caracteres HTML
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)

def format_test_case_for_html(test_case: dict, case_num: int) -> str:
    """
    Formatea un caso de prueba para HTML.
    
    Args:
        test_case: Diccionario con datos del caso de prueba
        case_num: Número del caso de prueba
        
    Returns:
        str: HTML formateado del caso de prueba
    """
    html_parts = []
    
    # helper para escapar y truncar
    def safe_text(text, length=None):
        if not text:
            return ""
        s = html.escape(str(text))
        if length and len(s) > length:
            return s[:length] + "..."
        return s

    # Título
    titulo = test_case.get('titulo_caso_prueba', test_case.get('titulo', ''))
    if not titulo or str(titulo).strip() == '' or 'por definir' in str(titulo).lower():
        case_id = test_case.get('id_caso_prueba', test_case.get('id', f'TC{case_num:03d}'))
        titulo = f'Caso de Prueba {case_id}'
    
    html_parts.append(f'<div class="story-title">CASO DE PRUEBA #{case_num}: {safe_text(titulo)}</div>')
    
    # ID del caso
    id_caso = test_case.get('id_caso_prueba', test_case.get('id', f'TC{case_num:03d}'))
    html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">ID:</span>
                            <span class="story-item-content"> {safe_text(id_caso)}</span>
                        </div>''')
    
    # Descripción
    descripcion = test_case.get('descripcion', test_case.get('Descripcion', ''))
    if descripcion:
        html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Descripción:</span>
                            <span class="story-item-content"> {safe_text(descripcion, 500)}</span>
                        </div>''')
    
    # Precondiciones
    precondiciones = test_case.get('precondiciones', test_case.get('Precondiciones', ''))
    if precondiciones:
        html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Precondiciones:</span>
                            <span class="story-item-content"> {safe_text(precondiciones, 500)}</span>
                        </div>''')
    
    # Tipo de prueba
    tipo_prueba = test_case.get('tipo_de_prueba', test_case.get('Tipo_de_prueba', 'Funcional'))
    html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Tipo de Prueba:</span>
                            <span class="story-item-content"> {safe_text(tipo_prueba)}</span>
                        </div>''')
    
    # Categoría
    categoria = test_case.get('categoria', test_case.get('Categoria', ''))
    if categoria:
        html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Categoría:</span>
                            <span class="story-item-content"> {safe_text(categoria)}</span>
                        </div>''')
    
    # Pasos
    pasos = test_case.get('pasos', test_case.get('Pasos', []))
    if pasos:
        if isinstance(pasos, str):
            pasos = [pasos]
        pasos_html = []
        for i, paso in enumerate(pasos, 1):
            if paso:
                pasos_html.append(f'''
                                <div class="story-sublist-item">
                                    <span class="bullet">*</span>
                                    <strong>Paso {i}:</strong> {safe_text(paso, 300)}
                                </div>''')
        if pasos_html:
            html_parts.append('''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Pasos:</span>
                            <div class="story-sublist">''')
            html_parts.extend(pasos_html)
            html_parts.append('''
                            </div>
                        </div>''')
    
    # Resultado esperado
    resultado_esperado = test_case.get('resultado_esperado', test_case.get('Resultado_esperado', []))
    if resultado_esperado:
        if isinstance(resultado_esperado, str):
            resultado_esperado = [resultado_esperado]
        resultados_html = []
        for i, resultado in enumerate(resultado_esperado, 1):
            if resultado:
                resultados_html.append(f'''
                                <div class="story-sublist-item">
                                    <span class="bullet">*</span>
                                    <strong>Resultado {i}:</strong> {safe_text(resultado, 300)}
                                </div>''')
        if resultados_html:
            html_parts.append('''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Resultado Esperado:</span>
                            <div class="story-sublist">''')
            html_parts.extend(resultados_html)
            html_parts.append('''
                            </div>
                        </div>''')
    
    # Prioridad
    prioridad = test_case.get('prioridad', test_case.get('Prioridad', 'Medium'))
    html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Prioridad:</span>
                            <span class="story-item-content"> {safe_text(prioridad)}</span>
                        </div>''')
    
    # Historia de usuario (si existe)
    historia = test_case.get('historia_de_usuario', test_case.get('historia', ''))
    if historia:
        html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Historia de Usuario:</span>
                            <span class="story-item-content"> {safe_text(historia, 200)}</span>
                        </div>''')
    
    return '<div class="story-container">\n' + '\n'.join(html_parts) + '\n                    </div>'


def get_basic_html_template():
    """Retorna un template HTML básico si no se encuentra el template completo."""
    return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Casos de Prueba</title>
</head>
<body>
    <h1>Casos de Prueba</h1>
    <!-- CONTENT -->
</body>
</html>'''


def generate_test_cases_html_document(test_cases: List[dict], project_name="Sistema de Gestión de Proyectos", client_name="Cliente"):
    """
    Genera un documento HTML para casos de prueba usando el template story_format_mockup.html.
    
    Args:
        test_cases: Lista de casos de prueba
        project_name: Nombre del proyecto
        client_name: Nombre del cliente
        
    Returns:
        str: Contenido HTML del documento
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    template_paths = [
        os.path.join(root_dir, 'docs', 'mockups', 'story_format_mockup.html'),
        os.path.join(root_dir, 'mockups', 'story_format_mockup.html'),
        'docs/mockups/story_format_mockup.html', # Fallback relative paths
        'mockups/story_format_mockup.html'
    ]
    
    template_path = None
    for path in template_paths:
        if os.path.exists(path):
            template_path = path
            break
    
    if not template_path:
        logger.warning("No se encontró el template HTML, usando template básico")
        html_template = get_basic_html_template()
    else:
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
        except Exception as e:
            logger.error(f"Error al leer template HTML: {e}")
            html_template = get_basic_html_template()
    
    # Generar contenido del índice
    index_items = []
    for i, test_case in enumerate(test_cases, 1):
        titulo = test_case.get('titulo_caso_prueba', test_case.get('titulo', ''))
        if not titulo or titulo.strip() == '' or 'por definir' in titulo.lower():
            case_id = test_case.get('id_caso_prueba', test_case.get('id', f'TC{i:03d}'))
            titulo = f'Caso de Prueba {case_id}'
        page_num = i + 2  # Página 3+ (después de portada e índice)
        index_items.append(f'''
                    <div class="index-item">
                        <span class="index-number">{i}.</span>
                        <span class="index-text">{titulo[:80]}</span>
                        <span class="index-page">{page_num}</span>
                    </div>''')
    
    index_html = '\n'.join(index_items)
    
    # Generar páginas de casos de prueba
    case_pages = []
    for i, test_case in enumerate(test_cases, 1):
        page_num = i + 2
        case_html = format_test_case_for_html(test_case, i)
        case_pages.append(f'''
            <!-- PÁGINA {page_num}: CASO DE PRUEBA {i} -->
            <div class="page">
                <div class="page-header">
                    <div>Documento de Casos de Prueba</div>
                    <div>Versión 1.0</div>
                </div>
                <div style="padding-top: 20px;">
                    {case_html}
                </div>
                <div class="page-footer">
                    <div>Confidencial</div>
                    <div class="page-number">Página {page_num}</div>
                    <div>© {datetime.now().year}</div>
                </div>
            </div>''')
    
    cases_html = '\n'.join(case_pages)
    
    # Portada
    portada_html = f'''
            <!-- PÁGINA 1: PORTADA -->
            <div class="page">
                <div class="cover-page">
                    <div class="cover-title">CASOS DE PRUEBA GENERADOS CON AI</div>
                </div>
            </div>'''
    
    # Índice
    indice_html = f'''
            <!-- PÁGINA 2: ÍNDICE -->
            <div class="page">
                <div class="page-header">
                    <div>Documento de Casos de Prueba</div>
                    <div>Versión 1.0</div>
                </div>
                <div style="padding-top: 20px;">
                    <div class="index-title">ÍNDICE</div>
                    {index_html}
                </div>
                <div class="page-footer">
                    <div>Confidencial</div>
                    <div class="page-number">Página 2</div>
                    <div>© {datetime.now().year}</div>
                </div>
            </div>'''
    
    # Insertar contenido en el template
    content_start_match = re.search(r'<div class="content">', html_template)
    
    html_content = None
    
    if content_start_match:
        start_pos = content_start_match.end()
        remaining = html_template[start_pos:]
        
        div_count = 1
        end_pos = start_pos
        pos = 0
        while pos < len(remaining) and div_count > 0:
            div_open = remaining.find('<div', pos)
            div_close = remaining.find('</div>', pos)
            
            if div_close == -1:
                break
            
            if div_open != -1 and div_open < div_close:
                div_count += 1
                pos = div_open + 4
            else:
                div_count -= 1
                if div_count == 0:
                    end_pos = start_pos + div_close + 6
                    break
                pos = div_close + 6
        
        if div_count == 0:
            before_content = html_template[:content_start_match.end()]
            after_content = html_template[end_pos:]
            html_content = before_content + '\n            ' + portada_html + '\n            ' + indice_html + '\n            ' + cases_html + '\n        ' + after_content
    
    # Fallback
    if html_content is None:
        html_content = html_template
        html_content = re.sub(r'<div class="header"[^>]*>.*?</div>\s*</div>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<!--[^>]*PÁGINA\s*1[^>]*PORTADA[^>]*-->.*?</div>\s*</div>\s*</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<!--[^>]*PÁGINA\s*2[^>]*ÍNDICE[^>]*-->.*?</div>\s*</div>\s*</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<!--[^>]*PÁGINA\s*\d+[^>]*HISTORIA[^>]*-->.*?</div>\s*</div>\s*</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        insert_point = html_content.find('<div class="content">')
        if insert_point != -1:
            insert_pos = insert_point + len('<div class="content">')
            html_content = html_content[:insert_pos] + '\n            ' + portada_html + '\n            ' + indice_html + '\n            ' + cases_html + '\n        ' + html_content[insert_pos:]
        else:
            body_end = html_content.find('</body>')
            if body_end != -1:
                html_content = html_content[:body_end] + '\n        <div class="content">\n            ' + portada_html + '\n            ' + indice_html + '\n            ' + cases_html + '\n        </div>\n    ' + html_content[body_end:]
    
    # Reemplazar texto hardcodeado de "Historias de usuario" por "Casos de Prueba" en el template
    if html_content:
        html_content = html_content.replace('HISTORIAS DE USUARIO GENERADAS CON AI', 'CASOS DE PRUEBA GENERADOS CON AI')
        html_content = html_content.replace('Historias de Usuario', 'Casos de Prueba')
        html_content = html_content.replace('Documento de Requisitos', 'Documento de Casos de Prueba')
        html_content = html_content.replace('Mockup - Formato de Historia de Usuario', 'Documento de Casos de Prueba')
    
    return html_content
