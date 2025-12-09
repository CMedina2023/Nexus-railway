# Implementación de Permisos por Rol - Sistema de Dashboard

## 📋 Resumen

Se ha implementado un sistema completo de permisos por rol que permite:

- **Administrador**: Ver métricas y dashboard de TODOS los usuarios
- **Analista QA**: Ver únicamente sus propias métricas y contenido generado
- **Usuario**: Ver únicamente sus propias métricas y contenido generado

## ✅ Cambios Implementados

### 1. Modelos de Datos Creados

Se crearon 4 nuevos modelos para almacenar el historial de actividades de los usuarios:

#### `app/models/user_story.py`
- Almacena historias de usuario generadas
- Campos: `id`, `user_id`, `project_key`, `story_title`, `story_content`, `jira_issue_key`, `created_at`, `updated_at`

#### `app/models/test_case.py`
- Almacena casos de prueba generados
- Campos: `id`, `user_id`, `project_key`, `test_case_title`, `test_case_content`, `jira_issue_key`, `created_at`, `updated_at`

#### `app/models/jira_report.py`
- Almacena reportes creados en Jira
- Campos: `id`, `user_id`, `project_key`, `report_type`, `report_title`, `report_content`, `jira_issue_key`, `created_at`, `updated_at`

#### `app/models/bulk_upload.py`
- Almacena cargas masivas realizadas
- Campos: `id`, `user_id`, `project_key`, `upload_type`, `total_items`, `successful_items`, `failed_items`, `upload_details`, `created_at`, `updated_at`

---

### 2. Repositorios Creados

Se crearon 4 repositorios para gestionar el acceso a datos:

#### `app/database/repositories/user_story_repository.py`
- Métodos: `create`, `get_by_id`, `get_by_user_id`, `get_all`, `count_by_user`, `count_all`, `update`, `delete`

#### `app/database/repositories/test_case_repository.py`
- Métodos: `create`, `get_by_id`, `get_by_user_id`, `get_all`, `count_by_user`, `count_all`, `update`, `delete`

#### `app/database/repositories/jira_report_repository.py`
- Métodos: `create`, `get_by_id`, `get_by_user_id`, `get_all`, `count_by_user`, `count_all`, `update`, `delete`

#### `app/database/repositories/bulk_upload_repository.py`
- Métodos: `create`, `get_by_id`, `get_by_user_id`, `get_all`, `count_by_user`, `count_all`, `update`, `delete`

---

### 3. Migración de Base de Datos

Se actualizó `app/database/db.py` para crear las siguientes tablas:

#### Tabla `user_stories`
```sql
CREATE TABLE IF NOT EXISTS user_stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    project_key TEXT NOT NULL,
    story_title TEXT NOT NULL,
    story_content TEXT NOT NULL,
    jira_issue_key TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

#### Tabla `test_cases`
```sql
CREATE TABLE IF NOT EXISTS test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    project_key TEXT NOT NULL,
    test_case_title TEXT NOT NULL,
    test_case_content TEXT NOT NULL,
    jira_issue_key TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

#### Tabla `jira_reports`
```sql
CREATE TABLE IF NOT EXISTS jira_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    project_key TEXT NOT NULL,
    report_type TEXT NOT NULL,
    report_title TEXT NOT NULL,
    report_content TEXT NOT NULL,
    jira_issue_key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

#### Tabla `bulk_uploads`
```sql
CREATE TABLE IF NOT EXISTS bulk_uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    project_key TEXT NOT NULL,
    upload_type TEXT NOT NULL,
    total_items INTEGER NOT NULL,
    successful_items INTEGER NOT NULL DEFAULT 0,
    failed_items INTEGER NOT NULL DEFAULT 0,
    upload_details TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

**Índices creados** para optimizar consultas:
- `idx_user_stories_user` en `user_stories(user_id)`
- `idx_user_stories_project` en `user_stories(project_key)`
- `idx_test_cases_user` en `test_cases(user_id)`
- `idx_test_cases_project` en `test_cases(project_key)`
- `idx_jira_reports_user` en `jira_reports(user_id)`
- `idx_jira_reports_project` en `jira_reports(project_key)`
- `idx_bulk_uploads_user` en `bulk_uploads(user_id)`
- `idx_bulk_uploads_project` en `bulk_uploads(project_key)`

---

### 4. Rutas de Dashboard con Filtrado por Rol

Se creó `app/auth/dashboard_routes.py` con los siguientes endpoints:

