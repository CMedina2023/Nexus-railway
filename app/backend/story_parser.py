"""
Módulo de Parsing de Historias de Usuario.

Este módulo contiene todas las funciones relacionadas con el parsing
y extracción de datos de historias de usuario.
"""

import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def extract_story_titles(stories: List[str]) -> List[str]:
    """
    Extrae los títulos de las historias para el índice.
    
    Args:
        stories: Lista de historias de usuario
        
    Returns:
        List[str]: Lista de títulos extraídos
    """
    titles = []
    for story in stories:
        # Buscar título después de "HISTORIA #X:" pero solo hasta encontrar COMO, QUIERO, PARA, etc.
        match = re.search(
            r'HISTORIA\s*#?\s*(?:\d+)?\s*:\s*([^\n]+)',
            story,
            re.IGNORECASE
        )
        if match:
            title = match.group(1).strip()
            # Limpiar el título
            title = re.sub(r'═+', '', title).strip()
            title = re.sub(r'^\*\s*\*\*', '', title).strip()
            title = re.sub(r'\*\*$', '', title).strip()
            # Si el título contiene marcadores, cortar ahí
            for marker in ['COMO:', 'QUIERO:', 'PARA:', 'CRITERIOS', 'REGLAS', 'PRIORIDAD', 'COMPLEJIDAD']:
                if marker in title:
                    title = title.split(marker)[0].strip()
                    break
            titles.append(title[:80])
        else:
            # Si no encontramos, buscar en las primeras líneas
            lines = story.split('\n')
            for line in lines[:10]:
                cleaned = line.strip()
                if cleaned and not cleaned.startswith(('═', '╔', '╚')) and not cleaned.startswith('HISTORIA') and len(cleaned) > 10:
                    if not cleaned.upper().startswith(('COMO:', 'QUIERO:', 'PARA:', 'CRITERIOS', 'REGLAS', 'PRIORIDAD', 'COMPLEJIDAD')):
                        # Limpiar también aquí para evitar campos
                        cleaned_title = cleaned
                        for marker in ['COMO:', 'QUIERO:', 'PARA:', 'CRITERIOS', 'REGLAS', 'PRIORIDAD', 'COMPLEJIDAD']:
                            if marker in cleaned_title.upper():
                                cleaned_title = cleaned_title.split(marker)[0].strip()
                                break
                        titles.append(cleaned_title[:80])
                        break
            else:
                # Si no encontramos, usar número
                match = re.search(r'HISTORIA\s*#\s*(\d+)', story, re.IGNORECASE)
                if match:
                    titles.append(f"Historia #{match.group(1)}")
                else:
                    titles.append(f"Historia {len(titles) + 1}")
    return titles


