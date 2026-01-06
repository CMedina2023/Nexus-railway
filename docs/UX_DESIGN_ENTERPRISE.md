# 🎨 Diseño UX/UI y Flujos Enterprise: Nexus Railway

**Fecha**: 2026-01-06  
**Estatus**: Propuesta de Diseño  
**Objetivo**: Visualizar el impacto de las mejoras Enterprise en la interfaz y el viaje del usuario.

---

## 🔄 El Cambio de Paradigma

Actualmente, Nexus Railway funciona como una **Herramienta Transaccional**:
> *Subo archivo -> Genero -> Descargo -> Me olvido.*

Con las mejoras Enterprise (Base de Conocimiento, Trazabilidad, Workflow), pasamos a una **Plataforma de Gestión**:
> *Selecciono Proyecto -> Entreno a la IA (Contexto) -> Genero Artefactos -> Reviso/Apruebo -> Versiono.*

---

## 🗺️ Nuevo Mapa de Navegación

### 1. 🏠 Dashboard de Proyecto (Nuevo "Home")
Antes, entrabas directo a "Generar Historia". Ahora, el punto de entrada debe ser el **Proyecto**.

*   **UI Propuesta**: Tarjetas de Proyectos Activos.
*   **Acción**: Al hacer clic en "Proyecto Nexus Railway", entras al "Workspace" de ese proyecto.
*   **Datos Clave**: Estado general (% de Cobertura, Historias Aprobadas vs Pendientes).

### 2. 🧠 La Base de Conocimiento (El "Cerebro")
Esta es la interfaz nueva más crítica. Sustituye la subida repetitiva de archivos.

*   **Ubicación**: Pestaña "Contexto" dentro de un Proyecto.
*   **Componentes UI**:
    *   **Dropzone Multi-archivo**: "Arrastra aquí Req Funcionales, Reglas de Negocio, Diagramas DB".
    *   **Lista de Documentos Activos**: Tabla con status "Analizado", "Pendiente".
    *   **Visor de Contexto**: Un acordeón que muestra lo que la IA entendió:
        *   *Glosario Detectado* (ej: "Usuario Admin" = Roles > 2).
        *   *Reglas Globales* (ej: "Toda fecha debe ser UTC").
*   **Impacto en Flujo**: El usuario sube los docs **una sola vez**.

### 3. ✨ Flujo de Generación (Simplificado)

El formulario de generación (`stories-form`) cambia drásticamente.

*   **Antes**: Upload File (Obligatorio) -> Prompt -> Generar.
*   **Ahora**:
    *   **Select Context (Checkboxes)**: "¿Qué documentos de la Base de Conocimiento debe considerar la IA?" (Por defecto: Todos).
    *   **Foco (Prompt)**: "¿Qué quieres generar hoy?" (ej: "Solo el módulo de Pagos").
    *   **Upload (Opcional)**: "Subir documento extra solo para esta sesión".

> **Beneficio UX**: Generas historias coherentes con todo el proyecto sin volver a subir 5 archivos PDF gigantes.

### 4. 👁️ Vista de Resultados (Trazabilidad y Workflow)

Las tablas de resultados (`preview-table`) se enriquecen visualmente.

#### A. Gestión de Estado (Workflow)
*   **Indicador Visual**: Cada fila tiene un Badge: `DRAFT` (Gris), `REVIEW` (Amarillo), `APPROVED` (Verde).
*   **Acciones**:
    *   Botón "Solicitar Revisión" (Mueve de Draft a Review).
    *   Para Revisores: Botones "Aprobar" / "Rechazar" (con modal para feedback).

#### B. Trazabilidad
*   **Columna Nueva "Origen"**: Muestra de qué parráfo/documento salió esta historia.
*   **Enlace Cruzado**: Si es un Caso de Prueba, muestra un Link a la Historia de Usuario que valida.

#### C. Versionado
*   **Pestaña "Historial"**: Al hacer clic en una historia, se abre un panel lateral (Drawer).
*   **Diff Visual**: Texto verde (nuevo) vs rojo (eliminado) comparando la Versión 1 vs Versión 2.

---

## 🚦 Comparativa de Flujos

### Escenario: Crear Casos de Prueba para un Módulo Nuevo

| Paso | Flujo Actual (Legacy) | Flujo Enterprise (Nuevo) |
| :--- | :--- | :--- |
| **Inicio** | Subo el PDF de requerimientos. | Entro al proyecto y veo que el PDF ya está en la **Base de Conocimiento**. |
| **Config** | Selecciono "Casos de Prueba". | Selecciono "Generar Casos" y marco "Usar contexto global". |
| **Generación** | La IA lee el PDF y genera. | La IA lee el PDF + Reglas de Negocio + Glosario del proyecto y genera. |
| **Resultado** | Veo una lista plana. | Veo casos en estado **DRAFT**. |
| **Validación** | Leo y edito a ojo. | Veo que el caso 5 cubre el Req 2.1 (**Trazabilidad**). |
| **Cierre** | Descargo Excel. | Hago clic en "Enviar a Aprobación". El QA Lead recibe notificación. |

---

## 🧩 Componentes UI Reutilizables Requeridos

Para lograr esto sin duplicar código, necesitamos estandarizar estos componentes UI:

1.  **`ProjectContextSelector`**: Widget para elegir qué documentos usar.
2.  **`StatusBadge`**: Componente visual para los estados del workflow.
3.  **`ApprovalControls`**: Botonera estandarizada (Approve/Reject/Comment).
4.  **`DiffViewer`**: Componente para mostrar cambios entre versiones (texto).

---

## 🖼️ Mockups Visuales

Hemos generado prototipos de alta fidelidad para guiar la implementación, respetando la paleta de colores Dark Mode (`#0f172a`, `#1e293b`) y el estilo Glassmorphism.

### 1. Dashboard de Proyectos
El nuevo "Home" donde se gestionan múltiples proyectos. Note las tarjetas con diseño estilizado consistente con el Sidebar actual.

![Dashboard de Proyectos Nexus](nexus_enterprise_dashboard_mockup.png)

### 2. Base de Conocimiento (Knowledge Base)
Interfaz centralizada de carga de documentos, integrando el dropzone existente pero escalado para gestión multi-archivo.

![Base de Conocimiento Nexus](nexus_knowledge_base_ui_mockup.png)

### 3. Tabla de Resultados con Workflow
La evolución de la tabla de vista previa. Incluye Badges de estado (`Draft`, `Approved`) y columna de Trazabilidad, respetando la estética de tablas del sistema.

![Resultados y Workflow Nexus](nexus_stories_workflow_mockup.png)

---

## 🛡️ Conclusión de Impacto

1.  **Backend**: El cambio es masivo (Persistencia, Relaciones, IA más compleja).
2.  **Frontend**: El cambio es de **Arquitectura de Información**. Pasamos de formularios simples a Paneles de Gestión.
3.  **Usuario Final**: Curva de aprendizaje inicial ligeramente mayor (entender "Proyectos"), pero productividad exponencialmente mayor a largo plazo (no repetir uploads, confianza en los datos).
