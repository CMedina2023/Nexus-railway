# Permisos por Rol

> Nota: Algunas capacidades listadas aún no están implementadas en el sistema. Este documento define el alcance esperado para cada rol.

## Roles
- Administrador
- Analista QA
- Usuario

## Detalle de permisos

### Administrador
- Panel de administración:
  - Habilitar/deshabilitar usuarios
  - Cambiar roles
  - Acceso completo al panel de administración
- Métricas:
  - Ver métricas globales de todos los usuarios
- Dashboard:
  - Ver todo lo generado por los usuarios (sin restricciones)
- Generador de Historias:
  - Crear historias en el generador
- Generador de Casos de Prueba:
  - Crear casos de prueba en el generador
- Reporte en Jira:
  - Crear reportes a través de la API de Jira
- Carga Masiva en Jira:
  - Cargar masivamente a través de la API de Jira

### Analista QA
- Métricas:
  - Ver únicamente las métricas que el Analista QA generó
- Dashboard:
  - Ver únicamente lo que el Analista QA generó (historias, casos de prueba, reportes o cargas masivas)
- Generador de Historias:
  - Crear historias en el generador
- Generador de Casos de Prueba:
  - Crear casos de prueba en el generador
- Reporte en Jira:
  - Crear reportes a través de la API de Jira
- Carga Masiva en Jira:
  - Cargar masivamente a través de la API de Jira

### Usuario
- Métricas:
  - Ver únicamente las métricas que el Usuario generó
- Dashboard:
  - Ver únicamente lo que el Usuario generó (historias, casos de prueba, reportes o cargas masivas)
- Generador de Historias:
  - Crear historias en el generador (solo si está en el proyecto)
- Generador de Casos de Prueba:
  - Crear casos de prueba en el generador (solo si está en el proyecto)
- Reporte en Jira:
  - Crear reportes a través de la API de Jira
- Carga Masiva en Jira:
  - Cargar masivamente a través de la API de Jira (con validación previa de pertenencia al proyecto)

## Notas pendientes/roadmap
- Validar e implementar en UI y backend el scope de visibilidad de métricas y dashboard por rol (Administrador ve todo; Analista QA/Usuario solo lo propio).
- Implementar controles de pertenencia a proyecto para creación/carga de historias y casos de prueba (Usuario).
- Validar permisos en integraciones de Jira (creación y carga masiva) por rol.
- Registrar auditoría de cambios de roles y estado de usuario en el panel de administración.