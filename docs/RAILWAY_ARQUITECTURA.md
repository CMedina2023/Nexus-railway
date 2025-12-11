# 📊 Diagrama de Arquitectura - Railway Deploy

## 🏗️ Arquitectura de la Aplicación en Railway

```
┌─────────────────────────────────────────────────────────────┐
│                     RAILWAY PROJECT                          │
│                                                              │
│  ┌────────────────────┐         ┌───────────────────────┐  │
│  │   Web Service      │◄────────┤   PostgreSQL DB       │  │
│  │                    │         │                       │  │
│  │  - Gunicorn        │         │  - nexus_ai          │  │
│  │  - Flask App       │         │  - Auto-backups      │  │
│  │  - Playwright      │         │  - DATABASE_URL      │  │
│  │                    │         │                       │  │
│  └─────────┬──────────┘         └───────────────────────┘  │
│            │                                                │
│            │ PORT (auto)                                    │
│            │ Environment Variables                          │
│            │                                                │
└────────────┼────────────────────────────────────────────────┘
             │
             │ HTTPS
             │
        ┌────▼─────┐
        │  Public  │
        │  Domain  │
        │          │
        │ nexus... │
        │.railway  │
        │  .app    │
        └──────────┘
```

## 🔄 Flujo de Deploy

```
┌──────────────┐
│   GitHub     │
│   Push to    │
│   main       │
└──────┬───────┘
       │
       │ Webhook
       │
┌──────▼────────────────────────────────────────────────────┐
│                  RAILWAY BUILD PROCESS                     │
│                                                            │
│  1. Clone Repository ✓                                    │
│     └── git clone https://github.com/user/Nexus-railway   │
│                                                            │
│  2. Detect Build Environment ✓                            │
│     ├── Found: railway.json                               │
│     ├── Found: nixpacks.toml                              │
│     └── Found: requirements.txt → Python detected         │
│                                                            │
│  3. Setup Phase (nixpacks.toml)                           │
│     ├── Install Python 3.11                               │
│     ├── Install Playwright driver                         │
│     └── Install Chromium                                  │
│                                                            │
│  4. Install Dependencies                                  │
│     ├── pip install --upgrade pip                         │
│     ├── pip install -r requirements.txt                   │
│     ├── playwright install chromium                       │
│     └── playwright install-deps chromium                  │
│                                                            │
│  5. Build Phase                                           │
│     ├── chmod +x build.sh                                 │
│     └── ./build.sh                                        │
│         ├── Creates database tables                       │
│         ├── Runs migrations                               │
│         └── Initializes data                              │
│                                                            │
│  6. Start Application                                     │
│     └── gunicorn -w 2 -k eventlet -b 0.0.0.0:${PORT}      │
│         run:app                                           │
│                                                            │
└────────────────────────────┬──────────────────────────────┘
                             │
                             │ Success
                             │
                    ┌────────▼────────┐
                    │  App Running    │
                    │  Status: Active │
                    │  Health: ✓      │
                    └─────────────────┘
```

## 🔐 Variables de Entorno - Flujo

```
┌─────────────────────┐
│  Railway Dashboard  │
│  Variables Tab      │
└──────────┬──────────┘
           │
           │ Inyecta variables al contenedor
           │
┌──────────▼─────────────────────────────────────────────┐
│            ENVIRONMENT VARIABLES                        │
│                                                         │
│  Automáticas (Railway):                                │
│  ├── PORT=7438 (ejemplo)                               │
│  ├── DATABASE_URL=postgresql://user:pass@host:port/db  │
│  ├── RAILWAY_ENVIRONMENT=production                    │
│  └── RAILWAY_PROJECT_ID=xxx                            │
│                                                         │
│  Manuales (Tú configuras):                             │
│  ├── GOOGLE_API_KEY=tu_api_key                         │
│  ├── SECRET_KEY=tu_secret_32_chars_min                 │
│  ├── ENCRYPTION_KEY=tu_fernet_key                      │
│  ├── FLASK_ENV=production                              │
│  └── SESSION_COOKIE_SECURE=True                        │
│                                                         │
└──────────┬──────────────────────────────────────────────┘
           │
           │ app/core/config.py lee estas variables
           │
┌──────────▼────────────────────────────────────┐
│         Config Class                          │
│                                               │
│  FLASK_PORT = int(os.getenv('PORT',          │
│                   os.getenv('FLASK_PORT',    │
│                   '5000')))                   │
│                                               │
│  DATABASE_URL = os.getenv('DATABASE_URL')    │
│  GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')│
│  SECRET_KEY = os.getenv('SECRET_KEY')        │
│  ...                                         │
│                                               │
└───────────────────────────────────────────────┘
```

