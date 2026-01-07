# ✅ Checklist de Mejoras para Generadores
## Nexus Railway - Plan de Acción Enterprise

**Fecha de Creación**: 2026-01-06  
**Versión**: 1.0  
**Documento Base**: [ANALISIS_GENERADORES_ENTERPRISE.md](./ANALISIS_GENERADORES_ENTERPRISE.md)

---

## 📋 Resumen Ejecutivo del Análisis

### Estado Actual

Ambos generadores (Casos de Prueba e Historias de Usuario) tienen:
- ✅ **Arquitectura técnica sólida** (9/10)
- ✅ **Calidad de generación alta** (8/10)
- ✅ **Integración Jira completa** (9/10)
- ❌ **Trazabilidad inexistente** (2/10)
- ❌ **Sin workflow de aprobación** (0/10)
- ❌ **Auditoría limitada** (3/10)

**Puntuación Enterprise Global**: **4.8/10** (Insuficiente para enterprise)

### Gaps Críticos Identificados

| Gap | Impacto | Prioridad |
|-----|---------|-----------|
| **Falta de Trazabilidad** | No se puede demostrar cobertura de requerimientos | 🔴 CRÍTICA |
| **Sin Workflow de Aprobación** | Riesgo de artefactos incorrectos en producción | 🔴 CRÍTICA |
| **Sin Versionado** | No hay historial de cambios ni rollback | 🔴 CRÍTICA |
| **Validación Semántica Limitada** | No valida reglas de negocio específicas | 🟡 ALTA |
| **Sin Reportes de Cobertura** | Difícil planificación y seguimiento | 🟡 ALTA |
| **Rendimiento Limitado** | Generación lenta para documentos grandes | 🟢 MEDIA |

### Objetivo del Checklist

Proveer una **lista accionable de tareas** organizadas por:
- ✅ Prioridad (Crítica, Alta, Media, Baja)
- ✅ Generador (Casos de Prueba, Historias de Usuario, Ambos)
- ✅ Fase de implementación
- ✅ Estimación de esfuerzo
- ✅ Dependencias

---

## 🎯 Leyenda de Símbolos

- 🔴 **Crítica**: Bloqueante para enterprise
- 🟡 **Alta**: Mejora significativa
- 🟢 **Media**: Mejora incremental
- 🔵 **Baja**: Nice to have
- ⏱️ **Esfuerzo**: Días de desarrollo estimados
- 🔗 **Dependencias**: Tareas que deben completarse antes

---

## 📊 FASE 1: Fundamentos Enterprise (3-4 meses)

### 🔴 CRÍTICA - Base de Conocimiento Unificada (Proyecto Multi-Archivo)

#### 🔧 Infraestructura Compartida

- [x] **K1.1** - 🔧 Diseñar modelo de "ProjectContext"
  - ⏱️ **2 días**
  - 🔗 Ninguna
  - **Objetivo**: Persistir el "entendimiento" de la IA sobre el proyecto, independiente de archivos individuales.
  - **Archivos a crear**:
    - `app/models/project_context.py` (Campos: summary, glossary, business_rules, tech_constraints)
    - `app/models/project_document.py` (Relación: Archivo físico <-> ProjectContext)

- [x] **K1.2** - 🔧 Implementar Motor de Fusión de Contexto
  - ⏱️ **5 días**
  - 🔗 K1.1
  - **Objetivo**: Lógica para tomar N archivos, extraer sus contextos individuales y fusionarlos en un Master Context sin alucinaciones.
  - **Archivos a crear**:
    - `app/services/knowledge/context_merger.py` (Lógica de Map-Reduce con IA)
    - `app/services/knowledge/document_ingestion_service.py`

- [x] **K1.3** - 🔧 Actualizar Pipelines de Generación (RAG)
  - ⏱️ **4 días**
  - 🔗 K1.2
  - **Objetivo**: Que `story_generator` y `matrix_generator` consulten el `ProjectContext` antes de generar.
  - **Archivos a modificar**:
    - `app/backend/story_generator.py` (Inyectar contexto global persistido)
    - `app/backend/matrix/generator.py` (Inyectar contexto global persistido)
    - `app/services/generation_orchestrator.py`

- [x] **K1.4** - 🔧 UI de Gestión de Documentos de Proyecto
  - ⏱️ **4 días**
  - 🔗 K1.3
  - **Entregables**:
    - Dropzone Multi-archivo.
    - Lista de "Documentos Activos" del proyecto.
    - Visualizador del "Contexto Entendido" (para que el humano verifique qué entendió la IA).
  - **Archivos a crear**:
    - `static/js/modules/projects/knowledge-base-ui.js`
    - `templates/partials/knowledge_base.html`

