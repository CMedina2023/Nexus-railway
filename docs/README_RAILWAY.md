___
   ____       _ __                     ____             __           
  / __ \____ _(_) /__      ______ ___  / __ \___  ____  / /___  __  __
 / /_/ / __ `/ / / _ \/ | / / __ `/ / / / __ / _ \/ __ \/ / __ \/ / / /
/ _, _/ /_/ / / /  __/ |/ / /_/ / /_/ / /_/ /  __/ /_/ / / /_/ / /_/ / 
/_/ |_|\__,_/_/_/\___/|___/\__,_/\__, /_____/\___/ .___/_/\____/\__, /  
                                /____/          /_/            /____/   
___

# 🚂 Deploy en Railway - Nexus AI

Este proyecto está configurado para deployar en **Railway** con PostgreSQL.

## 🚀 Deploy Rápido

### Opción 1: Guía Visual (Recomendada)
📖 Lee: **[INICIO_RAPIDO.md](INICIO_RAPIDO.md)**

### Opción 2: Guía Completa
📚 Lee: **[RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)**

### Opción 3: Solo Checklist
✅ Lee: **[RAILWAY_CHECKLIST.md](RAILWAY_CHECKLIST.md)**

## 📁 Archivos de Configuración Railway

- `railway.json` - Configuración principal
- `nixpacks.toml` - Build configuration
- `Procfile` - Comando de inicio
- `.railwayignore` - Archivos a ignorar
- `.env.railway.example` - Template de variables

## 🔑 Variables de Entorno Requeridas

Necesitas configurar estas 3 variables en Railway:

```bash
GOOGLE_API_KEY=tu_api_key_aqui
SECRET_KEY=genera_con_script
ENCRYPTION_KEY=genera_con_script
```

### Generar claves:

```bash
# Opción 1: Script incluido
python generate_railway_secrets.py

# Opción 2: Comandos Python
python -c "import secrets; print(secrets.token_hex(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 📦 Estructura del Deploy

```
1. Railway clona tu repo desde GitHub
2. Instala dependencias (requirements.txt)
3. Instala Playwright para PDFs
4. Ejecuta build.sh (inicializa BD)
5. Inicia Gunicorn con tu app
6. PostgreSQL se conecta automáticamente
```

## ✅ Checklist Ultra-Rápido

- [ ] Push del código a GitHub
- [ ] Crear proyecto en Railway desde GitHub repo
- [ ] Agregar PostgreSQL al proyecto
- [ ] Configurar 3 variables obligatorias
- [ ] Generar dominio público
- [ ] Verificar deploy exitoso
- [ ] Crear usuario admin

## 🔧 El Problema del Puerto (Solucionado)

### ❌ Error original:
```
Error: '$PORT' is not a valid port number.
```

### ✅ Solución aplicada:

1. **Procfile actualizado:**
   ```bash
   web: gunicorn ... -b 0.0.0.0:${PORT} run:app
   ```

2. **config.py actualizado:**
   ```python
   FLASK_PORT = int(os.getenv('PORT', os.getenv('FLASK_PORT', '5000')))
   ```

## 🗄️ Base de Datos

Railway configura automáticamente PostgreSQL:
- `DATABASE_URL` se inyecta automáticamente
- Backups automáticos incluidos
- Interfaz web para queries SQL

## 🆘 Troubleshooting

### Deploy falla
1. Revisa logs en Railway → Deployments
2. Verifica variables de entorno
3. Confirma que PostgreSQL está activo

### Error de BD
1. Verifica que PostgreSQL esté en el mismo proyecto
2. `DATABASE_URL` debe estar presente (automática)

### App no responde
1. Verifica que el dominio esté generado
2. Espera 1-2 min después del deploy
3. Revisa los logs para errores

## 📚 Documentación

| Archivo | Descripción |
|---------|-------------|
| [INICIO_RAPIDO.md](INICIO_RAPIDO.md) | 🎯 Guía visual paso a paso (COMIENZA AQUÍ) |
| [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) | 📖 Guía completa y detallada |
| [RAILWAY_CHECKLIST.md](RAILWAY_CHECKLIST.md) | ✅ Checklist de deploy |
| [RAILWAY_RESUMEN.md](RAILWAY_RESUMEN.md) | 📋 Resumen de cambios |
| [.env.railway.example](.env.railway.example) | ⚙️ Template de variables |

## 🔗 Enlaces Útiles

- 🌐 [Railway Dashboard](https://railway.app/dashboard)
- 📖 [Railway Docs](https://docs.railway.app)
- 🔑 [Google AI Studio](https://aistudio.google.com/app/apikey)
- 💬 [Railway Discord](https://discord.gg/railway)

## 💡 Railway vs Render

| Feature | Render | Railway |
|---------|--------|---------|
| Puerto | `$PORT` | `${PORT}` |
| Config | `render.yaml` | `railway.json` |
| Build | Docker/Native | Nixpacks |
| BD | Manual setup | Auto-inject |
| Precio Free | $0/mes | $5 crédito/mes |

## 📊 Stack Tecnológico

- **Backend:** Flask + Python 3.11
- **Base de Datos:** PostgreSQL (Railway)
- **IA:** Google Gemini API
- **PDFs:** Playwright + Chromium
- **Server:** Gunicorn + Eventlet
- **Deploy:** Railway (Nixpacks)

## 🎯 Siguientes Pasos

1. **Lee:** [INICIO_RAPIDO.md](INICIO_RAPIDO.md)
2. **Genera:** Tus claves secretas
3. **Deploy:** Sigue los pasos
4. **Verifica:** Que todo funcione
5. **Disfruta:** Tu app en producción! 🎉

---

**¿Listo para deployar?** Empieza con [INICIO_RAPIDO.md](INICIO_RAPIDO.md) 🚀

---

<p align="center">
  <strong>Nexus AI - QA Academy</strong><br>
  Deployado en Railway con ❤️
</p>
