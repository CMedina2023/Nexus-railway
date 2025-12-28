import os
import re
import logging
from datetime import datetime
from typing import List

from app.backend.story_parser import extract_story_titles

logger = logging.getLogger(__name__)

def format_story_for_html(story_text: str, story_num: int) -> str:
    """
    Formatea una historia para HTML.
    
    Args:
        story_text: Texto de la historia
        story_num: Número de la historia
        
    Returns:
        str: HTML formateado de la historia
    """
    html_parts = []
    
    # Parseo desde el texto completo
    full_text = story_text
    
    # Extraer título y número
    title_pattern = r'HISTORIA\s*#?\s*(\d+)?\s*:\s*([^\n]+)'
    title_match = re.search(title_pattern, story_text, re.IGNORECASE)
    
    if title_match:
        original_num = title_match.group(1)
        title = title_match.group(2).strip()
        
        display_num = original_num if original_num else story_num
        
        # Limpiar el título
        title = re.sub(r'═+', '', title).strip()
        title = re.sub(r'^\*\s*\*\*', '', title).strip()
        title = re.sub(r'\*\*$', '', title).strip()
        for marker in ['COMO:', 'QUIERO:', 'PARA:', 'CRITERIOS', 'REGLAS', 'PRIORIDAD', 'COMPLEJIDAD']:
            if marker in title:
                title = title.split(marker)[0].strip()
                break
        html_parts.append(f'<div class="story-title">HISTORIA #{display_num}: {title}</div>')
    else:
        html_parts.append(f'<div class="story-title">HISTORIA #{story_num}</div>')
    
    # Buscar campos en el texto completo
    como_match = re.search(r'COMO:\s*([^\n]+?)(?:\s+QUIERO:|PARA:|CRITERIOS|REGLAS|PRIORIDAD|COMPLEJIDAD|$)', full_text, re.IGNORECASE)
    quiero_match = re.search(r'QUIERO:\s*([^\n]+?)(?:\s+PARA:|CRITERIOS|REGLAS|PRIORIDAD|COMPLEJIDAD|$)', full_text, re.IGNORECASE)
    para_match = re.search(r'PARA:\s*([^\n]+?)(?:\s+CRITERIOS|REGLAS|PRIORIDAD|COMPLEJIDAD|$)', full_text, re.IGNORECASE)
    prioridad_match = re.search(r'PRIORIDAD:\s*([^\n]+?)(?:\s+COMPLEJIDAD|CRITERIOS|REGLAS|$)', full_text, re.IGNORECASE)
    complejidad_match = re.search(r'COMPLEJIDAD:\s*([^\n]+?)(?:\s+CRITERIOS|REGLAS|$)', full_text, re.IGNORECASE)
    
    # Criterios de Aceptación
    criterios_match = re.search(
        r'CRITERIOS\s+DE\s+ACEPTACI[ÓO]N:\s*(.*?)(?:\s+REGLAS\s+DE\s+NEGOCIO|PRIORIDAD|COMPLEJIDAD|$)',
        full_text,
        re.IGNORECASE | re.DOTALL
    )
    
    # Reglas de Negocio
    reglas_match = re.search(
        r'REGLAS\s+DE\s+NEGOCIO:\s*(.*?)(?:\s+PRIORIDAD|COMPLEJIDAD|CRITERIOS|$)',
        full_text,
        re.IGNORECASE | re.DOTALL
    )
    
    # Procesar campos encontrados
    if como_match or quiero_match or para_match:
        if como_match:
            content = como_match.group(1).strip()
            content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'🔹\s*', '', content)
            if len(content) > 500:
                content = content[:500] + '...'
            html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">COMO:</span>
                            <span class="story-item-content"> {content}</span>
                        </div>''')
        
        if quiero_match:
            content = quiero_match.group(1).strip()
            content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
            content = re.sub(r'🔹\s*', '', content)
            if len(content) > 500:
                content = content[:500] + '...'
            html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">QUIERO:</span>
                            <span class="story-item-content"> {content}</span>
                        </div>''')
        
        if para_match:
            content = para_match.group(1).strip()
            content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
            content = re.sub(r'🔹\s*', '', content)
            if len(content) > 500:
                content = content[:500] + '...'
            html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">PARA:</span>
                            <span class="story-item-content"> {content}</span>
                        </div>''')
        
        if prioridad_match:
            content = prioridad_match.group(1).strip()
            content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
            html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Prioridad:</span>
                            <span class="story-item-content"> {content}</span>
                        </div>''')
        
        if complejidad_match:
            content = complejidad_match.group(1).strip()
            content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
            html_parts.append(f'''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Complejidad:</span>
                            <span class="story-item-content"> {content}</span>
                        </div>''')
        
        # Agregar Criterios de Aceptación si se encuentran
        if criterios_match:
            html_parts.append(_format_criterios_html(criterios_match.group(1).strip()))
        
        # Agregar Reglas de Negocio si se encuentran
        if reglas_match:
            html_parts.append(_format_reglas_html(reglas_match.group(1).strip()))
    
    # Envolver en story-container
    if len(html_parts) > 0:
        return '<div class="story-container">\n' + '\n'.join(html_parts) + '\n                    </div>'
    else:
        return '<div class="story-container">\n<div class="story-title">HISTORIA #{story_num}</div>\n                    </div>'


