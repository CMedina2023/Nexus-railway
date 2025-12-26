"""
Tests unitarios para utilidades de archivos
"""
import unittest
from unittest.mock import patch, mock_open, MagicMock
from app.utils.file_utils import FileUtils


class TestFileUtils(unittest.TestCase):
    """Tests para FileUtils"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.file_utils = FileUtils()

    @patch('builtins.open', new_callable=mock_open, read_data='test content')
    def test_read_file_success(self, mock_file):
        """Test lectura de archivo exitosa"""
        result = self.file_utils.read_file('test.txt')
        
        self.assertEqual(result, 'test content')

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_read_file_not_found(self, mock_file):
        """Test lectura de archivo no encontrado"""
        with self.assertRaises(FileNotFoundError):
            self.file_utils.read_file('nonexistent.txt')

    @patch('builtins.open', new_callable=mock_open)
    def test_write_file_success(self, mock_file):
        """Test escritura de archivo exitosa"""
        self.file_utils.write_file('output.txt', 'content')
        
        mock_file.assert_called_once_with('output.txt', 'w', encoding='utf-8')

    @patch('os.path.exists', return_value=True)
    def test_file_exists_true(self, mock_exists):
        """Test verificación de existencia de archivo positiva"""
        result = self.file_utils.file_exists('test.txt')
        
        self.assertTrue(result)

    @patch('os.path.exists', return_value=False)
    def test_file_exists_false(self, mock_exists):
        """Test verificación de existencia de archivo negativa"""
        result = self.file_utils.file_exists('nonexistent.txt')
        
        self.assertFalse(result)

    @patch('os.remove')
    def test_delete_file_success(self, mock_remove):
        """Test eliminación de archivo exitosa"""
        self.file_utils.delete_file('test.txt')
        
        mock_remove.assert_called_once_with('test.txt')

    @patch('os.makedirs')
    def test_create_directory_success(self, mock_makedirs):
        """Test creación de directorio exitosa"""
        self.file_utils.create_directory('new_dir')
        
        mock_makedirs.assert_called_once()

    @patch('os.path.getsize', return_value=1024)
    def test_get_file_size(self, mock_getsize):
        """Test obtener tamaño de archivo"""
        result = self.file_utils.get_file_size('test.txt')
        
        self.assertEqual(result, 1024)

    @patch('os.listdir', return_value=['file1.txt', 'file2.txt'])
    def test_list_files_in_directory(self, mock_listdir):
        """Test listar archivos en directorio"""
        result = self.file_utils.list_files('directory')
        
        self.assertEqual(len(result), 2)

    def test_get_file_extension(self):
        """Test obtener extensión de archivo"""
        result = self.file_utils.get_file_extension('document.pdf')
        
        self.assertEqual(result, '.pdf')

    @patch('shutil.copy')
    def test_copy_file_success(self, mock_copy):
        """Test copia de archivo exitosa"""
        self.file_utils.copy_file('source.txt', 'destination.txt')
        
        mock_copy.assert_called_once()

    @patch('shutil.move')
    def test_move_file_success(self, mock_move):
        """Test mover archivo exitoso"""
        self.file_utils.move_file('source.txt', 'destination.txt')
        
        mock_move.assert_called_once()


if __name__ == '__main__':
    unittest.main()