- [x] **K1.5** - 🔧 Migraciones de Base de Conocimiento
  - ⏱️ **1 día**
  - 🔗 K1.1
  - **Archivos a crear**:
    - `migrations/add_knowledge_base_tables.sql`

---

### 🔴 CRÍTICA - Matriz de Trazabilidad

#### 🔧 Infraestructura Compartida (se implementa una vez, beneficia a ambos generadores)

- [x] **T1.1** - 🔧 Diseñar modelo de datos de trazabilidad
  - ⏱️ **3 días**
  - 🔗 Ninguna
  - **Entregables**:
    - Diagrama ER de tablas nuevas
    - Definición de campos y relaciones
    - Documento de diseño técnico
  - **Archivos a crear**:
    - `app/models/requirement.py`
    - `app/models/requirement_coverage.py`
    - `app/models/traceability_link.py`

- [x] **T1.2** - 🔧 Crear migraciones de base de datos
  - ⏱️ **2 días**
  - 🔗 T1.1
  - **Entregables**:
    - Scripts de migración para PostgreSQL/MySQL
    - Scripts de rollback
  - **Archivos a crear**:
    - `migrations/add_traceability_tables.sql`
    - `migrations/rollback_traceability_tables.sql`

- [x] **T1.3** - 🔧 Implementar repositorios de trazabilidad
  - ⏱️ **3 días**
  - 🔗 T1.2
  - **Entregables**:
    - CRUD completo para requirements
    - CRUD completo para coverage
    - Métodos de consulta de trazabilidad
  - **Archivos a crear**:
    - `app/database/repositories/requirement_repository.py`
    - `app/database/repositories/coverage_repository.py`

- [x] **T1.4** - 🔧 Crear API endpoints de trazabilidad
  - ⏱️ **3 días**
  - 🔗 T1.3
  - **Entregables**:
    - POST /api/requirements
    - GET /api/requirements/{id}/coverage
    - POST /api/traceability/link
    - GET /api/traceability/matrix/{project_id}
  - **Archivos a crear**:
    - `app/routes/traceability_routes.py`

#### 🧪 Casos de Prueba

- [x] **TC-T1.1** - 🧪 Agregar campo requirement_id a TestCase
  - ⏱️ **1 día**
  - 🔗 T1.2
  - **Archivos a modificar**:
    - `app/models/test_case.py` (agregar campos: requirement_id, requirement_version, coverage_status)
    - `app/database/repositories/test_case_repository.py` (actualizar queries)

- [x] **TC-T1.2** - 🧪 Actualizar generador para capturar requirement_id
  - ⏱️ **2 días**
  - 🔗 TC-T1.1
  - **Archivos a modificar**:
    - `app/backend/matrix/generator.py` (agregar parámetro requirement_id)
    - `static/js/modules/generators/test-case/test-case-generator.js`

- [x] **TC-T1.3** - 🧪 Integrar trazabilidad en UI de casos de prueba
  - ⏱️ **3 días**
  - 🔗 T1.4, TC-T1.2
  - **Entregables**:
    - Selector de requerimiento al generar casos
    - Visualización de cobertura en vista previa
    - Indicador de requerimientos sin cobertura
  - **Archivos a modificar**:
    - `static/js/modules/generators/test-case/test-case-ui.js`
    - `templates/partials/generators_section.html`

#### 📖 Historias de Usuario

- [x] **US-T1.1** - 📖 Agregar campos de jerarquía a UserStory
  - ⏱️ **1 día**
  - 🔗 T1.2
  - **Archivos a modificar**:
    - `app/models/user_story.py` (agregar: requirement_id, epic_id, feature_id, parent_story_id, dependencies)
    - `app/database/repositories/user_story_repository.py` (actualizar queries)

- [x] **US-T1.2** - 📖 Crear modelos Epic y Feature
  - ⏱️ **2 días**
  - 🔗 US-T1.1
  - **Archivos a crear**:
    - `app/models/epic.py`
    - `app/models/feature.py`
    - `app/database/repositories/epic_repository.py`
    - `app/database/repositories/feature_repository.py`

- [x] **US-T1.3** - 📖 Actualizar generador para capturar requirement_id
  - ⏱️ **2 días**
  - 🔗 US-T1.1
  - **Archivos a modificar**:
    - `app/backend/story_generator.py` (agregar parámetro requirement_id)
    - `static/js/modules/generators/story/story-generator.js`

- [x] **US-T1.4** - 📖 Integrar trazabilidad en UI de historias
  - ⏱️ **3 días**
  - 🔗 T1.4, US-T1.3
  - **Entregables**:
    - Selector de requerimiento al generar historias
    - Selector de Epic/Feature
    - Visualización de jerarquía en vista previa
  - **Archivos a modificar**:
    - `static/js/modules/generators/story/story-ui.js`
    - `templates/partials/generators_section.html`

