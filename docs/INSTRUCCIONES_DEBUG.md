# 🔧 Instrucciones Rápidas - Debug de Usuario

## 🎯 Tu Problema

No puedes acceder con `test2@test.com` y contraseña `Pruebas1`, aunque el usuario está registrado.

---

## ✅ Solución Rápida

### **Paso 1: Hacer Deploy**

```bash
git add .
git commit -m "Add: Endpoints de debug temporal para diagnóstico"
git push origin main
```

Espera 2-3 minutos a que Render despliegue.

---

### **Paso 2: Verificar que el Usuario Existe**

Abre en tu navegador:

```
https://nexus-ai-XXXXX.onrender.com/debug/check_user/test2@test.com
```

(Reemplaza `XXXXX` con tu URL de Render)

**Posibles resultados:**

#### ✅ Si ves esto:
```json
{
  "found": true,
  "active": true,
  "is_locked": false
}
```
→ **Ir al Paso 3**

#### ❌ Si ves esto:
```json
{
  "found": false
}
```
→ **Ir al Paso 4**

---

### **Paso 3: Probar la Contraseña**

Abre en tu navegador:

```
https://nexus-ai-XXXXX.onrender.com/debug/test_password/test2@test.com/Pruebas1
```

#### ✅ Si dice `"is_valid": true`
→ El problema es de sesión/cookies. **Prueba login en modo incógnito**.

#### ❌ Si dice `"is_valid": false`
→ La contraseña guardada es incorrecta. **Ir al Paso 4**.

---

### **Paso 4: Recrear el Usuario**

**Opción A: Con curl (si tienes terminal)**

```bash
curl -X POST https://nexus-ai-XXXXX.onrender.com/debug/recreate_user/test2@test.com/Pruebas1
```

**Opción B: Con JavaScript en consola del navegador**

1. Abre la consola del navegador (F12)
2. Pega esto y presiona Enter:

```javascript
fetch('https://nexus-ai-XXXXX.onrender.com/debug/recreate_user/test2@test.com/Pruebas1', {
  method: 'POST'
})
.then(r => r.json())
.then(data => console.log(data));
```

**Opción C: Con Postman**

1. Abre Postman
2. Crea petición POST
3. URL: `https://nexus-ai-XXXXX.onrender.com/debug/recreate_user/test2@test.com/Pruebas1`
4. Envía

---

### **Paso 5: Probar Login**

1. Ve a tu app: `https://nexus-ai-XXXXX.onrender.com/auth/login`
2. Email: `test2@test.com`
3. Contraseña: `Pruebas1`
4. **Usa modo incógnito** para evitar autocomplete

---

## 🔍 Si Aún No Funciona

### **Ver Todos los Usuarios**

```
https://nexus-ai-XXXXX.onrender.com/debug/list_users
```

Esto te mostrará todos los usuarios en la base de datos.

---

## ⚠️ IMPORTANTE: Eliminar Después

Una vez que resuelvas el problema, **DEBES eliminar** estos endpoints:

1. Elimina `app/auth/debug_routes.py`
2. Elimina las líneas de registro en `app/core/app.py`
3. Haz commit y push

---

## 📞 Resumen de URLs

Reemplaza `XXXXX` con tu URL de Render:

1. **Verificar usuario**: `/debug/check_user/test2@test.com`
2. **Probar contraseña**: `/debug/test_password/test2@test.com/Pruebas1`
3. **Recrear usuario**: `/debug/recreate_user/test2@test.com/Pruebas1` (POST)
4. **Listar usuarios**: `/debug/list_users`

---

**Fecha**: 2025-12-11  
**Propósito**: Diagnóstico rápido de problema de login

