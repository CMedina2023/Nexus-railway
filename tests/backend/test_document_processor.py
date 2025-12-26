"""
Tests unitarios para el procesador de documentos
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
from app.backend.document_processor import DocumentProcessor


class TestDocumentProcessor(unittest.TestCase):
    """Tests para DocumentProcessor"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.document_processor = DocumentProcessor()

    @patch('builtins.open', new_callable=mock_open, read_data='test content')
    def test_read_file_success(self, mock_file):
        """Test lectura de archivo exitosa"""
        result = self.document_processor.read_file('test.txt')
        
        self.assertEqual(result, 'test content')
        mock_file.assert_called_once_with('test.txt', 'r', encoding='utf-8')

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_read_file_not_found(self, mock_file):
        """Test lectura de archivo no encontrado"""
        with self.assertRaises(FileNotFoundError):
            self.document_processor.read_file('nonexistent.txt')

    @patch('builtins.open', new_callable=mock_open, read_data=b'PDF content')
    def test_process_pdf_success(self, mock_file):
        """Test procesamiento de PDF exitoso"""
        with patch('app.backend.document_processor.PyPDF2.PdfReader') as mock_pdf:
            mock_pdf.return_value.pages = [MagicMock(extract_text=lambda: 'PDF text')]
            
            result = self.document_processor.process_pdf('test.pdf')
            
            self.assertIsNotNone(result)

    def test_extract_text_from_docx(self):
        """Test extracción de texto de DOCX"""
        with patch('app.backend.document_processor.Document') as mock_doc:
            mock_doc.return_value.paragraphs = [
                MagicMock(text='Paragraph 1'),
                MagicMock(text='Paragraph 2')
            ]
            
            result = self.document_processor.extract_text_from_docx('test.docx')
            
            self.assertIn('Paragraph 1', result)
            self.assertIn('Paragraph 2', result)

    def test_validate_file_extension_valid(self):
        """Test validación de extensión de archivo válida"""
        result = self.document_processor.validate_file_extension('test.pdf', ['.pdf', '.docx'])
        
        self.assertTrue(result)

    def test_validate_file_extension_invalid(self):
        """Test validación de extensión de archivo inválida"""
        result = self.document_processor.validate_file_extension('test.txt', ['.pdf', '.docx'])
        
        self.assertFalse(result)

    @patch('builtins.open', new_callable=mock_open)
    def test_save_processed_content(self, mock_file):
        """Test guardado de contenido procesado"""
        content = 'processed content'
        
        self.document_processor.save_processed_content(content, 'output.txt')
        
        mock_file.assert_called_once()

    def test_chunk_document_by_size(self):
        """Test división de documento por tamaño"""
        large_text = 'word ' * 1000
        
        chunks = self.document_processor.chunk_document(large_text, chunk_size=100)
        
        self.assertGreater(len(chunks), 1)

    def test_extract_metadata_from_file(self):
        """Test extracción de metadatos de archivo"""
        with patch('os.path.getsize', return_value=1024):
            with patch('os.path.getmtime', return_value=1234567890):
                metadata = self.document_processor.extract_metadata('test.txt')
                
                self.assertIn('size', metadata)
                self.assertIn('modified', metadata)

    def test_process_empty_document(self):
        """Test procesamiento de documento vacío"""
        with patch('builtins.open', new_callable=mock_open, read_data=''):
            result = self.document_processor.read_file('empty.txt')
            
            self.assertEqual(result, '')


if __name__ == '__main__':
    unittest.main()
