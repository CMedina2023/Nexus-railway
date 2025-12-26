"""
Tests unitarios para generadores - Factory
"""
import unittest
from unittest.mock import patch, MagicMock
from app.backend.generators.factory import GeneratorFactory


class TestGeneratorFactory(unittest.TestCase):
    """Tests para GeneratorFactory"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.factory = GeneratorFactory()

    def test_create_story_generator(self):
        """Test creación de generador de historias"""
        generator = self.factory.create_generator('story')
        
        self.assertIsNotNone(generator)

    def test_create_test_case_generator(self):
        """Test creación de generador de casos de prueba"""
        generator = self.factory.create_generator('test_case')
        
        self.assertIsNotNone(generator)

    def test_create_matrix_generator(self):
        """Test creación de generador de matriz"""
        generator = self.factory.create_generator('matrix')
        
        self.assertIsNotNone(generator)

    def test_create_invalid_generator_type(self):
        """Test creación de tipo de generador inválido"""
        with self.assertRaises(ValueError):
            self.factory.create_generator('invalid_type')

    def test_register_custom_generator(self):
        """Test registro de generador personalizado"""
        custom_generator = MagicMock()
        
        self.factory.register('custom', custom_generator)
        
        result = self.factory.create_generator('custom')
        self.assertIsNotNone(result)

    def test_get_available_generators(self):
        """Test obtener generadores disponibles"""
        generators = self.factory.get_available_generators()
        
        self.assertIsInstance(generators, list)
        self.assertGreater(len(generators), 0)

    def test_create_generator_with_config(self):
        """Test creación de generador con configuración"""
        config = {'max_tokens': 500}
        
        generator = self.factory.create_generator('story', config=config)
        
        self.assertIsNotNone(generator)

    def test_factory_singleton_pattern(self):
        """Test patrón singleton de factory"""
        factory1 = GeneratorFactory()
        factory2 = GeneratorFactory()
        
        self.assertIs(factory1, factory2)


if __name__ == '__main__':
    unittest.main()
