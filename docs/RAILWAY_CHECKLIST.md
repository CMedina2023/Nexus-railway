# ✅ Railway Deploy - Checklist Rápido

## Antes del deploy

- [ ] Commit y push de todos los cambios
  ```bash
  git add .
  git commit -m "Configure for Railway"
  git push origin main
  ```

- [ ] Generar claves secretas
  ```bash
  python generate_railway_secrets.py
  ```
  Guarda las claves generadas, las necesitarás en Railway.

## En Railway

### 1. Crear Proyecto
- [ ] Ir a https://railway.app/dashboard
- [ ] Click "New Project"
- [ ] Seleccionar "Deploy from GitHub repo"
- [ ] Elegir repositorio `Nexus-railway`

### 2. Agregar PostgreSQL
- [ ] En el proyecto, click "+ New"
- [ ] Seleccionar "Database" → "Add PostgreSQL"
- [ ] Esperar a que se active

### 3. Configurar Variables de Entorno

En tu servicio **web**, agregar estas variables:

#### ⚠️ OBLIGATORIAS
```bash
GOOGLE_API_KEY=tu_google_api_key_aqui
SECRET_KEY=clave_generada_por_script
ENCRYPTION_KEY=clave_generada_por_script
```

#### ⚙️ Recomendadas
```bash
FLASK_ENV=production
SESSION_COOKIE_SECURE=True
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
```

#### 📊 Opcionales (Jira)
```bash
JIRA_BASE_URL=https://tu-empresa.atlassian.net
JIRA_EMAIL=tu-email@empresa.com
JIRA_API_TOKEN=tu_jira_token
```

**Nota:** `DATABASE_URL` se configura automáticamente ✅

### 4. Generar Dominio
- [ ] En el servicio web, ir a "Settings"
- [ ] Sección "Networking"
- [ ] Click "Generate Domain"
- [ ] Copiar la URL: `https://tu-proyecto.up.railway.app`

### 5. Verificar Deploy
- [ ] Ir a "Deployments"
- [ ] Ver logs del deployment activo
- [ ] Buscar mensaje: `Listening at: http://0.0.0.0:XXXX`
- [ ] Abrir la URL generada
- [ ] Verificar que carga la página de login

## Post-Deploy

### Crear usuario admin
Opción A - Railway Shell (desde dashboard):
```bash
python scripts/make_admin.py
```

Opción B - Railway CLI:
```bash
railway login
railway link
railway run python scripts/make_admin.py
```

### Verificar funcionalidades
- [ ] Login funciona
- [ ] Dashboard carga
- [ ] Gemini responde (test con una historia)
- [ ] PDFs se generan
- [ ] (Opcional) Jira conecta

## Troubleshooting común

### Error: "$PORT is not valid"
✅ Ya solucionado en `config.py` y `Procfile`

### Error: "Application failed to respond"
- Verificar logs en Railway
- Confirmar todas las variables de entorno
- Verificar que PostgreSQL esté activo

### Error: "Database connection failed"
- Verificar que `DATABASE_URL` esté presente
- Confirmar que PostgreSQL esté corriendo

### Error: Module not found
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

## Comandos útiles

```bash
# Ver logs en tiempo real
railway logs

# Ver variables
railway variables

# Abrir shell
railway shell

# Conectar a PostgreSQL
railway connect postgres
```

## Enlaces importantes

- 📊 Dashboard: https://railway.app/dashboard
- 📖 Docs: https://docs.railway.app
- 💬 Discord: https://discord.gg/railway

---

**¿Todo listo?** Si todos los checkboxes están marcados, ¡tu app está en producción! 🎉

Para más detalles, consulta: `RAILWAY_DEPLOY.md`