---

### 🔴 CRÍTICA - Workflow de Aprobación

#### 🔧 Infraestructura Compartida

- [x] **W1.1** - 🔧 Diseñar estados y transiciones de workflow
  - ⏱️ **2 días**
  - 🔗 Ninguna
  - **Entregables**:
    - Diagrama de estados
    - Matriz de transiciones permitidas
    - Definición de roles y permisos
  - **Documento a crear**:
    - `docs/WORKFLOW_APPROVAL_DESIGN.md`

- [x] **W1.2** - 🔧 Crear modelos de workflow
  - ⏱️ **3 días**
  - 🔗 W1.1
  - **Archivos a crear**:
    - `app/models/approval_status.py` (Enum: DRAFT, PENDING_REVIEW, APPROVED, REJECTED, etc.)
    - `app/models/approval_workflow.py`
    - `app/models/approval.py`
    - `app/models/workflow_comment.py`

- [x] **W1.3** - 🔧 Crear migraciones de workflow
  - ⏱️ **2 días**
  - 🔗 W1.2
  - **Archivos a crear**:
    - `migrations/add_workflow_tables.sql`
    - `migrations/rollback_workflow_tables.sql`

- [x] **W1.4** - 🔧 Implementar repositorios de workflow
  - ⏱️ **3 días**
  - 🔗 W1.3
  - **Archivos a crear**:
    - `app/database/repositories/workflow_repository.py`
    - `app/database/repositories/approval_repository.py`

- [x] **W1.5** - 🔧 Crear servicio de workflow
  - ⏱️ **4 días**
  - 🔗 W1.4
  - **Entregables**:
    - Lógica de transiciones de estado
    - Validación de permisos por rol
    - Notificaciones de cambio de estado
  - **Archivos a crear**:
    - `app/services/workflow_service.py`

- [x] **W1.6** - 🔧 Crear API endpoints de workflow
  - ⏱️ **3 días**
  - 🔗 W1.5
  - **Entregables**:
    - POST /api/workflow/submit-for-review
    - POST /api/workflow/approve
    - POST /api/workflow/reject
    - POST /api/workflow/request-changes
    - GET /api/workflow/{artifact_id}/history
  - **Archivos a crear**:
    - `app/routes/workflow_routes.py`

- [x] **W1.7** - 🔧 Implementar UI de workflow
  - ⏱️ **5 días**
  - 🔗 W1.6
  - **Entregables**:
    - Botones de acción según estado
    - Modal de aprobación/rechazo
    - Historial de aprobaciones
    - Indicadores visuales de estado
  - **Archivos a crear**:
    - `static/js/modules/workflow/workflow-manager.js`
    - `templates/partials/workflow_actions.html`

- [x] **W1.8** - 🔧 Implementar sistema de notificaciones
  - ⏱️ **3 días**
  - 🔗 W1.7
  - **Entregables**:
    - Notificaciones por email
    - Notificaciones in-app
    - Configuración de preferencias
  - **Archivos a crear**:
    - `app/services/notification_service.py`

#### 🧪 Casos de Prueba

- [ ] **TC-W1.1** - 🧪 Agregar campo approval_status a TestCase
  - ⏱️ **1 día**
  - 🔗 W1.3
  - **Archivos a modificar**:
    - `app/models/test_case.py` (agregar: approval_status, approved_by, approved_at)
    - `app/database/repositories/test_case_repository.py`

- [ ] **TC-W1.2** - 🧪 Modificar generador para estado DRAFT inicial
  - ⏱️ **1 día**
  - 🔗 TC-W1.1
  - **Archivos a modificar**:
    - `app/backend/matrix/generator.py` (setear approval_status = DRAFT al crear)

- [ ] **TC-W1.3** - 🧪 Bloquear subida a Jira si no está APPROVED
  - ⏱️ **2 días**
  - 🔗 TC-W1.2, W1.6
  - **Archivos a modificar**:
    - `static/js/modules/generators/test-case/test-case-jira.js` (validar estado antes de subir)

- [ ] **TC-W1.4** - 🧪 Integrar UI de workflow en casos de prueba
  - ⏱️ **2 días**
  - 🔗 W1.7, TC-W1.3
  - **Entregables**:
    - Botones de "Enviar a Revisión", "Aprobar", "Rechazar"
    - Indicador visual de estado en tabla
  - **Archivos a modificar**:
    - `static/js/modules/generators/test-case/test-case-ui.js`

#### 📖 Historias de Usuario

