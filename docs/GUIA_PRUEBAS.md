# 🧪 GUÍA DE PRUEBAS - SISTEMA DE AUTENTICACIÓN

## ⚡ INICIO RÁPIDO

### 1. **Activar Entorno Virtual**

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# O Windows CMD
.venv\Scripts\activate.bat

# Linux/Mac
source .venv/bin/activate
```

### 2. **Instalar Dependencias**

```bash
pip install -r requirements.txt
```

### 3. **Inicializar el Sistema**

Ejecuta el script de inicialización:

```bash
python scripts/init_auth.py
```

Este script:
- ✅ Genera `SECRET_KEY` y `ENCRYPTION_KEY` automáticamente
- ✅ Crea/actualiza el archivo `.env`
- ✅ Inicializa la base de datos
- ✅ Te permite crear el primer usuario admin

### 4. **Iniciar el Servidor**

```bash
python run.py
```

El servidor debería iniciar en: `http://localhost:5000`

---

## 🧪 PROBAR ENDPOINTS

### Opción 1: Usando curl (Línea de comandos)

#### **1. Crear Usuario Admin (si no lo creaste antes)**

```bash
python -c "from app.database import init_db; from app.auth.user_service import UserService; init_db(); UserService().create_user('admin@test.com', 'Admin123!', 'admin')"
```

#### **2. Login**

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@test.com\",\"password\":\"Admin123!\"}" \
  -c cookies.txt
```

**Respuesta esperada:**
```json
{
  "message": "Login exitoso",
  "user": {
    "id": "...",
    "email": "admin@test.com",
    "role": "admin"
  }
}
```

#### **3. Verificar Sesión**

```bash
curl http://localhost:5000/auth/session \
  -b cookies.txt
```

#### **4. Configurar Proyecto Jira (Admin)**

```bash
curl -X POST http://localhost:5000/api/projects/config \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d "{
    \"project_key\": \"TEST\",
    \"jira_base_url\": \"https://tu-empresa.atlassian.net\",
    \"email\": \"jira@empresa.com\",
    \"token\": \"tu-token-jira\"
  }"
```

#### **5. Listar Proyectos Configurados**

```bash
curl http://localhost:5000/api/projects/list \
  -b cookies.txt
```

#### **6. Ver Métricas Generales (Admin/Manager)**

```bash
curl "http://localhost:5000/api/jira/metrics/TEST?view_type=general" \
  -b cookies.txt
```

#### **7. Ver Métricas Personales**

```bash
curl "http://localhost:5000/api/jira/metrics/TEST?view_type=personal" \
  -b cookies.txt
```

#### **8. Configurar Token Personal**

```bash
curl -X POST http://localhost:5000/api/jira/personal-token/TEST \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d "{
    \"email\": \"usuario@empresa.com\",
    \"token\": \"tu-token-personal\",
    \"use_personal\": true
  }"
```

#### **9. Logout**

```bash
curl -X POST http://localhost:5000/auth/logout \
  -b cookies.txt
```

---

### Opción 2: Usando Python requests

Crea un archivo `test_auth.py`:

```python
import requests
import json

BASE_URL = "http://localhost:5000"
session = requests.Session()