## 🗄️ Base de Datos - Conexión

```
┌────────────────────┐
│  PostgreSQL        │
│  Service           │
│  (Railway)         │
└─────────┬──────────┘
          │
          │ Genera automáticamente:
          │ - PGHOST
          │ - PGPORT
          │ - PGUSER
          │ - PGPASSWORD
          │ - PGDATABASE
          │ - DATABASE_URL ← La que usamos
          │
┌─────────▼──────────────────────────────────────┐
│   DATABASE_URL Format:                         │
│                                                │
│   postgresql://USER:PASSWORD@HOST:PORT/DB      │
│                                                │
│   Ejemplo:                                     │
│   postgresql://postgres:abc123@railway-       │
│   postgres.railway.internal:5432/railway       │
│                                                │
└─────────┬──────────────────────────────────────┘
          │
          │ SQLAlchemy usa esta URL
          │
┌─────────▼──────────────────────────────────────┐
│  app/__init__.py                               │
│                                                │
│  db = SQLAlchemy()                             │
│  app.config['SQLALCHEMY_DATABASE_URI'] =      │
│      Config.DATABASE_URL                       │
│  db.init_app(app)                              │
│                                                │
└────────────────────────────────────────────────┘
```

## 🌐 Networking & Routing

```
┌──────────────────────────────────────────────┐
│         Internet / User Browser              │
└──────────────────┬───────────────────────────┘
                   │
                   │ HTTPS Request
                   │
┌──────────────────▼───────────────────────────┐
│    Railway Load Balancer                     │
│    - SSL/TLS Termination (HTTPS)             │
│    - Health Checks                           │
│    - Auto-scaling Ready                      │
└──────────────────┬───────────────────────────┘
                   │
                   │ HTTP to Container
                   │ Port: ${PORT} (Railway injected)
                   │
┌──────────────────▼───────────────────────────┐
│    Gunicorn Server (Container)               │
│    - Workers: 2                              │
│    - Worker Class: eventlet (async)          │
│    - Binding: 0.0.0.0:${PORT}                │
│    - Timeout: 300s                           │
│    - Graceful Timeout: 30s                   │
└──────────────────┬───────────────────────────┘
                   │
                   │ WSGI Protocol
                   │
┌──────────────────▼───────────────────────────┐
│    Flask Application                         │
│    - Routes handling                         │
│    - Session management                      │
│    - Database queries                        │
│    - Gemini API calls                        │
│    - PDF generation                          │
└──────────────────────────────────────────────┘
```

## 🔁 Request Lifecycle

```
1. User Request
   │
   ├─→ https://nexus-railway.up.railway.app/dashboard
   │
2. Railway Load Balancer
   │
   ├─→ SSL Termination
   ├─→ Health Check (is app alive?)
   ├─→ Route to container
   │
3. Container (Gunicorn)
   │
   ├─→ Worker picks up request
   ├─→ Pass to Flask via WSGI
   │
4. Flask App
   │
   ├─→ Check authentication (Flask-Login)
   ├─→ Load session from DB
   ├─→ Execute route handler
   │   │
   │   ├─→ Query PostgreSQL (via DATABASE_URL)
   │   ├─→ Call Gemini API (if needed)
   │   ├─→ Generate PDF (if needed)
   │   └─→ Render template
   │
5. Response
   │
   ├─→ Flask returns HTML/JSON
   ├─→ Gunicorn sends to client
   ├─→ Railway LB adds headers
   └─→ User receives response
```

