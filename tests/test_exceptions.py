"""
Tests para excepciones personalizadas
"""
import unittest

from app.utils.exceptions import (
    ConfigurationError,
    FileProcessingError,
    AIProcessingError,
    JiraError,
    ValidationError
)


class TestExceptions(unittest.TestCase):
    """Tests para excepciones personalizadas"""
    
    def test_configuration_error(self):
        """Verifica ConfigurationError"""
        error = ConfigurationError("Config inválida")
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Config inválida")
    
    def test_file_processing_error(self):
        """Verifica FileProcessingError"""
        error = FileProcessingError("Error procesando archivo")
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Error procesando archivo")
    
    def test_validation_error(self):
        """Verifica ValidationError"""
        error = ValidationError("Validación fallida")
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Validación fallida")


if __name__ == '__main__':
    unittest.main()

