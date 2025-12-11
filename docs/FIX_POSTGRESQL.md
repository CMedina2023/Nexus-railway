# 🔧 Fix: Conexión a PostgreSQL en Render

## 📋 Problema Identificado

La aplicación estaba usando **SQLite local** en lugar de **PostgreSQL**, causando que los datos se borraran cada vez que Render reiniciaba el servicio.

## ✅ Solución Implementada

### 1. **Modificado `app/database/db.py`**

- ✅ Ahora soporta **SQLite** (desarrollo) y **PostgreSQL** (producción)
- ✅ Usa **SQLAlchemy** para gestión de conexiones
- ✅ Detecta automáticamente el tipo de base de datos desde `DATABASE_URL`
- ✅ Convierte automáticamente placeholders SQL (`?` → `%s`)

### 2. **Creado `app/database/query_adapter.py`**

- ✅ Adaptador que convierte consultas SQLite a PostgreSQL automáticamente
- ✅ Los repositorios existentes funcionan sin cambios

### 3. **Script de Verificación**

- ✅ `scripts/test_db_connection.py` - Para probar la conexión

## 🚀 Pasos para Desplegar

### **Paso 1: Verificar Variables de Entorno en Render**

Ve a tu servicio en Render → **Environment** y verifica:

```bash
DATABASE_URL=postgresql://...  # ✅ Debe estar configurada automáticamente desde nexus-ai-db
GOOGLE_API_KEY=tu_api_key      # ⚠️ Configura manualmente
SECRET_KEY=auto_generado       # ✅ Auto-generado por Render
ENCRYPTION_KEY=tu_fernet_key   # ⚠️ Configura manualmente
```

### **Paso 2: Generar ENCRYPTION_KEY (si no lo tienes)**

```bash
python scripts/generar_claves.py
```

Copia el valor de `ENCRYPTION_KEY` y agrégalo en Render.

### **Paso 3: Hacer Deploy**

```bash
git add .
git commit -m "Fix: Soporte PostgreSQL en producción"
git push origin main
```

Render detectará el push y hará el deploy automáticamente.

### **Paso 4: Verificar en Render**

1. Ve a **Logs** en tu servicio
2. Busca el mensaje: `"Conectado a PostgreSQL"`
3. Verifica que no haya errores de conexión

### **Paso 5: Crear Usuario Admin**

Una vez desplegado, ejecuta desde el **Shell** de Render:

```bash
python scripts/init_auth.py
```

Esto creará:
- Usuario admin por defecto
- Tablas necesarias en PostgreSQL

## 🧪 Probar Localmente (Opcional)

### Con SQLite (desarrollo):

```bash
# .env
DATABASE_URL=sqlite:///nexus_ai.db
```

```bash
python scripts/test_db_connection.py
```

### Con PostgreSQL (local):

```bash
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/nexus_ai
```

```bash
python scripts/test_db_connection.py
```

## 📊 Verificar que Funciona

1. **Login** en la aplicación
2. **Crea una historia de usuario**
3. **Espera 15 minutos** (Render se duerme en plan free)
4. **Vuelve a entrar**
5. ✅ **Los datos deben persistir**

## 🔍 Troubleshooting

### Error: "No module named 'psycopg2'"

**Solución**: Verifica que `requirements.txt` tenga:

```txt
psycopg2-binary>=2.9.9
```

### Error: "Connection refused"

**Solución**: Verifica que `DATABASE_URL` esté configurada correctamente en Render.

### Error: "SSL required"

**Solución**: PostgreSQL en Render requiere SSL. SQLAlchemy lo maneja automáticamente.

### Los datos aún se borran

**Solución**: Verifica en los logs que diga `"Conectado a PostgreSQL"` y no `"Conectado a SQLite"`.

## 📝 Cambios Técnicos

### Antes:

```python
# Solo SQLite
import sqlite3
conn = sqlite3.connect('nexus_ai.db')
```

### Después:

```python
# SQLite o PostgreSQL automático
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)  # Detecta automáticamente
```

### Compatibilidad:

- ✅ Los repositorios existentes funcionan sin cambios
- ✅ Las consultas SQL se adaptan automáticamente
- ✅ Los placeholders `?` se convierten a `%s` en PostgreSQL
- ✅ Los tipos de datos se ajustan (TEXT → TIMESTAMP en fechas)

## 🎯 Resultado Esperado

- ✅ Datos persisten después de reiniciar Render
- ✅ Usuarios, historias, configuraciones se mantienen
- ✅ No más pérdida de datos al dormir el servicio

---

**Última actualización**: 2025-12-11  
**Versión**: 1.0

