# Fix de row_factory para SQLite

## Problema Identificado

Los scripts `make_admin.py` y `view_db.py` fallaban con el error:
```
TypeError: tuple indices must be integers or slices, not str
```

### Causa Raíz

Durante una refactorización previa para usar SQLAlchemy en lugar de conexiones directas de `sqlite3`, se olvidó configurar `row_factory` para SQLite. Esto causaba que las consultas retornaran **tuplas** en lugar de **diccionarios/Row objects**.

## Solución Implementada

### 1. Configuración de row_factory en el Engine (db.py)

**Archivo**: `app/database/db.py`

**Cambio**: Se agregó un event listener de SQLAlchemy para configurar `row_factory` automáticamente cuando se crea una conexión SQLite:

```python
# Configurar row_factory para retornar diccionarios en SQLite
@event.listens_for(self.engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    import sqlite3
    dbapi_conn.row_factory = sqlite3.Row
```

**Ubicación**: Líneas 57-61, dentro del bloque `if self.is_sqlite:`

**Impacto**: 
- ✅ Solo afecta conexiones SQLite
- ✅ NO afecta PostgreSQL (producción)
- ✅ Se aplica automáticamente a todas las conexiones del pool

### 2. Actualización de Scripts

**Archivos modificados**:
- `scripts/make_admin.py`
- `scripts/view_db.py`

**Cambios**:
- Reemplazado `db.get_connection()` por `db.get_cursor()` (context manager)
- Removidos emojis que causaban problemas de encoding en Windows
- Mejorado manejo de resultados para compatibilidad con ambos tipos de BD

## Verificación de Compatibilidad

### ✅ SQLite (Desarrollo Local)

**Pruebas realizadas**:
1. ✅ `python scripts/make_admin.py --list` - Funciona correctamente
2. ✅ `python scripts/view_db.py` - Funciona correctamente
3. ✅ `python test_app_functionality.py` - Todas las pruebas pasan
4. ✅ UserRepository y UserService funcionan correctamente

**Resultado**: `sqlite3.Row` objects se retornan correctamente, permitiendo acceso por clave.

### ✅ PostgreSQL (Producción)

**Análisis de impacto**:

1. **El evento NO se registra para PostgreSQL**:
   ```python
   if self.is_sqlite:
       # Solo se ejecuta para SQLite
       @event.listens_for(self.engine, "connect")
       def set_sqlite_pragma(dbapi_conn, connection_record):
           ...
   ```

2. **PostgreSQL usa RealDictCursor**:
   - En `get_cursor()`, PostgreSQL usa `psycopg2.extras.RealDictCursor`
   - Este comportamiento NO cambió
   - Retorna diccionarios nativamente

3. **Los scripts NO se ejecutan en producción**:
   - Railway solo ejecuta `python start_server.py`
   - Los scripts en `scripts/` son herramientas de administración manual
   - Están en `.railwayignore` (aunque se suban, no se ejecutan automáticamente)

## Archivos Modificados

### Archivos de Código
1. `app/database/db.py` - Agregado event listener para row_factory
2. `scripts/make_admin.py` - Actualizado para usar get_cursor()
3. `scripts/view_db.py` - Actualizado para usar get_cursor()

### Archivos de Prueba (temporales, pueden eliminarse)
1. `test_db_fix.py` - Script de prueba del fix
2. `test_app_functionality.py` - Script de prueba de funcionalidad

## Impacto en Producción

### ❌ NO Afecta Producción

**Razones**:
1. El cambio solo afecta SQLite (desarrollo local)
2. PostgreSQL (producción) usa un mecanismo diferente (RealDictCursor)
3. El código de la aplicación web (UserRepository, UserService) ya usaba `get_cursor()` correctamente
4. Los scripts modificados son herramientas de administración que no se ejecutan en producción

### ✅ Beneficios

1. **Desarrollo local funcional**: Los scripts de administración ahora funcionan correctamente
2. **Consistencia**: Tanto SQLite como PostgreSQL retornan objetos dict-like
3. **Mejor debugging**: Más fácil inspeccionar datos en desarrollo local
4. **Sin regresiones**: La aplicación web sigue funcionando igual

## Recomendaciones

### Para Deploy

✅ **Es seguro hacer deploy** con estos cambios porque:
1. No afectan el código de producción (PostgreSQL)
2. Mejoran la experiencia de desarrollo local
3. No cambian la lógica de negocio
4. Todas las pruebas pasan

### Para Desarrollo

1. Ejecutar siempre scripts desde la raíz del proyecto:
   ```bash
   python scripts/make_admin.py --list
   python scripts/view_db.py
   ```

2. Usar `get_cursor()` en lugar de `get_connection()` para nuevo código que necesite acceso a datos

3. Los archivos de prueba temporales pueden eliminarse después de verificar:
   ```bash
   del test_db_fix.py
   del test_app_functionality.py
   ```

## Conclusión

✅ **Fix implementado correctamente**
✅ **SQLite funciona en desarrollo local**
✅ **PostgreSQL no afectado (producción)**
✅ **Aplicación web funciona correctamente**
✅ **Seguro para deploy**

---

**Fecha**: 2025-12-11
**Autor**: Sistema de desarrollo Nexus AI