# 1. Login
print("🔐 Login...")
response = session.post(
    f"{BASE_URL}/auth/login",
    json={"email": "admin@test.com", "password": "Admin123!"}
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# 2. Ver sesión
print("\n👤 Ver sesión...")
response = session.get(f"{BASE_URL}/auth/session")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# 3. Configurar proyecto (Admin)
print("\n⚙️ Configurar proyecto...")
response = session.post(
    f"{BASE_URL}/api/projects/config",
    json={
        "project_key": "TEST",
        "jira_base_url": "https://empresa.atlassian.net",
        "email": "jira@empresa.com",
        "token": "tu-token-jira"
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# 4. Ver métricas
print("\n📊 Ver métricas...")
response = session.get(f"{BASE_URL}/api/jira/metrics/TEST?view_type=personal")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# 5. Logout
print("\n🚪 Logout...")
response = session.post(f"{BASE_URL}/auth/logout")
print(f"Status: {response.status_code}")
```

Ejecuta:
```bash
python test_auth.py
```

---

### Opción 3: Usando Postman

#### **Colección de Endpoints:**

1. **Login**
   - Method: `POST`
   - URL: `http://localhost:5000/auth/login`
   - Headers: `Content-Type: application/json`
   - Body (raw JSON):
     ```json
     {
       "email": "admin@test.com",
       "password": "Admin123!"
     }
     ```

2. **Session Info**
   - Method: `GET`
   - URL: `http://localhost:5000/auth/session`
   - (La cookie de sesión se maneja automáticamente)

3. **Create Project Config** (Admin)
   - Method: `POST`
   - URL: `http://localhost:5000/api/projects/config`
   - Body:
     ```json
     {
       "project_key": "TEST",
       "jira_base_url": "https://empresa.atlassian.net",
       "email": "jira@empresa.com",
       "token": "tu-token-jira"
     }
     ```

4. **Get Metrics**
   - Method: `GET`
   - URL: `http://localhost:5000/api/jira/metrics/TEST?view_type=personal`

5. **Logout**
   - Method: `POST`
   - URL: `http://localhost:5000/auth/logout`

---

## ✅ CHECKLIST DE PRUEBAS

### Autenticación
- [ ] Login exitoso
- [ ] Login con credenciales incorrectas (debe fallar)
- [ ] Logout
- [ ] Acceso a endpoint protegido sin autenticación (debe retornar 401)
- [ ] Acceso a endpoint protegido con autenticación (debe funcionar)

### Configuración de Proyectos
- [ ] Crear configuración de proyecto (Admin)
- [ ] Listar proyectos configurados
- [ ] Obtener configuración de proyecto específico
- [ ] Actualizar configuración de proyecto (Admin)
- [ ] Usuario no-admin no puede crear/actualizar (debe retornar 403)

### Métricas
- [ ] Ver métricas generales (Admin/Manager)
- [ ] Ver métricas personales (todos)
- [ ] Usuario sin permisos no puede ver generales (debe retornar 403)

### Tokens Personales
- [ ] Guardar token personal
- [ ] Obtener configuración personal
- [ ] Toggle entre personal y compartido
- [ ] Eliminar configuración personal

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### Error: "ModuleNotFoundError: No module named 'flask_session'"
**Solución:** Instala dependencias
```bash
pip install -r requirements.txt
```

### Error: "SECRET_KEY no está configurada"
**Solución:** Ejecuta el script de inicialización
```bash
python scripts/init_auth.py
```

### Error: "ENCRYPTION_KEY inválida"
**Solución:** El script de inicialización genera una nueva. Verifica que `.env` tenga `ENCRYPTION_KEY` válida.

### Error: "Base de datos no inicializada"
**Solución:**
```bash
python -c "from app.database import init_db; init_db()"
```

### Error: "Usuario no autenticado" al acceder a endpoints
**Solución:** Asegúrate de haber hecho login primero y que las cookies de sesión se estén enviando.

### Error 403: "No autorizado"
**Solución:** Verifica que tu usuario tenga el rol correcto (admin, manager, usuario).

---

## 📝 NOTAS

1. **Cookies de Sesión**: Los endpoints usan cookies de sesión. En curl, usa `-c cookies.txt` para guardar y `-b cookies.txt` para usar cookies.

2. **Rate Limiting**: 
   - Login: máximo 5 intentos por minuto
   - Registro: máximo 3 intentos por hora

3. **Bloqueo de Cuenta**: Después de 5 intentos fallidos de login, la cuenta se bloquea por 15 minutos.

4. **Tokens Encriptados**: Los tokens se encriptan automáticamente antes de guardar en la base de datos.

---

## 🚀 PRÓXIMOS PASOS DESPUÉS DE PROBAR

Una vez que todo funcione:

1. ✅ Integrar frontend (páginas de login/registro)
2. ✅ Proteger endpoints existentes con `@login_required`
3. ✅ Agregar UI para configuración de proyectos
4. ✅ Agregar UI para métricas
5. ✅ Agregar UI para tokens personales

---

**¡Listo para probar!** 🎉


