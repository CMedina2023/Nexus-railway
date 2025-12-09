# Tests - Nexus AI

## 📋 Descripción

Este directorio contiene los tests unitarios del proyecto. Los tests están organizados siguiendo la estructura del proyecto principal.

## 🏗️ Estructura

```
tests/
├── __init__.py
├── test_routes_protection.py      # Tests de protección de rutas
├── test_complete_auth_system.py   # Tests completos del sistema de autenticación
├── test_login.py                  # Tests de login
├── run_all_tests.py               # Script para ejecutar todos los tests
└── run_tests.py                   # Script helper para tests de rutas
```

## 🚀 Ejecutar Tests

### Prerequisitos

1. **Activar el entorno virtual:**
   ```powershell
   # En PowerShell
   .venv\Scripts\Activate.ps1
   
   # O en CMD
   .venv\Scripts\activate.bat
   ```

2. **Verificar que Flask está instalado:**
   ```bash
   pip list | findstr Flask
   ```

### Opción 1: Ejecutar todos los tests

```bash
python tests/run_all_tests.py
```

### Opción 2: Tests de protección de rutas

```bash
python -m unittest tests.test_routes_protection -v
```

### Opción 3: Tests completos del sistema

```bash
python -m unittest tests.test_complete_auth_system -v
```

### Opción 4: Usando el script helper

```bash
python tests/run_tests.py
```

### Opción 5: Ejecutar todos los tests con unittest

```bash
python -m unittest discover tests -v
```

## 📊 Qué Verificar

Los tests verifican:

✅ **Rutas protegidas requieren autenticación:**
- `/` → Redirige a `/auth/login` (302)
- `/agent` → Redirige a `/auth/login` (302)
- `/api/*` → Retorna 401 (No autenticado)

✅ **Rutas públicas son accesibles:**
- `/auth/login` → 200 (OK)
- `/auth/register` → 200 (OK)
- `/infografia` → 200 (OK)

✅ **Rutas funcionan con autenticación:**
- Usuario autenticado puede acceder a rutas protegidas

✅ **Panel de administración:**
- Requiere rol de admin
- Usuarios normales reciben 403

✅ **Gestión de perfil:**
- Cambio de contraseña funciona
- Validaciones de contraseña funcionan

## ⚠️ Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'flask'"
**Solución:** Activa el entorno virtual primero:
```powershell
.venv\Scripts\Activate.ps1
```

### Error: "No module named 'app'"
**Solución:** Asegúrate de estar en el directorio raíz del proyecto:
```bash
cd D:\Proyectos_python\Proyectos_AI\Agenteai2
```

### Error: "Database is locked"
**Solución:** Cierra cualquier conexión a la base de datos y vuelve a ejecutar los tests.

## 📝 Escribir Nuevos Tests

Al agregar nueva funcionalidad, asegúrate de:

1. ✅ Crear tests correspondientes
2. ✅ Seguir el patrón de nomenclatura `test_*.py`
3. ✅ Usar docstrings descriptivos
4. ✅ Testear casos exitosos y casos de error
5. ✅ Mantener cobertura > 80%

## 📝 Notas

- Los tests crean una base de datos temporal para pruebas
- Los tests deshabilitan CSRF para facilitar las pruebas
- Cada test se ejecuta en un contexto aislado

## 📚 Recursos

- [unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)