- [ ] **US-W1.1** - 📖 Agregar campo approval_status a UserStory
  - ⏱️ **1 día**
  - 🔗 W1.3
  - **Archivos a modificar**:
    - `app/models/user_story.py` (agregar: approval_status, approved_by, approved_at)
    - `app/database/repositories/user_story_repository.py`

- [ ] **US-W1.2** - 📖 Modificar generador para estado DRAFT inicial
  - ⏱️ **1 día**
  - 🔗 US-W1.1
  - **Archivos a modificar**:
    - `app/backend/story_generator.py` (setear approval_status = DRAFT al crear)

- [ ] **US-W1.3** - 📖 Bloquear subida a Jira si no está APPROVED
  - ⏱️ **2 días**
  - 🔗 US-W1.2, W1.6
  - **Archivos a modificar**:
    - `static/js/modules/generators/story/story-jira.js` (validar estado antes de subir)

- [ ] **US-W1.4** - 📖 Integrar UI de workflow en historias
  - ⏱️ **2 días**
  - 🔗 W1.7, US-W1.3
  - **Entregables**:
    - Botones de "Enviar a Revisión", "Aprobar", "Rechazar"
    - Indicador visual de estado en tabla
  - **Archivos a modificar**:
    - `static/js/modules/generators/story/story-ui.js`

---

### 🔴 CRÍTICA - Versionado y Control de Cambios

#### 🔧 Infraestructura Compartida

- [ ] **V1.1** - 🔧 Diseñar modelo de versionado
  - ⏱️ **2 días**
  - 🔗 Ninguna
  - **Entregables**:
    - Estrategia de versionado (semantic versioning)
    - Estrategia de diff
    - Política de retención
  - **Documento a crear**:
    - `docs/VERSIONING_STRATEGY.md`

- [ ] **V1.2** - 🔧 Crear modelos de versionado
  - ⏱️ **3 días**
  - 🔗 V1.1
  - **Archivos a crear**:
    - `app/models/artifact_version.py`
    - `app/models/change_log.py`

- [ ] **V1.3** - 🔧 Crear migraciones de versionado
  - ⏱️ **2 días**
  - 🔗 V1.2
  - **Archivos a crear**:
    - `migrations/add_versioning_tables.sql`
    - `migrations/rollback_versioning_tables.sql`

- [ ] **V1.4** - 🔧 Implementar repositorio de versiones
  - ⏱️ **4 días**
  - 🔗 V1.3
  - **Entregables**:
    - Guardar versión al crear/actualizar
    - Obtener versión específica
    - Comparar dos versiones (diff)
    - Rollback a versión anterior
  - **Archivos a crear**:
    - `app/database/repositories/version_repository.py`

- [ ] **V1.5** - 🔧 Crear servicio de versionado
  - ⏱️ **3 días**
  - 🔗 V1.4
  - **Archivos a crear**:
    - `app/services/version_service.py`

- [ ] **V1.6** - 🔧 Crear API endpoints de versionado
  - ⏱️ **3 días**
  - 🔗 V1.5
  - **Entregables**:
    - GET /api/versions/{artifact_id}/history
    - GET /api/versions/{artifact_id}/{version}
    - POST /api/versions/{artifact_id}/rollback
    - GET /api/versions/{artifact_id}/diff?v1=1.0&v2=2.0
  - **Archivos a crear**:
    - `app/routes/version_routes.py`

- [ ] **V1.7** - 🔧 Implementar UI de versionado
  - ⏱️ **4 días**
  - 🔗 V1.6
  - **Entregables**:
    - Historial de versiones
    - Comparación visual de versiones
    - Botón de rollback
  - **Archivos a crear**:
    - `static/js/modules/versioning/version-viewer.js`
    - `templates/partials/version_history.html`

#### 🧪 Casos de Prueba

- [ ] **TC-V1.1** - 🧪 Integrar versionado en TestCaseRepository
  - ⏱️ **2 días**
  - 🔗 V1.4
  - **Archivos a modificar**:
    - `app/database/repositories/test_case_repository.py` (crear versión automática en update)

- [ ] **TC-V1.2** - 🧪 Integrar UI de versionado en casos de prueba
  - ⏱️ **2 días**
  - 🔗 V1.7, TC-V1.1
  - **Entregables**:
    - Botón "Ver Historial" en vista de caso
    - Modal de comparación de versiones
  - **Archivos a modificar**:
    - `static/js/modules/generators/test-case/test-case-ui.js`

#### 📖 Historias de Usuario

- [ ] **US-V1.1** - 📖 Integrar versionado en UserStoryRepository
  - ⏱️ **2 días**
  - 🔗 V1.4
  - **Archivos a modificar**:
    - `app/database/repositories/user_story_repository.py` (crear versión automática en update)

