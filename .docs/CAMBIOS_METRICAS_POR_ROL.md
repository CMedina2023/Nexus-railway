# Cambios Implementados: Métricas Filtradas por Rol

**Fecha**: 2025-12-08  
**Versión**: 2.6  
**Estado**: ✅ Completado

---

## 🎯 Objetivo

Implementar el filtrado correcto de métricas por rol de usuario, de manera que:
- **Administrador**: Ve todas las métricas generadas por todos los usuarios
- **Analista QA**: Solo ve sus propias métricas (lo que él generó)
- **Usuario**: Solo ve sus propias métricas (lo que él generó)

---

## 🐛 Problema Identificado

El sistema anterior usaba **localStorage del navegador** para almacenar las métricas, lo que causaba:

1. ❌ Las métricas eran locales al navegador, no al usuario
2. ❌ No había filtrado por `user_id` porque todo estaba en el navegador
3. ❌ Si cambias de navegador o computadora, se perdían las métricas
4. ❌ Todos los roles veían las mismas métricas porque compartían el mismo navegador

### Código Problemático (ANTES):

```javascript
function getMetrics() {
    const metrics = localStorage.getItem('nexus_metrics');
    if (metrics) {
        return JSON.parse(metrics);
    }
    return { stories: 0, testCases: 0, history: [] };
}

function saveMetrics(metrics) {
    localStorage.setItem('nexus_metrics', JSON.stringify(metrics));
}
```

---

## ✅ Solución Implementada

### 1. **Backend ya estaba preparado** ✅

El backend ya tenía implementado correctamente el sistema de permisos por rol:

- **Endpoints disponibles** (en `app/auth/dashboard_routes.py`):
  - `GET /api/dashboard/summary` - Resumen completo filtrado por rol
  - `GET /api/dashboard/activity-metrics` - Métricas filtradas por rol
  - `GET /api/dashboard/stories` - Historias filtradas por `user_id`
  - `GET /api/dashboard/test-cases` - Casos de prueba filtrados por `user_id`
  - `GET /api/dashboard/reports` - Reportes filtrados por `user_id`
  - `GET /api/dashboard/bulk-uploads` - Cargas masivas filtradas por `user_id`

- **Guardado automático**:
  - Las historias se guardan con `user_id` en `UserStoryRepository`
  - Los casos de prueba se guardan con `user_id` en `TestCaseRepository`
  - Las cargas masivas se guardan con `user_id` en `BulkUploadRepository`
  - Los reportes ahora se guardan con `user_id` en `JiraReportRepository` ✨ **NUEVO**

### 2. **Cambios en el Frontend** (templates/index.html)

#### A. Reemplazar funciones que usan localStorage por llamadas a la API

**ANTES**:
```javascript
function getMetrics() {
    const metrics = localStorage.getItem('nexus_metrics');
    // ...
}
```

**DESPUÉS**:
```javascript
async function getMetrics() {
    try {
        const response = await fetch('/api/dashboard/activity-metrics', {
            method: 'GET',
            credentials: 'include'
        });
        
        if (!response.ok) {
            console.error('Error al obtener métricas:', response.status);
            return { stories: 0, testCases: 0, history: [] };
        }
        
        const data = await response.json();
        if (data.success) {
            const storiesHistory = await getStoriesHistory();
            const testCasesHistory = await getTestCasesHistory();
            
            return {
                stories: data.metrics.stories_generated || 0,
                testCases: data.metrics.test_cases_generated || 0,
                history: [...storiesHistory, ...testCasesHistory]
                    .sort((a, b) => new Date(b.date) - new Date(a.date))
                    .slice(0, 50)
            };
        }
        
        return { stories: 0, testCases: 0, history: [] };
    } catch (error) {
        console.error('Error al obtener métricas:', error);
        return { stories: 0, testCases: 0, history: [] };
    }
}
```

#### B. Funciones actualizadas a asíncronas

- ✅ `getMetrics()` - Ahora obtiene datos del backend
- ✅ `getJiraMetrics()` - Ahora obtiene datos del backend
- ✅ `getStoriesHistory()` - Nueva función para obtener historial
- ✅ `getTestCasesHistory()` - Nueva función para obtener historial
- ✅ `getReportsHistory()` - Nueva función para obtener historial
- ✅ `getUploadsHistory()` - Nueva función para obtener historial
- ✅ `loadMetrics()` - Ahora es asíncrona
- ✅ `loadDashboardMetrics()` - Ahora es asíncrona
- ✅ `loadAllMetrics()` - Ahora es asíncrona
- ✅ `updateMetrics()` - Ahora es asíncrona
- ✅ `downloadMetrics()` - Ahora es asíncrona
- ✅ `navigateToSection()` - Ahora es asíncrona

