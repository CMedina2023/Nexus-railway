# 🚀 DESPLIEGUE RÁPIDO - NEXUS AI EN RENDER

> **Guía rápida de referencia para desplegar Nexus AI en Render**

---

## 📚 DOCUMENTACIÓN COMPLETA

Para una guía paso a paso detallada (especialmente si es tu primera vez), consulta:

📖 **[GUIA_DESPLIEGUE_RENDER.md](GUIA_DESPLIEGUE_RENDER.md)** - Guía completa con explicaciones

✅ **[CHECKLIST_DESPLIEGUE.md](CHECKLIST_DESPLIEGUE.md)** - Checklist interactivo

🔐 **[GENERAR_CLAVES.md](GENERAR_CLAVES.md)** - Cómo generar claves secretas

---

## ⚡ INICIO RÁPIDO (5 PASOS)

### 1️⃣ Preparar Repositorio GitHub

```bash
# Subir código a GitHub
git add .
git commit -m "Preparar para despliegue"
git push origin main
```

### 2️⃣ Generar Claves Secretas

```bash
# Ejecutar script
python scripts/generar_claves.py
```

Guarda las claves generadas (las necesitarás en el paso 4).

### 3️⃣ Crear Base de Datos en Render

1. Ve a [render.com](https://render.com) → **New +** → **PostgreSQL**
2. Configura:
   - Name: `nexus-ai-db`
   - Plan: **Free**
3. Copia la **Internal Database URL**

### 4️⃣ Crear Web Service en Render

1. **New +** → **Web Service**
2. Conecta tu repositorio GitHub
3. Configura:
   - Name: `nexus-ai`
   - Build Command: `chmod +x build.sh && ./build.sh`
   - Start Command: `gunicorn -w 4 -b 0.0.0.0:$PORT run:app`
   - Plan: **Free**

4. **Agregar Variables de Entorno**:

```env
DATABASE_URL=<URL de PostgreSQL>
GOOGLE_API_KEY=<Tu API Key de Google>
SECRET_KEY=<Clave generada en paso 2>
ENCRYPTION_KEY=<Clave generada en paso 2>
FLASK_ENV=production
SESSION_COOKIE_SECURE=True
```

5. Click en **"Create Web Service"**

### 5️⃣ Crear Usuario Admin

Cuando el despliegue termine (5-10 min):

1. Ve a tu Web Service → **Shell**
2. Ejecuta:

```bash
python scripts/init_auth.py
```

3. Sigue las instrucciones para crear tu usuario admin

---

## 🔑 VARIABLES DE ENTORNO REQUERIDAS

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | URL de PostgreSQL | `postgresql://user:pass@host/db` |
| `GOOGLE_API_KEY` | API Key de Gemini | `AIzaSy...` |
| `SECRET_KEY` | Clave para sesiones | (64 caracteres hex) |
| `ENCRYPTION_KEY` | Clave para tokens | (44 caracteres base64) |
| `FLASK_ENV` | Entorno | `production` |
| `SESSION_COOKIE_SECURE` | Cookies seguras | `True` |

**Opcional (Jira)**:
- `JIRA_BASE_URL`
- `JIRA_EMAIL`
- `JIRA_API_TOKEN`

---

## 📁 ARCHIVOS DE CONFIGURACIÓN

Estos archivos ya están creados en el proyecto:

- ✅ `Procfile` - Comando de inicio
- ✅ `build.sh` - Script de build
- ✅ `render.yaml` - Configuración de Render
- ✅ `requirements.txt` - Dependencias Python
- ✅ `.gitignore` - Archivos a ignorar

**No necesitas modificarlos**, están listos para usar.

---

## 🔍 VERIFICAR DESPLIEGUE

### ✅ Señales de Éxito

1. **Build completado**: Status "Live" en verde
2. **Aplicación accesible**: URL funciona
3. **Login visible**: Página de login carga
4. **HTTPS activo**: Candado verde en navegador

### ❌ Problemas Comunes

| Problema | Solución |
|----------|----------|
| "Application failed to start" | Revisar logs, verificar variables de entorno |
| "502 Bad Gateway" | Verificar Start Command usa `$PORT` |
| "Database connection failed" | Verificar DATABASE_URL (usar Internal URL) |
| "Playwright not found" | Re-desplegar, verificar build.sh |

**Ver logs**: Web Service → **Logs** (en tiempo real)

---

## 🛠️ COMANDOS ÚTILES

### Generar Claves Secretas

```bash
python scripts/generar_claves.py
```

### Crear Usuario Admin

```bash
python scripts/init_auth.py
```

### Hacer Admin a Usuario Existente

```bash
python scripts/make_admin.py
```

### Ver Base de Datos

```bash
python scripts/view_db.py
```

---

## 🔄 ACTUALIZAR APLICACIÓN

Render se actualiza automáticamente cuando haces push a GitHub:

```bash
# Hacer cambios en el código
git add .
git commit -m "Descripción de cambios"
git push origin main
```

Render detectará el cambio y re-desplegará automáticamente (2-5 min).

---

## 📊 MONITOREO

### Ver Logs en Tiempo Real

1. Ve a tu Web Service en Render
2. Click en **"Logs"** (menú izquierdo)
3. Verás logs en tiempo real

### Ver Métricas

1. Click en **"Metrics"**
2. Verás:
   - CPU usage
   - Memory usage
   - Response times
   - Requests per second

---

## 💾 BACKUP DE BASE DE DATOS

**IMPORTANTE**: El plan gratuito NO incluye backups automáticos.

### Hacer Backup Manual

```bash
# Obtener External Database URL de Render
# Luego ejecutar:
pg_dump "postgresql://..." > backup_$(date +%Y%m%d).sql
```

**Recomendación**: Hacer backups semanales.

---

## 💰 PLAN GRATUITO - LIMITACIONES

### Web Service (Free)
- ✅ 750 horas/mes (suficiente para 1 app 24/7)
- ⚠️ Se "duerme" después de 15 min sin uso
- ⚠️ Tarda 30-60s en "despertar"

### PostgreSQL (Free)
- ✅ 90 días gratis
- ✅ 1 GB almacenamiento
- ⚠️ Sin backups automáticos
- ⚠️ Expira después de 90 días

### Soluciones

**Para evitar que se duerma**:
- Usar [UptimeRobot](https://uptimerobot.com/) (gratis)
- Hace ping cada 5 minutos

**Para base de datos**:
- Hacer backups manuales
- Upgrade a plan Starter ($7/mes) para sin expiración

---

## 🆙 UPGRADE A PLAN PAGO

### ¿Cuándo considerar upgrade?

Considera actualizar si:
- ✅ Tienes usuarios reales
- ✅ No quieres el delay de 30-60s
- ✅ Necesitas backups automáticos
- ✅ Necesitas más de 90 días de DB

### Planes Recomendados

**Web Service Starter** ($7/mes):
- Siempre activo (no se duerme)
- 512 MB RAM
- Respuestas instantáneas

**PostgreSQL Starter** ($7/mes):
- Sin expiración
- Backups diarios automáticos
- 1 GB almacenamiento

**Total**: $14/mes para app + DB en producción seria

---

## 🔐 SEGURIDAD

### ✅ Buenas Prácticas

- ✅ Usa variables de entorno para secretos
- ✅ NO subas `.env` a GitHub
- ✅ Genera claves únicas para producción
- ✅ Usa HTTPS (Render lo provee gratis)
- ✅ Habilita `SESSION_COOKIE_SECURE=True`

### ⚠️ NUNCA

- ❌ Hardcodear API keys en el código
- ❌ Subir archivos `.db` a GitHub
- ❌ Compartir claves por email sin encriptar
- ❌ Usar claves de desarrollo en producción

---

## 📞 SOPORTE

### Documentación
- 📖 [Guía Completa](GUIA_DESPLIEGUE_RENDER.md)
- ✅ [Checklist](CHECKLIST_DESPLIEGUE.md)
- 🔐 [Generar Claves](GENERAR_CLAVES.md)

### Render
- 📚 [Render Docs](https://render.com/docs)
- 💬 [Community Forum](https://community.render.com/)
- 📧 Email: support@render.com
- 🔍 [Status Page](https://status.render.com/)

### Proyecto
- 📁 Ver `docs/README.md` para documentación técnica
- 🧪 Ver `tests/README.md` para testing

---

## 🎯 PRÓXIMOS PASOS

Después de desplegar:

1. **Configurar UptimeRobot** - Mantener app activa
2. **Configurar backups** - Proteger datos
3. **Configurar dominio** - URL personalizada (opcional)
4. **Configurar Redis** - Mejores sesiones (opcional)
5. **Configurar Sentry** - Tracking de errores (opcional)

---

## 🎉 ¡LISTO!

Tu aplicación Nexus AI está ahora en producción.

**URL**: `https://tu-app.onrender.com`

Para cualquier duda, consulta la [Guía Completa](GUIA_DESPLIEGUE_RENDER.md).

---

*Última actualización: Diciembre 2025*  
*Versión: 1.0*

