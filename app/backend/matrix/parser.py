"""
Módulo de parseo para Matrix Backend.
Contiene utilidades para limpiar texto, extraer historias y parsear casos de prueba.
"""
import json
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def clean_json_response(response_text):
    """Limpia y extrae JSON de la respuesta del modelo."""
    if not response_text:
        return None
    try:
        data = json.loads(response_text)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'matrix' in data:
            return data['matrix']
        elif isinstance(data, dict) and 'test_cases' in data:
            return data['test_cases']
    except json.JSONDecodeError:
        pass
    json_patterns = [
        r'```json\s*\n([\s\S]*?)\n```',
        r'```\s*\n([\s\S]*?)\n```',
        r'\[[\s\S]*\]'
    ]
    for pattern in json_patterns:
        match = re.search(pattern, response_text, re.MULTILINE)
        if match:
            json_str = match.group(1).strip()
            try:
                data = json.loads(json_str)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'matrix' in data:
                    return data['matrix']
            except json.JSONDecodeError:
                continue
    try:
        start = response_text.find('[')
        end = response_text.rfind(']')
        if start != -1 and end != -1 and end > start:
            json_str = response_text[start:end + 1]
            data = json.loads(json_str)
            if isinstance(data, list):
                return data
    except json.JSONDecodeError:
        pass
    return None

def clean_text(text):
    """Limpia el texto eliminando caracteres problemáticos."""
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    return text.strip()

def extract_stories_from_text(text):
    """Extrae nombres de historias de usuario del texto del documento."""
    pattern = r'HISTORIA #\d+:[^\n]+'
    matches = re.findall(pattern, text, re.MULTILINE)
    return matches if matches else ['Historia de usuario general']

def parse_test_case_data(test_case: dict) -> dict:
    """
    Parsea un caso de prueba y extrae los datos necesarios para CSV de Jira.
    
    Args:
        test_case: Diccionario con datos del caso de prueba
        
    Returns:
        dict: Diccionario con summary, description, priority, y otros campos
    """
    # Extraer summary (título) - mejorar manejo de valores por defecto
    summary = test_case.get('titulo_caso_prueba', '')
    
    # Si está vacío o es el valor por defecto, usar ID o descripción
    if not summary or summary.strip() == '' or 'por definir' in summary.lower() or 'título descriptivo' in summary.lower():
        # Intentar usar ID del caso
        case_id = test_case.get('id_caso_prueba', '')
        if case_id:
            summary = f"Caso de prueba {case_id}"
        else:
            # Intentar usar descripción como fallback
            descripcion = test_case.get('Descripcion', '')
            if descripcion and descripcion.strip() and 'por definir' not in descripcion.lower():
                # Usar primeros 50 caracteres de la descripción
                summary = descripcion[:50].strip()
                if len(descripcion) > 50:
                    summary += '...'
            else:
                summary = 'Caso de prueba sin título'
    
    # Limpiar el summary de caracteres problemáticos
    summary = summary.strip()
    
    # Log para depuración si el summary sigue siendo problemático
    if not summary or len(summary) < 3:
        logger.warning(f"Summary muy corto o vacío para caso {test_case.get('id_caso_prueba', 'N/A')}: '{summary}'")
        summary = f"Caso de prueba {test_case.get('id_caso_prueba', 'TC')}"

    
    # Construir descripción completa
    description_parts = []
    
    # Descripción
    descripcion = test_case.get('Descripcion', '')
    if descripcion:
        description_parts.append(f"* Descripción: {descripcion}")
    
    # Precondiciones
    precondiciones = test_case.get('Precondiciones', '')
    if precondiciones:
        description_parts.append(f"* Precondiciones: {precondiciones}")
    
    # Pasos
    pasos = test_case.get('Pasos', [])
    if pasos:
        if isinstance(pasos, str):
            pasos = [pasos]
        pasos_text = '\n'.join([f"  {i+1}. {paso}" for i, paso in enumerate(pasos) if paso])
        if pasos_text:
            description_parts.append(f"* Pasos:\n{pasos_text}")
    
    # Resultado esperado
    resultado_esperado = test_case.get('Resultado_esperado', [])
    if resultado_esperado:
        if isinstance(resultado_esperado, str):
            resultado_esperado = [resultado_esperado]
        resultado_text = '\n'.join([f"  • {res}" for res in resultado_esperado if res])
        if resultado_text:
            description_parts.append(f"* Resultado Esperado:\n{resultado_text}")
    
    # Tipo de prueba
    tipo_prueba = test_case.get('Tipo_de_prueba', 'Funcional')
    if tipo_prueba:
        description_parts.append(f"* Tipo de Prueba: {tipo_prueba}")
    
    # Categoría
    categoria = test_case.get('Categoria', '')
    if categoria:
        description_parts.append(f"* Categoría: {categoria}")
    
    # Historia de usuario (si existe)
    historia = test_case.get('historia_de_usuario', '')
    if historia:
        description_parts.append(f"* Historia de Usuario: {historia}")
    
    description = '\n'.join(description_parts)
    
    # Prioridad
    prioridad = test_case.get('Prioridad', 'Medium')
    if isinstance(prioridad, str):
        prioridad_lower = prioridad.lower()
        if 'alta' in prioridad_lower or 'high' in prioridad_lower:
            priority = 'High'
        elif 'media' in prioridad_lower or 'medium' in prioridad_lower:
            priority = 'Medium'
        elif 'baja' in prioridad_lower or 'low' in prioridad_lower:
            priority = 'Low'
        else:
            priority = 'Medium'
    else:
        priority = 'Medium'
    
    return {
        'summary': summary[:255] if len(summary) > 255 else summary,
        'description': description,
        'priority': priority,
        'issuetype': 'Test Case',
        'tipo_prueba': tipo_prueba,
        'categoria': categoria,
        'precondiciones': precondiciones,
        'pasos': pasos if isinstance(pasos, list) else [pasos] if pasos else [],
        'resultado_esperado': resultado_esperado if isinstance(resultado_esperado, list) else [resultado_esperado] if resultado_esperado else []
    }


