# Pipeline de Generación - Nexus Railway

El pipeline de generación implementado en Nexus Railway es un sistema de **6 pasos** que orquesta la creación de historias de usuario y casos de prueba mediante IA, con validación semántica, crítica automática y ensamblaje protegido.

---

## Arquitectura del Pipeline

### Componentes Principales

1. **GenerationOrchestrator** (`app/services/generation_orchestrator.py`)
   - Orquesta el flujo completo de generación
   - Coordina validación, transformación y persistencia
   - Emite eventos SSE para seguimiento en tiempo real

2. **Generadores Especializados** (`app/backend/generators/`)
   - `StoryGenerator`: Genera historias de usuario
   - `MatrixGenerator`: Genera casos de prueba
   - Implementan patrón Strategy con clase base `Generator`

3. **Servicios de Soporte**
   - `DataTransformer`: Limpieza y normalización de datos
   - `Validator`: Validación semántica y estructural
   - `FileGenerator`: Generación de archivos (DOCX, CSV, JSON, ZIP)

---

## Pipeline de 6 Pasos

### **Paso 0: Inyección de Contexto Global** 🔄
```
Entrada: project_key (opcional)
Proceso: Carga contexto persistido del proyecto desde BD
Salida: Parámetros enriquecidos con reglas de negocio y glosario
```

**Objetivo**: Enriquecer la generación con contexto empresarial específico del proyecto.

---

### **Paso 1: Generación Inicial con LLM** 🤖
```
Entrada: Documento + Parámetros (rol, contexto, área)
Proceso: 
  - Extracción de Contexto Global (para historias)
  - Identificación de actores y perfiles
  - Generación de historias/casos con IA
  - Aplicación de contexto de negocio
Salida: Contenido generado en bruto
```

**Características**:
- Ejecución en **hilo separado** para evitar bloqueos
- Progreso simulado con mensajes descriptivos
- Heartbeat cada 2s para mantener conexión SSE viva
- Estrategia de "Dos Pasadas" para historias (contexto global → generación individual)

---

### **Paso 2: Evaluación por LLM Critic** 🔍
```
Entrada: Contenido generado
Proceso: Análisis crítico de calidad y coherencia
Salida: Recomendaciones de mejora (activado si hay fallos en Paso 3)
```

**Objetivo**: Detectar inconsistencias lógicas antes de validación formal.

---

### **Paso 3: Validación Semántica Profunda** ✅
```
Entrada: Historias/Casos generados
Proceso:
  - Validación de coherencia con documento original
  - Verificación de criterios de aceptación
  - Detección de ambigüedades
Salida: Lista de issues encontrados
```

**Validadores**:
- `semantic_validate_story()`: Para historias de usuario
- `semantic_validate_case()`: Para casos de prueba

---

### **Paso 4: Verificación de Calidad** 🎯
```
Entrada: Contenido validado semánticamente
Proceso: Verificación de estándares de calidad
Salida: Confirmación de calidad
```

**Nota**: La validación semántica ya se ejecuta en el backend, este paso es principalmente visual.

---

### **Paso 5: Validación Final de Integridad** 🛡️
```
Entrada: Contenido procesado
Proceso:
  - Validación estructural completa
  - Verificación de campos obligatorios
  - Filtrado de elementos inválidos
Salida: Contenido final validado
```

**Métodos**:
- `validate_stories()`: Retorna historias válidas + mensaje de error
- `validate_test_cases()`: Retorna casos válidos + mensaje de error

---

### **Paso 6: Ensamblaje Protegido** 📦
```
Entrada: Contenido validado
Proceso:
  1. Generación de archivos (DOCX, CSV, JSON)
  2. Creación de HTML para preview
  3. Persistencia en base de datos
  4. Empaquetado en ZIP (si aplica)
Salida: Archivos descargables + datos para UI
```

**Persistencia**:
- Historias → Tabla `user_stories`
- Casos de Prueba → Tabla `test_cases`
- Incluye: `user_id`, `project_key`, `area`, `content` (JSON), timestamps

---

