"""
Tests unitarios para el servicio de validación
"""
import unittest
from app.services.validator import Validator


class TestValidator(unittest.TestCase):
    """Tests para Validator"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.validator = Validator()

    def test_validate_email_valid(self):
        """Test validación de email válido"""
        result = self.validator.validate_email('test@example.com')
        
        self.assertTrue(result)

    def test_validate_email_invalid(self):
        """Test validación de email inválido"""
        result = self.validator.validate_email('invalid-email')
        
        self.assertFalse(result)

    def test_validate_email_empty(self):
        """Test validación de email vacío"""
        result = self.validator.validate_email('')
        
        self.assertFalse(result)

    def test_validate_username_valid(self):
        """Test validación de username válido"""
        result = self.validator.validate_username('valid_user123')
        
        self.assertTrue(result)

    def test_validate_username_too_short(self):
        """Test validación de username muy corto"""
        result = self.validator.validate_username('ab')
        
        self.assertFalse(result)

    def test_validate_username_invalid_characters(self):
        """Test validación de username con caracteres inválidos"""
        result = self.validator.validate_username('user@name!')
        
        self.assertFalse(result)

    def test_validate_password_strong(self):
        """Test validación de contraseña fuerte"""
        result = self.validator.validate_password('StrongP@ss123')
        
        self.assertTrue(result)

    def test_validate_password_weak(self):
        """Test validación de contraseña débil"""
        result = self.validator.validate_password('weak')
        
        self.assertFalse(result)

    def test_validate_url_valid(self):
        """Test validación de URL válida"""
        result = self.validator.validate_url('https://example.com')
        
        self.assertTrue(result)

    def test_validate_url_invalid(self):
        """Test validación de URL inválida"""
        result = self.validator.validate_url('not-a-url')
        
        self.assertFalse(result)

    def test_validate_json_valid(self):
        """Test validación de JSON válido"""
        result = self.validator.validate_json('{"key": "value"}')
        
        self.assertTrue(result)

    def test_validate_json_invalid(self):
        """Test validación de JSON inválido"""
        result = self.validator.validate_json('{invalid json}')
        
        self.assertFalse(result)

    def test_validate_required_fields_complete(self):
        """Test validación de campos requeridos completos"""
        data = {'field1': 'value1', 'field2': 'value2'}
        required = ['field1', 'field2']
        
        result = self.validator.validate_required_fields(data, required)
        
        self.assertTrue(result)

    def test_validate_required_fields_missing(self):
        """Test validación de campos requeridos faltantes"""
        data = {'field1': 'value1'}
        required = ['field1', 'field2']
        
        result = self.validator.validate_required_fields(data, required)
        
        self.assertFalse(result)

    def test_validate_phone_number_valid(self):
        """Test validación de número telefónico válido"""
        result = self.validator.validate_phone('+1234567890')
        
        self.assertTrue(result)

    def test_validate_date_format_valid(self):
        """Test validación de formato de fecha válido"""
        result = self.validator.validate_date_format('2024-01-15', '%Y-%m-%d')
        
        self.assertTrue(result)

    def test_validate_date_format_invalid(self):
        """Test validación de formato de fecha inválido"""
        result = self.validator.validate_date_format('15/01/2024', '%Y-%m-%d')
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