def parse_test_cases_to_dict(test_cases: List[dict]) -> List[dict]:
    """
    Convierte una lista de casos de prueba (dicts) a una lista de diccionarios estructurados.
    
    Args:
        test_cases: Lista de casos de prueba como diccionarios
        
    Returns:
        List[Dict]: Lista de diccionarios con estructura:
            {
                'index': int,
                'summary': str,
                'description': str,
                'issuetype': str,
                'priority': str,
                'raw_data': dict
            }
    """
    parsed_cases = []
    for idx, test_case in enumerate(test_cases, 1):
        try:
            data = parse_test_case_data(test_case)
            
            # Validar que el summary no esté vacío
            summary = data.get('summary', '').strip()
            if not summary or len(summary) < 3:
                # Fallback adicional: usar ID o índice
                case_id = test_case.get('id_caso_prueba', f'TC{idx:03d}')
                summary = f"Caso de prueba {case_id}"
                logger.warning(f"Summary vacío para caso {idx}, usando fallback: '{summary}'")
            
            parsed_cases.append({
                'index': idx,
                'summary': summary,
                'description': data.get('description', ''),
                'issuetype': data.get('issuetype', 'Test Case'),
                'priority': data.get('priority', 'Medium'),
                'tipo_prueba': data.get('tipo_prueba', 'Funcional'),
                'categoria': data.get('categoria', ''),
                'preconditions': data.get('precondiciones', ''),
                'steps': data.get('pasos', []),
                'expected_result': data.get('resultado_esperado', []),
                'raw_data': test_case
            })
        except Exception as e:
            logger.error(f"Error al parsear caso de prueba {idx}: {e}", exc_info=True)
            # Agregar caso con valores por defecto para no perder el caso
            parsed_cases.append({
                'index': idx,
                'summary': f"Caso de prueba {test_case.get('id_caso_prueba', f'TC{idx:03d}')}",
                'description': '',
                'issuetype': 'Test Case',
                'priority': 'Medium',
                'tipo_prueba': 'Funcional',
                'categoria': '',
                'raw_data': test_case
            })
    return parsed_cases