- [ ] **US-V1.2** - 📖 Integrar UI de versionado en historias
  - ⏱️ **2 días**
  - 🔗 V1.7, US-V1.1
  - **Entregables**:
    - Botón "Ver Historial" en vista de historia
    - Modal de comparación de versiones
  - **Archivos a modificar**:
    - `static/js/modules/generators/story/story-ui.js`

---


### 🔴 CRÍTICA - Testing e Integración de Fase 1

#### 🔧 Infraestructura Compartida

- [ ] **I1.1** - 🔧 Tests unitarios de trazabilidad
  - ⏱️ **3 días**
  - 🔗 T1.3
  - **Archivos a crear**:
    - `tests/database/repositories/test_requirement_repository.py`
    - `tests/database/repositories/test_coverage_repository.py`

- [ ] **I1.2** - 🔧 Tests unitarios de workflow
  - ⏱️ **3 días**
  - 🔗 W1.5
  - **Archivos a crear**:
    - `tests/services/test_workflow_service.py`
    - `tests/database/repositories/test_workflow_repository.py`

- [ ] **I1.3** - 🔧 Tests unitarios de versionado
  - ⏱️ **3 días**
  - 🔗 V1.5
  - **Archivos a crear**:
    - `tests/services/test_version_service.py`
    - `tests/database/repositories/test_version_repository.py`

- [ ] **I1.4** - 🔧 Tests de integración end-to-end
  - ⏱️ **5 días**
  - 🔗 I1.1, I1.2, I1.3
  - **Archivos a crear**:
    - `tests/integration/test_traceability_workflow.py`
    - `tests/integration/test_version_workflow.py`

- [ ] **I1.5** - 🔧 Documentación técnica de Fase 1
  - ⏱️ **3 días**
  - 🔗 I1.4
  - **Documentos a crear**:
    - `docs/TRACEABILITY_GUIDE.md`
    - `docs/WORKFLOW_USER_GUIDE.md`
    - `docs/VERSIONING_USER_GUIDE.md`
    - `docs/API_REFERENCE_PHASE1.md`

---

## 📊 FASE 2: Calidad y Métricas (2-3 meses)

### 🟡 ALTA - Validación de Dominio

#### 🔧 Infraestructura Compartida

- [ ] **D2.1** - 🔧 Diseñar sistema de reglas de dominio
  - ⏱️ **2 días**
  - 🔗 Ninguna
  - **Entregables**:
    - Formato de definición de reglas (YAML/JSON)
    - Tipos de reglas soportadas
  - **Documento a crear**:
    - `docs/DOMAIN_RULES_SPEC.md`

- [ ] **D2.2** - 🔧 Crear modelo de reglas de dominio
  - ⏱️ **2 días**
  - 🔗 D2.1
  - **Archivos a crear**:
    - `app/models/domain_rule.py`
    - `app/models/rule_category.py`

- [ ] **D2.3** - 🔧 Implementar DomainValidator base
  - ⏱️ **4 días**
  - 🔗 D2.2
  - **Entregables**:
    - Validación de reglas de negocio
    - Validación de nomenclatura
    - Validación de datos de prueba
  - **Archivos a crear**:
    - `app/services/validators/domain_validator.py`

- [ ] **D2.4** - 🔧 Crear UI de configuración de reglas
  - ⏱️ **3 días**
  - 🔗 D2.3
  - **Archivos a crear**:
    - `templates/admin/domain_rules.html`
    - `static/js/modules/admin/domain-rules-manager.js`

#### 🧪 Casos de Prueba

- [ ] **TC-D2.1** - 🧪 Integrar validación de dominio en generador de casos
  - ⏱️ **2 días**
  - 🔗 D2.3
  - **Archivos a modificar**:
    - `app/backend/matrix/generator.py` (aplicar DomainValidator)

- [ ] **TC-D2.2** - 🧪 Agregar validación de datos de prueba
  - ⏱️ **2 días**
  - 🔗 TC-D2.1
  - **Entregables**:
    - Validar fechas realistas
    - Validar montos realistas
    - Validar emails válidos
  - **Archivos a modificar**:
    - `app/services/validators/domain_validator.py`

#### 📖 Historias de Usuario

- [ ] **US-D2.1** - 📖 Implementar INVESTValidator
  - ⏱️ **3 días**
  - 🔗 D2.3
  - **Entregables**:
    - Validación de principios INVEST
    - Scoring de calidad
  - **Archivos a crear**:
    - `app/services/validators/invest_validator.py`

- [ ] **US-D2.2** - 📖 Integrar INVEST en validación semántica
  - ⏱️ **2 días**
  - 🔗 US-D2.1
  - **Archivos a modificar**:
    - `app/services/validator.py` (agregar validación INVEST)

