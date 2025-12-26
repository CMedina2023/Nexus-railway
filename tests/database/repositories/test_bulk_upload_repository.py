"""
Tests unitarios para repositorio de carga masiva
"""
import unittest
from unittest.mock import patch, MagicMock
from app.database.repositories.bulk_upload_repository import BulkUploadRepository


class TestBulkUploadRepository(unittest.TestCase):
    """Tests para BulkUploadRepository"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.mock_db = MagicMock()
        self.repository = BulkUploadRepository(self.mock_db)

    def test_create_bulk_upload_success(self):
        """Test creación de registro de carga masiva exitosa"""
        upload_data = {
            'user_id': 1,
            'file_name': 'issues.csv',
            'total_records': 100
        }
        
        self.mock_db.execute.return_value.lastrowid = 1
        
        result = self.repository.create(upload_data)
        
        self.assertEqual(result, 1)

    def test_get_upload_by_id_success(self):
        """Test obtener carga por ID exitoso"""
        self.mock_db.execute.return_value.fetchone.return_value = {
            'id': 1,
            'file_name': 'issues.csv'
        }
        
        result = self.repository.get_by_id(1)
        
        self.assertEqual(result['id'], 1)

    def test_get_uploads_by_user(self):
        """Test obtener cargas por usuario"""
        self.mock_db.execute.return_value.fetchall.return_value = [
            {'id': 1, 'user_id': 1},
            {'id': 2, 'user_id': 1}
        ]
        
        result = self.repository.get_by_user(1)
        
        self.assertEqual(len(result), 2)

    def test_update_upload_status(self):
        """Test actualización de estado de carga"""
        self.mock_db.execute.return_value.rowcount = 1
        
        result = self.repository.update_status(1, 'completed')
        
        self.assertTrue(result)

    def test_get_upload_statistics(self):
        """Test obtener estadísticas de carga"""
        self.mock_db.execute.return_value.fetchone.return_value = {
            'total_records': 100,
            'successful': 95,
            'failed': 5
        }
        
        result = self.repository.get_statistics(1)
        
        self.assertEqual(result['successful'], 95)

    def test_get_failed_records(self):
        """Test obtener registros fallidos"""
        self.mock_db.execute.return_value.fetchall.return_value = [
            {'record_id': 1, 'error': 'Invalid data'},
            {'record_id': 2, 'error': 'Missing field'}
        ]
        
        result = self.repository.get_failed_records(1)
        
        self.assertEqual(len(result), 2)

    def test_delete_upload_success(self):
        """Test eliminación de carga exitosa"""
        self.mock_db.execute.return_value.rowcount = 1
        
        result = self.repository.delete(1)
        
        self.assertTrue(result)

    def test_get_recent_uploads(self):
        """Test obtener cargas recientes"""
        self.mock_db.execute.return_value.fetchall.return_value = [
            {'id': 3, 'created_at': '2024-01-03'},
            {'id': 2, 'created_at': '2024-01-02'}
        ]
        
        result = self.repository.get_recent(limit=2)
        
        self.assertEqual(len(result), 2)

    def test_update_progress(self):
        """Test actualización de progreso de carga"""
        self.mock_db.execute.return_value.rowcount = 1
        
        result = self.repository.update_progress(1, 50)
        
        self.assertTrue(result)

    def test_get_uploads_by_status(self):
        """Test obtener cargas por estado"""
        self.mock_db.execute.return_value.fetchall.return_value = [
            {'id': 1, 'status': 'in_progress'},
            {'id': 2, 'status': 'in_progress'}
        ]
        
        result = self.repository.get_by_status('in_progress')
        
        self.assertEqual(len(result), 2)


if __name__ == '__main__':
    unittest.main()
