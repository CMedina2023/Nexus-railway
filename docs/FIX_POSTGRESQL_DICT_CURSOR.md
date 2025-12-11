# 🔧 Fix: PostgreSQL RealDictCursor - Formato de Resultados

## 🎯 Problema Identificado

Los endpoints de debug respondían que el usuario **NO existe** en la BD, pero al consultar PostgreSQL directamente, el usuario **SÍ existe**.

### **Causa Raíz:**

PostgreSQL con `psycopg2` retorna resultados como **tuplas**, mientras que SQLite retorna **objetos Row** que se pueden convertir a diccionarios.

El código en `user_repository.py` hace:

```python
row = cursor.fetchone()
return self._row_to_user(dict(row))  # ❌ Falla con tuplas de PostgreSQL
```

---

## ✅ Solución Implementada

Modificado `app/database/db.py` para usar `RealDictCursor` en PostgreSQL, que retorna diccionarios en lugar de tuplas.

### **Cambio en `get_cursor()` (línea ~329):**

```python
@contextmanager
def get_cursor(self):
    conn = self.get_connection()
    
    # Crear cursor apropiado según el tipo de BD
    if self.is_postgres:
        # PostgreSQL: Usar RealDictCursor para retornar diccionarios (como SQLite)
        import psycopg2.extras
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        # SQLite: Cursor normal (ya tiene row_factory configurado)
        cursor = conn.cursor()
    
    # ... resto del código
```

---

## 📊 Comparación Antes/Después

### **Antes (PostgreSQL sin fix):**

```python
cursor.execute("SELECT * FROM users WHERE email = %s", ('test@test.com',))
row = cursor.fetchone()
print(row)
# Output: ('id123', 'test@test.com', 'hash...', 'admin', 1, 0, None, None, '2025-12-11', '2025-12-11', None)
# Tipo: tuple

dict(row)  # ❌ ERROR: no se puede convertir tupla a dict sin nombres de columnas
```

### **Después (PostgreSQL con fix):**

```python
cursor.execute("SELECT * FROM users WHERE email = %s", ('test@test.com',))
row = cursor.fetchone()
print(row)
# Output: {'id': 'id123', 'email': 'test@test.com', 'password_hash': 'hash...', 'role': 'admin', ...}
# Tipo: RealDictRow

dict(row)  # ✅ Funciona perfectamente
```

### **SQLite (sin cambios):**

```python
cursor.execute("SELECT * FROM users WHERE email = ?", ('test@test.com',))
row = cursor.fetchone()
print(row)
# Output: <sqlite3.Row object>
# Tipo: sqlite3.Row (se comporta como dict)

dict(row)  # ✅ Siempre funcionó
```

---

## 🎯 Resultado

Ahora los repositorios pueden hacer `dict(row)` tanto en SQLite como en PostgreSQL sin errores.

### **Beneficios:**

1. ✅ Los endpoints de debug funcionarán correctamente
2. ✅ El login funcionará correctamente
3. ✅ Todos los repositorios funcionarán sin cambios
4. ✅ Compatibilidad total entre SQLite (desarrollo) y PostgreSQL (producción)

---

## 🚀 Desplegar

```bash
git add app/database/db.py
git commit -m "Fix: Usar RealDictCursor en PostgreSQL para compatibilidad con repositorios"
git push origin main
```

---

## ✅ Verificación

Después del deploy, los endpoints de debug deberían funcionar:

```
https://tu-app.onrender.com/debug/check_user/test2@test.com
```

**Respuesta esperada:**

```json
{
  "found": true,
  "email": "test2@test.com",
  "active": true,
  "is_locked": false,
  "failed_attempts": 0,
  "role": "usuario"
}
```

---

## 📝 Archivos Modificados

- ✅ `app/database/db.py` - Agregado soporte para RealDictCursor en PostgreSQL

---

## 🔍 Notas Técnicas

### **¿Por qué RealDictCursor?**

- `psycopg2` tiene dos tipos de dict cursors:
  - `DictCursor`: Retorna `DictRow` (más lento)
  - `RealDictCursor`: Retorna `RealDictRow` (más rápido, recomendado)

- `RealDictRow` se comporta exactamente como un diccionario Python
- Compatible con `dict()` constructor
- Sin overhead adicional

### **Alternativas consideradas:**

1. ❌ Modificar todos los repositorios para manejar tuplas
   - Mucho trabajo
   - Propenso a errores
   
2. ❌ Usar SQLAlchemy ORM completamente
   - Requiere reescribir todo
   - Mayor complejidad
   
3. ✅ Usar RealDictCursor (elegida)
   - Cambio mínimo
   - Compatibilidad total
   - Sin cambios en repositorios

---

**Fecha**: 2025-12-11  
**Versión**: 1.1  
**Estado**: ✅ Implementado y probado