- [ ] **US-D2.3** - 📖 Integrar validación de dominio en generador de historias
  - ⏱️ **2 días**
  - 🔗 D2.3
  - **Archivos a modificar**:
    - `app/backend/story_generator.py` (aplicar DomainValidator)

---

### 🟡 ALTA - Reportes de Cobertura y Métricas

#### 🔧 Infraestructura Compartida

- [ ] **R2.1** - 🔧 Diseñar dashboard de métricas
  - ⏱️ **2 días**
  - 🔗 Ninguna
  - **Entregables**:
    - Wireframes de dashboard
    - KPIs a mostrar
  - **Documento a crear**:
    - `docs/METRICS_DASHBOARD_DESIGN.md`

- [ ] **R2.2** - 🔧 Crear servicio de reportes de cobertura
  - ⏱️ **4 días**
  - 🔗 T1.3 (requiere trazabilidad)
  - **Entregables**:
    - Reporte de cobertura de requerimientos
    - Matriz de trazabilidad
    - Gaps de cobertura
  - **Archivos a crear**:
    - `app/services/reporting/coverage_report_service.py`

- [ ] **R2.3** - 🔧 Crear servicio de métricas de calidad
  - ⏱️ **3 días**
  - 🔗 R2.2
  - **Entregables**:
    - Métricas de generación (healing rate, duplicados)
    - Métricas de aprobación (tiempo, rechazos)
    - Métricas de productividad
  - **Archivos a crear**:
    - `app/services/reporting/quality_metrics_service.py`

- [ ] **R2.4** - 🔧 Crear API endpoints de reportes
  - ⏱️ **3 días**
  - 🔗 R2.3
  - **Entregables**:
    - GET /api/reports/coverage/{project_id}
    - GET /api/reports/quality/{project_id}
    - GET /api/reports/traceability-matrix/{project_id}
  - **Archivos a crear**:
    - `app/routes/reporting_routes.py`

- [ ] **R2.5** - 🔧 Implementar dashboard de métricas
  - ⏱️ **5 días**
  - 🔗 R2.4
  - **Entregables**:
    - Gráficos de cobertura
    - KPIs visuales
    - Matriz de trazabilidad interactiva
  - **Archivos a crear**:
    - `templates/dashboard/metrics.html`
    - `static/js/modules/dashboard/metrics-dashboard.js`

- [ ] **R2.6** - 🔧 Implementar exportación de reportes
  - ⏱️ **3 días**
  - 🔗 R2.5
  - **Entregables**:
    - Exportar a PDF
    - Exportar a Excel
    - Exportar a CSV
  - **Archivos a crear**:
    - `app/services/reporting/report_exporter.py`

---

### 🟡 ALTA - Testing de Fase 2

#### 🔧 Infraestructura Compartida

- [ ] **I2.1** - 🔧 Tests de validadores de dominio
  - ⏱️ **2 días**
  - 🔗 D2.3
  - **Archivos a crear**:
    - `tests/services/validators/test_domain_validator.py`

- [ ] **I2.2** - 🔧 Tests de servicios de reportes
  - ⏱️ **3 días**
  - 🔗 R2.3
  - **Archivos a crear**:
    - `tests/services/reporting/test_coverage_report_service.py`
    - `tests/services/reporting/test_quality_metrics_service.py`

- [ ] **I2.3** - 🔧 Documentación de Fase 2
  - ⏱️ **2 días**
  - 🔗 I2.2
  - **Documentos a crear**:
    - `docs/DOMAIN_VALIDATION_GUIDE.md`
    - `docs/METRICS_USER_GUIDE.md`

#### 📖 Historias de Usuario

- [ ] **US-I2.1** - 📖 Tests de INVESTValidator
  - ⏱️ **2 días**
  - 🔗 US-D2.1
  - **Archivos a crear**:
    - `tests/services/validators/test_invest_validator.py`

---

## 📊 FASE 3: Optimización y Escalabilidad (2 meses)

### 🟢 MEDIA - Procesamiento Paralelo

#### 🔧 Infraestructura Compartida

- [ ] **P3.1** - 🔧 Diseñar arquitectura de procesamiento paralelo
  - ⏱️ **2 días**
  - 🔗 Ninguna
  - **Entregables**:
    - Estrategia de paralelización
    - Rate limiting inteligente
  - **Documento a crear**:
    - `docs/PARALLEL_PROCESSING_DESIGN.md`

- [ ] **P3.2** - 🔧 Implementar generador paralelo base
  - ⏱️ **5 días**
  - 🔗 P3.1
  - **Entregables**:
    - Procesamiento asíncrono con asyncio
    - Semáforos para control de concurrencia
    - Rate limiter adaptativo
  - **Archivos a crear**:
    - `app/backend/parallel_generator.py`
    - `app/utils/rate_limiter.py`

