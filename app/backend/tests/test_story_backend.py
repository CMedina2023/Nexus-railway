"""
Tests para el módulo de Story Backend.

Este módulo contiene tests unitarios y de integración para validar
la funcionalidad de generación de historias de usuario.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.backend import story_parser, story_formatters, story_generator


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_story_text():
    """Historia de usuario de ejemplo para testing."""
    return """
╔════════════════════════════════════════════════════════════════════════════════
HISTORIA #1: Gestión de Usuarios
════════════════════════════════════════════════════════════════════════════════

COMO: Administrador del sistema
QUIERO: Poder crear, editar y eliminar usuarios
PARA: Mantener el control de acceso al sistema

CRITERIOS DE ACEPTACIÓN:

🔹 Escenario Principal:
   DADO que soy un administrador autenticado
   CUANDO accedo al módulo de usuarios
   ENTONCES puedo ver la lista completa de usuarios

🔹 Escenario Alternativo:
   DADO que intento crear un usuario con email duplicado
   CUANDO envío el formulario
   ENTONCES recibo un mensaje de error

🔹 Validaciones:
   DADO que los campos obligatorios están vacíos
   CUANDO intento guardar
   ENTONCES se muestran mensajes de validación

REGLAS DE NEGOCIO:
• El email debe ser único en el sistema
• La contraseña debe tener al menos 8 caracteres
• Los usuarios inactivos no pueden acceder al sistema

PRIORIDAD: Alta
COMPLEJIDAD: Moderada

════════════════════════════════════════════════════════════════════════════════
"""


@pytest.fixture
def sample_stories_list():
    """Lista de historias de usuario para testing."""
    return [
        """
HISTORIA #1: Login de Usuario

COMO: Usuario del sistema
QUIERO: Poder iniciar sesión
PARA: Acceder a mis datos

PRIORIDAD: Alta
COMPLEJIDAD: Simple
""",
        """
HISTORIA #2: Recuperar Contraseña

COMO: Usuario del sistema
QUIERO: Poder recuperar mi contraseña
PARA: Acceder nuevamente si la olvido

PRIORIDAD: Media
COMPLEJIDAD: Moderada
"""
    ]


@pytest.fixture
def mock_gemini_model():
    """Mock del modelo de Gemini para testing."""
    mock = MagicMock()
    mock.generate_content.return_value.text = """
╔════════════════════════════════════════════════════════════════════════════════
HISTORIA #1: Test Story
════════════════════════════════════════════════════════════════════════════════

COMO: Test User
QUIERO: Test functionality
PARA: Test purposes

PRIORIDAD: Alta
COMPLEJIDAD: Simple