def parse_story_data(story_text: str) -> Dict:
    """
    Parsea una historia de usuario y extrae los datos necesarios para CSV de Jira.
    
    Args:
        story_text: Texto completo de la historia
        
    Returns:
        dict: Diccionario con summary, description, priority, complexity
    """
    data = {
        'summary': '',
        'description': '',
        'priority': 'Medium',
        'complexity': ''
    }
    
    # Extraer título (Summary)
    title_pattern = r'HISTORIA\s*#?\s*(?:\d+)?\s*:\s*([^\n]+)'
    title_match = re.search(title_pattern, story_text, re.IGNORECASE)
    if title_match:
        data['summary'] = title_match.group(1).strip()
        # Limpiar el título
        data['summary'] = re.sub(r'═+', '', data['summary']).strip()
        data['summary'] = re.sub(r'^\*\s*\*\*', '', data['summary']).strip()
        data['summary'] = re.sub(r'\*\*$', '', data['summary']).strip()
        # Remover contenido después del título
        for marker in ['COMO:', 'QUIERO:', 'PARA:', 'CRITERIOS', 'REGLAS', 'PRIORIDAD', 'COMPLEJIDAD']:
            if marker in data['summary']:
                data['summary'] = data['summary'].split(marker)[0].strip()
                break
    else:
        # Fallback: buscar título en las primeras líneas
        lines = story_text.split('\n')
        for line in lines[:5]:
            line_clean = line.strip()
            if line_clean and not line_clean.startswith(('*', '═', '╔', '╚', 'COMO', 'QUIERO', 'PARA', 'CRITERIOS', 'REGLAS', 'PRIORIDAD', 'COMPLEJIDAD')):
                if len(line_clean) > 10 and len(line_clean) < 200:
                    data['summary'] = line_clean[:200]
                    break
    
    # Extraer campos individuales
    como_match = re.search(r'(?:\*\s*)?\*\*COMO:\*\*\s*([^\n]+?)(?:\s+QUIERO:|PARA:|CRITERIOS|REGLAS|PRIORIDAD|COMPLEJIDAD|CONTINÚA|$)', story_text, re.IGNORECASE)
    if not como_match:
        como_match = re.search(r'COMO:\s*([^\n]+?)(?:\s+QUIERO:|PARA:|CRITERIOS|REGLAS|PRIORIDAD|COMPLEJIDAD|CONTINÚA|$)', story_text, re.IGNORECASE)
    
    quiero_match = re.search(r'(?:\*\s*)?\*\*QUIERO:\*\*\s*([^\n]+?)(?:\s+PARA:|CRITERIOS|REGLAS|PRIORIDAD|COMPLEJIDAD|CONTINÚA|$)', story_text, re.IGNORECASE)
    if not quiero_match:
        quiero_match = re.search(r'QUIERO:\s*([^\n]+?)(?:\s+PARA:|CRITERIOS|REGLAS|PRIORIDAD|COMPLEJIDAD|CONTINÚA|$)', story_text, re.IGNORECASE)
    
    para_match = re.search(r'(?:\*\s*)?\*\*PARA:\*\*\s*([^\n]+?)(?:\s+CRITERIOS|REGLAS|PRIORIDAD|COMPLEJIDAD|CONTINÚA|$)', story_text, re.IGNORECASE)
    if not para_match:
        para_match = re.search(r'PARA:\s*([^\n]+?)(?:\s+CRITERIOS|REGLAS|PRIORIDAD|COMPLEJIDAD|CONTINÚA|$)', story_text, re.IGNORECASE)
    
    prioridad_match = re.search(r'(?:\*\s*)?\*\*Prioridad:\*\*\s*([^\n]+)', story_text, re.IGNORECASE)
    if not prioridad_match:
        prioridad_match = re.search(r'PRIORIDAD:\s*([^\n]+)', story_text, re.IGNORECASE)
    
    complejidad_match = re.search(r'(?:\*\s*)?\*\*Complejidad:\*\*\s*([^\n]+)', story_text, re.IGNORECASE)
    if not complejidad_match:
        complejidad_match = re.search(r'COMPLEJIDAD:\s*([^\n]+)', story_text, re.IGNORECASE)
    
    # Construir descripción
    description_parts = []
    
    # 1. COMO
    if como_match:
        como_text = como_match.group(1).strip()
        como_text = re.sub(r'CONTINÚA\s+EN\s+EL\s+SIGUIENTE\s+LOTE.*$', '', como_text, flags=re.IGNORECASE)
        como_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', como_text)
        como_text = re.sub(r'🔹\s*', '', como_text)
        como_text = re.sub(r'\s+', ' ', como_text).strip()
        if como_text:
            description_parts.append(f"* COMO: {como_text}")
    
    # 2. QUIERO
    if quiero_match:
        quiero_text = quiero_match.group(1).strip()
        quiero_text = re.sub(r'CONTINÚA\s+EN\s+EL\s+SIGUIENTE\s+LOTE.*$', '', quiero_text, flags=re.IGNORECASE)
        quiero_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', quiero_text)
        quiero_text = re.sub(r'🔹\s*', '', quiero_text)
        quiero_text = re.sub(r'\s+', ' ', quiero_text).strip()
        if quiero_text:
            description_parts.append(f"* QUIERO: {quiero_text}")
    
    # 3. PARA
    if para_match:
        para_text = para_match.group(1).strip()
        para_text = re.sub(r'CONTINÚA\s+EN\s+EL\s+SIGUIENTE\s+LOTE.*$', '', para_text, flags=re.IGNORECASE)
        para_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', para_text)
        para_text = re.sub(r'🔹\s*', '', para_text)
        para_text = re.sub(r'\s+', ' ', para_text).strip()
        if para_text:
            description_parts.append(f"* PARA: {para_text}")
    
    # 4. Criterios de Aceptación
    criterios_match = re.search(
        r'CRITERIOS\s+DE\s+ACEPTACI[ÓO]N:\s*(.*?)(?:\s+REGLAS\s+DE\s+NEGOCIO|PRIORIDAD|COMPLEJIDAD|CONTINÚA|$)',
        story_text,
        re.IGNORECASE | re.DOTALL
    )
    if criterios_match:
        criterios_text = criterios_match.group(1).strip()
        criterios_text = re.sub(r'CONTINÚA\s+EN\s+EL\s+SIGUIENTE\s+LOTE.*$', '', criterios_text, flags=re.IGNORECASE | re.DOTALL)
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
        
        if escenario_principal_match or escenario_alternativo_match or validaciones_match:
            description_parts.append("* Criterios de Aceptación:")
            
            if escenario_principal_match:
                escenario_text = escenario_principal_match.group(1).strip()
                escenario_text = re.sub(r'^\s*DADO\s+que\s*', '', escenario_text, flags=re.IGNORECASE | re.MULTILINE)
                escenario_text = re.sub(r'\s+CUANDO\s+', ' CUANDO ', escenario_text, flags=re.IGNORECASE)
                escenario_text = re.sub(r'\s+ENTONCES\s+', ' ENTONCES ', escenario_text, flags=re.IGNORECASE)
                escenario_text = re.sub(r'\s+', ' ', escenario_text).strip()
                if escenario_text:
                    description_parts.append(f"  • Escenario Principal: {escenario_text}")
            
            if escenario_alternativo_match:
                escenario_text = escenario_alternativo_match.group(1).strip()
                escenario_text = re.sub(r'^\s*DADO\s+que\s*', '', escenario_text, flags=re.IGNORECASE | re.MULTILINE)
                escenario_text = re.sub(r'\s+CUANDO\s+', ' CUANDO ', escenario_text, flags=re.IGNORECASE)
                escenario_text = re.sub(r'\s+ENTONCES\s+', ' ENTONCES ', escenario_text, flags=re.IGNORECASE)
                escenario_text = re.sub(r'\s+', ' ', escenario_text).strip()
                if escenario_text:
                    description_parts.append(f"  • Escenario Alternativo: {escenario_text}")
            
            if validaciones_match:
                validaciones_text = validaciones_match.group(1).strip()
                validaciones_text = re.sub(r'^\s*DADO\s+que\s*', '', validaciones_text, flags=re.IGNORECASE | re.MULTILINE)
                validaciones_text = re.sub(r'\s+CUANDO\s+', ' CUANDO ', validaciones_text, flags=re.IGNORECASE)
                validaciones_text = re.sub(r'\s+ENTONCES\s+', ' ENTONCES ', validaciones_text, flags=re.IGNORECASE)
                validaciones_text = re.sub(r'\s+', ' ', validaciones_text).strip()
                if validaciones_text:
                    description_parts.append(f"  • Validaciones: {validaciones_text}")
    
    # 5. Prioridad
    if prioridad_match:
        priority_text = prioridad_match.group(1).strip()
        priority_text = re.sub(r'CONTINÚA\s+EN\s+EL\s+SIGUIENTE\s+LOTE.*$', '', priority_text, flags=re.IGNORECASE)
        priority_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', priority_text)
        priority_clean = re.sub(r'\s+', ' ', priority_clean).strip()
        priority_lower = priority_clean.lower()
        if 'alta' in priority_lower or 'high' in priority_lower:
            data['priority'] = 'High'
            description_parts.append(f"* Prioridad: Alta")
        elif 'media' in priority_lower or 'medium' in priority_lower:
            data['priority'] = 'Medium'
            description_parts.append(f"* Prioridad: Media")
        elif 'baja' in priority_lower or 'low' in priority_lower:
            data['priority'] = 'Low'
            description_parts.append(f"* Prioridad: Baja")
        else:
            data['priority'] = 'Medium'
            if priority_clean:
                description_parts.append(f"* Prioridad: {priority_clean}")
    else:
        data['priority'] = 'Medium'
    
    # 6. Complejidad
    if complejidad_match:
        complexity_text = complejidad_match.group(1).strip()
        complexity_text = re.sub(r'CONTINÚA\s+EN\s+EL\s+SIGUIENTE\s+LOTE.*$', '', complexity_text, flags=re.IGNORECASE)
        data['complexity'] = complexity_text
        complexity_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', data['complexity'])
        complexity_clean = re.sub(r'\s+', ' ', complexity_clean).strip()
        if complexity_clean:
            description_parts.append(f"* Complejidad: {complexity_clean}")
    
    # 7. Reglas de Negocio
    reglas_match = re.search(
        r'REGLAS\s+DE\s+NEGOCIO(?:\s+CLAVE)?:\s*(.*?)(?:\s+PRIORIDAD|COMPLEJIDAD|CONTINÚA|$)',
        story_text,
        re.IGNORECASE | re.DOTALL
    )
    if reglas_match:
        reglas_text = reglas_match.group(1).strip()
        reglas_text = re.sub(r'CONTINÚA\s+EN\s+EL\s+SIGUIENTE\s+LOTE.*$', '', reglas_text, flags=re.IGNORECASE | re.DOTALL)
        reglas_items = re.findall(r'[•\*]\s*([^\n•\*]+)', reglas_text)
        if not reglas_items:
            reglas_items = re.findall(r'^\s*[•\*]\s+(.+)$', reglas_text, re.MULTILINE)
        if reglas_items:
            description_parts.append("* Reglas de Negocio Clave:")
            for item in reglas_items[:5]:
                item_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', item.strip())
                item_clean = re.sub(r'\s+', ' ', item_clean).strip()
                if item_clean:
                    description_parts.append(f"  • {item_clean}")
    
    data['description'] = '\n'.join(description_parts)
    
    return data


def parse_stories_to_dict(stories: List[str]) -> List[Dict]:
    """
    Convierte una lista de historias (strings) a una lista de diccionarios estructurados.
    
    Args:
        stories: Lista de historias como strings
        
    Returns:
        List[Dict]: Lista de diccionarios con estructura definida
    """
    parsed_stories = []
    for idx, story_text in enumerate(stories, 1):
        data = parse_story_data(story_text)
        parsed_stories.append({
            'index': idx,
            'summary': data.get('summary', 'Sin título'),
            'description': data.get('description', ''),
            'issuetype': 'Story',
            'priority': data.get('priority', 'Medium'),
            'raw_text': story_text
        })
    return parsed_stories