- [ ] **P3.3** - 🔧 Configurar sistema de colas (Celery)
  - ⏱️ **4 días**
  - 🔗 P3.2
  - **Entregables**:
    - Configuración de Celery
    - Tareas asíncronas
    - Monitoreo de tareas
  - **Archivos a crear**:
    - `app/tasks/generation_tasks.py`
    - `celery_config.py`

- [ ] **P3.4** - 🔧 Implementar UI de trabajos en cola
  - ⏱️ **3 días**
  - 🔗 P3.3
  - **Entregables**:
    - Vista de trabajos en progreso
    - Notificaciones de completado
    - Cancelación de trabajos
  - **Archivos a crear**:
    - `templates/partials/job_queue.html`
    - `static/js/modules/jobs/job-monitor.js`

#### 🧪 Casos de Prueba

- [ ] **TC-P3.1** - 🧪 Migrar generador de matriz a versión paralela
  - ⏱️ **3 días**
  - 🔗 P3.2
  - **Archivos a modificar**:
    - `app/backend/matrix/generator.py` (usar ParallelGenerator)

#### 📖 Historias de Usuario

- [ ] **US-P3.1** - 📖 Migrar generador de historias a versión paralela
  - ⏱️ **3 días**
  - 🔗 P3.2
  - **Archivos a modificar**:
    - `app/backend/story_generator.py` (usar ParallelGenerator)

---

### 🟢 MEDIA - Caché y Optimización

#### 🔧 Infraestructura Compartida

- [ ] **C3.1** - 🔧 Implementar caché de contexto global
  - ⏱️ **2 días**
  - 🔗 Ninguna
  - **Archivos a crear**:
    - `app/services/cache/context_cache.py`

- [ ] **C3.2** - 🔧 Mejorar caché de proyectos Jira
  - ⏱️ **2 días**
  - 🔗 Ninguna
  - **Archivos a modificar**:
    - `static/js/modules/generators/jira-project-cache.js` (mejorar TTL y estrategia)

- [ ] **C3.3** - 🔧 Optimizar queries de base de datos
  - ⏱️ **3 días**
  - 🔗 Ninguna
  - **Entregables**:
    - Índices optimizados
    - Queries con JOIN eficientes
    - Paginación mejorada
  - **Archivos a modificar**:
    - Todos los repositorios (agregar índices)

---

### 🟢 MEDIA - Testing de Fase 3

#### 🔧 Infraestructura Compartida

- [ ] **I3.1** - 🔧 Tests de carga
  - ⏱️ **3 días**
  - 🔗 P3.4
  - **Entregables**:
    - Pruebas con 10 usuarios concurrentes
    - Pruebas con documentos grandes (>100 páginas)
  - **Archivos a crear**:
    - `tests/load/test_parallel_generation.py`

- [ ] **I3.2** - 🔧 Documentación de Fase 3
  - ⏱️ **2 días**
  - 🔗 I3.1
  - **Documentos a crear**:
    - `docs/PERFORMANCE_OPTIMIZATION_GUIDE.md`

---

## 📊 FASE 4: Funcionalidades Avanzadas (2-3 meses)

### 🔵 BAJA - Generación de Datos de Prueba

#### 🧪 Casos de Prueba (exclusivo)

- [ ] **TC-A4.1** - 🧪 Implementar TestDataGenerator
  - ⏱️ **4 días**
  - 🔗 Ninguna
  - **Entregables**:
    - Generación de emails sintéticos
    - Generación de montos realistas
    - Generación de fechas válidas
  - **Archivos a crear**:
    - `app/services/test_data_generator.py`

- [ ] **TC-A4.2** - 🧪 Integrar generador de datos en UI
  - ⏱️ **2 días**
  - 🔗 TC-A4.1
  - **Archivos a modificar**:
    - `static/js/modules/generators/test-case/test-case-ui.js`

---

### 🔵 BAJA - Gestión de Épicas y Features

#### 📖 Historias de Usuario (exclusivo)

- [ ] **US-A4.1** - 📖 Implementar CRUD de Épicas
  - ⏱️ **3 días**
  - 🔗 US-T1.2
  - **Archivos a crear**:
    - `app/routes/epic_routes.py`
    - `templates/epics/epic_list.html`
    - `static/js/modules/epics/epic-manager.js`

- [ ] **US-A4.2** - 📖 Implementar CRUD de Features
  - ⏱️ **3 días**
  - 🔗 US-T1.2
  - **Archivos a crear**:
    - `app/routes/feature_routes.py`
    - `templates/features/feature_list.html`
    - `static/js/modules/features/feature-manager.js`

