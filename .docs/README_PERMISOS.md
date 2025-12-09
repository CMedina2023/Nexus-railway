# Sistema de Permisos por Rol - Guía de Uso

## 🎯 Objetivo

Implementar un sistema de permisos donde cada rol (Administrador, Analista QA, Usuario) solo pueda ver sus propias métricas y datos generados, excepto el Administrador que puede ver todo.

## 📦 Instalación

### 1. Aplicar Migraciones de Base de Datos

```bash
# Opción 1: Ejecutar script de inicialización
python scripts/init_dashboard_tables.py

# Opción 2: Reiniciar la aplicación (las tablas se crean automáticamente)
python run.py
```

### 2. Verificar Tablas Creadas

Las siguientes tablas deben existir en la base de datos:

- `user_stories` - Historias de usuario generadas
- `test_cases` - Casos de prueba generados
- `jira_reports` - Reportes creados en Jira
- `bulk_uploads` - Cargas masivas realizadas

## 🔐 Permisos por Rol

### Administrador

**Métricas de Jira**:
- ✅ Ver métricas globales de todos los usuarios
- ✅ Ver métricas personales (opcional)

**Dashboard Local**:
- ✅ Ver todo lo generado por todos los usuarios
- ✅ Ver historias, casos de prueba, reportes y cargas masivas de todos

**Indicador**: `view_type: "global"`

### Analista QA

**Métricas de Jira**:
- ✅ Ver únicamente sus propias métricas
- ❌ No puede ver métricas de otros usuarios
- ✅ Utiliza el token compartido del proyecto

**Dashboard Local**:
- ✅ Ver únicamente lo que él generó
- ❌ No puede ver contenido de otros usuarios

**Indicador**: `view_type: "personal"`

### Usuario

**Métricas de Jira**:
- ✅ Ver únicamente sus propias métricas
- ❌ No puede ver métricas de otros usuarios
- ✅ Utiliza el token compartido del proyecto

**Dashboard Local**:
- ✅ Ver únicamente lo que él generó
- ❌ No puede ver contenido de otros usuarios

**Indicador**: `view_type: "personal"`

## 🚀 Uso de los Endpoints

### Obtener Resumen del Dashboard

```javascript
// GET /api/dashboard/summary
fetch('/api/dashboard/summary', {
  method: 'GET',
  credentials: 'include'
})
.then(response => response.json())
.then(data => {
  console.log('Resumen:', data.summary);
  console.log('Tipo de vista:', data.summary.view_type);
  console.log('Rol del usuario:', data.user_role);
  
  if (data.summary.view_type === 'global') {
    // Mostrar indicador de vista global (admin)
    showGlobalViewIndicator();
  } else {
    // Mostrar indicador de vista personal
    showPersonalViewIndicator();
  }
});
```

### Obtener Métricas de Actividad

```javascript
// GET /api/dashboard/activity-metrics
fetch('/api/dashboard/activity-metrics', {
  method: 'GET',
  credentials: 'include'
})
.then(response => response.json())
.then(data => {
  const metrics = data.metrics;
  
  // Actualizar UI con métricas
  document.getElementById('stories-count').textContent = metrics.stories_generated;
  document.getElementById('tests-count').textContent = metrics.test_cases_generated;
  document.getElementById('reports-count').textContent = metrics.reports_created;
  document.getElementById('uploads-count').textContent = metrics.bulk_uploads_performed;
});
```

### Obtener Historias Generadas

```javascript
// GET /api/dashboard/stories?limit=10
fetch('/api/dashboard/stories?limit=10', {
  method: 'GET',
  credentials: 'include'
})
.then(response => response.json())
.then(data => {
  const stories = data.stories;
  
  // Renderizar historias en la UI
  stories.forEach(story => {
    console.log(`Historia: ${story.story_title}`);
    console.log(`Proyecto: ${story.project_key}`);
    console.log(`Fecha: ${story.created_at}`);
  });
});
```

## 🔧 Configuración de Token de Jira

### Para Todos los Roles

Todos los usuarios (Administrador, Analista QA y Usuario) utilizan el **mismo token compartido del proyecto** para:
- Consultar métricas de Jira
- Crear issues en Jira
- Realizar cargas masivas
- Cualquier operación con la API de Jira