## 📦 File Structure in Railway

```
/app  (container filesystem)
│
├── /opt/nixpacks/
│   └── ... (Nixpacks build tools)
│
├── /app/  (your code)
│   ├── run.py
│   ├── requirements.txt
│   ├── build.sh
│   ├── railway.json
│   ├── nixpacks.toml
│   ├── Procfile
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── config.py  ← Lee env vars
│   │   │   └── app.py
│   │   ├── routes/
│   │   ├── models/
│   │   └── utils/
│   │
│   ├── templates/
│   ├── static/
│   └── scripts/
│
└── /ms-playwright/
    └── chromium/  (para PDFs)
```

## ⚡ Performance & Scaling

```
┌────────────────────────────────────────────────┐
│          Railway Container                     │
│                                                │
│  Resources (Free Tier):                        │
│  ├── RAM: 512MB                                │
│  ├── CPU: Shared                               │
│  ├── Disk: 1GB                                 │
│  └── Monthly: $5 credit                        │
│                                                │
│  Auto-restart on:                              │
│  ├── Crashes                                   │
│  ├── Out of Memory                             │
│  └── Health check fails                        │
│                                                │
│  Gunicorn Workers: 2                           │
│  └── Eventlet (async) for WebSocket support   │
│                                                │
└────────────────────────────────────────────────┘
```

## 🔒 Security Flow

```
┌─────────────────────────────────────────────┐
│  User Login Request                         │
└──────────────┬──────────────────────────────┘
               │
               │ POST /login
               │ {username, password}
               │
┌──────────────▼──────────────────────────────┐
│  Flask-Login + Bcrypt                       │
│  1. Hash incoming password (bcrypt)         │
│  2. Compare with DB hash                    │
│  3. Check login attempts                    │
│  4. Generate session                        │
└──────────────┬──────────────────────────────┘
               │
               │ Session Created
               │
┌──────────────▼──────────────────────────────┐
│  Session Storage (PostgreSQL)               │
│  - session_id (encrypted)                   │
│  - user_id                                  │
│  - expiry (8 hours default)                 │
│  - secure cookie (HTTPS only)               │
└─────────────────────────────────────────────┘
```

## 📝 Monitoring & Logs

```
Railway Dashboard
│
├── Metrics Tab
│   ├── CPU Usage
│   ├── Memory Usage
│   ├── Network I/O
│   └── Request Count
│
├── Deployments Tab
│   ├── Build logs
│   ├── Runtime logs
│   └── Error traces
│
└── Database Tab (PostgreSQL)
    ├── Connection count
    ├── Query performance
    └── Storage usage
```

## 🎯 Deploy Trigger Flow

```
┌─────────────┐
│ Git Push    │
│ to main     │
└──────┬──────┘
       │
       │ GitHub Webhook
       │
┌──────▼────────────────┐
│ Railway detects push │
└──────┬────────────────┘
       │
┌──────▼────────────────┐     ┌──────────────┐
│ Start new build       │────►│ Keep old     │
│ Zero-downtime         │     │ version      │
│ deployment            │     │ running      │
└──────┬────────────────┘     └──────────────┘
       │
       │ Build Success?
       │
┌──────▼────────────────┐
│ YES: Switch traffic   │
│ to new version        │
│                       │
│ NO: Keep old version  │
│ running, alert user   │
└───────────────────────┘
```

---

## 📚 Referencias

- [Railway Architecture Docs](https://docs.railway.app/reference/architecture)
- [Nixpacks Build Process](https://nixpacks.com/docs)
- [Flask Deployment Best Practices](https://flask.palletsprojects.com/en/latest/deploying/)

---

**Este diagrama te ayuda a entender cómo funciona tu aplicación en Railway** 🚂
