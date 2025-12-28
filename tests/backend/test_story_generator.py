"""
Tests unitarios actualizados para el generador de historias (story_generator.py)
"""
import pytest
from unittest.mock import Mock, patch
from app.backend import story_generator

@pytest.fixture
def mock_genai():
    with patch('app.backend.story_generator.genai') as mock:
        yield mock

@pytest.fixture
def mock_config():
    with patch('app.backend.story_generator.Config') as mock:
        mock.GOOGLE_API_KEY = "fake_key"
        mock.GEMINI_MODEL = "gemini-pro"
        mock.MAX_RETRIES = 1
        mock.RETRY_DELAY = 0
        mock.GEMINI_TIMEOUT_BASE = 1
        mock.GEMINI_TIMEOUT_INCREMENT = 0
        mock.MIN_RESPONSE_LENGTH = 10
        yield mock

def test_generate_story_from_chunk_success(mock_genai, mock_config):
    """Test de generación exitosa desde un chunk."""
    # Setup mock model
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text = "Historia generada exitosa..."
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model
    
    # Execute
    result = story_generator.generate_story_from_chunk(
        chunk="Texto de prueba", 
        role="Usuario", 
        story_type="Funcionalidad",
        skip_healing=True
    )
    
    # Assert
    assert result['status'] == 'success'
    assert result['story'] == "Historia generada exitosa..."
    mock_model.generate_content.assert_called()

def test_generate_story_from_chunk_api_key_missing(mock_genai, mock_config):
    """Test de manejo de error cuando falta la API Key."""
    mock_config.GOOGLE_API_KEY = None
    
    result = story_generator.generate_story_from_chunk("t", "r", "s")
    
    assert result['status'] == 'error'
    assert "API Key no configurada" in result['message']

def test_generate_story_from_chunk_short_response(mock_genai, mock_config):
    """Test de manejo de respuestas demasiado cortas."""
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text = "Corta" # < Config.MIN_RESPONSE_LENGTH
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model
    
    result = story_generator.generate_story_from_chunk("t", "r", "s", skip_healing=True)
    
    # Debe fallar tras reintentos
    assert result['status'] == 'error'
    assert "Error en la generación" in result['message']

def test_generate_story_from_text_end_to_end(mock_genai, mock_config):
    """Test de integración simulada de generate_story_from_text (Dos Pasadas)"""
    # Mocks adicionales necesarios para las dependencias internas
    with patch('app.backend.story_generator.split_document_into_chunks') as mock_split, \
         patch('app.backend.story_generator.process_large_document') as mock_process, \
         patch('app.services.text_processor.TextProcessor') as mock_tp_cls, \
         patch('app.services.validator.Validator') as mock_val_cls, \
         patch('app.backend.story_generator.create_advanced_prompt') as mock_prompt, \
         patch('app.backend.context_extractor.ContextExtractor') as mock_extractor_cls, \
         patch('app.backend.story_generator.call_with_retry', side_effect=lambda func, **kwargs: func()): # Bypass retry
        
        # [NEW] Mock Context Extractor
        mock_extractor_instance = mock_extractor_cls.return_value
        mock_extractor_instance.extract_global_context.return_value = "CONTEXTO GLOBAL MOCKEADO"

        # Flujo simple: 1 chunk
        mock_split.return_value = ["chunk1"]
        mock_prompt.return_value = "Prompt normal" # Asegurar que no sea CHUNK_PROCESSING_NEEDED
        
        # Mock generate_story_from_chunk (llamada interna)
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Historia generada valida 1"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Mock TextProcessor y Validator
        mock_tp = mock_tp_cls.return_value
        mock_tp.split_story_text_into_individual_stories.return_value = ["Historia generada valida 1"]
        
        mock_val = mock_val_cls.return_value
        mock_val.find_duplicates.return_value = []
        mock_val.semantic_validate_story.return_value = {"is_valid": True, "score": 10}
        
        # Execute
        result = story_generator.generate_story_from_text("doc completo", "rol", "tipo", skip_healing=True)
        
        # Verify Context Extractor was called
        mock_extractor_cls.assert_called_once()
        mock_extractor_instance.extract_global_context.assert_called_with("doc completo")

        if result['status'] != 'success':
            pytest.fail(f"TEST FAILED: Status={result.get('status')} Message={result.get('message', 'No message')}")
        
        # Verify generation was called
        mock_model.generate_content.assert_called()
        
        assert result['status'] == 'success'
        assert len(result['stories']) == 1
        assert result['stories'][0] == "Historia generada valida 1"