**No se requiere configuración de tokens personales**. El filtrado de datos se realiza automáticamente en el backend según el rol del usuario, consultando la base de datos local.

## 📊 Flujo de Datos

### Cuando un Usuario Genera Contenido

1. Usuario genera historias/casos de prueba
2. Contenido se guarda automáticamente en BD local con `user_id`
3. Usuario puede ver su contenido en el dashboard
4. Administrador puede ver el contenido de todos los usuarios

### Cuando un Usuario Realiza Carga Masiva

1. Usuario sube CSV y crea issues en Jira
2. Carga se registra en BD local con `user_id`
3. Usuario puede ver su historial de cargas
4. Administrador puede ver todas las cargas

## 🧪 Pruebas

### Verificar Aislamiento de Datos

```bash
# 1. Crear contenido con Usuario A
curl -X POST http://localhost:5000/api/stories/generate \
  -H "Cookie: session=..." \
  -F "file=@documento.pdf" \
  -F "project_key=PROJ"

# 2. Iniciar sesión con Usuario B
# 3. Consultar dashboard
curl -X GET http://localhost:5000/api/dashboard/summary \
  -H "Cookie: session=..."

# Resultado esperado: Usuario B NO ve el contenido de Usuario A
```

### Verificar Vista de Administrador

```bash
# 1. Crear contenido con varios usuarios
# 2. Iniciar sesión como Administrador
# 3. Consultar dashboard
curl -X GET http://localhost:5000/api/dashboard/summary \
  -H "Cookie: session=..."

# Resultado esperado:
# - view_type: "global"
# - Se muestran datos de TODOS los usuarios
```

## 📝 Endpoints Disponibles

| Endpoint | Método | Descripción | Admin | Analista QA | Usuario |
|----------|--------|-------------|-------|-------------|---------|
| `/api/dashboard/stories` | GET | Historias generadas | Todas | Solo suyas | Solo suyas |
| `/api/dashboard/test-cases` | GET | Casos de prueba | Todos | Solo suyos | Solo suyos |
| `/api/dashboard/reports` | GET | Reportes en Jira | Todos | Solo suyos | Solo suyos |
| `/api/dashboard/bulk-uploads` | GET | Cargas masivas | Todas | Solo suyas | Solo suyas |
| `/api/dashboard/activity-metrics` | GET | Métricas de actividad | Globales | Personales | Personales |
| `/api/dashboard/summary` | GET | Resumen completo | Global | Personal | Personal |

## 🐛 Troubleshooting

### Error: "Usuario no encontrado"

**Causa**: Token de sesión inválido o expirado

**Solución**: Cerrar sesión e iniciar sesión nuevamente

### Error: "Error al obtener configuración de Jira"

**Causa**: No hay token compartido configurado para el proyecto

**Solución**: El administrador debe configurar el token compartido del proyecto en la configuración de proyectos

### No se muestran datos en el dashboard

**Causa**: No se ha generado contenido aún

**Solución**: Generar historias, casos de prueba o realizar cargas masivas primero

### Administrador no ve datos de otros usuarios

**Causa**: Posible error en la lógica de filtrado

**Solución**: Verificar logs del servidor y revisar que `user.role == 'admin'`

## 📚 Documentación Adicional

- **API Completa**: `.docs/dashboard_api.md`
- **Implementación Técnica**: `.docs/implementacion_permisos_por_rol.md`
- **Especificación de Permisos**: `.docs/permisos.md`

## 🔄 Migración desde Sistema Anterior

Si estabas usando endpoints anteriores:

1. **Reemplaza** llamadas a endpoints antiguos con `/api/dashboard/*`
2. **Elimina** lógica de filtrado por rol en el frontend
3. **Agrega** indicadores visuales de vista (global/personal)
4. **Actualiza** métricas para usar nuevos endpoints

## 📞 Soporte

Para reportar problemas:

1. Revisar logs del servidor
2. Verificar que las tablas existen en la BD
3. Verificar que el usuario tiene sesión activa
4. Contactar al equipo de desarrollo

---

**Versión**: 1.0  
**Fecha**: 2025-12-06  
**Estado**: ✅ Implementado y Documentado

