# 🔧 Endpoints de Debug - Diagnóstico de Usuarios

## ⚠️ ADVERTENCIA

**Estos endpoints son SOLO para diagnóstico temporal. DEBEN ser eliminados después de resolver el problema.**

---

## 📋 Endpoints Disponibles

### 1. **Verificar si un Usuario Existe**

```
GET /debug/check_user/<email>
```

**Ejemplo:**
```bash
https://tu-app.onrender.com/debug/check_user/test2@test.com
```

**Respuesta si existe:**
```json
{
  "found": true,
  "email": "test2@test.com",
  "active": true,
  "is_locked": false,
  "failed_attempts": 0,
  "role": "usuario",
  "hash_preview": "$2b$12$abcdefghijklmnopqrst...",
  "created_at": "2025-12-11T10:30:00",
  "last_login": "2025-12-11T11:00:00"
}
```

**Respuesta si NO existe:**
```json
{
  "found": false,
  "message": "Usuario no encontrado en la base de datos"
}
```

---

### 2. **Probar una Contraseña**

```
GET /debug/test_password/<email>/<password>
```

**Ejemplo:**
```bash
https://tu-app.onrender.com/debug/test_password/test2@test.com/Pruebas1
```

**Respuesta:**
```json
{
  "email": "test2@test.com",
  "password_tested": "Pruebas1",
  "password_length": 8,
  "is_valid": true,
  "message": "✅ Contraseña correcta"
}
```

---

### 3. **Desbloquear un Usuario**

```
POST /debug/unlock_user/<email>
```

**Ejemplo con curl:**
```bash
curl -X POST https://tu-app.onrender.com/debug/unlock_user/test2@test.com
```

**Ejemplo con navegador (usando extensión o Postman):**
```
POST https://tu-app.onrender.com/debug/unlock_user/test2@test.com
```

**Respuesta:**
```json
{
  "message": "Usuario desbloqueado exitosamente",
  "email": "test2@test.com",
  "active": true,
  "failed_attempts": 0,
  "is_locked": false
}
```

---

### 4. **Recrear un Usuario**

```
POST /debug/recreate_user/<email>/<password>
```

**⚠️ CUIDADO:** Esto eliminará el usuario existente y creará uno nuevo.

**Ejemplo con curl:**
```bash
curl -X POST https://tu-app.onrender.com/debug/recreate_user/test2@test.com/Pruebas1
```

**Respuesta:**
```json
{
  "message": "Usuario recreado exitosamente",
  "email": "test2@test.com",
  "role": "usuario",
  "active": true,
  "created_at": "2025-12-11T12:00:00"
}
```

---

### 5. **Listar Todos los Usuarios**

```
GET /debug/list_users
```

**Ejemplo:**
```bash
https://tu-app.onrender.com/debug/list_users
```

**Respuesta:**
```json
{
  "total_users": 3,
  "users": [
    {
      "email": "admin@example.com",
      "role": "admin",
      "active": true,
      "is_locked": false,
      "failed_attempts": 0,
      "created_at": "2025-12-10T10:00:00",
      "last_login": "2025-12-11T09:00:00"
    },
    {
      "email": "test2@test.com",
      "role": "usuario",
      "active": true,
      "is_locked": false,
      "failed_attempts": 0,
      "created_at": "2025-12-11T10:30:00",
      "last_login": null
    }
  ]
}
```

---

## 🚀 Flujo de Diagnóstico Recomendado

### **Paso 1: Verificar si el Usuario Existe**

```bash
https://tu-app.onrender.com/debug/check_user/test2@test.com
```

**Posibles resultados:**

#### ✅ **Usuario existe y está activo**
```json
{
  "found": true,
  "active": true,
  "is_locked": false,
  "failed_attempts": 0
}
```
→ **Ir al Paso 2**

#### ⚠️ **Usuario existe pero está bloqueado**
```json
{
  "found": true,
  "active": true,
  "is_locked": true,
  "failed_attempts": 5
}
```
→ **Ir al Paso 3 (Desbloquear)**

#### ⚠️ **Usuario existe pero está inactivo**
```json
{
  "found": true,
  "active": false
}
```
→ **Ir al Paso 3 (Desbloquear)**

#### ❌ **Usuario NO existe**
```json
{
  "found": false
}
```
→ **Ir al Paso 4 (Recrear)**

---

### **Paso 2: Probar la Contraseña**

