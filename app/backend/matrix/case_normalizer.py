"""
Módulo de normalización para casos de prueba.
Responsabilidad única: Asegurar la consistencia y completitud de los datos de un caso de prueba.
"""
from typing import Dict, Any, List

def normalize_test_case(case: Dict[str, Any], index: int, base_id_count: int, story_chunk: str) -> Dict[str, Any]:
    """
    Normaliza un diccionario de caso de prueba.
    
    Args:
        case: Diccionario del caso raw
        index: Índice en el chunk actual
        base_id_count: Cantidad base de casos ya existentes (para IDs)
        story_chunk: Historia de usuario asociada
        
    Returns:
        Dict: Caso normalizado
    """
    # 1. ID
    if not case.get('id_caso_prueba'):
        case['id_caso_prueba'] = f"TC{base_id_count + index + 1:03d}"
    
    # 2. Historia
    case['historia_de_usuario'] = story_chunk
    
    # 3. Estado de Aprobación (Nuevo requerimiento TC-W1.2)
    # Se establece en 'draft' al crear el caso.
    case['approval_status'] = 'draft'
    
    # 4. Título (Lógica de fallback)
    titulo = case.get('titulo_caso_prueba', '')
    if not titulo or titulo.strip() == '' or 'por definir' in titulo.lower() or 'título descriptivo' in titulo.lower():
        # Intentar generar título desde descripción
        descripcion = case.get('Descripcion', '')
        if descripcion and descripcion.strip() and 'por definir' not in descripcion.lower():
            # Usar primeros 60 caracteres de la descripción como título
            titulo = descripcion[:60].strip()
            if len(descripcion) > 60:
                titulo += '...'
        else:
            # Generar título basado en tipo de prueba y categoría
            tipo_prueba = case.get('Tipo_de_prueba', 'Funcional')
            categoria = case.get('Categoria', '')
            if categoria:
                titulo = f"Validar {categoria} - {tipo_prueba}"
            else:
                titulo = f"Caso de prueba {tipo_prueba} - {case['id_caso_prueba']}"
        case['titulo_caso_prueba'] = titulo
    
    # 5. Campos por defecto
    if not case.get('Descripcion') or not case['Descripcion']:
        case['Descripcion'] = "Verificar funcionalidad según requerimientos"
    if not case.get('Precondiciones') or not case['Precondiciones']:
        case['Precondiciones'] = "Sistema configurado y usuario autenticado"
    if not case.get('Tipo_de_prueba') or not case['Tipo_de_prueba']:
        case['Tipo_de_prueba'] = "Funcional"
    
    # 6. Pasos y Resultados (Listas)
    if not isinstance(case.get('Pasos'), list):
        pasos = case.get('Pasos', '')
        if pasos:
            case['Pasos'] = [str(pasos)]
        else:
            case['Pasos'] = ["Ejecutar la funcionalidad especificada"]
            
    if not isinstance(case.get('Resultado_esperado'), list):
        resultado = case.get('Resultado_esperado', '')
        if resultado:
            case['Resultado_esperado'] = [str(resultado)]
        else:
            case['Resultado_esperado'] = ["El sistema responde correctamente según especificación"]
            
    return case
