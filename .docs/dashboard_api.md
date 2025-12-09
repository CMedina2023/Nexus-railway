# API de Dashboard con Filtrado por Rol

## Descripción

Este documento describe los nuevos endpoints del dashboard que implementan filtrado por rol, permitiendo que:

- **Administrador**: Vea métricas y datos de TODOS los usuarios
- **Analista QA**: Vea solo sus propias métricas y datos generados
- **Usuario**: Vea solo sus propias métricas y datos generados

## Endpoints Disponibles

### 1. Obtener Historias Generadas

**Endpoint**: `GET /api/dashboard/stories`

**Autenticación**: Requerida

**Query Parameters**:
- `limit` (opcional): Número máximo de resultados a retornar

**Respuesta Exitosa** (200):
```json
{
  "success": true,
  "stories": [
    {
      "id": 1,
      "user_id": "user-123",
      "project_key": "PROJ",
      "story_title": "Como usuario quiero...",
      "story_content": "{...}",
      "jira_issue_key": "PROJ-123",
      "created_at": "2025-12-06T10:30:00",
      "updated_at": "2025-12-06T10:30:00"
    }
  ],
  "total": 10
}
```

**Comportamiento por Rol**:
- **Admin**: Retorna todas las historias de todos los usuarios
- **Analista QA / Usuario**: Retorna solo las historias del usuario autenticado

---

### 2. Obtener Casos de Prueba Generados

**Endpoint**: `GET /api/dashboard/test-cases`

**Autenticación**: Requerida

**Query Parameters**:
- `limit` (opcional): Número máximo de resultados a retornar

**Respuesta Exitosa** (200):
```json
{
  "success": true,
  "test_cases": [
    {
      "id": 1,
      "user_id": "user-123",
      "project_key": "PROJ",
      "test_case_title": "Verificar login exitoso",
      "test_case_content": "{...}",
      "jira_issue_key": "PROJ-456",
      "created_at": "2025-12-06T10:30:00",
      "updated_at": "2025-12-06T10:30:00"
    }
  ],
  "total": 15
}
```

**Comportamiento por Rol**:
- **Admin**: Retorna todos los casos de prueba de todos los usuarios
- **Analista QA / Usuario**: Retorna solo los casos del usuario autenticado

---

### 3. Obtener Reportes Creados en Jira

**Endpoint**: `GET /api/dashboard/reports`

**Autenticación**: Requerida

**Query Parameters**:
- `limit` (opcional): Número máximo de resultados a retornar
- `report_type` (opcional): Tipo de reporte para filtrar ('bug', 'test_case', 'story', etc.)

**Respuesta Exitosa** (200):
```json
{
  "success": true,
  "reports": [
    {
      "id": 1,
      "user_id": "user-123",
      "project_key": "PROJ",
      "report_type": "bug",
      "report_title": "Error en login",
      "report_content": "{...}",
      "jira_issue_key": "PROJ-789",
      "created_at": "2025-12-06T10:30:00",
      "updated_at": "2025-12-06T10:30:00"
    }
  ],
  "total": 5
}
```

**Comportamiento por Rol**:
- **Admin**: Retorna todos los reportes de todos los usuarios
- **Analista QA / Usuario**: Retorna solo los reportes del usuario autenticado

---

### 4. Obtener Cargas Masivas Realizadas

**Endpoint**: `GET /api/dashboard/bulk-uploads`

**Autenticación**: Requerida

**Query Parameters**:
- `limit` (opcional): Número máximo de resultados a retornar
- `upload_type` (opcional): Tipo de carga para filtrar ('stories', 'test_cases', 'csv_upload', etc.)

**Respuesta Exitosa** (200):
```json
{
  "success": true,
  "bulk_uploads": [
    {
      "id": 1,
      "user_id": "user-123",
      "project_key": "PROJ",
      "upload_type": "csv_upload",
      "total_items": 50,
      "successful_items": 45,
      "failed_items": 5,
      "upload_details": "{...}",
      "created_at": "2025-12-06T10:30:00",
      "updated_at": "2025-12-06T10:30:00"
    }
  ],
  "total": 3
}
```

**Comportamiento por Rol**:
- **Admin**: Retorna todas las cargas masivas de todos los usuarios
- **Analista QA / Usuario**: Retorna solo las cargas del usuario autenticado

---

### 5. Obtener Métricas de Actividad

**Endpoint**: `GET /api/dashboard/activity-metrics`

**Autenticación**: Requerida

**Respuesta Exitosa** (200):
```json
{
  "success": true,
  "metrics": {
    "stories_generated": 25,
    "test_cases_generated": 40,
    "reports_created": 10,
    "bulk_uploads_performed": 3,
    "view_type": "personal"  // "global" para admin, "personal" para otros
  },
  "user_role": "analista_qa"
}
```