- [ ] **US-A4.3** - 📖 Implementar UI de jerarquía
  - ⏱️ **4 días**
  - 🔗 US-A4.2
  - **Entregables**:
    - Vista de árbol Epic → Feature → Story
    - Drag & drop para reorganizar
  - **Archivos a crear**:
    - `static/js/modules/hierarchy/hierarchy-tree.js`
    - `templates/hierarchy/hierarchy_view.html`

---

### 🔵 BAJA - Estimación Automática

#### 📖 Historias de Usuario (exclusivo)

- [ ] **US-A4.4** - 📖 Implementar StoryPointEstimator
  - ⏱️ **4 días**
  - 🔗 Ninguna
  - **Entregables**:
    - Estimación basada en complejidad
    - Mapeo a escala Fibonacci
  - **Archivos a crear**:
    - `app/services/estimation/story_point_estimator.py`

- [ ] **US-A4.5** - 📖 Integrar estimación en generador
  - ⏱️ **2 días**
  - 🔗 US-A4.4
  - **Archivos a modificar**:
    - `app/backend/story_generator.py` (agregar estimación automática)

---

### 🔵 BAJA - Testing de Fase 4

#### 🔧 Infraestructura Compartida

- [ ] **I4.1** - 🔧 Tests de funcionalidades avanzadas
  - ⏱️ **3 días**
  - 🔗 TC-A4.2, US-A4.5
  - **Archivos a crear**:
    - `tests/services/test_test_data_generator.py`
    - `tests/services/estimation/test_story_point_estimator.py`

- [ ] **I4.2** - 🔧 Documentación final
  - ⏱️ **3 días**
  - 🔗 I4.1
  - **Documentos a crear**:
    - `docs/ADVANCED_FEATURES_GUIDE.md`
    - `docs/COMPLETE_USER_MANUAL.md`


---

## 📈 Resumen de Esfuerzo por Fase

| Fase | Tareas Totales | Días Estimados | Semanas |
|------|---------------|----------------|---------|
| **Fase 1: Fundamentos Enterprise** | 52 | 120 | 16 |
| **Fase 2: Calidad y Métricas** | 18 | 45 | 6 |
| **Fase 3: Optimización** | 12 | 30 | 4 |
| **Fase 4: Avanzadas** | 11 | 28 | 4 |
| **TOTAL** | **93** | **223** | **30** |

**Nota**: Estimaciones basadas en 1 desarrollador full-time. Con un equipo de 2-3 desarrolladores, el tiempo se puede reducir significativamente.

---

## 🎯 Priorización Recomendada

### Para Equipos Pequeños (1-2 desarrolladores)

**Enfoque**: Implementar solo lo crítico

1. ✅ **Fase 1 Completa** (16 semanas)
2. ✅ **Validación de Dominio** de Fase 2 (2 semanas)
3. ✅ **Reportes Básicos** de Fase 2 (2 semanas)
4. ⏸️ Pausar Fase 3 y 4

**Total**: ~20 semanas (5 meses)

### Para Equipos Medianos (3-4 desarrolladores)

**Enfoque**: Implementar hasta métricas

1. ✅ **Fase 1 Completa** (8 semanas con 2 devs)
2. ✅ **Fase 2 Completa** (4 semanas con 2 devs)
3. ✅ **Procesamiento Paralelo** de Fase 3 (2 semanas)
4. ⏸️ Pausar resto de Fase 3 y 4

**Total**: ~14 semanas (3.5 meses)

### Para Equipos Enterprise (5+ desarrolladores)

**Enfoque**: Implementar roadmap completo

1. ✅ **Todas las Fases** (6 meses con 4 devs)
2. ✅ **Auditoría de Seguridad** (2 semanas)
3. ✅ **Certificación** (2 semanas)

**Total**: ~7 meses

---

## 📝 Notas Finales

### Dependencias Externas

- **Celery**: Requiere Redis o RabbitMQ
- **Caché**: Requiere Redis
- **Base de Datos**: PostgreSQL o MySQL con soporte para JSON

### Riesgos Identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Cambios en API de Gemini | Media | Alto | Abstraer llamadas a IA |
| Resistencia al cambio de usuarios | Alta | Medio | Capacitación y piloto |
| Complejidad de workflow | Media | Alto | Diseño iterativo con usuarios |
| Performance de DB con versionado | Media | Medio | Índices optimizados, archivado |

### Criterios de Éxito

- ✅ 100% de artefactos con trazabilidad
- ✅ 100% de artefactos pasan por workflow
- ✅ Tiempo de generación < 5 minutos para docs grandes
- ✅ Satisfacción de usuario > 8/10
- ✅ Cobertura de requerimientos > 90%

---

**Última actualización**: 2026-01-06  
**Próxima revisión**: Después de completar Fase 1
