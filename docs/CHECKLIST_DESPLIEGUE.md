# ✅ CHECKLIST DE DESPLIEGUE EN RENDER

Usa este checklist para asegurarte de que no olvidas ningún paso.

---

## 📦 FASE 1: PREPARACIÓN LOCAL

### Código y Repositorio
- [ ] Proyecto funciona correctamente en local
- [ ] Todos los cambios están guardados (`git status` limpio)
- [ ] Archivo `.gitignore` creado (no subir `.env`, `*.db`, etc.)
- [ ] Archivo `requirements.txt` actualizado con todas las dependencias
- [ ] Archivos de configuración creados:
  - [ ] `Procfile`
  - [ ] `build.sh`
  - [ ] `render.yaml`
  - [ ] `env.example`

### GitHub
- [ ] Repositorio creado en GitHub
- [ ] Código subido a GitHub:
  ```bash
  git add .
  git commit -m "Preparar para despliegue en Render"
  git push origin main
  ```
- [ ] Verificar que el código está en GitHub (visitar la URL del repositorio)

### Claves y Credenciales
- [ ] Google API Key obtenida (https://makersuite.google.com/app/apikey)
- [ ] SECRET_KEY generada (ejecutar `python scripts/generar_claves.py`)
- [ ] ENCRYPTION_KEY generada (ejecutar `python scripts/generar_claves.py`)
- [ ] Credenciales de Jira (si aplica):
  - [ ] JIRA_BASE_URL
  - [ ] JIRA_EMAIL
  - [ ] JIRA_API_TOKEN
- [ ] Todas las claves guardadas en lugar seguro

---

## 🌐 FASE 2: CONFIGURACIÓN EN RENDER

### Cuenta de Render
- [ ] Cuenta creada en [render.com](https://render.com)
- [ ] Email verificado
- [ ] GitHub conectado a Render

### Base de Datos PostgreSQL
- [ ] Nueva base de datos PostgreSQL creada
- [ ] Configuración:
  - [ ] Name: `nexus-ai-db`
  - [ ] Database: `nexus_ai`
  - [ ] Region: (elegir la más cercana)
  - [ ] Plan: Free
- [ ] Estado: **"Available"** (verde)
- [ ] **Internal Database URL** copiada y guardada

### Web Service
- [ ] Nuevo Web Service creado
- [ ] Repositorio GitHub conectado
- [ ] Configuración básica:
  - [ ] Name: `nexus-ai`
  - [ ] Region: (mismo que la base de datos)
  - [ ] Branch: `main`
  - [ ] Runtime: Python 3
  - [ ] Build Command: `chmod +x build.sh && ./build.sh`
  - [ ] Start Command: `gunicorn -w 4 -b 0.0.0.0:$PORT run:app`
  - [ ] Plan: Free

---

## 🔐 FASE 3: VARIABLES DE ENTORNO

### Variables Obligatorias
- [ ] `DATABASE_URL` = (URL de PostgreSQL copiada)
- [ ] `GOOGLE_API_KEY` = (tu API key de Google)
- [ ] `SECRET_KEY` = (clave generada)
- [ ] `ENCRYPTION_KEY` = (clave generada)
- [ ] `FLASK_ENV` = `production`
- [ ] `SESSION_COOKIE_SECURE` = `True`

### Variables Opcionales (Jira)
- [ ] `JIRA_BASE_URL` = (si usas Jira)
- [ ] `JIRA_EMAIL` = (si usas Jira)
- [ ] `JIRA_API_TOKEN` = (si usas Jira)

### Verificación
- [ ] Todas las variables configuradas sin errores de tipeo
- [ ] No hay espacios extra al inicio o final de las claves
- [ ] DATABASE_URL es la **Internal** (no External)

---

## 🚀 FASE 4: DESPLIEGUE

### Iniciar Despliegue
- [ ] Click en **"Create Web Service"**
- [ ] Build iniciado (ver logs en tiempo real)
- [ ] Esperar 5-10 minutos

### Verificar Build
- [ ] ✅ Instalando dependencias... (OK)
- [ ] ✅ Instalando Playwright... (OK)
- [ ] ✅ Creando base de datos... (OK)
- [ ] ✅ Build completado (OK)
- [ ] ✅ Estado: **"Live"** (verde)

### Errores Comunes
Si el build falla, verificar:
- [ ] Todas las variables de entorno están configuradas
- [ ] DATABASE_URL es correcta
- [ ] GOOGLE_API_KEY es válida
- [ ] No hay errores de sintaxis en el código

---

## ✅ FASE 5: VERIFICACIÓN POST-DESPLIEGUE

### Acceso a la Aplicación
- [ ] URL de la aplicación copiada (ej: `https://nexus-ai.onrender.com`)
- [ ] Página carga correctamente (no error 502)
- [ ] Página de login visible
- [ ] HTTPS funciona (candado verde en el navegador)

### Crear Usuario Admin
Opción 1 - Shell de Render:
- [ ] Ir a Web Service → Shell
- [ ] Ejecutar: `python scripts/init_auth.py`
- [ ] Crear usuario admin

Opción 2 - Registro manual:
- [ ] Ir a `/auth/register`
- [ ] Crear cuenta
- [ ] Usar Shell para ejecutar: `python scripts/make_admin.py`

### Probar Funcionalidades
- [ ] Login funciona
- [ ] Dashboard carga correctamente
- [ ] Subir documento de prueba
- [ ] Generar historia de usuario (funciona)
- [ ] Generar matriz de trazabilidad (funciona)
- [ ] Integración Jira (si aplica)

---

## 🔍 FASE 6: MONITOREO INICIAL

### Logs
- [ ] Revisar logs en Render (pestaña "Logs")
- [ ] No hay errores críticos (en rojo)
- [ ] Aplicación responde a peticiones

### Métricas
- [ ] Ir a pestaña "Metrics"
- [ ] Verificar:
  - [ ] CPU usage normal (< 50%)
  - [ ] Memory usage normal (< 80%)
  - [ ] Response times aceptables (< 2s)

### Base de Datos
- [ ] Ir a PostgreSQL database
- [ ] Verificar estado: "Available"
- [ ] Verificar conexiones activas

---

## 📋 FASE 7: POST-DESPLIEGUE

### Documentación
- [ ] Actualizar README.md con URL de producción
- [ ] Documentar proceso de despliegue (este checklist)
- [ ] Guardar credenciales en gestor de contraseñas

### Backup
- [ ] Configurar backup manual de base de datos
- [ ] Documentar proceso de backup
- [ ] Programar backups periódicos (semanal recomendado)

### Seguridad
- [ ] Verificar que `.env` NO está en GitHub
- [ ] Verificar que `*.db` NO está en GitHub
- [ ] Verificar que claves secretas NO están en el código
- [ ] Cambiar contraseñas de prueba (si existen)

### Comunicación
- [ ] Compartir URL con el equipo
- [ ] Documentar credenciales de acceso
- [ ] Crear usuarios para el equipo (si aplica)

---

## 🎯 FASE 8: OPTIMIZACIÓN (OPCIONAL)

### Rendimiento
- [ ] Configurar UptimeRobot para mantener app activa
- [ ] Considerar upgrade a plan Starter ($7/mes) si hay uso constante
- [ ] Configurar Redis para sesiones (mejora persistencia)

### Monitoreo
- [ ] Configurar alertas de downtime
- [ ] Configurar Sentry para tracking de errores
- [ ] Configurar Google Analytics (si aplica)

### Dominio Personalizado
- [ ] Comprar dominio (opcional)
- [ ] Configurar dominio en Render
- [ ] Actualizar DNS

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Si la aplicación no inicia:
1. [ ] Revisar logs en Render (pestaña "Logs")
2. [ ] Verificar variables de entorno
3. [ ] Verificar DATABASE_URL
4. [ ] Re-desplegar manualmente

### Si hay error 502:
1. [ ] Verificar Start Command
2. [ ] Verificar que usa `$PORT` (no puerto fijo)
3. [ ] Revisar logs de gunicorn

### Si la base de datos no conecta:
1. [ ] Verificar DATABASE_URL (debe ser Internal)
2. [ ] Verificar que la base de datos está "Available"
3. [ ] Verificar que psycopg2-binary está en requirements.txt

### Si Playwright falla:
1. [ ] Verificar que build.sh tiene `playwright install chromium`
2. [ ] Verificar que build.sh tiene `playwright install-deps chromium`
3. [ ] Re-desplegar

---

## ✅ CHECKLIST FINAL

Antes de considerar el despliegue completo:

- [ ] ✅ Aplicación accesible en URL de Render
- [ ] ✅ Login funciona
- [ ] ✅ Generación de historias funciona
- [ ] ✅ Generación de matriz funciona
- [ ] ✅ No hay errores en logs
- [ ] ✅ Usuario admin creado
- [ ] ✅ Backup configurado
- [ ] ✅ Equipo notificado
- [ ] ✅ Documentación actualizada

---

## 🎉 ¡DESPLIEGUE COMPLETADO!

Si todos los checkboxes están marcados, **¡felicidades!** 🚀

Tu aplicación Nexus AI está ahora en producción y accesible desde cualquier lugar del mundo.

**URL de producción**: `https://tu-app.onrender.com`

---

## 📞 RECURSOS ÚTILES

- **Guía completa**: Ver `GUIA_DESPLIEGUE_RENDER.md`
- **Generar claves**: `python scripts/generar_claves.py`
- **Render Docs**: https://render.com/docs
- **Soporte Render**: support@render.com
- **Status Render**: https://status.render.com/

---

*Última actualización: Diciembre 2025*  
*Versión: 1.0*

