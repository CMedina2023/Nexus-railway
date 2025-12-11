# 🔧 Solución al Error de Deploy en Railway

## 🚨 Error: "There was an error deploying from source"

Este error genérico puede tener varias causas. Sigue estos pasos en orden:

---

## ✅ SOLUCIÓN 1: Verificar Variables de Entorno (MÁS COMÚN)

### Paso 1: Ve a tu servicio web en Railway
1. Click en tu servicio **web** (no PostgreSQL)
2. Ve a la pestaña **"Variables"**

### Paso 2: Verifica que tengas ESTAS 3 variables mínimas:

```bash
DATABASE_URL=postgresql://... (generada automáticamente por Railway)
GOOGLE_API_KEY=tu_api_key_aqui
SECRET_KEY=tu_secret_key_generada
```

**⚠️ Si falta alguna, agrégala ahora:**

#### Para generar SECRET_KEY localmente:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

#### Para generar ENCRYPTION_KEY (opcional pero recomendada):
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Paso 3: Redeploy después de agregar variables
1. Ve a "Deployments"
2. Click en los 3 puntos del último deployment
3. Click "Redeploy"

---

## ✅ SOLUCIÓN 2: Verificar PostgreSQL está conectado

### Paso 1: Verifica que PostgreSQL existe
En tu proyecto Railway, debes ver 2 servicios:
- `web` (tu aplicación)
- `postgres` (tu base de datos)

### Si NO ves PostgreSQL:
1. Click en "+ New"
2. Selecciona "Database"
3. Click "Add PostgreSQL"
4. Espera que se active

### Paso 2: Verifica la variable DATABASE_URL
1. En tu servicio **web**, ve a "Variables"
2. Busca `DATABASE_URL`
3. **Debe comenzar con:** `postgresql://`

### Si no existe DATABASE_URL:
1. Ve al servicio PostgreSQL
2. Click en "Variables"
3. Copia el valor de `DATABASE_URL`
4. Ve a tu servicio web → Variables
5. Agrega: `DATABASE_URL=<valor_copiado>`

---

## ✅ SOLUCIÓN 3: Build Simple (Sin Playwright)

Si el error persiste, puede ser por Playwright. Vamos a probarlo sin Playwright:

### Paso 1: Usa el build simple
```bash
# En tu terminal local
cp build.simple.sh build.sh
git add build.sh
git commit -m "Use simple build without Playwright"
git push origin main
```

### Paso 2: El deploy debería funcionar ahora

**Nota:** Sin Playwright, la generación de PDFs no funcionará, pero la app arrancará.

---

## ✅ SOLUCIÓN 4: Verificar Logs Específicos

### Paso 1: Ver los logs del build
1. En Railway, ve a "Deployments"
2. Click en el deployment que falló
3. Lee todo el output

### Busca estos errores comunes:

#### Error: "Module not found"
**Causa:** Falta una dependencia en `requirements.txt`

**Solución:**
```bash
# Local
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements.txt"
git push
```

#### Error: "Permission denied"
**Causa:** build.sh no tiene permisos de ejecución

**Solución:** Ya está corregido en el código actualizado

#### Error: "Database connection failed"
**Causa:** DATABASE_URL no está configurada

**Solución:** Ver SOLUCIÓN 2

#### Error: "Invalid API key"
**Causa:** GOOGLE_API_KEY incorrecta o falta

**Solución:**
1. Ve a https://aistudio.google.com/app/apikey
2. Genera una nueva API key
3. Agrégala en Railway Variables

---

## ✅ SOLUCIÓN 5: Configuración Mínima Garantizada

Si nada funciona, usa esta configuración mínima garantizada:

### 1. Actualiza `nixpacks.toml`:
```toml
[phases.setup]
nixPkgs = ["python311"]

[phases.install]
cmds = [
  "pip install --upgrade pip",
  "pip install -r requirements.txt"
]

[phases.build]
cmds = ["chmod +x build.sh", "./build.sh"]

[start]
cmd = "gunicorn -w 2 -k eventlet --timeout 300 --graceful-timeout 30 -b 0.0.0.0:${PORT} run:app"
```

### 2. Actualiza `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn -w 2 -k eventlet --timeout 300 --graceful-timeout 30 -b 0.0.0.0:${PORT} run:app",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 3. Usa `build.simple.sh`:
Renombra o reemplaza:
```bash
cp build.simple.sh build.sh
```

### 4. Commit y push:
```bash
git add .
git commit -m "Use minimal Railway configuration"
git push origin main
```

---

## ✅ SOLUCIÓN 6: Verificar requirements.txt

Asegúrate de que `requirements.txt` tenga todas las dependencias:

```bash
# En tu terminal local
pip install -r requirements.txt
# Si falla, hay un error en requirements.txt

# Regenerar desde cero
pip freeze > requirements.txt.new
# Compara y actualiza
```

---

## 📋 Checklist de Verificación

Marca cada uno:

- [ ] PostgreSQL está agregado al proyecto
- [ ] `DATABASE_URL` existe en Variables del servicio web
- [ ] `GOOGLE_API_KEY` está configurada en Variables
- [ ] `SECRET_KEY` está configurada en Variables
- [ ] Los archivos `railway.json` y `nixpacks.toml` están actualizados
- [ ] `build.sh` tiene permisos (chmod +x)
- [ ] `requirements.txt` es válido
- [ ] He hecho commit y push de todos los cambios

---

## 🆘 Si NADA funciona

### Opción 1: Deploy sin Postgres (SQLite temporal)

1. En Railway Variables, **comenta** o elimina `DATABASE_URL`
2. La app usará SQLite local (temporal)
3. Esto te permite verificar si el problema es PostgreSQL

### Opción 2: Logs detallados

Comparte los logs completos del deploy:
1. Railway → Deployments → [Failed deployment]
2. Copia TODO el output
3. Busca líneas que digan "ERROR" o "FAILED"

### Opción 3: Railway CLI

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Vincular proyecto
railway link

# Ver logs en tiempo real
railway logs

# Deploy manual
railway up
```

---

## 🎯 Lo que YA se corrigió

✅ Error de puerto `$PORT` → Ahora usa `${PORT}`
✅ `config.py` lee `PORT` correctamente
✅ `nixpacks.toml` simplificado
✅ `build.sh` mejorado con mejor manejo de errores
✅ Versión alternativa `build.simple.sh` sin Playwright

---

## 📞 Siguiente paso

1. **Primero:** Verifica SOLUCIÓN 1 (Variables de Entorno)
2. **Segundo:** Verifica SOLUCIÓN 2 (PostgreSQL)
3. **Tercero:** Prueba SOLUCIÓN 3 (Build simple)
4. **Si persiste:** Comparte los logs completos del deploy

---

**Los cambios ya están listos en tu código local. Solo necesitas:**
```bash
git add .
git commit -m "Fix Railway deployment configuration"
git push origin main
```

¡Esto debería resolver el error! 🚀
