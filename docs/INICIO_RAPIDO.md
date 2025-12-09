# ⚡ INICIO RÁPIDO - DESPLIEGUE EN RENDER

> **Guía ultra-rápida para desplegar Nexus AI en Render en 15 minutos**

---

## ✅ TU PROYECTO ESTÁ LISTO

**Todos los archivos de configuración ya están creados.**  
Solo necesitas seguir estos pasos.

---

## 🚀 5 PASOS PARA DESPLEGAR

### 1️⃣ GENERAR CLAVES (2 minutos)

```bash
python scripts/generar_claves.py
```

**Guarda las claves** que aparecen (las necesitarás en el paso 4).

---

### 2️⃣ SUBIR A GITHUB (3 minutos)

```bash
git add .
git commit -m "Preparar para despliegue en Render"
git push origin main
```

Si no tienes repositorio en GitHub:
1. Ve a [github.com](https://github.com) → New repository
2. Crea el repositorio
3. Ejecuta los comandos que GitHub te muestra

---

### 3️⃣ CREAR BASE DE DATOS EN RENDER (3 minutos)

1. Ve a [render.com](https://render.com) → **Sign Up** (con GitHub)
2. Click en **"New +"** → **"PostgreSQL"**
3. Configura:
   - Name: `nexus-ai-db`
   - Plan: **Free**
4. Click en **"Create Database"**
5. **Copia la "Internal Database URL"** (la necesitarás en el paso 4)

---

### 4️⃣ CREAR WEB SERVICE EN RENDER (5 minutos)

1. Click en **"New +"** → **"Web Service"**
2. Conecta tu repositorio de GitHub
3. Configura:
   - Name: `nexus-ai`
   - Build Command: `chmod +x build.sh && ./build.sh`
   - Start Command: `gunicorn -w 4 -b 0.0.0.0:$PORT run:app`
   - Plan: **Free**

4. **Agregar Variables de Entorno** (scroll hacia abajo):

   Click en **"Add Environment Variable"** para cada una:

   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | (URL que copiaste en paso 3) |
   | `GOOGLE_API_KEY` | (Tu API Key de Google) |
   | `SECRET_KEY` | (Primera clave del paso 1) |
   | `ENCRYPTION_KEY` | (Segunda clave del paso 1) |
   | `FLASK_ENV` | `production` |
   | `SESSION_COOKIE_SECURE` | `True` |

5. Click en **"Create Web Service"**

---

### 5️⃣ CREAR USUARIO ADMIN (2 minutos)

Espera a que el build termine (5-10 min). Cuando veas **"Live"** en verde:

1. Ve a tu Web Service → **"Shell"**
2. Click en **"Launch Shell"**
3. Ejecuta:

```bash
python scripts/init_auth.py
```

4. Sigue las instrucciones para crear tu usuario admin

---

## ✅ ¡LISTO!

Tu aplicación está en: `https://tu-app.onrender.com`

**Prueba**:
1. Accede a la URL
2. Inicia sesión con tu usuario admin
3. Sube un documento y genera una historia

---

## 🆘 ¿PROBLEMAS?

### Error: "Application failed to start"
→ Ve a **Logs** en Render y busca el error en rojo  
→ Verifica que todas las variables de entorno estén configuradas

### Error: "502 Bad Gateway"
→ Verifica que el Start Command sea exactamente:  
`gunicorn -w 4 -b 0.0.0.0:$PORT run:app`

### Error: "Database connection failed"
→ Verifica que DATABASE_URL sea la **Internal** (no External)

### Más ayuda
→ Lee la guía completa: `GUIA_DESPLIEGUE_RENDER.md`

---

## 📚 DOCUMENTACIÓN COMPLETA

Si necesitas más detalles:

- **Principiantes**: `GUIA_DESPLIEGUE_RENDER.md` (paso a paso detallado)
- **Checklist**: `CHECKLIST_DESPLIEGUE.md` (lista de verificación)
- **Referencia**: `DEPLOY_README.md` (comandos y tablas)

---

## 🔑 ¿CÓMO OBTENER GOOGLE API KEY?

1. Ve a: https://makersuite.google.com/app/apikey
2. Inicia sesión con Google
3. Click en **"Create API Key"**
4. Copia la clave

---

## 💡 TIPS

### Mantener la App Activa (Plan Gratuito)

El plan gratuito "duerme" la app después de 15 min sin uso.

**Solución**: Usa [UptimeRobot](https://uptimerobot.com/) (gratis)
- Crea una cuenta
- Agrega tu URL de Render
- Configura ping cada 5 minutos

### Hacer Backups

El plan gratuito NO incluye backups automáticos.

**Solución**: Haz backups manuales semanales
1. Ve a tu PostgreSQL database en Render
2. Copia la "External Database URL"
3. Ejecuta: `pg_dump "URL" > backup.sql`

---

## 🎯 CHECKLIST RÁPIDO

Antes de empezar:

- [ ] Python instalado
- [ ] Git instalado
- [ ] Cuenta de GitHub
- [ ] Código en GitHub
- [ ] Google API Key obtenida

Durante el despliegue:

- [ ] Claves generadas
- [ ] Base de datos PostgreSQL creada
- [ ] Web Service creado
- [ ] Variables de entorno configuradas
- [ ] Build completado (status "Live")
- [ ] Usuario admin creado

Verificación:

- [ ] URL accesible
- [ ] Login funciona
- [ ] Generar historia funciona

---

## 📞 SOPORTE

- 📖 Guía completa: `GUIA_DESPLIEGUE_RENDER.md`
- ✅ Checklist: `CHECKLIST_DESPLIEGUE.md`
- 🔐 Generar claves: `GENERAR_CLAVES.md`
- 📚 Render Docs: https://render.com/docs

---

**¡Éxito con tu despliegue!** 🚀

*Tiempo total estimado: 15 minutos*