def _format_criterios_html(criterios_text: str) -> str:
    """Formatea criterios de aceptación para HTML."""
    criterios_text = re.sub(r'🔹\s*', '', criterios_text)
    criterios_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', criterios_text)
    
    # Buscar escenarios
    escenario_principal_match = re.search(
        r'Escenario\s+Principal:\s*(.*?)(?=Escenario\s+Alternativo:|Validaciones:|$)',
        criterios_text,
        re.IGNORECASE | re.DOTALL
    )
    escenario_alternativo_match = re.search(
        r'Escenario\s+Alternativo:\s*(.*?)(?=Validaciones:|$)',
        criterios_text,
        re.IGNORECASE | re.DOTALL
    )
    validaciones_match = re.search(
        r'Validaciones:\s*(.*?)$',
        criterios_text,
        re.IGNORECASE | re.DOTALL
    )
    
    html = '''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Criterios de Aceptación:</span>
                            <div class="story-sublist">'''
    
    if escenario_principal_match:
        escenario_text = escenario_principal_match.group(1).strip()
        escenario_text = re.sub(r'^\s*DADO\s+que\s*', '', escenario_text, flags=re.IGNORECASE)
        escenario_text = re.sub(r'\s+', ' ', escenario_text)
        if len(escenario_text) > 300:
            escenario_text = escenario_text[:300] + '...'
        html += f'''
                                <div class="story-sublist-item">
                                    <span class="bullet">*</span>
                                    <strong>Escenario Principal:</strong> {escenario_text}
                                </div>'''
    
    if escenario_alternativo_match:
        escenario_text = escenario_alternativo_match.group(1).strip()
        escenario_text = re.sub(r'^\s*DADO\s+que\s*', '', escenario_text, flags=re.IGNORECASE)
        escenario_text = re.sub(r'\s+', ' ', escenario_text)
        if len(escenario_text) > 300:
            escenario_text = escenario_text[:300] + '...'
        html += f'''
                                <div class="story-sublist-item">
                                    <span class="bullet">*</span>
                                    <strong>Escenario Alternativo:</strong> {escenario_text}
                                </div>'''
    
    if validaciones_match:
        validaciones_text = validaciones_match.group(1).strip()
        validaciones_text = re.sub(r'^\s*DADO\s+que\s*', '', validaciones_text, flags=re.IGNORECASE)
        validaciones_text = re.sub(r'\s+', ' ', validaciones_text)
        if len(validaciones_text) > 300:
            validaciones_text = validaciones_text[:300] + '...'
        html += f'''
                                <div class="story-sublist-item">
                                    <span class="bullet">*</span>
                                    <strong>Validaciones:</strong> {validaciones_text}
                                </div>'''
    
    html += '''
                            </div>
                        </div>'''
    
    return html


def _format_reglas_html(reglas_text: str) -> str:
    """Formatea reglas de negocio para HTML."""
    reglas_text = re.sub(r'🔹\s*', '', reglas_text)
    reglas_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', reglas_text)
    
    # Dividir por bullets
    reglas_items = re.split(r'•\s*', reglas_text)
    
    html = '''
                        <div class="story-item">
                            <span class="bullet">*</span>
                            <span class="story-item-label">Reglas de Negocio Clave:</span>
                            <div class="story-sublist">'''
    
    for item in reglas_items[:5]:  # Limitar a 5 reglas
        item = item.strip()
        if item:
            html += f'''
                                <div class="story-sublist-item">
                                    <span class="bullet">*</span>
                                    {item[:200]}
                                </div>'''
    
    html += '''
                            </div>
                        </div>'''
    
    return html


