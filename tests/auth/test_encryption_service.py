"""
Tests unitarios para el servicio de encriptación
"""
import unittest
from unittest.mock import patch, MagicMock
from app.auth.encryption_service import EncryptionService


class TestEncryptionService(unittest.TestCase):
    """Tests para EncryptionService"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.encryption_service = EncryptionService()

    @patch('app.auth.encryption_service.Fernet')
    def test_encrypt_data_success(self, mock_fernet):
        """Test encriptación exitosa de datos"""
        mock_cipher = MagicMock()
        mock_cipher.encrypt.return_value = b'encrypted_data'
        mock_fernet.return_value = mock_cipher

        result = self.encryption_service.encrypt_data("test_data")
        
        self.assertIsNotNone(result)
        mock_cipher.encrypt.assert_called_once()

    @patch('app.auth.encryption_service.Fernet')
    def test_decrypt_data_success(self, mock_fernet):
        """Test desencriptación exitosa de datos"""
        mock_cipher = MagicMock()
        mock_cipher.decrypt.return_value = b'decrypted_data'
        mock_fernet.return_value = mock_cipher

        result = self.encryption_service.decrypt_data(b'encrypted_data')
        
        self.assertIsNotNone(result)
        mock_cipher.decrypt.assert_called_once()

    def test_encrypt_empty_string(self):
        """Test encriptación de string vacío"""
        result = self.encryption_service.encrypt_data("")
        self.assertIsNotNone(result)

    def test_decrypt_invalid_data(self):
        """Test desencriptación de datos inválidos"""
        with self.assertRaises(Exception):
            self.encryption_service.decrypt_data(b'invalid_data')

    @patch('app.auth.encryption_service.Fernet')
    def test_encrypt_unicode_data(self, mock_fernet):
        """Test encriptación de datos unicode"""
        mock_cipher = MagicMock()
        mock_cipher.encrypt.return_value = b'encrypted_unicode'
        mock_fernet.return_value = mock_cipher

        result = self.encryption_service.encrypt_data("测试数据")
        
        self.assertIsNotNone(result)

    def test_encrypt_none_value(self):
        """Test encriptación de valor None"""
        with self.assertRaises((TypeError, AttributeError)):
            self.encryption_service.encrypt_data(None)

    @patch('app.auth.encryption_service.Fernet')
    def test_encrypt_decrypt_roundtrip(self, mock_fernet):
        """Test ciclo completo de encriptación y desencriptación"""
        original_data = "test_data"
        mock_cipher = MagicMock()
        mock_cipher.encrypt.return_value = b'encrypted'
        mock_cipher.decrypt.return_value = original_data.encode()
        mock_fernet.return_value = mock_cipher

        encrypted = self.encryption_service.encrypt_data(original_data)
        decrypted = self.encryption_service.decrypt_data(encrypted)
        
        self.assertEqual(decrypted.decode(), original_data)


if __name__ == '__main__':
    unittest.main()