#### `GET /api/dashboard/stories`
- Obtiene historias generadas según el rol del usuario
- Admin: ve todas las historias
- Analista QA / Usuario: solo ven sus propias historias

#### `GET /api/dashboard/test-cases`
- Obtiene casos de prueba generados según el rol
- Admin: ve todos los casos
- Analista QA / Usuario: solo ven sus propios casos

#### `GET /api/dashboard/reports`
- Obtiene reportes creados en Jira según el rol
- Admin: ve todos los reportes
- Analista QA / Usuario: solo ven sus propios reportes

#### `GET /api/dashboard/bulk-uploads`
- Obtiene cargas masivas realizadas según el rol
- Admin: ve todas las cargas
- Analista QA / Usuario: solo ven sus propias cargas

#### `GET /api/dashboard/activity-metrics`
- Obtiene métricas de actividad según el rol
- Admin: métricas globales de todos los usuarios
- Analista QA / Usuario: solo sus propias métricas

#### `GET /api/dashboard/summary`
- Obtiene resumen completo del dashboard según el rol
- Admin: resumen global de todos los usuarios
- Analista QA / Usuario: solo su propio resumen

**Blueprint registrado** en `app/core/app.py`

---

### 5. Modificación de Endpoints de Generación

Se modificaron los siguientes endpoints para guardar automáticamente en la base de datos local:

#### `POST /api/stories/generate`
- **Modificación**: Ahora guarda cada historia generada en la tabla `user_stories`
- **Campos guardados**: `user_id`, `project_key`, `story_title`, `story_content`
- **Ubicación**: `app/core/app.py` líneas ~1136-1157

#### `POST /api/tests/generate`
- **Modificación**: Ahora guarda cada caso de prueba generado en la tabla `test_cases`
- **Campos guardados**: `user_id`, `project_key`, `test_case_title`, `test_case_content`
- **Ubicación**: `app/core/app.py` líneas ~1210-1231

#### `POST /api/jira/upload-csv`
- **Modificación**: Ahora guarda cada carga masiva en la tabla `bulk_uploads`
- **Campos guardados**: `user_id`, `project_key`, `upload_type`, `total_items`, `successful_items`, `failed_items`, `upload_details`
- **Ubicación**: `app/core/app.py` líneas ~2801-2822

**Nota**: El guardado en BD local no afecta el flujo principal. Si falla, se registra en los logs pero no se interrumpe la operación.

---

### 6. Documentación para Frontend

Se creó documentación completa para el frontend:

#### `.docs/dashboard_api.md`
- Descripción de todos los endpoints nuevos
- Ejemplos de respuestas JSON
- Comportamiento por rol
- Ejemplos de uso en JavaScript/Fetch
- Guía de migración desde sistema anterior

---

## 🔒 Sistema de Permisos Implementado

### Métricas de Jira (Ya existente)

**Endpoint**: `/api/jira/metrics/<project_key>`

**Comportamiento actual**:
- ✅ Admin: puede ver métricas generales o personales (parámetro `view_type`)
- ✅ Analista QA / Usuario: SOLO pueden ver métricas personales (forzado en backend)
- ✅ Todos los roles utilizan el mismo token compartido del proyecto
- ✅ El filtrado se realiza en el backend según el rol del usuario

### Dashboard Local (Nuevo)

**Endpoints**: `/api/dashboard/*`

**Comportamiento**:
- ✅ Admin: ve datos de TODOS los usuarios
- ✅ Analista QA / Usuario: solo ven SUS PROPIOS datos
- ✅ Filtrado automático en el backend por `user_id`
- ✅ Indicador de vista (`view_type`: "global" o "personal")

**Implementación**:
```python
if user.role == 'admin':
    # Admin ve todo
    stories = story_repo.get_all(limit=limit)
else:
    # Analista QA y Usuario solo ven lo suyo
    stories = story_repo.get_by_user_id(user.id, limit=limit)
```

---

## 📊 Flujo de Datos

### Generación de Historias/Casos de Prueba

```
Usuario genera contenido
    ↓
Endpoint de generación (/api/stories/generate o /api/tests/generate)
    ↓
Contenido generado exitosamente
    ↓
Guardado en BD local (user_stories o test_cases)
    ├─ user_id: ID del usuario autenticado
    ├─ project_key: Proyecto de Jira
    ├─ title: Título del contenido
    ├─ content: Contenido completo (JSON)
    └─ jira_issue_key: NULL (se actualizará al subir a Jira)
    ↓
Retorno de respuesta al frontend
```

### Carga Masiva en Jira

