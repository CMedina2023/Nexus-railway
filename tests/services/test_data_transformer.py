"""
Tests unitarios para el transformador de datos
"""
import unittest
from app.services.data_transformer import DataTransformer


class TestDataTransformer(unittest.TestCase):
    """Tests para DataTransformer"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.transformer = DataTransformer()

    def test_transform_to_json(self):
        """Test transformación a JSON"""
        data = {'key': 'value', 'number': 123}
        
        result = self.transformer.to_json(data)
        
        self.assertIsInstance(result, str)
        self.assertIn('key', result)

    def test_transform_from_json(self):
        """Test transformación desde JSON"""
        json_str = '{"key": "value", "number": 123}'
        
        result = self.transformer.from_json(json_str)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['key'], 'value')

    def test_transform_csv_to_dict(self):
        """Test transformación de CSV a diccionario"""
        csv_data = "name,age\nJohn,30\nJane,25"
        
        result = self.transformer.csv_to_dict(csv_data)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'John')

    def test_transform_dict_to_csv(self):
        """Test transformación de diccionario a CSV"""
        data = [
            {'name': 'John', 'age': 30},
            {'name': 'Jane', 'age': 25}
        ]
        
        result = self.transformer.dict_to_csv(data)
        
        self.assertIn('name,age', result)
        self.assertIn('John,30', result)

    def test_flatten_nested_dict(self):
        """Test aplanar diccionario anidado"""
        nested = {
            'user': {
                'name': 'John',
                'address': {
                    'city': 'NYC'
                }
            }
        }
        
        result = self.transformer.flatten_dict(nested)
        
        self.assertIn('user.name', result)
        self.assertIn('user.address.city', result)

    def test_normalize_data(self):
        """Test normalización de datos"""
        data = [
            {'value': 10},
            {'value': 20},
            {'value': 30}
        ]
        
        result = self.transformer.normalize(data, 'value')
        
        self.assertGreaterEqual(result[0]['value'], 0)
        self.assertLessEqual(result[-1]['value'], 1)

    def test_aggregate_data(self):
        """Test agregación de datos"""
        data = [
            {'category': 'A', 'value': 10},
            {'category': 'A', 'value': 20},
            {'category': 'B', 'value': 15}
        ]
        
        result = self.transformer.aggregate(data, 'category', 'sum')
        
        self.assertEqual(result['A'], 30)
        self.assertEqual(result['B'], 15)

    def test_pivot_data(self):
        """Test pivoteo de datos"""
        data = [
            {'date': '2024-01', 'category': 'A', 'value': 10},
            {'date': '2024-01', 'category': 'B', 'value': 20}
        ]
        
        result = self.transformer.pivot(data, 'date', 'category', 'value')
        
        self.assertIn('2024-01', result)


if __name__ == '__main__':
    unittest.main()
