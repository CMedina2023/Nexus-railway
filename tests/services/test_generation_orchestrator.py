"""
Tests unitarios para el orquestador de generación
"""
import unittest
from unittest.mock import patch, MagicMock
from app.services.generation_orchestrator import GenerationOrchestrator


class TestGenerationOrchestrator(unittest.TestCase):
    """Tests para GenerationOrchestrator"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.orchestrator = GenerationOrchestrator()

    @patch('app.services.generation_orchestrator.StoryGenerator')
    def test_orchestrate_story_generation_success(self, mock_generator):
        """Test orquestación de generación de historias exitosa"""
        mock_generator.return_value.generate.return_value = ['Story 1', 'Story 2']
        
        result = self.orchestrator.orchestrate_story_generation('Create login feature')
        
        self.assertEqual(len(result), 2)

    @patch('app.services.generation_orchestrator.TestCaseGenerator')
    def test_orchestrate_test_generation_success(self, mock_generator):
        """Test orquestación de generación de casos de prueba exitosa"""
        mock_generator.return_value.generate.return_value = ['Test 1', 'Test 2']
        
        result = self.orchestrator.orchestrate_test_generation('Login feature')
        
        self.assertEqual(len(result), 2)

    def test_orchestrate_with_validation(self):
        """Test orquestación con validación"""
        with patch('app.services.generation_orchestrator.Validator') as mock_validator:
            mock_validator.return_value.validate.return_value = True
            
            result = self.orchestrator.orchestrate_with_validation('input data')
            
            self.assertTrue(result)

    @patch('app.services.generation_orchestrator.StoryGenerator')
    def test_orchestrate_batch_generation(self, mock_generator):
        """Test orquestación de generación por lotes"""
        mock_generator.return_value.generate.return_value = ['Story']
        
        prompts = ['Prompt 1', 'Prompt 2', 'Prompt 3']
        result = self.orchestrator.orchestrate_batch(prompts)
        
        self.assertEqual(len(result), 3)

    def test_orchestrate_with_error_handling(self):
        """Test orquestación con manejo de errores"""
        with patch('app.services.generation_orchestrator.StoryGenerator') as mock_gen:
            mock_gen.return_value.generate.side_effect = Exception('Generation error')
            
            result = self.orchestrator.orchestrate_with_error_handling('prompt')
            
            self.assertIn('error', result)

    @patch('app.services.generation_orchestrator.FileManager')
    def test_orchestrate_with_file_save(self, mock_file_manager):
        """Test orquestación con guardado de archivo"""
        mock_file_manager.return_value.save.return_value = True
        
        result = self.orchestrator.orchestrate_and_save('content', 'output.txt')
        
        self.assertTrue(result)

    def test_orchestrate_pipeline_success(self):
        """Test orquestación de pipeline completo"""
        with patch.multiple('app.services.generation_orchestrator',
                          Validator=MagicMock(),
                          StoryGenerator=MagicMock(),
                          FileManager=MagicMock()):
            
            result = self.orchestrator.orchestrate_pipeline('input')
            
            self.assertIsNotNone(result)

    def test_orchestrate_with_retry_logic(self):
        """Test orquestación con lógica de reintentos"""
        with patch('app.services.generation_orchestrator.StoryGenerator') as mock_gen:
            mock_gen.return_value.generate.side_effect = [
                Exception('Temporary error'),
                ['Success']
            ]
            
            result = self.orchestrator.orchestrate_with_retry('prompt', max_retries=2)
            
            self.assertEqual(len(result), 1)

    @patch('app.services.generation_orchestrator.MetricsCollector')
    def test_orchestrate_with_metrics(self, mock_metrics):
        """Test orquestación con recolección de métricas"""
        mock_metrics.return_value.collect.return_value = {'duration': 1.5}
        
        result = self.orchestrator.orchestrate_with_metrics('input')
        
        self.assertIn('duration', result['metrics'])

    def test_orchestrate_parallel_execution(self):
        """Test orquestación con ejecución paralela"""
        with patch('app.services.generation_orchestrator.ThreadPoolExecutor'):
            tasks = ['Task 1', 'Task 2', 'Task 3']
            
            result = self.orchestrator.orchestrate_parallel(tasks)
            
            self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
