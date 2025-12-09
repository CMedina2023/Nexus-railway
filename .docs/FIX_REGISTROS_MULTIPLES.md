# Fix: Registros Múltiples y "UNKNOWN" en Métricas

**Fecha**: 2025-12-08  
**Versión**: 2.6.1  
**Estado**: ✅ Completado

---

## 🐛 Problemas Identificados

### Problema 1: Se guardaban múltiples registros individuales
**Síntoma**: Al generar 15 casos de prueba, se creaban 15 registros separados en la base de datos en lugar de 1 registro con 15 casos.

**Causa**: Había un bucle `for` que iteraba sobre cada caso/historia y creaba un registro individual en la base de datos.

**Ubicación**: 
- `app/core/app.py` líneas 1155-1166 (historias)
- `app/core/app.py` líneas 1253-1264 (casos de prueba)

### Problema 2: Aparecía "UNKNOWN" en lugar del área
**Síntoma**: En el dashboard, los registros aparecían con "UNKNOWN" en lugar del área seleccionada (Finanzas, RRHH, etc.).

**Causa**: El frontend no estaba enviando el campo `project_key` (que contiene el área) en el FormData.

**Ubicación**: `templates/index.html` líneas 8961-8968

---

## ✅ Soluciones Implementadas

### Solución 1: Guardar UN SOLO registro con todo el contenido

#### Historias de Usuario (`app/core/app.py`)

**ANTES** (líneas 1150-1171):
```python
story_repo = UserStoryRepository()
for story in validated_stories:  # ← Bucle que crea múltiples registros
    story_title = story.get('summary', story.get('title', 'Historia sin título'))[:200]
    
    user_story = UserStory(
        user_id=user_id,
        project_key=project_key,
        story_title=story_title,
        story_content=json.dumps(story, ensure_ascii=False),
        jira_issue_key=None
    )
    story_repo.create(user_story)  # ← Se guarda 1 por 1
```

**DESPUÉS**:
```python
# Crear UN SOLO registro con todas las historias
story_repo = UserStoryRepository()
story_title = f"Generación de {stories_count} historias de usuario - {project_key}"

user_story = UserStory(
    user_id=user_id,
    project_key=project_key,  # Área: Finanzas, RRHH, etc.
    story_title=story_title,
    story_content=json.dumps(validated_stories, ensure_ascii=False),  # ← Todas juntas
    jira_issue_key=None
)
story_repo.create(user_story)  # ← Se guarda 1 solo registro
```

#### Casos de Prueba (`app/core/app.py`)

**ANTES** (líneas 1248-1269):
```python
test_case_repo = TestCaseRepository()
for test_case in matrix_data:  # ← Bucle que crea múltiples registros
    test_case_title = test_case.get('summary', test_case.get('title', 'Caso de prueba sin título'))[:200]
    
    test_case_obj = TestCase(
        user_id=user_id,
        project_key=project_key,
        test_case_title=test_case_title,
        test_case_content=json.dumps(test_case, ensure_ascii=False),
        jira_issue_key=None
    )
    test_case_repo.create(test_case_obj)  # ← Se guarda 1 por 1
```

**DESPUÉS**:
```python
# Crear UN SOLO registro con todos los casos de prueba
test_case_repo = TestCaseRepository()
test_case_title = f"Generación de {test_cases_count} casos de prueba - {project_key}"

test_case_obj = TestCase(
    user_id=user_id,
    project_key=project_key,  # Área: Finanzas, RRHH, etc.
    test_case_title=test_case_title,
    test_case_content=json.dumps(matrix_data, ensure_ascii=False),  # ← Todos juntos
    jira_issue_key=None
)
test_case_repo.create(test_case_obj)  # ← Se guarda 1 solo registro
```

### Solución 2: Enviar el área desde el frontend

**ANTES** (`templates/index.html` líneas 8961-8968):
```javascript
const formData = new FormData();

if (this.currentFile) {
    formData.append('file', this.currentFile);
}

formData.append('task_type', action);
formData.append('role', 'Usuario');
// ← NO se enviaba el área
```

**DESPUÉS**:
```javascript
const formData = new FormData();

if (this.currentFile) {
    formData.append('file', this.currentFile);
}

formData.append('task_type', action);
formData.append('role', 'Usuario');
// ← NUEVO: Enviar el área seleccionada
formData.append('project_key', this.selectedArea || 'General');
```

---

## 📊 Resultado

### Antes del Fix ❌
- Generar 15 casos de prueba → **15 registros** en BD
- Área mostrada: **"UNKNOWN"**
- Dashboard confuso con muchas entradas duplicadas

### Después del Fix ✅
- Generar 15 casos de prueba → **1 registro** en BD
- Área mostrada: **"Finanzas"** (o el área seleccionada)
- Dashboard limpio con una entrada por generación
- Título descriptivo: "Generación de 15 casos de prueba - Finanzas"

---

## 🧪 Cómo Probar

1. **Iniciar sesión** en la aplicación
2. **Ir al Agente AI** (chat)
3. **Seleccionar un área** (ej: Finanzas)
4. **Subir un documento** y generar casos de prueba
5. **Verificar en el dashboard**:
   - ✅ Debe aparecer **1 solo registro**
   - ✅ El título debe ser: "Generación de X casos de prueba - Finanzas"
   - ✅ El área debe ser "Finanzas" (no "UNKNOWN")

---

## 📝 Archivos Modificados

### Backend:
- ✅ `app/core/app.py` - Eliminados bucles que creaban registros múltiples

### Frontend:
- ✅ `templates/index.html` - Agregado envío del área en FormData

### Documentación:
- ✅ `.docs/FIX_REGISTROS_MULTIPLES.md` - Este documento

---

## ⚠️ Notas Importantes

1. **Compatibilidad**: Los registros antiguos (múltiples) permanecerán en la base de datos. Solo las nuevas generaciones usarán el formato correcto (1 registro).

2. **Naming confuso**: El campo se llama `project_key` en la base de datos, pero realmente almacena el **área** (Finanzas, RRHH, etc.), no el proyecto de Jira. Esto es por diseño histórico del sistema.

3. **Contenido JSON**: Ahora el campo `story_content` o `test_case_content` contiene un **array JSON** con todas las historias/casos, en lugar de un solo objeto.

4. **Logs mejorados**: Los logs ahora indican claramente cuántos items se guardaron en un solo registro:
   ```
   Historias guardadas en BD local: 1 registro con 15 historias para user_id=123, área=Finanzas
   ```

---

## 🎉 Beneficios

✅ **Dashboard más limpio**: Una entrada por generación en lugar de múltiples  
✅ **Mejor organización**: Fácil identificar cuándo se generó cada lote  
✅ **Área correcta**: Ya no aparece "UNKNOWN"  
✅ **Mejor trazabilidad**: El título indica cuántos items se generaron  
✅ **Consistencia**: Mismo comportamiento para historias y casos de prueba  

---

**Versión**: 2.6.1  
**Última actualización**: 2025-12-08