```
Usuario sube CSV
    ↓
Endpoint de carga masiva (/api/jira/upload-csv)
    ↓
Issues creados en Jira
    ↓
Guardado en BD local (bulk_uploads)
    ├─ user_id: ID del usuario autenticado
    ├─ project_key: Proyecto de Jira
    ├─ upload_type: Tipo de carga
    ├─ total_items: Total de items
    ├─ successful_items: Items exitosos
    ├─ failed_items: Items fallidos
    └─ upload_details: Detalles (JSON)
    ↓
Retorno de respuesta con resumen
```

### Consulta de Dashboard

```
Usuario solicita dashboard
    ↓
Endpoint de dashboard (/api/dashboard/summary)
    ↓
Verificación de rol del usuario
    ├─ Admin: consulta get_all()
    └─ Analista QA / Usuario: consulta get_by_user_id(user_id)
    ↓
Retorno de datos filtrados
    ├─ view_type: "global" o "personal"
    └─ user_role: rol del usuario
```

---

## 🧪 Testing

### Pruebas Manuales Recomendadas

1. **Como Administrador**:
   - Generar historias y casos de prueba
   - Realizar carga masiva
   - Verificar que `/api/dashboard/summary` muestra datos de TODOS los usuarios
   - Verificar que `view_type` es "global"

2. **Como Analista QA**:
   - Generar historias y casos de prueba
   - Realizar carga masiva
   - Verificar que `/api/dashboard/summary` muestra SOLO sus propios datos
   - Verificar que `view_type` es "personal"
   - Intentar acceder a `/api/jira/metrics/<project>` sin token personal (debe fallar)

3. **Como Usuario**:
   - Generar historias y casos de prueba
   - Realizar carga masiva
   - Verificar que `/api/dashboard/summary` muestra SOLO sus propios datos
   - Verificar que `view_type` es "personal"
   - Intentar acceder a `/api/jira/metrics/<project>` sin token personal (debe fallar)

### Pruebas de Seguridad

1. **Aislamiento de Datos**:
   - Crear contenido con Usuario A
   - Iniciar sesión con Usuario B (mismo rol)
   - Verificar que Usuario B NO ve el contenido de Usuario A

2. **Escalación de Privilegios**:
   - Intentar modificar parámetros de URL para acceder a datos de otros usuarios
   - Verificar que el backend filtra correctamente por `user_id` de la sesión

3. **Token Personal de Jira**:
   - Intentar acceder a métricas de Jira sin configurar token personal
   - Verificar que se bloquea el acceso con error 403

---

## 📝 Notas Importantes

### Compatibilidad con Sistema Anterior

- ✅ Las métricas de Jira existentes (`/api/jira/metrics/<project>`) siguen funcionando
- ✅ Los endpoints de generación existentes siguen funcionando
- ✅ El guardado en BD local es adicional, no reemplaza funcionalidad existente
- ✅ Si falla el guardado en BD local, no se interrumpe la operación principal

### Token de Jira

- **Todos los roles**: Utilizan el mismo token compartido del proyecto para todas las operaciones con Jira
- **No se requieren tokens personales**: El filtrado de datos se realiza en la base de datos local por `user_id`, no mediante tokens diferentes

### Escalabilidad

- Los índices creados optimizan las consultas por `user_id` y `project_key`
- Las consultas `get_by_user_id` son eficientes incluso con miles de registros
- El parámetro `limit` permite paginación en el frontend

---

## 🚀 Próximos Pasos

### Frontend

1. Actualizar dashboard para consumir nuevos endpoints
2. Agregar indicador visual de vista (global vs personal)
3. Implementar paginación en listados
4. Agregar filtros por proyecto y fecha

### Backend

1. Agregar endpoint para actualizar `jira_issue_key` cuando se sube contenido a Jira
2. Implementar soft delete en lugar de hard delete
3. Agregar auditoría de cambios (quién modificó qué y cuándo)
4. Implementar caché para consultas frecuentes

### Seguridad

1. Agregar rate limiting a endpoints de dashboard
2. Implementar validación de pertenencia a proyecto para Usuario
3. Agregar logs de auditoría para accesos a datos sensibles

---

## 📞 Soporte

Para preguntas o problemas con la implementación, revisar:

1. Este documento
2. `.docs/dashboard_api.md` - Documentación de API
3. `.docs/permisos.md` - Especificación de permisos por rol
4. Logs del servidor en caso de errores

---

**Fecha de implementación**: 2025-12-06  
**Versión**: 1.0  
**Estado**: ✅ Completado

