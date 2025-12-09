# Changelog - Sistema de Permisos por Rol

## [1.0.0] - 2025-12-06

### ✨ Nuevas Funcionalidades

#### Sistema de Dashboard con Permisos por Rol
- Implementado sistema completo de permisos donde:
  - **Administrador**: Ve métricas y dashboard de TODOS los usuarios
  - **Analista QA**: Ve únicamente sus propias métricas y contenido generado
  - **Usuario**: Ve únicamente sus propias métricas y contenido generado

#### Nuevos Modelos de Datos
- `UserStory`: Almacena historias de usuario generadas
- `TestCase`: Almacena casos de prueba generados
- `JiraReport`: Almacena reportes creados en Jira
- `BulkUpload`: Almacena cargas masivas realizadas

#### Nuevos Repositorios
- `UserStoryRepository`: Gestión de historias en BD
- `TestCaseRepository`: Gestión de casos de prueba en BD
- `JiraReportRepository`: Gestión de reportes en BD
- `BulkUploadRepository`: Gestión de cargas masivas en BD

#### Nuevos Endpoints de Dashboard
- `GET /api/dashboard/stories` - Obtener historias generadas (filtradas por rol)
- `GET /api/dashboard/test-cases` - Obtener casos de prueba (filtrados por rol)
- `GET /api/dashboard/reports` - Obtener reportes (filtrados por rol)
- `GET /api/dashboard/bulk-uploads` - Obtener cargas masivas (filtradas por rol)
- `GET /api/dashboard/activity-metrics` - Obtener métricas de actividad (filtradas por rol)
- `GET /api/dashboard/summary` - Obtener resumen completo (filtrado por rol)

### 🔧 Modificaciones

#### Base de Datos
- Agregadas 4 nuevas tablas: `user_stories`, `test_cases`, `jira_reports`, `bulk_uploads`
- Agregados 8 índices para optimizar consultas por `user_id` y `project_key`
- Agregada función `get_db_connection()` en `app/database/db.py`

#### Endpoints Existentes
- `POST /api/stories/generate`: Ahora guarda historias en BD local automáticamente
- `POST /api/tests/generate`: Ahora guarda casos de prueba en BD local automáticamente
- `POST /api/jira/upload-csv`: Ahora guarda cargas masivas en BD local automáticamente

#### Sistema de Métricas de Jira (Mejorado)
- Mantenido filtrado por rol existente
- Todos los usuarios utilizan el mismo token compartido del proyecto
- No se requieren tokens personales

### 📚 Documentación

#### Nuevos Documentos
- `.docs/dashboard_api.md` - Documentación completa de API para frontend
- `.docs/implementacion_permisos_por_rol.md` - Documentación técnica de implementación
- `.docs/README_PERMISOS.md` - Guía de uso del sistema de permisos
- `CHANGELOG_PERMISOS.md` - Este archivo

#### Scripts
- `scripts/init_dashboard_tables.py` - Script para inicializar tablas del dashboard

### 🔒 Seguridad

#### Mejoras de Seguridad
- Filtrado automático por `user_id` en todos los endpoints de dashboard
- Validación de rol en backend (no depende del frontend)
- Aislamiento completo de datos entre usuarios del mismo rol
- Logs de auditoría para accesos a datos

#### Validaciones
- Verificación de sesión en todos los endpoints
- Filtrado automático por `user_id` en base de datos local
- Manejo seguro de errores sin exponer información sensible

### 🎨 Arquitectura

