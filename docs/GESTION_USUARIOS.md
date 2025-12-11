# 📋 Gestión de Usuarios - Comandos Básicos

> **Guía completa para la gestión de usuarios en Nexus AI**
>
> **Última actualización**: Diciembre 2025
> **Versión**: 1.0

---

## 📋 TABLA DE CONTENIDOS

1. [Información General](#información-general)
2. [Crear Usuarios](#crear-usuarios)
3. [Modificar Usuarios](#modificar-usuarios)
4. [Eliminar Usuarios](#eliminar-usuarios)
5. [Consultar Usuarios](#consultar-usuarios)
6. [Scripts de Utilidad](#scripts-de-utilidad)

---

## ℹ️ INFORMACIÓN GENERAL

### Sistema de Usuarios
- **Tabla**: `users`
- **Roles válidos**: `admin`, `usuario`, `analista_qa`
- **Hash de contraseña**: bcrypt (12 rondas)
- **Campos requeridos**: `id` (UUID), `email`, `password_hash`, `role`

### Requisitos de Contraseña
- Mínimo 8 caracteres
- Al menos una mayúscula
- Al menos una minúscula
- Al menos un número

---

## 👤 CREAR USUARIOS

### Usando SQL Directo (DBeaver/PostgreSQL)

#### Usuario Regular
```sql
INSERT INTO users (
    id,
    email,
    password_hash,
    role,
    active,
    failed_login_attempts,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'usuario@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj9.3CXzWJae',
    'usuario',
    true,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

#### Usuario Administrador
```sql
INSERT INTO users (
    id,
    email,
    password_hash,
    role,
    active,
    failed_login_attempts,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'admin@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj9.3CXzWJae',
    'admin',
    true,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

#### Analista QA
```sql
INSERT INTO users (
    id,
    email,
    password_hash,
    role,
    active,
    failed_login_attempts,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'analista@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj9.3CXzWJae',
    'analista_qa',
    true,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

### Usando Scripts de Python

#### Crear Usuario con Script Interactivo
```bash
# Ejecutar el script de inicialización (crea admin)
python scripts/init_auth.py

# Crear usuario manualmente
python -c "
from app.auth.user_service import UserService
service = UserService()
user = service.create_user('email@example.com', 'Password123!', 'usuario')
print(f'Usuario creado: {user.email}')
"
```

#### Crear Administrador
```bash
# Usar el script make_admin para convertir usuario existente
python scripts/make_admin.py usuario@example.com
```

---

## ✏️ MODIFICAR USUARIOS

### Cambiar Rol de Usuario

#### Usando SQL
```sql
-- Cambiar a administrador
UPDATE users
SET role = 'admin', updated_at = CURRENT_TIMESTAMP
WHERE email = 'usuario@example.com';

-- Cambiar a analista QA
UPDATE users
SET role = 'analista_qa', updated_at = CURRENT_TIMESTAMP
WHERE email = 'usuario@example.com';

-- Cambiar a usuario regular
UPDATE users
SET role = 'usuario', updated_at = CURRENT_TIMESTAMP
WHERE email = 'admin@example.com';
```

#### Usando Scripts de Python
```bash
# Usar el script make_admin
python scripts/make_admin.py usuario@example.com

# Cambiar rol manualmente
python -c "
from app.auth.user_service import UserService
service = UserService()
user = service.update_user_role('user-id-aqui', 'admin', 'admin-id')
print(f'Rol actualizado: {user.email} -> {user.role}')
"
```

### Cambiar Email
```sql
UPDATE users
SET email = 'nuevo_email@example.com', updated_at = CURRENT_TIMESTAMP
WHERE id = 'user-id-aqui';
```

### Resetear Intentos de Login Fallidos
```sql
UPDATE users
SET failed_login_attempts = 0, locked_until = NULL, updated_at = CURRENT_TIMESTAMP
WHERE email = 'usuario@example.com';
```

### Cambiar Contraseña
```sql
-- Generar nuevo hash primero
-- SELECT crypt('NuevaPassword123!', gen_salt('bf', 12));

UPDATE users
SET password_hash = '$2b$12$nuevo_hash_aqui', updated_at = CURRENT_TIMESTAMP
WHERE email = 'usuario@example.com';
```

---

## 🗑️ ELIMINAR USUARIOS

> **⚠️ IMPORTANTE**: Este sistema usa "soft delete" (desactivación) en lugar de eliminación física por razones de auditoría.

### Desactivar Usuario (Soft Delete)
```sql
-- Desactivar usuario
UPDATE users
SET active = false, updated_at = CURRENT_TIMESTAMP
WHERE email = 'usuario@example.com';
```

### Activar Usuario
```sql
-- Reactivar usuario
UPDATE users
SET active = true, updated_at = CURRENT_TIMESTAMP
WHERE email = 'usuario@example.com';
```

### Eliminación Física (Solo en desarrollo/emergencias)
```sql
-- ⚠️ PELIGROSO: Solo usar en desarrollo o emergencias
DELETE FROM users WHERE email = 'usuario@example.com';
```

#### Usando Scripts de Python
```bash
# Desactivar usuario
python -c "
from app.auth.user_service import UserService
service = UserService()
user = service.deactivate_user('user-id-aqui')
print(f'Usuario desactivado: {user.email}')
"

# Activar usuario
python -c "
from app.auth.user_service import UserService
service = UserService()
user = service.activate_user('user-id-aqui')
print(f'Usuario activado: {user.email}')
"
```

---

## 👁️ CONSULTAR USUARIOS

### Ver Todos los Usuarios
```sql
SELECT
    id,
    email,
    role,
    active,
    failed_login_attempts,
    last_login,
    created_at,
    updated_at
FROM users
ORDER BY created_at DESC;
```

### Ver Usuarios por Rol
```sql
-- Administradores activos
SELECT email, TO_CHAR(created_at, 'YYYY-MM-DD') as creado
FROM users
WHERE role = 'admin' AND active = true;

-- Todos los usuarios por rol
SELECT role, COUNT(*) as cantidad
FROM users
WHERE active = true
GROUP BY role;
```

### Ver Usuarios con Problemas
```sql
-- Usuarios bloqueados
SELECT email, failed_login_attempts, locked_until
FROM users
WHERE locked_until IS NOT NULL AND locked_until > CURRENT_TIMESTAMP;

-- Usuarios inactivos
SELECT email, role, TO_CHAR(created_at, 'YYYY-MM-DD') as creado
FROM users
WHERE active = false;
```

### Usando Scripts de Python
```bash
# Listar todos los usuarios
python scripts/make_admin.py --list

# Ver usuarios desde código
python -c "
from app.auth.user_service import UserService
service = UserService()
users = service.get_all_users()
for user in users:
    print(f'{user.email} - {user.role} - {\"Activo\" if user.active else \"Inactivo\"}')
"
```

---

## 🔧 SCRIPTS DE UTILIDAD

### Generar Hash de Contraseña
```sql
-- Generar hash bcrypt (12 rondas)
SELECT crypt('TuContraseña123!', gen_salt('bf', 12));
```

### Verificar Estado de la Base de Datos
```sql
-- Contar usuarios totales
SELECT COUNT(*) as total_usuarios FROM users;

-- Verificar administradores
SELECT COUNT(*) as administradores_activos
FROM users
WHERE role = 'admin' AND active = true;
```

### Backup de Usuarios (para migraciones)
```sql
-- Crear backup de usuarios
CREATE TABLE users_backup AS
SELECT * FROM users WHERE active = true;
```

---

## 🚨 NOTAS DE SEGURIDAD

### ✅ RECOMENDACIONES
- **Nunca** almacenes contraseñas en texto plano
- **Siempre** usa hashes bcrypt con 12+ rondas
- **Audita** cambios de roles y desactivaciones
- **Monitorea** intentos de login fallidos

### ❌ EVITAR
- Modificar directamente los hashes de contraseña
- Eliminar usuarios sin auditoría
- Crear usuarios sin validación de email
- Usar roles personalizados no definidos

---

## 📞 SOPORTE

Si tienes problemas con la gestión de usuarios:

1. Verifica la conexión a PostgreSQL
2. Revisa los logs de la aplicación
3. Usa las consultas de verificación
4. Contacta al administrador del sistema

---

*Esta guía es específica para el sistema Nexus AI con PostgreSQL y Render.*