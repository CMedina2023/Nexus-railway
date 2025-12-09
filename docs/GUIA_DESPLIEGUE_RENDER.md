# 🚀 GUÍA COMPLETA DE DESPLIEGUE EN RENDER

> **Guía paso a paso para desplegar Nexus AI en Render (Web Service + Base de Datos PostgreSQL)**

**Fecha**: Diciembre 2025  
**Nivel**: Principiante (no se requiere experiencia previa)

---

## 📋 TABLA DE CONTENIDOS

1. [¿Qué es Render?](#qué-es-render)
2. [Requisitos Previos](#requisitos-previos)
3. [Preparación del Proyecto](#preparación-del-proyecto)
4. [Crear Cuenta en Render](#crear-cuenta-en-render)
5. [Desplegar Base de Datos PostgreSQL](#desplegar-base-de-datos-postgresql)
6. [Desplegar Aplicación Web](#desplegar-aplicación-web)
7. [Configurar Variables de Entorno](#configurar-variables-de-entorno)
8. [Verificar el Despliegue](#verificar-el-despliegue)
9. [Solución de Problemas](#solución-de-problemas)
10. [Mantenimiento y Actualizaciones](#mantenimiento-y-actualizaciones)

---

## 🤔 ¿Qué es Render?

**Render** es una plataforma en la nube que permite desplegar aplicaciones web de forma sencilla. Es similar a Heroku pero más moderna y con un plan gratuito generoso.

### ¿Por qué Render?
- ✅ **Fácil de usar** - No necesitas ser experto
- ✅ **Plan gratuito** - Incluye base de datos PostgreSQL
- ✅ **Despliegue automático** - Se actualiza solo cuando subes cambios a GitHub
- ✅ **SSL gratis** - Tu sitio tendrá HTTPS automáticamente
- ✅ **Base de datos incluida** - PostgreSQL gratis (90 días, luego expira pero puedes crear otra)

---

## ✅ REQUISITOS PREVIOS

### 1. Cuenta de GitHub
Tu proyecto **DEBE** estar en GitHub para desplegarse en Render.

**Si NO tienes el proyecto en GitHub:**

1. Ve a [github.com](https://github.com) y crea una cuenta (si no tienes)
2. Crea un nuevo repositorio:
   - Click en el botón **"+"** arriba a la derecha
   - Selecciona **"New repository"**
   - Nombre: `nexus-ai` (o el que prefieras)
   - Descripción: "Sistema de generación de historias de usuario con IA"
   - Selecciona **"Private"** (para que solo tú lo veas)
   - Click en **"Create repository"**

3. Sube tu proyecto a GitHub:
   ```bash
   # En la carpeta de tu proyecto (Agenteai2), ejecuta:
   git init
   git add .
   git commit -m "Preparar proyecto para despliegue en Render"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/nexus-ai.git
   git push -u origin main
   ```

   **Nota**: Reemplaza `TU_USUARIO` con tu nombre de usuario de GitHub.

### 2. API Keys Necesarias

Necesitarás tener a mano estas claves (las configuraremos después):

- ✅ **Google API Key** (Gemini AI) - **OBLIGATORIA**
- ✅ **Jira credentials** (si usas Jira) - Opcional
  - JIRA_BASE_URL
  - JIRA_EMAIL
  - JIRA_API_TOKEN

**¿Cómo obtener Google API Key?**
1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Inicia sesión con tu cuenta de Google
3. Click en **"Create API Key"**
4. Copia la clave (la necesitarás después)

---

## 🛠️ PREPARACIÓN DEL PROYECTO

### Paso 1: Verificar Archivos de Configuración

Tu proyecto ya tiene casi todo listo. Solo necesitamos crear algunos archivos adicionales.

Los archivos que crearemos:
- ✅ `Procfile` - Le dice a Render cómo iniciar tu aplicación
- ✅ `render.yaml` - Configuración automatizada de Render
- ✅ `build.sh` - Script para instalar dependencias y configurar la base de datos
- ✅ `.env.example` - Plantilla de variables de entorno

**No te preocupes, estos archivos ya están creados automáticamente en tu proyecto.**

### Paso 2: Actualizar requirements.txt

Ya tienes `requirements.txt`, pero necesitamos agregar algunas dependencias para producción:

```txt
# Servidor de producción
gunicorn>=21.2.0

# Base de datos PostgreSQL
psycopg2-binary>=2.9.9
```

### Paso 3: Crear archivo .gitignore (si no existe)

Asegúrate de que estos archivos NO se suban a GitHub:

```
# Variables de entorno
.env

# Base de datos local
*.db
nexus_ai.db

# Archivos temporales
temp_uploads/
sessions/
__pycache__/
*.pyc

# Backups
backups/
```

---

## 🌐 CREAR CUENTA EN RENDER

### Paso 1: Registrarse

1. Ve a [render.com](https://render.com)
2. Click en **"Get Started"** o **"Sign Up"**
3. **Recomendado**: Selecciona **"Sign up with GitHub"**
   - Esto facilita conectar tus repositorios
   - Autoriza a Render para acceder a tus repositorios
4. Completa tu perfil si es necesario

### Paso 2: Verificar Email

- Revisa tu correo electrónico
- Click en el enlace de verificación
- Ya estás listo para desplegar

---

## 🗄️ DESPLEGAR BASE DE DATOS POSTGRESQL

### Paso 1: Crear Base de Datos

1. En el dashboard de Render, click en **"New +"**
2. Selecciona **"PostgreSQL"**

### Paso 2: Configurar Base de Datos

Completa el formulario:

| Campo | Valor |
|-------|-------|
| **Name** | `nexus-ai-db` |
| **Database** | `nexus_ai` |
| **User** | `nexus_admin` (se crea automáticamente) |
| **Region** | Selecciona el más cercano (ej: `Oregon (US West)`) |
| **PostgreSQL Version** | `16` (la más reciente) |
| **Plan** | **Free** (90 días gratis) |

3. Click en **"Create Database"**

### Paso 3: Esperar a que se cree

- La base de datos tardará 1-2 minutos en crearse
- Verás un indicador de progreso
- Cuando esté lista, verás **"Available"** en verde

### Paso 4: Copiar URL de Conexión

**MUY IMPORTANTE**: Necesitarás esta URL para conectar tu aplicación.

1. En la página de tu base de datos, busca la sección **"Connections"**
2. Copia el valor de **"Internal Database URL"**
   - Se ve algo así: `postgresql://user:password@hostname/database`
3. **Guárdala en un lugar seguro** (la necesitarás en el siguiente paso)

**Ejemplo de URL**:
```
postgresql://nexus_admin:AbCd1234XyZ@dpg-abc123xyz-a.oregon-postgres.render.com/nexus_ai
```

---

## 🌍 DESPLEGAR APLICACIÓN WEB

### Paso 1: Crear Web Service

1. En el dashboard de Render, click en **"New +"**
2. Selecciona **"Web Service"**

### Paso 2: Conectar Repositorio de GitHub

1. Si es tu primera vez, click en **"Connect GitHub"**
2. Autoriza a Render para acceder a tus repositorios
3. Busca tu repositorio `nexus-ai` (o como lo hayas nombrado)
4. Click en **"Connect"**

### Paso 3: Configurar Web Service

Completa el formulario con estos valores:

| Campo | Valor |
|-------|-------|
| **Name** | `nexus-ai` (será parte de tu URL) |
| **Region** | **Mismo que la base de datos** (ej: Oregon) |
| **Branch** | `main` |
| **Root Directory** | (dejar vacío) |
| **Runtime** | `Python 3` |
| **Build Command** | `chmod +x build.sh && ./build.sh` |
| **Start Command** | `gunicorn -w 4 -b 0.0.0.0:$PORT run:app` |
| **Plan** | **Free** |

### Paso 4: NO hacer click en "Create Web Service" todavía

Primero necesitamos configurar las variables de entorno.

---

## 🔐 CONFIGURAR VARIABLES DE ENTORNO

### Paso 1: Agregar Variables de Entorno

Antes de crear el servicio, scroll hacia abajo hasta la sección **"Environment Variables"**.

Click en **"Add Environment Variable"** para cada una de estas:

#### Variables OBLIGATORIAS:

| Key | Value | Descripción |
|-----|-------|-------------|
| `DATABASE_URL` | `<URL que copiaste de PostgreSQL>` | Conexión a la base de datos |
| `GOOGLE_API_KEY` | `<Tu API Key de Google>` | Para Gemini AI |
| `SECRET_KEY` | `<Genera una clave aleatoria>` | Para sesiones (mínimo 32 caracteres) |
| `ENCRYPTION_KEY` | `<Genera una Fernet key>` | Para encriptar tokens |
| `FLASK_ENV` | `production` | Modo producción |
| `SESSION_COOKIE_SECURE` | `True` | Cookies seguras en HTTPS |

#### Variables OPCIONALES (si usas Jira):

| Key | Value |
|-----|-------|
| `JIRA_BASE_URL` | `https://tu-empresa.atlassian.net` |
| `JIRA_EMAIL` | `tu-email@empresa.com` |
| `JIRA_API_TOKEN` | `<Tu token de Jira>` |

### Paso 2: Generar Claves Secretas

**Para SECRET_KEY** (en tu computadora, ejecuta en Python):
```python
import secrets
print(secrets.token_hex(32))
```

**Para ENCRYPTION_KEY** (en tu computadora, ejecuta en Python):
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Copia los resultados y úsalos en las variables de entorno.

### Paso 3: Configuración Adicional (Opcional)

Si quieres personalizar más, puedes agregar:

| Key | Value | Descripción |
|-----|-------|-------------|
| `GEMINI_MODEL` | `gemini-2.5-flash` | Modelo de IA a usar |
| `MAX_UPLOAD_SIZE_MB` | `16` | Tamaño máximo de archivos |
| `FLASK_PORT` | `10000` | Puerto (Render usa $PORT automáticamente) |

### Paso 4: Crear el Web Service

Ahora sí, click en **"Create Web Service"** al final de la página.

---

## ✅ VERIFICAR EL DESPLIEGUE

### Paso 1: Esperar el Build

1. Render comenzará a construir tu aplicación
2. Verás logs en tiempo real:
   - Instalando dependencias...
   - Ejecutando build.sh...
   - Instalando Playwright...
   - Creando tablas de base de datos...
   - Iniciando aplicación...

**Esto puede tardar 5-10 minutos la primera vez.**

### Paso 2: Verificar que está "Live"

Cuando veas:
- ✅ **"Live"** en verde en la parte superior
- ✅ Mensaje: "Your service is live 🎉"

Tu aplicación está funcionando.

### Paso 3: Acceder a tu Aplicación

1. En la parte superior, verás tu URL:
   ```
   https://nexus-ai.onrender.com
   ```
   (El nombre depende de cómo llamaste tu servicio)

2. Click en la URL o cópiala en tu navegador

3. Deberías ver la página de login de Nexus AI

### Paso 4: Crear Usuario Administrador

**IMPORTANTE**: La primera vez, necesitas crear un usuario admin.

1. Accede a la consola de Render:
   - En tu Web Service, ve a la pestaña **"Shell"**
   - Click en **"Launch Shell"**

2. Ejecuta el script de inicialización:
   ```bash
   python scripts/init_auth.py
   ```

3. Sigue las instrucciones para crear tu usuario admin

**Alternativa**: Si no funciona el Shell, puedes usar el endpoint de registro:
- Ve a `https://tu-app.onrender.com/auth/register`
- Crea tu cuenta
- Luego usa el script `make_admin.py` para convertirla en admin

### Paso 5: Probar Funcionalidades

1. **Login**: Inicia sesión con tu usuario
2. **Generar Historia**: Sube un documento y genera una historia de usuario
3. **Matriz de Trazabilidad**: Prueba generar una matriz
4. **Jira** (si configuraste): Prueba la integración con Jira

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### Problema 1: "Application failed to start"

**Causa**: Error en el build o en las variables de entorno.

**Solución**:
1. Ve a la pestaña **"Logs"** en Render
2. Busca el error específico (generalmente en rojo)
3. Errores comunes:
   - `GOOGLE_API_KEY not found` → Agrega la variable de entorno
   - `ModuleNotFoundError` → Falta una dependencia en requirements.txt
   - `Database connection failed` → Verifica DATABASE_URL

### Problema 2: "502 Bad Gateway"

**Causa**: La aplicación no está respondiendo en el puerto correcto.

**Solución**:
1. Verifica que el **Start Command** sea:
   ```
   gunicorn -w 4 -b 0.0.0.0:$PORT run:app
   ```
2. NO uses un puerto fijo, Render asigna `$PORT` automáticamente

### Problema 3: "Database connection timeout"

**Causa**: La aplicación no puede conectarse a PostgreSQL.

**Solución**:
1. Verifica que DATABASE_URL esté correcta
2. Asegúrate de usar **"Internal Database URL"** (no External)
3. Verifica que la base de datos esté en **"Available"**

### Problema 4: "Playwright browser not found"

**Causa**: Playwright no se instaló correctamente.

**Solución**:
1. Verifica que `build.sh` tenga:
   ```bash
   playwright install chromium
   playwright install-deps chromium
   ```
2. Re-despliega manualmente:
   - Ve a **"Manual Deploy"** → **"Deploy latest commit"**

### Problema 5: "Free instance will spin down with inactivity"

**Esto es NORMAL en el plan gratuito.**

**Comportamiento**:
- Después de 15 minutos sin uso, Render "duerme" tu aplicación
- La primera petición después tardará 30-60 segundos en responder
- Luego funciona normal

**Soluciones**:
1. **Aceptarlo** - Es parte del plan gratuito
2. **Upgrade a plan pago** ($7/mes) - Mantiene la app siempre activa
3. **Usar un servicio de "ping"** - Hace peticiones cada 10 minutos para mantenerla activa
   - Ejemplo: [UptimeRobot](https://uptimerobot.com/) (gratis)

### Problema 6: "Session expired" constantemente

**Causa**: Las sesiones se pierden al reiniciar.

**Solución**:
En producción, las sesiones se guardan en archivos. Render puede reiniciar el servidor.

**Mejor solución** (para después):
- Usar Redis para sesiones persistentes
- Render ofrece Redis gratis

### Ver Logs en Tiempo Real

Para debugging:
1. Ve a tu Web Service en Render
2. Click en **"Logs"** en el menú izquierdo
3. Verás todos los logs en tiempo real
4. Busca errores en rojo

---

## 🔄 MANTENIMIENTO Y ACTUALIZACIONES

### Actualizar tu Aplicación

**Render se actualiza automáticamente** cuando haces push a GitHub:

1. Haz cambios en tu código local
2. Commit y push a GitHub:
   ```bash
   git add .
   git commit -m "Descripción de cambios"
   git push origin main
   ```
3. Render detectará el cambio y re-desplegará automáticamente
4. Verás el progreso en la pestaña "Events"

### Despliegue Manual

Si quieres forzar un re-despliegue:
1. Ve a tu Web Service en Render
2. Click en **"Manual Deploy"**
3. Selecciona **"Deploy latest commit"**

### Ver Uso de Recursos

1. Ve a tu Web Service
2. Click en **"Metrics"**
3. Verás:
   - CPU usage
   - Memory usage
   - Response times
   - Requests per second

### Backups de Base de Datos

**IMPORTANTE**: El plan gratuito NO incluye backups automáticos.

**Hacer backup manual**:
1. Ve a tu PostgreSQL database en Render
2. En la pestaña "Info", copia la **External Database URL**
3. Usa `pg_dump` para hacer backup:
   ```bash
   pg_dump "postgresql://..." > backup.sql
   ```

**Recomendación**: Haz backups semanales si tienes datos importantes.

### Renovar Base de Datos Gratuita

El plan gratuito de PostgreSQL expira después de 90 días.

**Antes de que expire**:
1. Haz backup de tus datos
2. Crea una nueva base de datos gratuita
3. Restaura el backup
4. Actualiza DATABASE_URL en tu Web Service

---

## 📊 MONITOREO Y LOGS

### Ver Logs de Aplicación

```bash
# En la pestaña "Logs" de Render, verás:
- Peticiones HTTP
- Errores de Python
- Logs de tu aplicación (logger.info, logger.error)
```

### Logs Importantes a Monitorear

- ✅ Errores de autenticación
- ✅ Fallos de API de Google
- ✅ Errores de base de datos
- ✅ Timeouts

### Alertas (Plan Pago)

En planes pagos, puedes configurar alertas por:
- Downtime
- Errores 500
- Alto uso de CPU/memoria

---

## 💰 COSTOS Y PLANES

### Plan Gratuito (Actual)

**Web Service**:
- ✅ 750 horas/mes (suficiente para 1 servicio 24/7)
- ✅ SSL gratis
- ✅ Despliegues automáticos
- ⚠️ Se "duerme" después de 15 min de inactividad
- ⚠️ Tarda 30-60s en "despertar"

**PostgreSQL**:
- ✅ 90 días gratis
- ✅ 1 GB de almacenamiento
- ⚠️ Sin backups automáticos
- ⚠️ Expira después de 90 días (puedes crear otra)

### Plan Starter ($7/mes por servicio)

**Web Service**:
- ✅ Siempre activo (no se duerme)
- ✅ Respuestas instantáneas
- ✅ Más recursos (512 MB RAM)

**PostgreSQL** ($7/mes):
- ✅ Sin expiración
- ✅ Backups diarios automáticos
- ✅ 1 GB de almacenamiento

### ¿Cuándo Actualizar?

Considera actualizar si:
- ✅ Tienes usuarios reales usando la app
- ✅ No quieres el delay de 30-60s
- ✅ Necesitas backups automáticos
- ✅ Necesitas más de 90 días de base de datos

---

## 🎯 CHECKLIST FINAL

Antes de considerar el despliegue completo:

### Preparación
- [ ] Proyecto subido a GitHub
- [ ] Google API Key obtenida
- [ ] Variables de entorno preparadas
- [ ] Archivos de configuración creados (Procfile, render.yaml, build.sh)

### Render
- [ ] Cuenta de Render creada y verificada
- [ ] Base de datos PostgreSQL creada
- [ ] DATABASE_URL copiada
- [ ] Web Service creado
- [ ] Variables de entorno configuradas
- [ ] Despliegue exitoso (status "Live")

### Verificación
- [ ] Aplicación accesible en la URL de Render
- [ ] Login funciona
- [ ] Usuario admin creado
- [ ] Generación de historias funciona
- [ ] Matriz de trazabilidad funciona
- [ ] Integración Jira funciona (si aplica)

### Post-Despliegue
- [ ] Backup de base de datos configurado
- [ ] Logs monitoreados
- [ ] Documentación actualizada con URL de producción

---

## 🆘 SOPORTE Y RECURSOS

### Documentación Oficial
- [Render Docs](https://render.com/docs)
- [Render Python Guide](https://render.com/docs/deploy-flask)
- [PostgreSQL on Render](https://render.com/docs/databases)

### Comunidad
- [Render Community Forum](https://community.render.com/)
- [Render Status](https://status.render.com/) - Ver si hay problemas con Render

### Contacto Render
- Email: support@render.com
- Chat en vivo en render.com (esquina inferior derecha)

---

## 🎉 ¡FELICIDADES!

Si llegaste hasta aquí y todo funciona, **¡tu aplicación está en producción!** 🚀

Tu aplicación ahora está:
- ✅ Accesible desde cualquier lugar del mundo
- ✅ Con HTTPS seguro
- ✅ Con base de datos PostgreSQL
- ✅ Con despliegues automáticos

**URL de tu aplicación**:
```
https://nexus-ai.onrender.com
```
(Reemplaza con tu URL real)

---

## 📝 PRÓXIMOS PASOS RECOMENDADOS

1. **Configurar dominio personalizado** (opcional)
   - Puedes usar tu propio dominio (ej: nexus.tuempresa.com)
   - Render lo soporta gratis

2. **Configurar Redis para sesiones** (recomendado)
   - Mejora la persistencia de sesiones
   - Render ofrece Redis gratis

3. **Configurar monitoreo** (recomendado)
   - UptimeRobot para mantener la app activa
   - Sentry para tracking de errores

4. **Configurar backups automáticos** (importante)
   - Script para backups diarios de PostgreSQL
   - Guardar en Google Drive o similar

5. **Documentar URL de producción**
   - Actualizar README.md con la URL
   - Compartir con tu equipo

---

**¿Preguntas o problemas?**
- Revisa la sección de [Solución de Problemas](#solución-de-problemas)
- Consulta los logs en Render
- Busca en [Render Community](https://community.render.com/)

---

*Última actualización: Diciembre 2025*  
*Versión: 1.0*

