"""
Script de prueba para verificar la generación de PDFs localmente
Simula los datos que se enviarían desde el frontend
"""

import requests
import json
import base64
from datetime import datetime

# URL del servidor (cambiar según entorno)
BASE_URL = "http://localhost:5000"  # Local
# BASE_URL = "https://tu-app.railway.app"  # Railway

def test_jira_pdf_generation():
    """Prueba la generación de PDF de reportes Jira"""
    
    print("🧪 Probando generación de PDF de Jira...")
    
    # Datos de prueba simulando el frontend
    test_data = {
        "project_key": "PC",
        "format": "pdf",
        "chart_images": {
            "test_cases": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "bugs_severity": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        },
        "table_data": {
            "test_cases_by_person": [
                {"person": "Juan Pérez", "exitoso": 45, "en_progreso": 20, "fallado": 24, "total": 89},
                {"person": "María García", "exitoso": 30, "en_progreso": 15, "fallado": 10, "total": 55},
                {"person": "Carlos López", "exitoso": 25, "en_progreso": 10, "fallado": 5, "total": 40}
            ],
            "defects_by_person": [
                {"key": "PC-101", "assignee": "Juan Pérez", "status": "Open", "summary": "Error en login", "severity": "High"},
                {"key": "PC-102", "assignee": "María García", "status": "In Progress", "summary": "Bug en formulario", "severity": "Medium"},
                {"key": "PC-103", "assignee": "Carlos López", "status": "Done", "summary": "Error de validación", "severity": "Low"},
                {"key": "PC-104", "assignee": "Juan Pérez", "status": "Open", "summary": "Problema de performance", "severity": "Critical"}
            ]
        },
        "active_widgets": [],
        "widget_chart_images": {},
        "widget_data": {},
        "filters": {}
    }
    
    # Calcular métricas esperadas
    total_test_cases = sum(item['total'] for item in test_data['table_data']['test_cases_by_person'])
    successful = sum(item['exitoso'] for item in test_data['table_data']['test_cases_by_person'])
    in_progress = sum(item['en_progreso'] for item in test_data['table_data']['test_cases_by_person'])
    total_defects = len(test_data['table_data']['defects_by_person'])
    open_defects = sum(1 for d in test_data['table_data']['defects_by_person'] 
                       if d['status'].lower() not in ['done', 'closed', 'resolved'])
    
    print(f"\n📊 Métricas esperadas:")
    print(f"  Total Test Cases: {total_test_cases}")
    print(f"  Successful %: {round(successful/total_test_cases*100, 2)}%")
    print(f"  Real Coverage: {round((successful+in_progress)/total_test_cases*100, 2)}%")
    print(f"  Total Defects: {total_defects}")
    print(f"  Defect Rate: {round(total_defects/total_test_cases*100, 2)}%")
    print(f"  Open Defects: {open_defects}")
    print(f"  Closed Defects: {total_defects - open_defects}")
    
    try:
        # Hacer request al endpoint
        response = requests.post(
            f"{BASE_URL}/api/jira/download-report",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            # Guardar PDF
            filename = f"test_jira_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"\n✅ PDF generado exitosamente: {filename}")
            print(f"   Tamaño: {len(response.content)} bytes")
            print(f"\n🔍 Verificar en el PDF:")
            print(f"   - Los iconos deben aparecer (📋, ✅, 📊, 🐛, 📈, 🔓, 🔒)")
            print(f"   - Los porcentajes NO deben estar en 0%")
            print(f"   - Las tablas deben mostrar los datos correctamente")
            
        else:
            print(f"\n❌ Error al generar PDF:")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ No se pudo conectar al servidor en {BASE_URL}")
        print(f"   Asegúrate de que el servidor esté corriendo")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")


def test_metrics_pdf_generation():
    """Prueba la generación de PDF de métricas"""
    
    print("\n\n🧪 Probando generación de PDF de Métricas...")
    
    test_data = {
        "selected_types": ["generator", "jira"],
        "generator_metrics": {
            "total_generated": 150,
            "by_type": {
                "test_cases": 80,
                "user_stories": 50,
                "bugs": 20
            }
        },
        "jira_metrics": {
            "reports": {
                "count": 25,
                "byProject": {
                    "PC": 15,
                    "DEMO": 10
                },
                "lastDate": "2025-12-18"
            },
            "uploads": {
                "count": 10,
                "itemsCount": 500,
                "byProject": {
                    "PC": 300,
                    "DEMO": 200
                },
                "issueTypesDistribution": {
                    "Test Case": 250,
                    "Story": 150,
                    "Bug": 100
                }
            }
        },
        "chart_images": {}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/metrics/download-report",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            filename = f"test_metrics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"\n✅ PDF de métricas generado: {filename}")
            print(f"   Tamaño: {len(response.content)} bytes")
        else:
            print(f"\n❌ Error al generar PDF de métricas:")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ No se pudo conectar al servidor en {BASE_URL}")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST DE GENERACIÓN DE PDFs")
    print("=" * 60)
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"✅ Servidor disponible en {BASE_URL}")
    except:
        print(f"⚠️  No se pudo verificar el servidor en {BASE_URL}")
        print(f"   Asegúrate de que esté corriendo antes de continuar")
        print(f"   Ejecuta: python run.py")
        exit(1)
    
    # Ejecutar pruebas
    test_jira_pdf_generation()
    test_metrics_pdf_generation()
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")
    print("=" * 60)
