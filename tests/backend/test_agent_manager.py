"""
Tests unitarios para el módulo agent_manager.
"""
import pytest
from unittest.mock import Mock, patch
from app.backend import agent_manager

# Test get_download_type
def test_get_download_type():
    assert agent_manager.get_download_type("matrix_generator") == 'zip'
    assert agent_manager.get_download_type("story_generator") == 'docx'
    assert agent_manager.get_download_type("unknown") == 'txt'

# Test simple_agent_processing
@patch('app.backend.agent_manager.GeneratorFactory')
def test_simple_agent_processing_success(mock_factory_cls):
    """Test de procesamiento exitoso con un generador específico."""
    # Setup mock factory
    mock_factory_instance = mock_factory_cls.return_value
    mock_generator = Mock()
    mock_generator.generate.return_value = {"status": "success", "result": "done"}
    mock_generator.get_output_format.return_value = "docx"
    
    mock_factory_instance.get_generator.return_value = mock_generator
    
    # Execute
    result = agent_manager.simple_agent_processing("story", "text", {})
    
    # Assert
    assert result['status'] == 'success'
    mock_factory_instance.get_generator.assert_called_with("story")
    mock_generator.generate.assert_called_with("text", {})

@patch('app.backend.agent_manager.GeneratorFactory')
def test_simple_agent_processing_auto(mock_factory_cls):
    """Test de procesamiento con autodeteción de generador."""
    # Setup mock factory
    mock_factory_instance = mock_factory_cls.return_value
    mock_generator = Mock()
    mock_generator.generate.return_value = {"status": "success"}
    mock_generator.get_output_format.return_value = "docx"
    
    mock_factory_instance.auto_detect_generator.return_value = mock_generator
    
    # Execute
    result = agent_manager.simple_agent_processing("auto", "text", {})
    
    # Assert
    assert result['status'] == 'success'
    mock_factory_instance.auto_detect_generator.assert_called_with("text", {})

@patch('app.backend.agent_manager.GeneratorFactory')
def test_simple_agent_processing_unknown_task(mock_factory_cls):
    """Test cuando se solicita un tipo de tarea desconocido."""
    # Setup mock factory
    mock_factory_instance = mock_factory_cls.return_value
    mock_factory_instance.get_generator.return_value = None
    mock_factory_instance.list_available_generators.return_value = ["story", "matrix"]
    
    # Execute
    result = agent_manager.simple_agent_processing("unknown", "text", {})
    
    # Assert
    assert result['status'] == 'error'
    assert "Tipo de tarea desconocido" in result['error']

@patch('app.backend.agent_manager.GeneratorFactory')
def test_simple_agent_processing_exception(mock_factory_cls):
    """Test de manejo de excepciones durante el procesamiento."""
    # Setup mock factory to raise exception
    mock_factory_instance = mock_factory_cls.return_value
    mock_factory_instance.get_generator.side_effect = Exception("Factory error")
    
    # Execute
    result = agent_manager.simple_agent_processing("story", "text", {})
    
    # Assert
    assert result['status'] == 'error'
    assert "Factory error" in result['error']
