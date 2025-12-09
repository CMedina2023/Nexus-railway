"""
Tests para utilidades de archivos
"""
import unittest
import os
import tempfile
from unittest.mock import Mock, patch, mock_open

from app.utils.file_utils import extract_text_from_file, get_file_size_mb, is_valid_file_format
from app.utils.exceptions import FileProcessingError


class TestFileUtils(unittest.TestCase):
    """Tests para utilidades de archivos"""
    
    def test_is_valid_file_format(self):
        """Verifica validación de formatos de archivo"""
        self.assertTrue(is_valid_file_format("documento.pdf"))
        self.assertTrue(is_valid_file_format("documento.docx"))
        self.assertTrue(is_valid_file_format("documento.doc"))
        self.assertFalse(is_valid_file_format("documento.txt"))
        self.assertFalse(is_valid_file_format("documento.jpg"))
    
    def test_get_file_size_mb(self):
        """Verifica cálculo de tamaño de archivo"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * (2 * 1024 * 1024))  # 2 MB
            tmp_path = tmp.name
        
        try:
            size = get_file_size_mb(tmp_path)
            self.assertAlmostEqual(size, 2.0, places=1)
        finally:
            os.unlink(tmp_path)


if __name__ == '__main__':
    unittest.main()

