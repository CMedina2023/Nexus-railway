# 🤖 NEXUS AI - Sistema de Generación de Historias de Usuario con IA

> **Sistema inteligente para generar historias de usuario, matrices de trazabilidad y análisis de proyectos usando Google Gemini AI**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Render](https://img.shields.io/badge/Deploy-Render-purple.svg)](https://render.com)

---

## 📋 TABLA DE CONTENIDOS

- [Características](#-características)
- [Tecnologías](#-tecnologías)
- [Instalación Local](#-instalación-local)
- [Despliegue en Render](#-despliegue-en-render)
- [Uso](#-uso)
- [Documentación](#-documentación)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Testing](#-testing)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## ✨ CARACTERÍSTICAS

### 🎯 Generación de Historias de Usuario
- ✅ Análisis inteligente de documentos (PDF, DOCX, TXT)
- ✅ Generación automática de historias de usuario con formato estándar
- ✅ Criterios de aceptación detallados
- ✅ Exportación a Word, CSV y HTML

### 📊 Matriz de Trazabilidad
- ✅ Generación automática de matrices de trazabilidad
- ✅ Vinculación de requisitos con casos de prueba
- ✅ Exportación a múltiples formatos

### 🔗 Integración con Jira
- ✅ Conexión segura con Jira Cloud
- ✅ Creación masiva de issues
- ✅ Sincronización de historias de usuario
- ✅ Generación de reportes de métricas
- ✅ Dashboard de proyectos

### 🔐 Sistema de Autenticación
- ✅ Registro y login seguro
- ✅ Gestión de usuarios y permisos
- ✅ Roles: Admin y Usuario
- ✅ Encriptación de tokens
- ✅ Sesiones seguras

### 📈 Dashboard y Métricas
- ✅ Dashboard personal de usuario
- ✅ Dashboard administrativo
- ✅ Historial de actividades
- ✅ Métricas de proyectos Jira
- ✅ Caché inteligente de métricas

---

## 🛠️ TECNOLOGÍAS

### Backend
- **Python 3.11+**
- **Flask 3.0** - Framework web
- **SQLAlchemy** - ORM para base de datos
- **PostgreSQL** - Base de datos (producción)
- **SQLite** - Base de datos (desarrollo)

### IA y Procesamiento
- **Google Gemini AI** - Generación de contenido
- **python-docx** - Procesamiento de documentos Word
- **pypdf** - Procesamiento de PDFs
- **Playwright** - Generación de PDFs

### Seguridad
- **Flask-Login** - Gestión de sesiones
- **bcrypt** - Hash de contraseñas
- **cryptography** - Encriptación de tokens
- **Flask-WTF** - Protección CSRF
- **Flask-Limiter** - Rate limiting

### Integraciones
- **Jira API** - Integración con Jira Cloud
- **Requests** - Cliente HTTP

---

## 💻 INSTALACIÓN LOCAL

### Requisitos Previos

- Python 3.11 o superior
- pip (gestor de paquetes de Python)
- Git
- Google API Key (Gemini)

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/nexus-ai.git
cd nexus-ai
```

### Paso 2: Crear Entorno Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar Dependencias

```bash
pip install -r requirements.txt
playwright install chromium
```

### Paso 4: Configurar Variables de Entorno

Copia el archivo de ejemplo y configura tus variables:

```bash
# Windows
copy env.example .env

# Linux/Mac
cp env.example .env
```

Edita `.env` y configura al menos:

```env
GOOGLE_API_KEY=tu_google_api_key_aqui
SECRET_KEY=genera_una_clave_aleatoria
ENCRYPTION_KEY=genera_una_fernet_key
```

**Generar claves**:

```bash
python scripts/generar_claves.py
```

### Paso 5: Inicializar Base de Datos

```bash
python scripts/init_auth.py
```

Sigue las instrucciones para crear tu usuario administrador.

### Paso 6: Ejecutar la Aplicación

```bash
python run.py
```

La aplicación estará disponible en: http://localhost:5000

---

## 🚀 DESPLIEGUE EN RENDER

### ¿Listo para Producción?

**¡SÍ!** Este proyecto está completamente configurado para desplegarse en Render.

### Documentación de Despliegue

Tenemos documentación completa para todos los niveles:

#### 📖 Para Principiantes (Nunca he desplegado nada)

```
GUIA_DESPLIEGUE_RENDER.md
```

**Incluye**:
- Explicación de qué es Render
- Cómo crear cuenta paso a paso
- Cómo obtener API keys
- Solución de problemas detallada
- Capturas y ejemplos

**Tiempo**: 30-45 minutos

#### ✅ Checklist Interactivo

```
CHECKLIST_DESPLIEGUE.md
```

**Incluye**:
- Lista de verificación por fases
- Checkboxes para marcar progreso
- Verificación de cada paso

**Tiempo**: 20-30 minutos

#### ⚡ Referencia Rápida (Para Expertos)

```
DEPLOY_README.md
```

**Incluye**:
- 5 pasos rápidos
- Comandos útiles
- Solución rápida de problemas

**Tiempo**: 10-15 minutos

### Inicio Rápido (5 Pasos)

```bash
# 1. Generar claves secretas
python scripts/generar_claves.py

# 2. Subir a GitHub
git add .
git commit -m "Preparar para despliegue"
git push origin main

# 3. Crear PostgreSQL en Render (desde la web)
# 4. Crear Web Service en Render (desde la web)
# 5. Configurar variables de entorno en Render
```

**Documentación completa**: Ver `GUIA_DESPLIEGUE_RENDER.md`

---

## 📖 USO

### 1. Iniciar Sesión

Accede a la aplicación y usa tus credenciales:

```
http://localhost:5000/auth/login
```

### 2. Generar Historia de Usuario

1. Ve a la página principal
2. Sube un documento (PDF, DOCX, TXT)
3. Configura los parámetros de generación
4. Click en "Generar Historia"
5. Descarga el resultado en el formato deseado

### 3. Generar Matriz de Trazabilidad

1. Sube un documento con requisitos
2. Selecciona "Generar Matriz"
3. Configura los parámetros
4. Descarga la matriz generada

### 4. Integración con Jira

1. Ve a tu perfil → Configuración de Jira
2. Ingresa tus credenciales de Jira
3. Selecciona un proyecto
4. Crea issues masivamente desde historias generadas

### 5. Ver Dashboard

- **Usuario**: Ve tu historial de actividades
- **Admin**: Ve todos los usuarios y actividades del sistema

---

## 📚 DOCUMENTACIÓN

### Documentación Técnica

- **[docs/README.md](docs/README.md)** - Documentación técnica completa
- **[docs/ARCHITECTURE_GUIDELINES.md](docs/ARCHITECTURE_GUIDELINES.md)** - Guías de arquitectura y principios SOLID
- **[docs/ANALISIS_SEGURIDAD.md](docs/ANALISIS_SEGURIDAD.md)** - Análisis de seguridad
- **[docs/GUIA_PRUEBAS.md](docs/GUIA_PRUEBAS.md)** - Guía de testing

### Documentación de Despliegue

- **[GUIA_DESPLIEGUE_RENDER.md](GUIA_DESPLIEGUE_RENDER.md)** - Guía completa de despliegue
- **[CHECKLIST_DESPLIEGUE.md](CHECKLIST_DESPLIEGUE.md)** - Checklist interactivo
- **[DEPLOY_README.md](DEPLOY_README.md)** - Referencia rápida
- **[GENERAR_CLAVES.md](GENERAR_CLAVES.md)** - Cómo generar claves secretas
- **[RESUMEN_DESPLIEGUE.md](RESUMEN_DESPLIEGUE.md)** - Resumen de archivos creados

### Testing

- **[tests/README.md](tests/README.md)** - Guía de testing

---

## 📁 ESTRUCTURA DEL PROYECTO

```
nexus-ai/
├── app/
│   ├── auth/              # Sistema de autenticación
│   ├── backend/           # Lógica de negocio
│   │   ├── generators/    # Generadores de contenido
│   │   └── jira/          # Integración con Jira
│   ├── core/              # Configuración y app principal
│   ├── database/          # Modelos y repositorios
│   ├── models/            # Modelos de datos
│   ├── services/          # Servicios de negocio
│   └── utils/             # Utilidades y helpers
├── docs/                  # Documentación técnica
├── scripts/               # Scripts de utilidad
├── static/                # Archivos estáticos (CSS, JS)
├── templates/             # Plantillas HTML
├── tests/                 # Tests unitarios
├── build.sh               # Script de build para Render
├── Procfile               # Configuración de Render
├── render.yaml            # Configuración automatizada
├── requirements.txt       # Dependencias Python
└── run.py                 # Punto de entrada
```

---

## 🧪 TESTING

### Ejecutar Tests

```bash
# Todos los tests
python tests/run_all_tests.py

# Tests específicos
python -m pytest tests/test_agent_manager.py
python -m pytest tests/test_auth_system.py
```

### Tests Disponibles

- ✅ Tests de autenticación
- ✅ Tests de generadores
- ✅ Tests de utilidades
- ✅ Tests de configuración
- ✅ Tests de protección de rutas

**Ver**: `tests/README.md` para más información

---

## 🏗️ ARQUITECTURA

### Principios SOLID

Este proyecto sigue estrictamente los principios SOLID:

- **S**ingle Responsibility Principle
- **O**pen/Closed Principle
- **L**iskov Substitution Principle
- **I**nterface Segregation Principle
- **D**ependency Inversion Principle

**Ver**: `docs/ARCHITECTURE_GUIDELINES.md` para guías completas

### Patrones de Diseño

- ✅ Factory Pattern (Generadores)
- ✅ Dependency Injection (Servicios)
- ✅ Strategy Pattern (Procesamiento)
- ✅ Decorator Pattern (Validación, manejo de errores)

---

## 🔐 SEGURIDAD

### Características de Seguridad

- ✅ Hash de contraseñas con bcrypt
- ✅ Encriptación de tokens con Fernet
- ✅ Protección CSRF
- ✅ Rate limiting
- ✅ Sesiones seguras
- ✅ Validación de entrada
- ✅ HTTPS en producción

**Ver**: `docs/ANALISIS_SEGURIDAD.md` para análisis completo

---

## 🤝 CONTRIBUIR

### Cómo Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Guías de Contribución

- Sigue los principios SOLID (ver `docs/ARCHITECTURE_GUIDELINES.md`)
- Escribe tests para nuevas funcionalidades
- Documenta tu código con docstrings
- Usa type hints en funciones
- Sigue las convenciones de nomenclatura del proyecto

---

## 📝 CHANGELOG

### v1.0.0 (Diciembre 2025)

**Nuevas Características**:
- ✅ Sistema completo de autenticación
- ✅ Dashboard de usuario y admin
- ✅ Integración completa con Jira
- ✅ Generación de historias de usuario
- ✅ Generación de matrices de trazabilidad
- ✅ Sistema de métricas con caché
- ✅ Configuración para despliegue en Render

**Mejoras**:
- ✅ Refactorización completa siguiendo SOLID
- ✅ Separación de responsabilidades
- ✅ Servicios especializados
- ✅ Manejo de errores robusto
- ✅ Documentación completa

---

## 📄 LICENCIA

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

## 👥 AUTORES

- **Tu Nombre** - *Desarrollo inicial* - [GitHub](https://github.com/tu-usuario)

---

## 🙏 AGRADECIMIENTOS

- Google Gemini AI por la API de generación de contenido
- Atlassian por la API de Jira
- Render por la plataforma de despliegue
- La comunidad de Flask por el excelente framework

---

## 📞 SOPORTE

### Documentación

- 📖 [Guía de Despliegue](GUIA_DESPLIEGUE_RENDER.md)
- 📚 [Documentación Técnica](docs/README.md)
- 🧪 [Guía de Testing](tests/README.md)

### Contacto

- 📧 Email: tu-email@ejemplo.com
- 🐛 Issues: [GitHub Issues](https://github.com/tu-usuario/nexus-ai/issues)
- 💬 Discusiones: [GitHub Discussions](https://github.com/tu-usuario/nexus-ai/discussions)

---

## 🎯 ROADMAP

### Próximas Características

- [ ] Integración con más herramientas (Azure DevOps, GitHub Projects)
- [ ] Soporte para más formatos de documentos
- [ ] API REST completa
- [ ] Modo oscuro en la interfaz
- [ ] Exportación a más formatos
- [ ] Plantillas personalizables
- [ ] Análisis de sentimiento en historias
- [ ] Sugerencias automáticas de mejora

---

## 📊 ESTADÍSTICAS

- **Líneas de código**: ~15,000+
- **Tests**: 20+ tests unitarios
- **Cobertura**: 80%+
- **Documentación**: 100% de funciones públicas documentadas

---

## 🌟 CARACTERÍSTICAS DESTACADAS

### ⚡ Rendimiento
- Procesamiento paralelo de issues de Jira
- Caché inteligente de métricas (6 horas TTL)
- Optimización de consultas a base de datos

### 🎨 Interfaz
- Diseño moderno y responsive
- Feedback visual en tiempo real
- Manejo de errores amigable

### 🔧 Mantenibilidad
- Código modular y reutilizable
- Principios SOLID aplicados
- Documentación completa
- Tests exhaustivos

---

**¿Listo para empezar?** 🚀

1. **Desarrollo local**: Sigue la sección [Instalación Local](#-instalación-local)
2. **Despliegue en producción**: Lee [GUIA_DESPLIEGUE_RENDER.md](GUIA_DESPLIEGUE_RENDER.md)

---

*Última actualización: Diciembre 2025*  
*Versión: 1.0.0*







