# 🔐 GENERAR CLAVES SECRETAS PARA RENDER

Este documento te ayuda a generar las claves secretas necesarias para desplegar en Render.

---

## 📋 Claves que Necesitas

1. **SECRET_KEY** - Para sesiones de Flask
2. **ENCRYPTION_KEY** - Para encriptar tokens de Jira

---

## 🐍 MÉTODO 1: Usando Python (Recomendado)

### Paso 1: Abrir Python

En tu terminal o PowerShell, ejecuta:

```bash
python
```

### Paso 2: Generar SECRET_KEY

Copia y pega este código:

```python
import secrets
print("SECRET_KEY:")
print(secrets.token_hex(32))
```

**Copia el resultado** (será algo como: `a1b2c3d4e5f6...`)

### Paso 3: Generar ENCRYPTION_KEY

Copia y pega este código:

```python
from cryptography.fernet import Fernet
print("\nENCRYPTION_KEY:")
print(Fernet.generate_key().decode())
```

**Copia el resultado** (será algo como: `AbCdEf1234...=`)

### Paso 4: Salir de Python

```python
exit()
```

---

## 💻 MÉTODO 2: Script Completo

Crea un archivo `generar_claves.py` con este contenido:

```python
"""
Script para generar claves secretas para Nexus AI
"""
import secrets
from cryptography.fernet import Fernet

print("=" * 60)
print("GENERADOR DE CLAVES SECRETAS - NEXUS AI")
print("=" * 60)
print()

# Generar SECRET_KEY
secret_key = secrets.token_hex(32)
print("SECRET_KEY (para Flask):")
print(secret_key)
print()

# Generar ENCRYPTION_KEY
encryption_key = Fernet.generate_key().decode()
print("ENCRYPTION_KEY (para encriptar tokens):")
print(encryption_key)
print()

print("=" * 60)
print("INSTRUCCIONES:")
print("=" * 60)
print("1. Copia estas claves")
print("2. Ve a Render → Tu Web Service → Environment")
print("3. Agrega estas variables:")
print("   - SECRET_KEY = [primera clave]")
print("   - ENCRYPTION_KEY = [segunda clave]")
print()
print("⚠️  IMPORTANTE: Guarda estas claves en un lugar seguro")
print("⚠️  NO las compartas ni las subas a GitHub")
print("=" * 60)
```

Luego ejecuta:

```bash
python generar_claves.py
```

---

## 📝 MÉTODO 3: Online (Si no tienes Python)

### Para SECRET_KEY:

1. Ve a: https://www.random.org/strings/
2. Configura:
   - **Number of strings**: 1
   - **Length**: 64
   - **Characters**: Hexadecimal
3. Click en **"Get Strings"**
4. Copia el resultado

### Para ENCRYPTION_KEY:

1. Ve a: https://generate-random.org/encryption-key-generator
2. Selecciona: **Fernet (256-bit)**
3. Click en **"Generate"**
4. Copia el resultado

---

## ✅ VERIFICAR LAS CLAVES

### SECRET_KEY debe:
- ✅ Tener al menos 64 caracteres
- ✅ Contener solo letras (a-f) y números (0-9)
- ✅ Ser completamente aleatoria

**Ejemplo válido**:
```
a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

### ENCRYPTION_KEY debe:
- ✅ Terminar en `=` o `==`
- ✅ Contener letras mayúsculas, minúsculas, números y símbolos
- ✅ Tener exactamente 44 caracteres

**Ejemplo válido**:
```
AbCdEfGhIjKlMnOpQrStUvWxYz0123456789+/=
```

---

## 🚨 SEGURIDAD

### ⚠️ NUNCA:
- ❌ Subas estas claves a GitHub
- ❌ Las compartas por email o chat sin encriptar
- ❌ Las incluyas en el código fuente
- ❌ Uses claves de ejemplo o de prueba en producción

### ✅ SIEMPRE:
- ✅ Genera claves nuevas para cada entorno (desarrollo, producción)
- ✅ Guárdalas en un gestor de contraseñas (1Password, LastPass, etc.)
- ✅ Úsalas solo como variables de entorno
- ✅ Regenera las claves si crees que fueron comprometidas

---

## 🔄 REGENERAR CLAVES

Si necesitas regenerar las claves (por ejemplo, si fueron comprometidas):

1. Genera nuevas claves usando cualquiera de los métodos anteriores
2. Actualiza las variables de entorno en Render
3. Re-despliega la aplicación
4. **IMPORTANTE**: Todos los usuarios tendrán que volver a iniciar sesión

---

## 📞 SOPORTE

Si tienes problemas generando las claves:

1. Verifica que tienes Python instalado: `python --version`
2. Verifica que tienes cryptography instalado: `pip install cryptography`
3. Si usas Windows, puede que necesites: `py` en lugar de `python`

---

## 📋 CHECKLIST

Antes de desplegar en Render:

- [ ] SECRET_KEY generada (64+ caracteres)
- [ ] ENCRYPTION_KEY generada (44 caracteres, termina en =)
- [ ] Claves guardadas en lugar seguro
- [ ] Claves NO están en el código fuente
- [ ] Claves NO están en GitHub
- [ ] Listo para configurar en Render

---

*Última actualización: Diciembre 2025*

