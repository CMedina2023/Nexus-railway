"""
Fachada para el backend de Matrices de Prueba.
Este archivo ha sido refactorizado. La lógica real se encuentra en app/backend/matrix/.
Este módulo se mantiene para compatibilidad hacia atrás.
"""
from app.backend.matrix import (
    generar_matriz_test,
    split_document_into_chunks,
    test_matrix_generation,
    HEALING_PROMPT_BATCH,
    validator,
    clean_json_response,
    clean_text,
    extract_stories_from_text,
    parse_test_case_data,
    parse_test_cases_to_dict,
    generate_test_cases_html_document
)

# Re-exportar módulos si es necesario, aunque se recomienda usar las funciones directamente
import app.backend.matrix.generator as generator
import app.backend.matrix.parser as parser
import app.backend.matrix.formatters as formatters

if __name__ == "__main__":
    test_matrix_generation()