════════════════════════════════════════════════════════════════════════════════
"""
    return mock


# ============================================================================
# TESTS DE PARSING
# ============================================================================

def test_extract_story_titles(sample_stories_list):
    """Test de extracción de títulos de historias."""
    titles = story_parser.extract_story_titles(sample_stories_list)
    
    assert len(titles) == 2
    assert "Login de Usuario" in titles[0]
    assert "Recuperar Contraseña" in titles[1]


def test_parse_story_data(sample_story_text):
    """Test de parsing de datos de una historia."""
    data = story_parser.parse_story_data(sample_story_text)
    
    assert data['summary'] == 'Gestión de Usuarios'
    assert 'Administrador del sistema' in data['description']
    assert data['priority'] == 'High'
    assert 'Moderada' in data['complexity']


def test_parse_story_data_missing_fields():
    """Test de parsing con campos faltantes."""
    incomplete_story = "HISTORIA #1: Test\n\nCOMO: Usuario"
    data = story_parser.parse_story_data(incomplete_story)
    
    assert data['summary'] == 'Test'
    assert data['priority'] == 'Medium'  # Default value


def test_parse_stories_to_dict(sample_stories_list):
    """Test de conversión de historias a diccionarios."""
    parsed = story_parser.parse_stories_to_dict(sample_stories_list)
    
    assert len(parsed) == 2
    assert parsed[0]['index'] == 1
    assert parsed[0]['issuetype'] == 'Story'
    assert 'Login de Usuario' in parsed[0]['summary']


# ============================================================================
# TESTS DE FORMATEO
# ============================================================================

def test_generate_jira_csv(sample_stories_list):
    """Test de generación de CSV para Jira."""
    csv_content = story_formatters.generate_jira_csv(sample_stories_list)
    
    assert 'Summary,Description,Issuetype,Priority' in csv_content
    assert 'Login de Usuario' in csv_content
    assert 'Story' in csv_content


def test_format_story_for_html(sample_story_text):
    """Test de formateo de historia a HTML."""
    html = story_formatters.format_story_for_html(sample_story_text, 1)
    
    assert '<div class="story-container">' in html
    assert 'HISTORIA #1' in html
    assert 'Gestión de Usuarios' in html
    assert 'story-item' in html


def test_create_word_document(sample_stories_list):
    """Test de creación de documento Word."""
    doc = story_formatters.create_word_document(sample_stories_list)
    
    assert doc is not None
    assert len(doc.paragraphs) > 0


# ============================================================================
# TESTS DE GENERACIÓN (con mocks)
# ============================================================================

@patch('app.backend.story_generator.genai')
@patch('app.backend.story_generator.Config')
def test_generate_story_from_chunk(mock_config, mock_genai, mock_gemini_model):
    """Test de generación de historia desde un chunk."""
    # Configurar mocks
    mock_config.GOOGLE_API_KEY = "test_key"
    mock_config.GEMINI_MODEL = "gemini-pro"
    mock_config.GEMINI_TIMEOUT_BASE = 60
    mock_config.MAX_RETRIES = 3
    mock_config.RETRY_DELAY = 1
    mock_config.GEMINI_TIMEOUT_INCREMENT = 10
    mock_config.MIN_RESPONSE_LENGTH = 50
    
    mock_genai.GenerativeModel.return_value = mock_gemini_model
    
    # Ejecutar
    result = story_generator.generate_story_from_chunk(
        chunk="Test document content",
        role="Usuario",
        story_type="funcionalidad",
        skip_healing=True  # Skip healing para simplificar el test
    )
    
    # Verificar
    assert result['status'] == 'success'
    assert 'story' in result


@patch('app.backend.document_processor.genai')
@patch('app.backend.document_processor.Config')
def test_split_document_into_chunks(mock_config):
    """Test de división de documento en chunks."""
    from app.backend.document_processor import split_document_into_chunks
    
    mock_config.STORY_MAX_CHUNK_SIZE = 1000
    
    long_text = "Test content. " * 200  # Texto largo
    chunks = split_document_into_chunks(long_text, max_chunk_size=500)
    
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 500


# ============================================================================
# TESTS DE INTEGRACIÓN
# ============================================================================

def test_end_to_end_story_parsing_and_formatting(sample_story_text):
    """Test de integración: parsing y formateo."""
    # Parse
    data = story_parser.parse_story_data(sample_story_text)
    
    # Verify parsing
    assert data['summary'] == 'Gestión de Usuarios'
    
    # Format to HTML
    html = story_formatters.format_story_for_html(sample_story_text, 1)
    
    # Verify formatting
    assert 'Gestión de Usuarios' in html
    assert '<div class="story-container">' in html


def test_csv_generation_from_parsed_stories(sample_stories_list):
    """Test de integración: parsing a CSV."""
    # Parse stories
    parsed = story_parser.parse_stories_to_dict(sample_stories_list)
    
    # Generate CSV
    csv_content = story_formatters.generate_jira_csv(sample_stories_list)
    
    # Verify
    assert len(parsed) == 2
    assert 'Login de Usuario' in csv_content
    assert 'Recuperar Contraseña' in csv_content


# ============================================================================
# TESTS DE VALIDACIÓN
# ============================================================================

def test_parse_story_with_special_characters():
    """Test de parsing con caracteres especiales."""
    story_with_special = """
HISTORIA #1: Test & Validación "Especial"

COMO: Usuario
QUIERO: Probar caracteres especiales: <>&"'
PARA: Validar el parsing

PRIORIDAD: Alta
"""
    data = story_parser.parse_story_data(story_with_special)
    
    assert 'Test & Validación' in data['summary']
    assert data['priority'] == 'High'


def test_empty_story_list():
    """Test con lista vacía de historias."""
    empty_list = []
    titles = story_parser.extract_story_titles(empty_list)
    
    assert len(titles) == 0


def test_malformed_story():
    """Test con historia mal formada."""
    malformed = "Esta es una historia sin formato correcto"
    data = story_parser.parse_story_data(malformed)
    
    # Debe manejar gracefully
    assert 'summary' in data
    assert 'priority' in data


# ============================================================================
# INSTRUCCIONES PARA EJECUTAR LOS TESTS
# ============================================================================

"""
Para ejecutar estos tests:

1. Instalar pytest si no está instalado:
   pip install pytest pytest-cov

2. Ejecutar todos los tests:
   pytest app/backend/tests/test_story_backend.py -v

3. Ejecutar con cobertura:
   pytest app/backend/tests/test_story_backend.py --cov=app.backend --cov-report=html

4. Ejecutar un test específico:
   pytest app/backend/tests/test_story_backend.py::test_extract_story_titles -v

5. Ejecutar solo tests de parsing:
   pytest app/backend/tests/test_story_backend.py -k "parsing" -v
"""