**Comportamiento por Rol**:
- **Admin**: Retorna métricas globales (suma de todos los usuarios)
- **Analista QA / Usuario**: Retorna solo métricas del usuario autenticado

---

### 6. Obtener Resumen Completo del Dashboard

**Endpoint**: `GET /api/dashboard/summary`

**Autenticación**: Requerida

**Respuesta Exitosa** (200):
```json
{
  "success": true,
  "summary": {
    "total_stories": 25,
    "total_test_cases": 40,
    "total_reports": 10,
    "total_bulk_uploads": 3,
    "recent_stories": [...],  // Últimas 5 historias
    "recent_test_cases": [...],  // Últimos 5 casos
    "recent_reports": [...],  // Últimos 5 reportes
    "recent_bulk_uploads": [...],  // Últimas 5 cargas
    "view_type": "personal"  // "global" para admin, "personal" para otros
  },
  "user_role": "usuario"
}
```

**Comportamiento por Rol**:
- **Admin**: Retorna resumen global de todos los usuarios
- **Analista QA / Usuario**: Retorna solo resumen del usuario autenticado

---

## Errores Comunes

### 401 Unauthorized
```json
{
  "error": "Usuario no encontrado"
}
```
**Causa**: Token de sesión inválido o expirado

### 404 Not Found
```json
{
  "error": "Usuario no encontrado"
}
```
**Causa**: El usuario autenticado no existe en la base de datos

### 500 Internal Server Error
```json
{
  "error": "Error al obtener historias"
}
```
**Causa**: Error interno del servidor (revisar logs)

---

## Ejemplo de Uso en Frontend

### JavaScript/Fetch

```javascript
// Obtener historias del usuario actual
async function fetchUserStories(limit = 10) {
  try {
    const response = await fetch(`/api/dashboard/stories?limit=${limit}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include'  // Incluir cookies de sesión
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`Historias obtenidas: ${data.total}`);
    return data.stories;
  } catch (error) {
    console.error('Error al obtener historias:', error);
    return [];
  }
}

// Obtener métricas de actividad
async function fetchActivityMetrics() {
  try {
    const response = await fetch('/api/dashboard/activity-metrics', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    });
    
    const data = await response.json();
    
    if (data.success) {
      console.log('Métricas:', data.metrics);
      console.log('Tipo de vista:', data.metrics.view_type);
      console.log('Rol del usuario:', data.user_role);
      
      // Actualizar UI con las métricas
      updateMetricsUI(data.metrics);
    }
  } catch (error) {
    console.error('Error al obtener métricas:', error);
  }
}

// Obtener resumen completo
async function fetchDashboardSummary() {
  try {
    const response = await fetch('/api/dashboard/summary', {
      method: 'GET',
      credentials: 'include'
    });
    
    const data = await response.json();
    
    if (data.success) {
      const { summary, user_role } = data;
      
      // Mostrar indicador de vista según rol
      if (summary.view_type === 'global') {
        console.log('Vista de administrador: viendo datos de todos los usuarios');
      } else {
        console.log('Vista personal: viendo solo mis datos');
      }
      
      // Actualizar dashboard
      updateDashboard(summary);
    }
  } catch (error) {
    console.error('Error al obtener resumen:', error);
  }
}
```

---

## Notas Importantes

1. **Autenticación**: Todos los endpoints requieren autenticación. Asegúrate de incluir las cookies de sesión en las peticiones.

2. **Filtrado Automático**: El filtrado por rol es automático en el backend. No necesitas enviar ningún parámetro adicional para indicar el rol.

3. **Indicador de Vista**: Usa el campo `view_type` en las respuestas para mostrar al usuario si está viendo datos globales o personales.

4. **Límite de Resultados**: Por defecto, los endpoints retornan todos los resultados. Usa el parámetro `limit` para paginar.

5. **Datos en Tiempo Real**: Los datos se guardan automáticamente cuando se generan historias, casos de prueba, reportes o cargas masivas. No necesitas hacer nada adicional.

6. **Token de Jira**: Todos los usuarios utilizan el mismo token compartido del proyecto para las operaciones con Jira. No se requieren tokens personales.

---

## Migración desde Sistema Anterior

Si estabas usando endpoints anteriores que no tenían filtrado por rol:

1. **Reemplaza** llamadas a endpoints antiguos con los nuevos endpoints de `/api/dashboard/`
2. **Elimina** lógica de filtrado por rol en el frontend (ahora se hace en el backend)
3. **Agrega** indicadores visuales para mostrar si el usuario está viendo datos globales o personales
4. **Actualiza** las métricas para usar `/api/dashboard/activity-metrics` en lugar de calcularlas manualmente

---

## Soporte

Para reportar problemas o solicitar nuevas funcionalidades, contacta al equipo de desarrollo.