#### C. Funciones deprecadas (ya no guardan en localStorage)

- `saveMetrics()` - No-op, el backend guarda automáticamente
- `saveJiraMetrics()` - No-op, el backend guarda automáticamente
- `incrementReportCount()` - No-op, el backend guarda automáticamente
- `incrementUploadCount()` - No-op, el backend guarda automáticamente
- `resetMetrics()` - Ahora muestra un mensaje explicativo

### 3. **Cambios en el Backend** (app/auth/metrics_routes.py)

#### A. Agregar guardado de reportes en base de datos

Se agregó el guardado automático de reportes de métricas cuando se generan:

```python
# Guardar reporte en base de datos local para métricas por usuario
try:
    report_repo = JiraReportRepository()
    jira_report = JiraReport(
        user_id=user.id,
        project_key=project_key,
        report_type='metrics',
        report_data=json.dumps(response_data, ensure_ascii=False),
        jira_issue_key=None
    )
    report_repo.create(jira_report)
    logger.info(f"Reporte de métricas guardado en BD local para user_id={user.id}, proyecto={project_key}")
except Exception as e:
    logger.error(f"Error al guardar reporte en BD local: {e}", exc_info=True)
    # No fallar la operación si falla el guardado en BD local
```

---

## 📊 Flujo de Datos (NUEVO)

### Cuando un usuario genera contenido:

1. **Usuario genera historias/casos de prueba/reportes/cargas masivas**
2. **Backend guarda automáticamente en BD local con `user_id`**
3. **Frontend obtiene métricas del backend** (filtradas por rol):
   - Admin: Ve todo
   - Analista QA: Solo lo suyo
   - Usuario: Solo lo suyo

### Cuando un usuario consulta métricas:

1. **Frontend llama a `/api/dashboard/activity-metrics`**
2. **Backend verifica el rol del usuario**:
   - Si es Admin: `SELECT * FROM ...` (todas las métricas)
   - Si es Analista QA o Usuario: `SELECT * FROM ... WHERE user_id = ?` (solo sus métricas)
3. **Backend retorna métricas filtradas**
4. **Frontend muestra las métricas**

---

## 🧪 Pruebas Recomendadas

### Prueba 1: Usuario genera contenido
1. Iniciar sesión como **Usuario A**
2. Generar 5 historias de usuario
3. Generar 3 casos de prueba
4. Verificar que el dashboard muestre: 5 historias, 3 casos de prueba

### Prueba 2: Otro usuario no ve contenido del primero
1. Iniciar sesión como **Usuario B**
2. Verificar que el dashboard muestre: 0 historias, 0 casos de prueba
3. Generar 2 historias de usuario
4. Verificar que el dashboard muestre: 2 historias, 0 casos de prueba

### Prueba 3: Admin ve todo
1. Iniciar sesión como **Administrador**
2. Verificar que el dashboard muestre:
   - 7 historias (5 de Usuario A + 2 de Usuario B)
   - 3 casos de prueba (3 de Usuario A)
   - Indicador: `view_type: "global"`

### Prueba 4: Analista QA solo ve lo suyo
1. Iniciar sesión como **Analista QA**
2. Generar 4 casos de prueba
3. Verificar que el dashboard muestre: 0 historias, 4 casos de prueba
4. Verificar que NO vea las historias/casos de Usuario A o Usuario B

---

## 📝 Archivos Modificados

### Frontend:
- ✅ `templates/index.html` - Reemplazadas funciones de localStorage por llamadas a API

### Backend:
- ✅ `app/auth/metrics_routes.py` - Agregado guardado de reportes en BD

### Documentación:
- ✅ `.docs/CAMBIOS_METRICAS_POR_ROL.md` - Este documento

---

## ⚠️ Notas Importantes

1. **Migración de datos**: Las métricas antiguas en localStorage NO se migran automáticamente. Los usuarios empezarán con métricas en 0 después de este cambio.

2. **Compatibilidad**: Las funciones antiguas (`saveMetrics`, `incrementReportCount`, etc.) se mantienen como no-op para evitar errores, pero ya no hacen nada.

3. **Performance**: El backend usa caché para métricas de Jira (6 horas de TTL), por lo que las consultas repetidas son rápidas.

4. **Seguridad**: Todos los endpoints requieren autenticación (`@login_required`) y respetan los permisos por rol.

---

## 🎉 Resultado Final

✅ **Administrador**: Ve todas las métricas de todos los usuarios  
✅ **Analista QA**: Solo ve sus propias métricas  
✅ **Usuario**: Solo ve sus propias métricas  
✅ **Las métricas persisten** en la base de datos, no en el navegador  
✅ **Las métricas se filtran correctamente** por `user_id` según el rol  

---

**Versión**: 2.6  
**Última actualización**: 2025-12-08





