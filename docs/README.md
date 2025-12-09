# Nexus AI - Documentación Técnica

> **⚠️ IMPORTANTE**: Antes de desarrollar cualquier funcionalidad nueva, consulta las **[Guías de Arquitectura](../ARCHITECTURE_GUIDELINES.md)** para asegurarte de seguir las buenas prácticas del proyecto.

## 📚 Índice

1. [Arquitectura del Proyecto](#arquitectura-del-proyecto)
2. [Módulos Core](#módulos-core)
3. [Módulos Backend](#módulos-backend)
4. [Servicios](#servicios)
5. [Utilidades](#utilidades)
6. [Configuración](#configuración)
7. [Tests](#tests)

---

## Arquitectura del Proyecto

El proyecto está organizado en una estructura modular que separa responsabilidades:

```
app/
├── core/          # Núcleo de la aplicación (Flask, configuración)
├── backend/       # Lógica de negocio (generación de historias, matrices, Jira)
├── services/      # Servicios de negocio (SRP)
└── utils/         # Utilidades compartidas (archivos, reintentos, excepciones)
```

### Principios de Diseño

- **Separación de responsabilidades (SRP)**: Cada módulo tiene una función específica
- **Open/Closed Principle (OCP)**: Extensible sin modificar código existente
- **Reutilización**: Funciones comunes en `utils/` y `services/`
- **Configuración centralizada**: Todas las configuraciones en `config.py`
- **Manejo de errores**: Excepciones personalizadas para mejor debugging

---

## Módulos Core

### `app.core.app`

**Responsabilidad**: Aplicación principal Flask y endpoints de API

**Funcionalidades principales**:
- Endpoints REST para generación de historias y matrices
- Integración con Jira
- Manejo de archivos y descargas
- Procesamiento de documentos

**Endpoints principales**:
- `GET /` - Página principal
- `POST /api/agent/process` - Procesamiento con agente inteligente
- `POST /api/story` - Generación de historias de usuario
- `POST /api/matrix` - Generación de matrices de prueba

### `app.core.config`

**Responsabilidad**: Configuración centralizada del proyecto

Lee valores de variables de entorno con valores por defecto sensibles.

---

## Módulos Backend

### `app.backend.story_backend`

**Responsabilidad**: Generación de historias de usuario desde documentos

### `app.backend.matrix_backend`

**Responsabilidad**: Generación de matrices de casos de prueba

### `app.backend.agent_manager`

**Responsabilidad**: Orquestación de generación usando Factory Pattern

### `app.backend.generators`

**Responsabilidad**: Generadores con interfaces (OCP)

- `base.py` - Interfaz Generator
- `factory.py` - Factory Pattern
- `story_generator.py` - Generador de historias
- `matrix_generator.py` - Generador de matrices

---

## Servicios

Servicios de negocio que implementan SRP:

### `app.services.file_manager`

**Responsabilidad**: Gestión de archivos temporales y subidos

### `app.services.document_analyzer`

**Responsabilidad**: Análisis de contenido de documentos

### `app.services.data_transformer`

**Responsabilidad**: Transformación y normalización de datos

### `app.services.validator`

**Responsabilidad**: Validación de historias y casos de prueba

### `app.services.file_generator`

**Responsabilidad**: Generación de archivos CSV, JSON y ZIP

### `app.services.generation_orchestrator`

**Responsabilidad**: Orquestación completa del proceso de generación

---

## Utilidades

### `app.utils.file_utils`

**Responsabilidad**: Utilidades para procesamiento de archivos

### `app.utils.retry_utils`

**Responsabilidad**: Utilidades para reintentos con backoff exponencial

### `app.utils.exceptions`

**Responsabilidad**: Excepciones personalizadas del proyecto

### `app.utils.document_chunker`

**Responsabilidad**: División de documentos en chunks manejables

### `app.utils.decorators`

**Responsabilidad**: Decoradores reutilizables para validación y manejo de errores

---

## Configuración

Toda la configuración se encuentra en `app.core.config.Config`:

- Variables de entorno leídas desde `.env`
- Valores por defecto sensibles
- Validación de configuraciones críticas

---

## Tests

Ver [tests/README.md](../tests/README.md) para más información sobre tests.

---

## 📚 Referencias

- **[ARCHITECTURE_GUIDELINES.md](ARCHITECTURE_GUIDELINES.md)** - Guías completas de arquitectura
- **[ANALISIS_SEGURIDAD.md](ANALISIS_SEGURIDAD.md)** - Análisis de seguridad y vulnerabilidades
- **[GUIA_PRUEBAS.md](GUIA_PRUEBAS.md)** - Guía de pruebas del sistema de autenticación
- **[GUIA_ADMINISTRACION.md](GUIA_ADMINISTRACION.md)** - Guía de administración de usuarios
- **[RESUMEN_IMPLEMENTACION_AUTENTICACION.md](RESUMEN_IMPLEMENTACION_AUTENTICACION.md)** - Resumen de implementación del sistema de autenticación

