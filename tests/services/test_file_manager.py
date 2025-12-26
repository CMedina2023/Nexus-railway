"""
Tests unitarios para el gestor de archivos
"""
import unittest
from unittest.mock import patch, mock_open, MagicMock
from app.services.file_manager import FileManager


class TestFileManager(unittest.TestCase):
    """Tests para FileManager"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.file_manager = FileManager()

    @patch('builtins.open', new_callable=mock_open, read_data='test content')
    def test_read_text_file(self, mock_file):
        """Test lectura de archivo de texto"""
        result = self.file_manager.read_text_file('test.txt')
        
        self.assertEqual(result, 'test content')

    @patch('builtins.open', new_callable=mock_open)
    def test_write_text_file(self, mock_file):
        """Test escritura de archivo de texto"""
        self.file_manager.write_text_file('output.txt', 'content')
        
        mock_file.assert_called_once()

    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    def test_delete_file(self, mock_remove, mock_exists):
        """Test eliminación de archivo"""
        result = self.file_manager.delete_file('test.txt')
        
        self.assertTrue(result)
        mock_remove.assert_called_once()

    @patch('os.makedirs')
    def test_create_directory(self, mock_makedirs):
        """Test creación de directorio"""
        self.file_manager.create_directory('new_dir')
        
        mock_makedirs.assert_called_once()

    @patch('shutil.copy2')
    def test_copy_file(self, mock_copy):
        """Test copia de archivo"""
        self.file_manager.copy_file('source.txt', 'dest.txt')
        
        mock_copy.assert_called_once()

    @patch('shutil.move')
    def test_move_file(self, mock_move):
        """Test mover archivo"""
        self.file_manager.move_file('source.txt', 'dest.txt')
        
        mock_move.assert_called_once()

    @patch('os.listdir', return_value=['file1.txt', 'file2.txt'])
    def test_list_files(self, mock_listdir):
        """Test listar archivos"""
        result = self.file_manager.list_files('directory')
        
        self.assertEqual(len(result), 2)

    @patch('os.path.getsize', return_value=2048)
    def test_get_file_size(self, mock_getsize):
        """Test obtener tamaño de archivo"""
        result = self.file_manager.get_file_size('test.txt')
        
        self.assertEqual(result, 2048)

    def test_get_file_extension(self):
        """Test obtener extensión de archivo"""
        result = self.file_manager.get_extension('document.pdf')
        
        self.assertEqual(result, '.pdf')

    @patch('zipfile.ZipFile')
    def test_compress_file(self, mock_zip):
        """Test comprimir archivo"""
        self.file_manager.compress_file('file.txt', 'archive.zip')
        
        mock_zip.assert_called_once()


if __name__ == '__main__':
    unittest.main()
