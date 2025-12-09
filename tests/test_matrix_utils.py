"""
Tests para utilidades de matrices
"""
import unittest
from app.utils.matrix_utils import extract_matrix_data


class TestMatrixUtils(unittest.TestCase):
    """Tests para utilidades de matrices"""
    
    def test_extract_matrix_data_from_list(self):
        """Verifica extracción de matriz desde lista"""
        data = [{"id": "TC001", "titulo": "Test 1"}]
        result = extract_matrix_data(data)
        self.assertEqual(result, data)
    
    def test_extract_matrix_data_from_dict(self):
        """Verifica extracción de matriz desde diccionario"""
        data = {"matrix": [{"id": "TC001"}]}
        result = extract_matrix_data(data)
        self.assertEqual(result, [{"id": "TC001"}])
    
    def test_extract_matrix_data_none(self):
        """Verifica que retorna None para datos inválidos"""
        result = extract_matrix_data(None)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()

