# Guía de Ejecución de Tests

## Instalación de Dependencias

```bash
pip install pytest pytest-cov pytest-mock
```

## Ejecutar Todos los Tests

```bash
pytest
```

## Ejecutar Tests por Módulo

### Tests de Autenticación
```bash
pytest tests/auth/
```

### Tests de Backend
```bash
pytest tests/backend/
```

### Tests de Base de Datos
```bash
pytest tests/database/
```

### Tests de Servicios
```bash
pytest tests/services/
```

### Tests de Utilidades
```bash
pytest tests/utils/
```

### Tests de Modelos
```bash
pytest tests/models/
```

### Tests de Rutas
```bash
pytest tests/routes/
```

### Tests de Integración
```bash
pytest tests/integration/
```

## Ejecutar Tests con Cobertura

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

## Ver Reporte de Cobertura

Después de ejecutar los tests con cobertura, abre:
```
htmlcov/index.html
```

## Ejecutar Tests Específicos

```bash
# Un archivo específico
pytest tests/auth/test_user_service.py

# Una clase específica
pytest tests/auth/test_user_service.py::TestUserService

# Un test específico
pytest tests/auth/test_user_service.py::TestUserService::test_create_user_success
```

## Ejecutar Tests por Markers

```bash
# Solo tests unitarios
pytest -m unit

# Solo tests de integración
pytest -m integration

# Excluir tests lentos
pytest -m "not slow"
```

## Generar Reporte XML (para CI/CD)

```bash
pytest --cov=app --cov-report=xml --junitxml=test-results.xml
```

## Objetivo de Cobertura

El proyecto tiene como objetivo mantener una cobertura mínima del **80%**.