```bash
https://tu-app.onrender.com/debug/test_password/test2@test.com/Pruebas1
```

**Si la contraseña es correcta:**
```json
{
  "is_valid": true,
  "message": "✅ Contraseña correcta"
}
```
→ **El problema puede ser de sesión o cookies. Prueba en modo incógnito.**

**Si la contraseña es incorrecta:**
```json
{
  "is_valid": false,
  "message": "❌ Contraseña incorrecta"
}
```
→ **Ir al Paso 4 (Recrear con contraseña correcta)**

---

### **Paso 3: Desbloquear Usuario**

```bash
curl -X POST https://tu-app.onrender.com/debug/unlock_user/test2@test.com
```

Después de desbloquear, vuelve al **Paso 2** para probar la contraseña.

---

### **Paso 4: Recrear Usuario**

```bash
curl -X POST https://tu-app.onrender.com/debug/recreate_user/test2@test.com/Pruebas1
```

Esto:
1. Elimina el usuario existente (si existe)
2. Crea un usuario nuevo con la contraseña `Pruebas1`
3. El usuario estará activo y desbloqueado

Después de recrear, intenta hacer login normalmente.

---

## 🔍 Casos de Uso Comunes

### **Caso 1: "No puedo hacer login"**

1. Verifica que el usuario existe: `/debug/check_user/tu@email.com`
2. Prueba la contraseña: `/debug/test_password/tu@email.com/TuPassword`
3. Si está bloqueado: `/debug/unlock_user/tu@email.com`
4. Si la contraseña es incorrecta: `/debug/recreate_user/tu@email.com/NuevaPassword`

---

### **Caso 2: "El usuario se creó pero no puedo acceder"**

1. Verifica que existe: `/debug/check_user/tu@email.com`
2. Si `found: false` → El usuario NO se creó correctamente
3. Recréalo: `/debug/recreate_user/tu@email.com/TuPassword`

---

### **Caso 3: "Cuenta bloqueada después de varios intentos"**

1. Verifica el estado: `/debug/check_user/tu@email.com`
2. Si `is_locked: true` → Desbloquear: `/debug/unlock_user/tu@email.com`
3. Intenta login de nuevo

---

## 🛠️ Herramientas para Hacer Peticiones POST

### **Opción 1: curl (Terminal)**

```bash
curl -X POST https://tu-app.onrender.com/debug/unlock_user/test2@test.com
```

### **Opción 2: Postman**

1. Abre Postman
2. Crea una nueva petición POST
3. URL: `https://tu-app.onrender.com/debug/unlock_user/test2@test.com`
4. Envía la petición

### **Opción 3: Extensión de Navegador**

Instala una extensión como:
- **REST Client** (VS Code)
- **Advanced REST Client** (Chrome)
- **RESTer** (Firefox)

### **Opción 4: JavaScript en Consola del Navegador**

```javascript
fetch('https://tu-app.onrender.com/debug/unlock_user/test2@test.com', {
  method: 'POST'
})
.then(r => r.json())
.then(data => console.log(data));
```

---

## ⚠️ ELIMINAR DESPUÉS DE USAR

### **Paso 1: Eliminar el archivo**

```bash
rm app/auth/debug_routes.py
```

### **Paso 2: Eliminar el registro en app.py**

Busca y elimina estas líneas en `app/core/app.py`:

```python
# ⚠️ DEBUG: Registrar blueprint de debug (ELIMINAR EN PRODUCCIÓN)
from app.auth.debug_routes import debug_bp
app.register_blueprint(debug_bp)
logger.warning("⚠️ Blueprint de DEBUG registrado - ELIMINAR EN PRODUCCIÓN")
```

### **Paso 3: Commit y Push**

```bash
git add .
git commit -m "Remove debug endpoints"
git push origin main
```

---

## 📝 Notas de Seguridad

- ⚠️ Estos endpoints **NO tienen autenticación**
- ⚠️ Cualquiera con la URL puede usarlos
- ⚠️ **NUNCA** dejar en producción permanentemente
- ⚠️ Solo usar para diagnóstico temporal
- ⚠️ Eliminar inmediatamente después de resolver el problema

---

**Fecha de creación**: 2025-12-11  
**Propósito**: Diagnóstico temporal de problemas de autenticación  
**Estado**: ⚠️ TEMPORAL - ELIMINAR DESPUÉS DE USAR