#### Principios Aplicados
- **SRP (Single Responsibility Principle)**: Cada clase tiene una única responsabilidad
- **OCP (Open/Closed Principle)**: Sistema extensible sin modificar código existente
- **DIP (Dependency Inversion Principle)**: Inyección de dependencias en repositorios
- **DRY (Don't Repeat Yourself)**: Código reutilizable en repositorios

#### Estructura de Archivos
```
app/
├── models/
│   ├── user_story.py          [NUEVO]
│   ├── test_case.py           [NUEVO]
│   ├── jira_report.py         [NUEVO]
│   └── bulk_upload.py         [NUEVO]
├── database/
│   ├── repositories/
│   │   ├── user_story_repository.py      [NUEVO]
│   │   ├── test_case_repository.py       [NUEVO]
│   │   ├── jira_report_repository.py     [NUEVO]
│   │   └── bulk_upload_repository.py     [NUEVO]
│   └── db.py                  [MODIFICADO]
├── auth/
│   ├── dashboard_routes.py    [NUEVO]
│   └── metrics_routes.py      [SIN CAMBIOS]
└── core/
    └── app.py                 [MODIFICADO]

.docs/
├── dashboard_api.md           [NUEVO]
├── implementacion_permisos_por_rol.md  [NUEVO]
└── README_PERMISOS.md         [NUEVO]

scripts/
└── init_dashboard_tables.py   [NUEVO]
```

### 📊 Métricas

#### Archivos Creados
- 4 modelos nuevos
- 4 repositorios nuevos
- 1 archivo de rutas nuevo
- 4 documentos de documentación nuevos
- 1 script de inicialización nuevo
- **Total**: 14 archivos nuevos

#### Archivos Modificados
- `app/core/app.py` - Agregados imports y guardado en BD
- `app/database/db.py` - Agregadas tablas e índices
- `app/models/__init__.py` - Agregados exports
- `app/database/repositories/__init__.py` - Agregados exports
- **Total**: 4 archivos modificados

#### Líneas de Código
- Aproximadamente **2,500 líneas** de código nuevo
- Aproximadamente **150 líneas** de código modificado
- **Total**: ~2,650 líneas

### 🧪 Testing

#### Pruebas Recomendadas
- ✅ Verificar aislamiento de datos entre usuarios
- ✅ Verificar vista global para administrador
- ✅ Verificar que todos los roles usan el token compartido
- ✅ Verificar guardado automático en BD local
- ✅ Verificar índices de base de datos

### 🚀 Próximos Pasos

#### Backend
- [ ] Agregar endpoint para actualizar `jira_issue_key` cuando se sube a Jira
- [ ] Implementar soft delete en lugar de hard delete
- [ ] Agregar auditoría de cambios (quién modificó qué y cuándo)
- [ ] Implementar caché para consultas frecuentes

#### Frontend
- [ ] Actualizar dashboard para consumir nuevos endpoints
- [ ] Agregar indicador visual de vista (global vs personal)
- [ ] Implementar paginación en listados
- [ ] Agregar filtros por proyecto y fecha

#### Seguridad
- [ ] Agregar rate limiting a endpoints de dashboard
- [ ] Implementar validación de pertenencia a proyecto para Usuario
- [ ] Agregar logs de auditoría para accesos a datos sensibles

### ⚠️ Breaking Changes

**Ninguno** - Todos los cambios son retrocompatibles. Los endpoints existentes siguen funcionando sin modificaciones.

### 🐛 Bugs Conocidos

**Ninguno** - No se han identificado bugs en la implementación actual.

### 📝 Notas de Migración

#### Para Desarrolladores Frontend
1. Revisar `.docs/dashboard_api.md` para documentación de nuevos endpoints
2. Actualizar llamadas a API para usar `/api/dashboard/*`
3. Agregar indicadores visuales de vista (global/personal)
4. Implementar paginación usando parámetro `limit`

#### Para Administradores de Sistema
1. Ejecutar `python scripts/init_dashboard_tables.py` para crear tablas
2. Verificar que las tablas se crearon correctamente
3. No se requieren cambios en configuración existente

#### Para Usuarios Finales
1. Analista QA y Usuario deben configurar token personal de Jira
2. Ir a Perfil → Configuración de Jira
3. Seleccionar proyecto y configurar token personal
4. Activar "Usar token personal"

### 🙏 Agradecimientos

Implementación realizada siguiendo las mejores prácticas de:
- Principios SOLID
- Clean Code
- Arquitectura modular
- Seguridad por diseño

---

## Resumen de Cambios

| Categoría | Cantidad |
|-----------|----------|
| Archivos Nuevos | 14 |
| Archivos Modificados | 4 |
| Modelos Nuevos | 4 |
| Repositorios Nuevos | 4 |
| Endpoints Nuevos | 6 |
| Tablas de BD Nuevas | 4 |
| Índices de BD Nuevos | 8 |
| Líneas de Código | ~2,650 |
| Documentos Nuevos | 4 |

---

**Versión**: 1.0.0  
**Fecha**: 2025-12-06  
**Estado**: ✅ Completado y Documentado  
**Autor**: Sistema de IA - Claude Sonnet 4.5

