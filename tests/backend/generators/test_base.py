"""
Tests unitarios para generadores - Base
"""
import unittest
from unittest.mock import MagicMock
from app.backend.generators.base import BaseGenerator


class TestBaseGenerator(unittest.TestCase):
    """Tests para BaseGenerator"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.generator = BaseGenerator()

    def test_generate_abstract_method(self):
        """Test método abstracto generate"""
        with self.assertRaises(NotImplementedError):
            self.generator.generate('input')

    def test_validate_input_success(self):
        """Test validación de entrada exitosa"""
        result = self.generator.validate_input('valid input')
        
        self.assertTrue(result)

    def test_validate_input_empty(self):
        """Test validación de entrada vacía"""
        with self.assertRaises(ValueError):
            self.generator.validate_input('')

    def test_validate_input_none(self):
        """Test validación de entrada None"""
        with self.assertRaises(ValueError):
            self.generator.validate_input(None)

    def test_preprocess_input(self):
        """Test preprocesamiento de entrada"""
        result = self.generator.preprocess('  input text  ')
        
        self.assertEqual(result, 'input text')

    def test_postprocess_output(self):
        """Test postprocesamiento de salida"""
        result = self.generator.postprocess('output text')
        
        self.assertIsNotNone(result)

    def test_get_generator_config(self):
        """Test obtener configuración del generador"""
        config = self.generator.get_config()
        
        self.assertIsInstance(config, dict)

    def test_set_generator_config(self):
        """Test establecer configuración del generador"""
        new_config = {'max_tokens': 1000}
        
        self.generator.set_config(new_config)
        
        self.assertEqual(self.generator.config['max_tokens'], 1000)


if __name__ == '__main__':
    unittest.main()
