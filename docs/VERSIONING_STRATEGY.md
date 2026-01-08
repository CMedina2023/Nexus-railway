# Estrategia de Versionado y Control de Cambios

## 1. Propósito
Este documento define la estrategia técnica y normativa para el manejo de versiones de los artefactos generados por Nexus Railway (Casos de Prueba, Historias de Usuario, Matrices de Trazabilidad, etc.). El objetivo es asegurar la trazabilidad histórica, facilitar la auditoría y permitir la recuperación ante errores.

## 2. Estrategia de Versionado (Semantic Versioning Adaptado)

Adoptaremos un esquema de versionado semántico simplificado para documentos (`MAJOR.MINOR`), dado que el concepto de "PATCH" es menos relevante en documentos de texto que en software compilado, a menos que sean correcciones ortográficas menores.

### Esquema de Versión: `vX.Y`

*   **X (MAJOR)**: Cambios estructurales o reescrituras significativas.
*   **Y (MINOR)**: Modificaciones de contenido, actualizaciones de campos o correcciones menores.

### Reglas de Incremento

| Tipo de Cambio | Incremento | Ejemplo Anterior | Ejemplo Nuevo | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| **Creación Inicial** | - | - | `v1.0` | Primera versión aprobada o generada oficialmente. |
| **Borrador (Draft)** | - | - | `v0.1` | Versiones preliminares generadas por la IA antes de aprobación humana. |
| **Edición de Contenido** | `MINOR` | `v1.0` | `v1.1` | Cambios en descripción, pasos, criterios de aceptación. |
| **Cambio de Estado** | `MINOR` | `v1.1` | `v1.2` | Transición de estados (ej. DRAFT -> PENDING_REVIEW). |
| **Regeneración IA** | `MAJOR` | `v1.2` | `v2.0` | El usuario solicita regenerar completamente el artefacto con nuevos prompts/contexto. |
| **Reestructuración** | `MAJOR` | `v1.5` | `v2.0` | Cambios masivos en la estructura del documento. |

### Metadatos de Versión
Cada registro de versión debe almacenar inmutablemente:
*   `version_number`: String (e.g., "1.2").
*   `created_at`: Timestamp UTC.
*   `created_by`: ID del usuario o "SYSTEM (AI)".
*   `change_reason`: Comentario del cambio (ej. "Regeneración por cambio en reglas de negocio" o "Corrección manual de ortografía").
*   `content_snapshot`: JSON/Texto completo del artefacto en ese momento.
*   `parent_version_id`: Puntero a la versión anterior (para listas enlazadas).

## 3. Estrategia de Diff (Comparación de Versiones)

Para permitir a los usuarios visualizar qué cambió entre dos versiones, se implementará un sistema de comparación a dos niveles:

### A. Diff Visual (Frontend)
*   **Librería**: Se utilizará `diff-match-patch` (Google) o similar en el frontend.
*   **Visualización**:
    *   <span style="background-color: #ffdce0; color: #cc0000; text-decoration: line-through;">Texto eliminado en rojo</span>.
    *   <span style="background-color: #e6ffed; color: #008000;">Texto agregado en verde</span>.
*   **Granularidad**: Diferencias a nivel de palabra para campos de texto largo (Descripciones), y a nivel de valor completo para campos cortos (Estados, IDs).

### B. Diff Estructural (Backend)
*   Para auditoría, el sistema calculará el delta de campos modificados.
*   Si se modificó solo el campo "Prioridad", el log de cambios debe reflejar explícitamente: `Prioridad: "Alta" -> "Crítica"`.

## 4. Política de Retención

Dado que el almacenamiento de texto es barato pero las versiones infinitas pueden degradar el rendimiento de las consultas, se establecen los siguientes límites:

### Reglas de Conservación
1.  **Versiones Aprobadas (Approved)**: Retención **PERMANENTE**. Nunca se eliminan versiones que hayan sido aprobadas formalmente.
2.  **Versiones Mayores (Major)**: Retención **PERMANENTE**. Hitos importantes en la vida del artefacto.
3.  **Borradores Intermedios (Drafts)**:
    *   Se retienen los últimos **10 borradores**.
    *   Borradores de más de **30 días** de antigüedad que no sean la versión activa actual serán archivados/purgados automáticamente.

### Limpieza (Pruning)
*   Un proceso cron (`maintenance_job`) se ejecutará semanalmente para identificar y compactar/eliminar versiones obsoletas que violen la política de retención.
*   **Compactación**: Si hubo 5 guardados manuales en 1 hora por el mismo usuario, se pueden fusionar en una sola versión representativa para no ensuciar el historial.

## 5. Implementación Técnica

### Tablas Requeridas (Estructura Base)
*   `artifact_versions`: Tabla polimórfica o específica por artefacto (ej. `test_case_versions`, `user_story_versions`) que almacena el snapshot.
*   `change_log`: Tabla para registrar el resumen de qué cambió (metadata) sin guardar todo el contenido pesado, útil para listados rápidos.

### Flujo de Rollback
1.  El usuario selecciona una versión `v1.5` anterior.
2.  El sistema crea una **NUEVA** versión `v2.0` (o la siguiente consecutiva) clonando el contenido de `v1.5`.
3.  **NO** se elimina la historia intermedia; se "avanza hacia el pasado". El `change_reason` indicará "Rollback a v1.5".