def generate_html_document(
    stories: List[str],
    project_name: str = "Sistema de Gestión de Proyectos",
    client_name: str = "Cliente"
) -> str:
    """
    Genera un documento HTML usando el template story_format_mockup.html.
    
    Args:
        stories: Lista de historias de usuario
        project_name: Nombre del proyecto
        client_name: Nombre del cliente
        
    Returns:
        str: Contenido HTML del documento
    """
    # Leer el template HTML
    template_paths = [
        'docs/mockups/story_format_mockup.html',
        'mockups/story_format_mockup.html',
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs', 'mockups', 'story_format_mockup.html'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mockups', 'story_format_mockup.html')
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
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
    
    # Extraer títulos para el índice
    story_titles = extract_story_titles(stories)
    
    # Generar contenido del índice
    index_items = []
    for i, title in enumerate(story_titles, 1):
        page_num = i + 2
        index_items.append(f'''
                    <div class="index-item">
                        <span class="index-number">{i}.</span>
                        <span class="index-text">{title}</span>
                        <span class="index-page">{page_num}</span>
                    </div>''')
    
    index_html = '\n'.join(index_items)
    
    # Generar páginas de historias
    story_pages = []
    for i, story in enumerate(stories, 1):
        page_num = i + 2
        story_html = format_story_for_html(story, i)
        story_pages.append(f'''
            <!-- PÁGINA {page_num}: HISTORIA {i} -->
            <div class="page">
                <div class="page-header">
                    <div>Documento de Requisitos</div>
                    <div>Versión 1.0</div>
                </div>
                <div style="padding-top: 20px;">
                    {story_html}
                </div>
                <div class="page-footer">
                    <div>Confidencial</div>
                    <div class="page-number">Página {page_num}</div>
                    <div>© {datetime.now().year}</div>
                </div>
            </div>''')
    
    stories_html = '\n'.join(story_pages)
    
    # Reemplazar placeholders en el template
    current_date = datetime.now().strftime("%B %Y")
    
    # Portada
    portada_html = f'''
            <!-- PÁGINA 1: PORTADA -->
            <div class="page">
                <div class="cover-page">
                    <div class="cover-title">HISTORIAS DE USUARIO GENERADAS CON AI</div>
                </div>
            </div>'''
    
    # Índice
    indice_html = f'''
            <!-- PÁGINA 2: ÍNDICE -->
            <div class="page">
                <div class="page-header">
                    <div>Documento de Requisitos</div>
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
    
    # Construir HTML final
    html_content = _build_final_html(html_template, portada_html, indice_html, stories_html)
    
    return html_content


def _build_final_html(template: str, portada: str, indice: str, stories: str) -> str:
    """Construye el HTML final insertando el contenido en el template."""
    # Limpiar el template del header del mockup
    html_template_clean = re.sub(r'<div class="header"[^>]*>.*?</div>\s*</div>', '', template, flags=re.DOTALL)
    
    # Encontrar el div content y reemplazar su contenido
    content_start_match = re.search(r'<div class="content">', html_template_clean)
    
    if content_start_match:
        start_pos = content_start_match.end()
        remaining = html_template_clean[start_pos:]
        
        # Contar divs para encontrar el cierre correcto
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
            before_content = html_template_clean[:content_start_match.end()]
            after_content = html_template_clean[end_pos:]
            
            html_content = before_content + '\n            ' + portada + '\n            ' + indice + '\n            ' + stories + '\n        ' + after_content
            
            # Validación
            if 'HISTORIAS DE USUARIO GENERADAS CON AI' in html_content and '<style>' in html_content:
                return html_content
    
    # Fallback: usar template básico
    logger.warning("Usando método de fallback para generar HTML")
    return get_basic_html_template()


def get_basic_html_template() -> str:
    """Retorna un template HTML básico si no se encuentra el template completo."""
    return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Historias de Usuario</title>
</head>
<body>
    <h1>Historias de Usuario</h1>
    <!-- CONTENT -->
</body>
</html>'''


def reconstruct_html_from_template(portada_html: str, indice_html: str, stories_html: str, original_template: str) -> str:
    """
    Reconstruye el HTML desde cero usando el template original como base.
    Se usa como última opción cuando las validaciones fallan.
    """
    # Extraer la parte completa del <head>
    head_match = re.search(r'<head>.*?</head>', original_template, re.DOTALL)
    if head_match:
        head_content = head_match.group(0)
    else:
        head_content = '''<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historias de Usuario</title>
    </head>'''
    
    # Construir HTML completo
    container_match = re.search(r'<div class="container">', original_template)
    if container_match:
        html = original_template[:container_match.start()]
        html += f'''    <div class="container">
        <div class="content">
            {portada_html}
            {indice_html}
            {stories_html}
        </div>
    </div>
</body>
</html>'''
    else:
        html = f'''<!DOCTYPE html>
<html lang="es">
{head_content}
<body>
    <div class="container">
        <div class="content">
            {portada_html}
            {indice_html}
            {stories_html}
        </div>
    </div>
</body>
</html>'''
    
    return html
