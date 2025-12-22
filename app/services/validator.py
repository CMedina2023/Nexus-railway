"""
Servicio para validación de datos
Responsabilidad única: Validar historias de usuario y casos de prueba
"""
import logging
from typing import List, Dict, Tuple, Optional, Any

from app.core.config import Config

logger = logging.getLogger(__name__)


class Validator:
    """Valida historias de usuario y casos de prueba"""
    
    # Valores permitidos para validación estructural
    VALID_PRIORITIES = ['Alta', 'Media', 'Baja', 'Crítica', 'P1', 'P2', 'P3', 'P4']
    VALID_TEST_TYPES = ['Funcional', 'No Funcional', 'Regresión', 'Humo', 'UI', 'API', 'Performance', 'Seguridad']
    
    # Red Flags (Pereza de IA o falta de detalle)
    RED_FLAGS = [
        'etc', '...', 'otros campos', 'rellenar campos', 'datos estándar', 
        'pasos normales', 'procedimiento habitual', 'repetir proceso', 
        'según sea necesario', 'completar el formulario'
    ]
    
    # Verbos de acción comunes en QA
    ACTION_VERBS = [
        'click', 'clic', 'presionar', 'seleccionar', 'ingresar', 'validar', 'verificar', 
        'navegar', 'abrir', 'esperar', 'llenar', 'enviar', 'escribir', 'moverse', 
        'arrastrar', 'soltar', 'comparar', 'revisar', 'autenticar', 'cerrar'
    ]


    def validate_stories(
        self, 
        stories_content: List[str]
    ) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Valida y filtra historias válidas
        
        Args:
            stories_content: Lista de historias a validar
            
        Returns:
            Tuple[Optional[List[str]], Optional[str]]: 
            - (historias_válidas, None) si hay historias válidas
            - (None, mensaje_error) si no hay historias válidas
        """
        if not stories_content or len(stories_content) == 0:
            return None, "No se generaron historias de usuario"
        
        valid_stories = []
        for s in stories_content:
            structural = self.structural_validate_story(s)
            if structural['is_valid']:
                valid_stories.append(s)
            else:
                logger.warning(f"Historia descartada por errores estructurales: {structural['issues']}")
        
        if not valid_stories:
            return None, "Todas las historias generadas tienen errores estructurales críticos"
        
        logger.info(f"Validadas {len(valid_stories)} historias de {len(stories_content)} totales")
        return valid_stories, None
    
    def validate_test_cases(
        self, 
        test_cases: List[Dict]
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Valida y filtra casos de prueba válidos (estructura básica)
        
        Args:
            test_cases: Lista de casos de prueba a validar
            
        Returns:
            Tuple[Optional[List[Dict]], Optional[str]]: 
            - (casos_válidos, None) si hay casos válidos
            - (None, mensaje_error) si no hay casos válidos
        """
        if not test_cases or len(test_cases) == 0:
            return None, "No se generaron casos de prueba"
        
        valid_cases = []
        for case in test_cases:
            if isinstance(case, dict):
                # Aplicar validación estructural básica
                structural = self.structural_validate_case(case)
                if structural['is_valid']:
                    valid_cases.append(case)
                else:
                    logger.warning(f"Caso de prueba descartado por errores estructurales: {structural['issues']}")
        
        if not valid_cases:
            return None, "Todos los casos de prueba generados tienen errores estructurales críticos"
        
        logger.info(f"Validados {len(valid_cases)} casos de {len(test_cases)} totales")
        return valid_cases, None

    def structural_validate_case(self, case: Dict) -> Dict:
        """
        Realiza una validación estructural de un caso de prueba.
        Verifica: campos vacíos, tipos incorrectos, pasos como lista, prioridades y tipos válidos.
        """
        issues = []
        
        # 1. Verificar campos obligatorios y no vacíos
        required_fields = {
            'titulo_caso_prueba': str,
            'Descripcion': str,
            'Precondiciones': (str, list),
            'Pasos': list,
            'Resultado_esperado': (str, list)
        }
        
        for field, expected_type in required_fields.items():
            value = case.get(field)
            
            # Verificar existencia y nulidad
            if value is None:
                issues.append(f"El campo '{field}' es obligatorio.")
                continue
                
            # Verificar tipo
            if not isinstance(value, expected_type):
                actual_type = type(value).__name__
                issues.append(f"El campo '{field}' tiene un tipo incorrecto: se esperaba {expected_type}, se obtuvo {actual_type}.")
                continue
                
            # Verificar contenido no vacío si es string o lista
            if isinstance(value, str) and not value.strip():
                issues.append(f"El campo '{field}' no puede estar vacío.")
            elif isinstance(value, list) and len(value) == 0:
                issues.append(f"El campo '{field}' debe contener al menos un elemento.")

        # 2. Validar Prioridad si existe
        prioridad = case.get('Prioridad')
        if prioridad:
            if not any(p.lower() == str(prioridad).lower() for p in self.VALID_PRIORITIES):
                issues.append(f"Prioridad '{prioridad}' no es válida. Valores permitidos: {', '.join(self.VALID_PRIORITIES)}")

        # 3. Validar Tipo de Prueba si existe
        tipo = case.get('Tipo_de_prueba') or case.get('tipo_prueba') or case.get('Tipo_prueba')
        if tipo:
            if not any(t.lower() == str(tipo).lower() for t in self.VALID_TEST_TYPES):
                issues.append(f"Tipo de prueba '{tipo}' no es válido. Valores permitidos: {', '.join(self.VALID_TEST_TYPES)}")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }

    def structural_validate_story(self, story_content: str) -> Dict:
        """
        Valida estructuralmente una historia de usuario.
        """
        issues = []
        
        if not story_content or not isinstance(story_content, str):
            issues.append("El contenido de la historia debe ser un texto no vacío.")
        elif len(story_content.strip()) < Config.MIN_RESPONSE_LENGTH:
            issues.append(f"La historia es demasiado corta (mínimo {Config.MIN_RESPONSE_LENGTH} caracteres).")
            
        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }

    def semantic_validate_case(self, case: Dict, story_context: str = "") -> Dict:
        """
        Realiza una validación semántica profunda de un caso de prueba individual.
        Detecta: pasos sin verbos de acción, resultados vagos, inconsistencia e incompletitud.
        """
        issues = []
        pasos = case.get('Pasos', [])
        resultados = case.get('Resultado_esperado', [])
        titulo = case.get('titulo_caso_prueba', '')
        
        # 1. Validar verbos de acción y composición (Acción + Objeto)
        steps_without_verb = 0
        steps_too_short = 0
        for paso in pasos:
            paso_lower = str(paso).lower()
            words = paso_lower.split()
            
            # Verificación de verbo usando la lista de clase
            has_verb = any(verb in paso_lower for verb in self.ACTION_VERBS)
            
            if not has_verb:
                steps_without_verb += 1
            
            # Verificación de composición (Acción + Objeto)
            # Un paso con menos de 3 palabras suele ser incompleto (ej: "Hacer click")
            if len(words) < 3:
                steps_too_short += 1
        
        if steps_without_verb > 0:
            issues.append(f"Se detectaron {steps_without_verb} pasos sin verbos de acción claros.")
        if steps_too_short > 0:
            issues.append(f"Se detectaron {steps_too_short} pasos demasiado cortos (posible falta de objeto de la acción).")

        # 2. Validar Red Flags (Pereza de IA)
        red_flags_found = []
        full_text = f"{titulo} {' '.join(str(p) for p in pasos)} {' '.join(str(r) for r in resultados)}".lower()
        for flag in self.RED_FLAGS:
            if flag in full_text:
                red_flags_found.append(flag)
        
        if red_flags_found:
            issues.append(f"Se detectaron términos vagos o incompletos (Red Flags): {', '.join(red_flags_found)}")

        # 3. Validar resultados vagos
        vague_terms = ['correctamente', 'bien', 'exitoso', 'esperado', 'funciona', 'ok', 'normal']
        vague_results = 0
        for res in resultados:
            res_lower = str(res).lower()
            if any(term in res_lower for term in vague_terms) and len(res_lower.split()) < 4:
                vague_results += 1
        
        if vague_results > 0:
            issues.append(f"Se detectaron {vague_results} resultados que carecen de criterios de éxito específicos.")

        # 4. Incompletitud estructural y coherencia
        if not pasos or len(pasos) < 3:
            issues.append("El caso de prueba tiene muy pocos pasos para ser exhaustivo.")
            
        if story_context and titulo:
            story_keywords = [w for w in story_context.lower().split() if len(w) > 5]
            if story_keywords and not any(kw in titulo.lower() for kw in story_keywords[:15]):
                issues.append("El título del caso de prueba no parece estar alineado con los conceptos clave de la historia.")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "score": max(0.0, 1.0 - (len(issues) * 0.20))
        }

    def semantic_validate_story(self, story_content: str, doc_context: str = "") -> Dict:
        """
        Valida semánticamente una historia de usuario.
        Detecta: falta de formato estándar, ausencia de criterios de aceptación, ambigüedad.
        """
        issues = []
        story_lower = story_content.lower()
        
        # 1. Formato estándar
        if not all(term in story_lower for term in ['como', 'quiero', 'para']):
            issues.append("La historia no sigue el formato estándar 'COMO... QUIERO... PARA...'.")
            
        # 2. Criterios de aceptación
        if 'criterios de aceptación' not in story_lower and 'escenario' not in story_lower:
            issues.append("La historia no define criterios de aceptación claros.")
            
        # 3. Ambigüedad
        if len(story_content.split()) < 30:
            issues.append("La historia parece demasiado corta o carece de detalle suficiente.")
            
        # 4. Keyword check contra el documento
        if doc_context:
            doc_keywords = [w for w in doc_context.lower().split() if len(w) > 5]
            if doc_keywords and not any(kw in story_lower for kw in doc_keywords[:20]):
                issues.append("La historia parece no estar alineada con el contexto del documento proporcionado.")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "score": max(0.0, 1.0 - (len(issues) * 0.33))
        }

    def find_duplicates(self, items: List[Any], threshold: float = 0.85) -> List[int]:
        """
        Identifica índices de ítems que son duplicados o muy similares.
        Útil para limpiar matrices de prueba o listas de historias.
        """
        from difflib import SequenceMatcher
        
        duplicates = []
        n = len(items)
        
        for i in range(n):
            if i in duplicates:
                continue
                
            item_i = str(items[i]).lower()
            for j in range(i + 1, n):
                if j in duplicates:
                    continue
                    
                item_j = str(items[j]).lower()
                
                # Comparación de similitud básica
                similarity = SequenceMatcher(None, item_i, item_j).ratio()
                if similarity > threshold:
                    duplicates.append(j)
                    logger.info(f"Detectado ítem similar (índice {j}) a ítem {i} (Similitud: {similarity:.2f})")
        
        return duplicates

