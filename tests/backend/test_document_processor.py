"""
Tests unitarios actualizados para document_processor.py
"""
import pytest
from unittest.mock import Mock, patch
from app.backend import document_processor

@patch('app.backend.document_processor.Config')
@patch('app.backend.document_processor.DocumentChunker')
def test_split_document_into_chunks(mock_chunker_cls, mock_config):
    """Test de división de documentos usando DocumentChunker."""
    mock_config.STORY_MAX_CHUNK_SIZE = 1000
    mock_chunker_instance = mock_chunker_cls.return_value
    mock_chunker_instance.split_document_into_chunks.return_value = ["chunk1", "chunk2"]
    
    result = document_processor.split_document_into_chunks("text")
    
    assert len(result) == 2
    assert result == ["chunk1", "chunk2"]

@patch('app.backend.document_processor.Config')
@patch('app.backend.document_processor.genai')
def test_process_large_document_success(mock_genai, mock_config):
    """Test de integración simulada para el procesamiento de documentos grandes."""
    # Setup
    mock_config.GOOGLE_API_KEY = "key"
    mock_config.GEMINI_MODEL = "model"
    mock_config.GEMINI_TIMEOUT_ANALYSIS = 10
    mock_config.STORY_BATCH_SIZE = 1
    mock_config.GEMINI_TIMEOUT_BASE = 1
    mock_config.GEMINI_TIMEOUT_INCREMENT = 0
    mock_config.MAX_RETRIES = 1
    mock_config.RETRY_DELAY = 0
    mock_config.MIN_RESPONSE_LENGTH = 5
    
    # Mock analysis response
    mock_model = Mock()
    mock_analysis_resp = Mock()
    mock_analysis_resp.text = "1. Funcionalidad A\n2. Funcionalidad B"
    
    # Mock story response
    mock_story_resp = Mock()
    mock_story_resp.text = "Story Content A"
    
    # Configure side_effect for generate_content to return analysis first, then stories
    # Se llamará 1 vez para análisis y luego N veces para lotes (aquí 2 funcionalidades, batch size 1 -> 2 lotes)
    mock_model.generate_content.side_effect = [mock_analysis_resp, mock_story_resp, mock_story_resp]
    
    mock_genai.GenerativeModel.return_value = mock_model
    
    # Mock dependencies
    with patch('app.services.text_processor.TextProcessor') as mock_tp, \
         patch('app.backend.document_processor._heal_stories_in_batch') as mock_heal, \
         patch('time.sleep'): # Evitar delay real
        
        mock_tp_inst = mock_tp.return_value
        mock_tp_inst.split_story_text_into_individual_stories.return_value = ["Story A"]
        
        # Execute
        result = document_processor.process_large_document("doc text", "role", "story", skip_healing=True)
        
        # Assert
        assert result['status'] == 'success'
        assert "ANÁLISIS COMPLETO" in result['story']
        assert "Funcionalidad A" in result['story']

@patch('app.backend.document_processor.Config')
def test_process_large_document_no_api_key(mock_config):
    """Test error cuando no hay API key."""
    mock_config.GOOGLE_API_KEY = None
    result = document_processor.process_large_document("text", "role", "story")
    assert result['status'] == 'error'
    assert "API Key no configurada" in result['message']
