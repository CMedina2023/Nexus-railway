# 🚂 Guía de Deploy en Railway - Nexus AI

Esta guía te ayudará a deployar tu aplicación **Nexus AI** en Railway con PostgreSQL incluida.

---

## 📋 Índice

1. [Prerrequisitos](#prerrequisitos)
2. [Preparación del Proyecto](#preparación-del-proyecto)
3. [Creación del Proyecto en Railway](#creación-del-proyecto-en-railway)
4. [Configuración de la Base de Datos](#configuración-de-la-base-de-datos)
5. [Configuración de Variables de Entorno](#configuración-de-variables-de-entorno)
6. [Deploy de la Aplicación](#deploy-de-la-aplicación)
7. [Verificación y Troubleshooting](#verificación-y-troubleshooting)
8. [Comandos Útiles](#comandos-útiles)

---

## 1️⃣ Prerrequisitos

- ✅ Cuenta en [Railway.app](https://railway.app)
- ✅ Código del proyecto en GitHub
- ✅ Google API Key para Gemini
- ✅ Git instalado localmente

---

## 2️⃣ Preparación del Proyecto

### 2.1 Verificar archivos de configuración

Asegúrate de que tu proyecto tenga estos archivos (ya están creados):

```
.
├── railway.json          # ✅ Configuración de Railway
├── nixpacks.toml         # ✅ Configuración de build
├── Procfile              # ✅ Comando de inicio
├── requirements.txt      # ✅ Dependencias Python
├── build.sh              # ✅ Script de build
└── run.py                # ✅ Punto de entrada
```

### 2.2 Actualizar el Procfile

El `Procfile` debe usar `${PORT}` en lugar de `$PORT`:

```
web: gunicorn -w 2 -k eventlet --timeout 300 --graceful-timeout 30 -b 0.0.0.0:${PORT} run:app
```

### 2.3 Commit y push de cambios

```bash
git add .
git commit -m "Configure for Railway deployment"
git push origin main
```

---

## 3️⃣ Creación del Proyecto en Railway

### 3.1 Crear nuevo proyecto

1. Ve a [Railway Dashboard](https://railway.app/dashboard)
2. Click en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Autoriza Railway para acceder a tu GitHub (si no lo has hecho)
5. Selecciona el repositorio `Nexus-railway`

### 3.2 Configuración inicial del proyecto

Railway detectará automáticamente que es un proyecto Python y:
- Usará `nixpacks.toml` para el build
- Instalará las dependencias de `requirements.txt`
- Ejecutará el comando definido en el Procfile

---

## 4️⃣ Configuración de la Base de Datos

### 4.1 Agregar PostgreSQL

1. En tu proyecto de Railway, click en **"+ New"**
2. Selecciona **"Database"**
3. Elige **"Add PostgreSQL"**
4. Railway creará automáticamente una instancia de PostgreSQL

### 4.2 Conectar la BD a tu aplicación

Railway automáticamente crea estas variables:
- `DATABASE_URL` - URL de conexión completa
- `PGHOST` - Host de la base de datos
- `PGPORT` - Puerto de PostgreSQL
- `PGUSER` - Usuario
- `PGPASSWORD` - Contraseña
- `PGDATABASE` - Nombre de la base de datos

✅ **Tu aplicación ya está configurada para usar `DATABASE_URL`**

### 4.3 Verificar la conexión

En el dashboard de PostgreSQL en Railway, puedes:
- 📊 Ver métricas de uso
- 🔌 Obtener strings de conexión
- 🗄️ Acceder via Query (interfaz web para ejecutar SQL)

---

## 5️⃣ Configuración de Variables de Entorno

### 5.1 Variables requeridas

En tu servicio web de Railway, ve a **"Variables"** y agrega:

#### 🔐 **Variables secretas (CRÍTICAS)**

```bash
# Google Gemini API
GOOGLE_API_KEY=tu_google_api_key_aqui

# Flask Security
SECRET_KEY=genera_una_clave_segura_de_32_caracteres_minimo

# Encriptación de tokens
ENCRYPTION_KEY=genera_una_clave_fernet_base64
```

#### ⚙️ **Variables de configuración opcionales**

```bash
# Flask
FLASK_ENV=production

# Seguridad
SESSION_COOKIE_SECURE=True

# Playwright (para PDFs)
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Gemini
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.2
GEMINI_TIMEOUT_BASE=180

# Jira (opcional, si lo usas)
# JIRA_BASE_URL=https://tu-empresa.atlassian.net
# JIRA_EMAIL=tu-email@empresa.com
# JIRA_API_TOKEN=tu_jira_token
```

### 5.2 Generar SECRET_KEY y ENCRYPTION_KEY

#### Opción A: Usando Python (recomendado)

```bash
# SECRET_KEY (32+ caracteres random)
python -c "import secrets; print(secrets.token_hex(32))"

# ENCRYPTION_KEY (Fernet key)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### Opción B: Usando los scripts del proyecto

```bash
# Si tienes el proyecto clonado localmente
cd scripts
python generar_claves.py
```

### 5.3 Obtener Google API Key

1. Ve a [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click en **"Create API Key"**
3. Copia la clave y pégala en `GOOGLE_API_KEY`

### 5.4 DATABASE_URL (Automática)

Railway ya configuró esta variable automáticamente cuando agregaste PostgreSQL. 

**Formato:**
```
postgresql://user:password@host:port/database
```

✅ **No necesitas hacer nada aquí**

---

## 6️⃣ Deploy de la Aplicación

### 6.1 Trigger del deploy

Railway hace deploy automático cuando:
- ✅ Haces push a tu rama principal (main/master)
- ✅ Cambias variables de entorno
- ✅ Click manual en **"Deploy"**

### 6.2 Proceso de build

El proceso sigue estos pasos:

1. **Clone** - Railway clona tu repositorio
2. **Setup** - Instala Python 3.11 y dependencias del sistema
3. **Install** - Ejecuta `pip install -r requirements.txt`
4. **Build** - Ejecuta `build.sh` (instala Playwright y crea BD)
5. **Start** - Ejecuta Gunicorn con tu aplicación

### 6.3 Monitorear el deploy

1. Ve a la pestaña **"Deployments"** de tu servicio
2. Click en el deployment activo
3. Verás los logs en tiempo real
4. Busca mensajes como:
   ```
   ✓ Build completed
   ✓ Starting webserver
   [INFO] Listening at: http://0.0.0.0:XXXX
   ```

### 6.4 Obtener la URL de tu app

1. En el dashboard del servicio, ve a **"Settings"**
2. Sección **"Networking"**
3. Click en **"Generate Domain"**
4. Railway te dará una URL como: `https://tu-proyecto.up.railway.app`

---

## 7️⃣ Verificación y Troubleshooting

### 7.1 Verificar que la app esté funcionando

Visita: `https://tu-proyecto.up.railway.app`

Deberías ver la página de login de Nexus AI.

### 7.2 Inicializar usuario admin

Si necesitas crear un usuario admin, conecta a Railway CLI:

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Conectar al proyecto
railway link

# Ejecutar comando en el servicio
railway run python scripts/make_admin.py
```

O usa el Railway Shell desde el dashboard:
1. Ve a tu servicio web
2. Click en **"Settings"**
3. Scroll hasta **"Service"**
4. Click en **"Open Shell"**
5. Ejecuta: `python scripts/make_admin.py`

### 7.3 Problemas comunes

#### ❌ Error: "Application failed to respond"

**Causa:** La app no se está iniciando correctamente.

**Solución:**
1. Revisa los logs en Railway
2. Verifica que todas las variables de entorno estén configuradas
3. Asegúrate de que `DATABASE_URL` esté presente

#### ❌ Error: "Module not found"

**Causa:** Dependencia faltante en `requirements.txt`

**Solución:**
```bash
# Localmente
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

#### ❌ Error: "Database connection failed"

**Causa:** PostgreSQL no está conectado o las credenciales son incorrectas.

**Solución:**
1. Verifica que el servicio PostgreSQL esté activo en Railway
2. Confirma que `DATABASE_URL` esté en las variables de entorno
3. En el dashboard de PostgreSQL, verifica el estado

#### ❌ Error: "Port already in use" o "$PORT is not valid"

**Causa:** Configuración incorrecta del puerto.

**Solución:** ✅ Ya está solucionado en `app/core/config.py`:
```python
FLASK_PORT = int(os.getenv('PORT', os.getenv('FLASK_PORT', '5000')))
```

#### ❌ Error: "Playwright installation failed"

**Causa:** Falta de dependencias del sistema.

**Solución:**
1. Verifica que `nixpacks.toml` incluya:
   ```toml
   nixPkgs = ["python311", "playwright-driver", "chromium"]
   ```
2. Verifica que `build.sh` instale Playwright correctamente

### 7.4 Ver logs en tiempo real

```bash
# Con Railway CLI
railway logs

# O en el dashboard
# Deployments > [Deployment activo] > Logs
```

---

## 8️⃣ Comandos Útiles

### 8.1 Railway CLI

```bash
# Login
railway login

# Vincular proyecto
railway link

# Ver variables de entorno
railway variables

# Agregar variable
railway variables set KEY=value

# Ver logs
railway logs

# Abrir shell
railway shell

# Deploy manual
railway up

# Ver estado
railway status
```

### 8.2 Gestión de la BD

```bash
# Conectar a PostgreSQL (Railway CLI)
railway connect postgres

# O desde el dashboard
# PostgreSQL Service > Data > Query
```

### 8.3 Backup de la BD

Railway hace backups automáticos, pero puedes hacer uno manual:

```bash
# Usando Railway CLI + pg_dump
railway run pg_dump $DATABASE_URL > backup.sql
```

### 8.4 Restaurar backup

```bash
# Usando psql
railway run psql $DATABASE_URL < backup.sql
```

---

## 🔄 Workflow de desarrollo recomendado

### Desarrollo local → Producción

1. **Local:** Trabaja en tu rama de desarrollo
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```

2. **Test:** Prueba localmente
   ```bash
   python run.py
   ```

3. **Commit:** Guarda cambios
   ```bash
   git add .
   git commit -m "Add nueva funcionalidad"
   ```

4. **Merge:** Fusiona a main
   ```bash
   git checkout main
   git merge feature/nueva-funcionalidad
   ```

5. **Deploy:** Push triggerea deploy automático
   ```bash
   git push origin main
   ```

6. **Verify:** Verifica en Railway dashboard que el deploy fue exitoso

---

## 📊 Monitoreo y métricas

En Railway puedes ver:
- **CPU Usage** - Uso de CPU
- **Memory Usage** - Uso de RAM
- **Network** - Tráfico de red
- **Deployments** - Historial de deploys
- **Logs** - Logs de la aplicación

### Alertas

Configura alertas en:
1. Project Settings > Notifications
2. Puedes recibir alertas por:
   - Discord
   - Email
   - Slack
   - Webhook

---

## 💰 Pricing y límites

### Plan gratuito (Hobby)
- ✅ $5 USD de crédito gratis al mes
- ✅ 500 horas de ejecución
- ✅ 512MB RAM
- ✅ 1GB de disco
- ✅ Base de datos incluida

### Si necesitas más recursos
- Upgrade a **Pro Plan** ($20/mes)
- O configura alertas de uso

---

## 🔒 Seguridad

### Checklist de seguridad

- ✅ `SESSION_COOKIE_SECURE=True` (HTTPS)
- ✅ `SECRET_KEY` generado de forma segura (32+ caracteres)
- ✅ `ENCRYPTION_KEY` Fernet key válida
- ✅ Variables sensibles en Railway (no en código)
- ✅ `.env` en `.gitignore`
- ✅ PostgreSQL con credenciales generadas por Railway
- ✅ HTTPS habilitado por defecto en Railway

### Rotar secretos

Si necesitas rotar tus secretos:
1. Genera nuevos valores (SECRET_KEY, ENCRYPTION_KEY)
2. Actualiza en Railway Variables
3. Railway redeploya automáticamente

---

## 📚 Recursos adicionales

- 📖 [Railway Docs](https://docs.railway.app)
- 🎓 [Railway Templates](https://railway.app/templates)
- 💬 [Railway Discord](https://discord.gg/railway)
- 🐛 [Railway GitHub](https://github.com/railwayapp/nixpacks)

---

## ✅ Checklist final de deploy

Antes de considerar el deploy completo, verifica:

- [ ] PostgreSQL está activo en Railway
- [ ] Todas las variables de entorno están configuradas
- [ ] `GOOGLE_API_KEY` es válida
- [ ] `SECRET_KEY` tiene 32+ caracteres
- [ ] `ENCRYPTION_KEY` es una Fernet key válida
- [ ] `DATABASE_URL` está presente (automática)
- [ ] El deploy terminó exitosamente (sin errores)
- [ ] La URL pública funciona y muestra la app
- [ ] Se puede hacer login
- [ ] Los PDFs se generan correctamente
- [ ] La integración con Gemini funciona
- [ ] (Opcional) Jira está conectado

---

## 🎉 ¡Deploy exitoso!

Si llegaste hasta aquí y todos los checks están ✅, ¡tu aplicación Nexus AI está corriendo en Railway!

**URL de tu app:** `https://tu-proyecto.up.railway.app`

### Próximos pasos

1. Configura un dominio personalizado (opcional)
2. Configura alertas de monitoreo
3. Haz backups regulares de la BD
4. Monitorea el uso de recursos

---

**Notas finales:**
- Railway hace deploy automático en cada push a `main`
- Los logs están disponibles en tiempo real
- La BD PostgreSQL tiene backups automáticos
- Puedes escalar verticalmente si necesitas más recursos

¿Preguntas? Revisa la sección de [Troubleshooting](#verificación-y-troubleshooting) o consulta los [recursos adicionales](#recursos-adicionales).
