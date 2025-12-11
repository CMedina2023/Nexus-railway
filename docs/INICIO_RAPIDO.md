# 🎯 INICIO RÁPIDO - Railway Deploy

## 📦 Paso 1: Preparar el código

```bash
# Asegúrate de estar en la rama correcta
git status

# Commit y push de todos los cambios
git add .
git commit -m "Configure for Railway deployment"
git push origin main
```

## 🔑 Paso 2: Generar claves secretas

Ejecuta este comando para generar SECRET_KEY:
```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
```

Ejecuta este comando para generar ENCRYPTION_KEY:
```bash
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

**💾 GUARDA ESTAS CLAVES**, las necesitarás en Railway.

## 🚂 Paso 3: Crear proyecto en Railway

1. Abre tu navegador en: https://railway.app/dashboard
2. Click en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Busca y selecciona **"Nexus-railway"**
5. Espera a que termine el primer deploy (probablemente fallará, ¡es normal!)

## 🗄️ Paso 4: Agregar PostgreSQL

1. En tu proyecto de Railway, click en **"+ New"**
2. Selecciona **"Database"**
3. Click en **"Add PostgreSQL"**
4. Espera unos segundos a que se active

## ⚙️ Paso 5: Configurar variables de entorno

1. Click en tu servicio **web** (no en PostgreSQL)
2. Ve a la pestaña **"Variables"**
3. Click en **"+ New Variable"**
4. Agrega estas 3 variables (usa las que generaste en Paso 2):

```
GOOGLE_API_KEY=tu_google_api_key_aqui
SECRET_KEY=tu_secret_key_generada
ENCRYPTION_KEY=tu_encryption_key_generada
```

5. Click en **"Add"** para cada una

### ¿Dónde conseguir GOOGLE_API_KEY?
- Ve a: https://aistudio.google.com/app/apikey
- Click "Create API Key"
- Copia la clave

### Opcional: Variables adicionales recomendadas

```
FLASK_ENV=production
SESSION_COOKIE_SECURE=True
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
```

## 🌐 Paso 6: Generar dominio público

1. En tu servicio web, ve a **"Settings"**
2. Scroll hasta **"Networking"**
3. Click en **"Generate Domain"**
4. Copia la URL (algo como: `https://nexus-railway-production.up.railway.app`)

## ✅ Paso 7: Redeploy y verificar

1. Ve a la pestaña **"Deployments"**
2. Si el último deploy falló, click en **"Deploy"** (menú de 3 puntos)
3. Selecciona **"Redeploy"**
4. Espera a que termine (mira los logs)
5. Busca este mensaje en los logs:
   ```
   [INFO] Listening at: http://0.0.0.0:XXXX
   ```
6. Abre la URL de tu app en el navegador
7. ✅ ¡Deberías ver la página de login de Nexus AI!

## 👤 Paso 8: Crear usuario admin

### Opción A: Desde Railway Dashboard

1. En tu servicio web, ve a **"Settings"**
2. Scroll hasta **"Service"**
3. Click en **"Open Shell"**
4. Ejecuta:
   ```bash
   python scripts/make_admin.py
   ```
5. Sigue las instrucciones en pantalla

### Opción B: Desde Railway CLI

```bash
# Instalar Railway CLI (solo una vez)
npm install -g @railway/cli

# Login
railway login

# Vincular al proyecto
railway link

# Ejecutar script
railway run python scripts/make_admin.py
```

## 🎉 ¡Listo!

Tu aplicación Nexus AI debería estar corriendo en Railway.

### URLs importantes:
- **Tu app:** https://tu-proyecto.up.railway.app
- **Railway Dashboard:** https://railway.app/project/[tu-proyecto]

### Verificar que todo funciona:
- [ ] La página de login carga
- [ ] Puedes hacer login con el usuario admin
- [ ] El dashboard muestra sin errores
- [ ] Puedes generar historias de usuario (test Gemini)
- [ ] Los PDFs se generan correctamente

## 🆘 ¿Problemas?

### El deploy falla
- Verifica los logs en Railway → Deployments
- Confirma que todas las variables de entorno están configuradas
- Asegúrate de que PostgreSQL está activo

### Error de conexión a base de datos
- Verifica que PostgreSQL esté en el mismo proyecto
- Confirma que `DATABASE_URL` aparece en las variables (automática)

### Error "$PORT is not valid"
- ✅ Ya está solucionado en tu código
- Si persiste, verifica que `app/core/config.py` tenga:
  ```python
  FLASK_PORT = int(os.getenv('PORT', os.getenv('FLASK_PORT', '5000')))
  ```

### La app no carga
- Verifica que el dominio esté generado
- Espera 1-2 minutos después del deploy
- Verifica los logs para ver errores

## 📚 Más información

Para detalles completos, consulta:
- **RAILWAY_DEPLOY.md** - Guía completa paso a paso
- **RAILWAY_CHECKLIST.md** - Checklist detallado
- **RAILWAY_RESUMEN.md** - Resumen de cambios

---

**¡Éxito con tu deploy!** 🚀

Si tienes dudas, revisa los logs en Railway o consulta la documentación completa.