## Flujo de Datos

```
Documento PDF/TXT
    ↓
[Paso 0] Inyección de Contexto
    ↓
[Paso 1] LLM Generación (Hilo separado)
    ↓
[Paso 2] LLM Critic 
    ↓
[Paso 3] Validación Semántica
    ↓
[Paso 4] Verificación de Calidad
    ↓
[Paso 5] Validación de Integridad
    ↓
[Paso 6] Ensamblaje + BD + Archivos
    ↓
Respuesta SSE con URLs de descarga
```

---

## Comunicación SSE (Server-Sent Events)

### Formato de Mensajes
```json
{
  "message": "Extrayendo Contexto Global...",
  "progress": 15,
  "status": "Contexto Global",
  "terminal": false,
  "data": null
}
```

### Estados del Pipeline
- **Inicio**: Progreso 0-10%
- **Generación IA**: Progreso 10-70%
- **Validación**: Progreso 70-90%
- **Ensamblaje**: Progreso 90-100%
- **completed**: Pipeline exitoso
- **error**: Fallo en algún paso

---

## Estrategia de Dos Pasadas (Historias)

### Primera Pasada: Extracción de Contexto Global
- Identifica reglas de negocio transversales
- Construye glosario de términos
- Detecta dependencias entre requisitos

### Segunda Pasada: Generación Individual
- Aplica contexto global a cada historia
- Genera criterios de aceptación contextualizados
- Asegura consistencia narrativa

**Beneficio**: Historias más coherentes y alineadas con el negocio.

---

## Manejo de Errores

### Niveles de Error
1. **Error en Generación IA**: Retorna mensaje de error + progreso 0
2. **Error en Validación**: Limpia archivos temporales + mensaje descriptivo
3. **Error en BD**: Loguea warning pero continúa el flujo
4. **Error Inesperado**: Captura en `try-except` + evento SSE de error

### Recuperación
- Archivos temporales se limpian automáticamente en caso de fallo
- Conexión SSE se mantiene viva con heartbeats
- Logs detallados en `logger` para debugging

---

## Tipos de Generación

### 1. Solo Historias (`task_type='story'`)
- Genera archivo `.docx` con historias
- Incluye HTML preview + CSV para Jira
- Persiste en tabla `user_stories`

### 2. Solo Casos de Prueba (`task_type='matrix'`)
- Genera `.zip` con JSON + CSV
- Incluye HTML preview
- Persiste en tabla `test_cases`

### 3. Generación Combinada (`task_type='both'`)
- Ejecuta ambos pipelines en secuencia
- Genera `.zip` combinado con todos los archivos
- Persiste en ambas tablas

---

## Optimizaciones Implementadas

1. **Ejecución Asíncrona**: IA corre en hilo separado
2. **Progreso Fluido**: Simulación sincronizada con pasos reales
3. **Heartbeat**: Mantiene conexión viva en proxies (Nginx)
4. **Validación Incremental**: Detecta errores temprano
5. **Caché de Contexto**: Reutiliza contexto global del proyecto
6. **Batch Processing**: Procesa historias en lotes para eficiencia

---

## Métricas de Rendimiento

- **Tiempo Promedio**: 30-60 segundos (depende del tamaño del documento)
- **Heartbeat Interval**: 2 segundos
- **Delay entre Pasos Simulados**: 3-5 segundos
- **Timeout de Proxy**: Evitado con heartbeats

---

## Próximas Mejoras (Roadmap)

- [ ] Implementar repositorio de contexto de proyecto (K1.5)
- [ ] Activar LLM Critic de forma automática
- [ ] Paralelizar generación de historias y casos
- [ ] Agregar métricas de calidad en respuesta
- [ ] Implementar retry automático en fallos transitorios

---

## Referencias Técnicas

- **Orquestador**: `app/services/generation_orchestrator.py`
- **Generadores**: `app/backend/generators/`
- **Validadores**: `app/services/validator.py`
- **Transformadores**: `app/services/data_transformer.py`
- **Repositorios**: `app/database/repositories/`

---
