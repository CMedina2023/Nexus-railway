# 🛠️ PATRONES DE DESARROLLO Y REGLAS PARA AGENTES - NEXUS AI

> **Propósito**: Este documento es la "Constitución Técnica" de Nexus AI. Define reglas estrictas y detalladas que cualquier desarrollador (humano o AGENTE AI) debe seguir sin excepción para asegurar la integridad, seguridad y escalabilidad del sistema.

**Versión**: 3.0 (Detallada)  
**Última actualización**: 2025-12-21

---

## 📋 REGLAS GENERALES PARA EL AGENTE
1. **No asumas, valida**: Antes de modificar código, lee los docstrings y las interfaces de los servicios existentes.
2. **Proactividad controlada**: Si detectas una brecha de seguridad (ej. falta de sanitización), corrígela e infórmalo.
3. **Preservación de Estilo**: No mezcles `camelCase` con `snake_case` en el mismo lenguaje (Python: snake, JS: camel).
4. **Documentación Obligatoria**: Cada nueva función DEBE incluir docstring en formato Google Style.

---

## 1. 📐 ARQUITECTURA DETALLADA (SOLID & PATTERNS)

### Principios de Implementación de Código
Cualquier fragmento de código debe pasar la prueba "SOLID":

*   **SRP (Single Responsibility)**: Las funciones no deben superar las 25 líneas. Si una función hace "A y luego B", debe dividirse en `_process_A()` y `_process_B()`.
*   **DIP (Dependency Inversion)**: NUNCA instancies clases pesadas dentro de un constructor. Usa inyección.
    ```python
    # ✅ REGLA: Inyección de Dependencias
    class JiraReporter:
        def __init__(self, api_client: JiraClientProtocol): # Usa Protocolos o ABCs
            self.client = api_client
    ```

### Patrones Obligatorios
*   **Factory**: Usa fábricas para instanciar generadores AI según el modelo (Gemini, OpenAI, etc.).
*   **Strategy**: Si el algoritmo de extracción de datos varía según el tipo de archivo (PDF, CSV), implementa una `ExtractionStrategy`.

---

## 2. 🛡️ SEGURIDAD TÉCNICA (BASADO EN OWASP WSTG v4.2)

El Agente debe aplicar estas reglas en cada commit:

### A. Prevención de Inyección (WSTG-INPV)
*   **Prohibido**: `f"SELECT * FROM users WHERE id = {user_id}"`.
*   **Obligatorio**: Uso de parámetros vinculados o SQLAlchemy ORM.
*   **Sanitización JS**: En el frontend, usa `textContent` en lugar de `innerHTML` para datos que provienen del usuario.

### B. Gestión de Secretos y Configuración (WSTG-CONF)
*   **Regla de Oro**: NUNCA hardcodees credenciales.
*   **Validación**: Antes de subir código, el Agente debe verificar que no existan strings que parezcan API Keys (`sk-...`, `AIza...`).
*   **Entorno**: Usa la clase `Config` centralizada en `app/core/config.py`.

### C. Headers de Seguridad
Cada respuesta de API debe incluir:
*   `X-Content-Type-Options: nosniff`
*   `X-Frame-Options: DENY` (Previene Clickjacking)
*   `Content-Security-Policy`: Restringir a dominios conocidos.

---

## 3. 🏗️ ESTRUCTURA DE MICROSERVICIOS (ANTIMONOLITO)

Nexus AI opera bajo una filosofía de **Soberanía de Servicio**:

### Reglas para Nuevos Módulos:
1.  **Aislamiento de Datos**: Un servicio NO puede leer la base de datos de otro. Debe solicitar los datos vía API REST.
2.  **Stateless**: Los servicios no deben guardar estado local. Usa Redis o la DB para persistencia.
3.  **Contratos API**: Antes de implementar la lógica, define el esquema JSON (Request/Response).
4.  **Estructura de Carpeta por Servicio**:
    ```text
    /services/nombre-servicio/
    ├── domain/         # Modelos y lógica pura
    ├── infrastructure/ # Conexiones externas, DB, APIs
    ├── application/    # Casos de uso y orquestación
    └── api/            # Endpoints y Serializadores
    ```

---

## 4. ✅ BUENAS PRÁCTICAS DE DESARROLLO (DETALLE TÉCNICO)

### Nomenclatura Estricta
*   **Clases**: `PascalCase` (ej. `DocumentProcessor`).
*   **Variables/Funciones Python**: `snake_case` (ej. `get_user_data`).
*   **Variables/Funciones JS**: `camelCase` (ej. `handleFileUpload`).
*   **Archivos**: `snake_case` (ej. `auth_middleware.py`).

### Manejo de Errores (Error Handling)
*   **No usar Try-Except Genérico**: `except Exception:` está prohibido a menos que se haga re-raise o logging crítico.
*   **Custom Exceptions**: Define excepciones en `app/utils/exceptions.py`.
    ```python
    class NexusSecurityError(Exception):
        """Error específico para violaciones de reglas de seguridad"""
    ```

### Logging y Trazabilidad
*   Cada log debe incluir un `correlation_id` para seguir la traza entre microservicios.
*   Log Levels:
    *   `DEBUG`: Variables internas, payloads de entrada.
    *   `INFO`: Inicio/Fin de procesos importantes.
    *   `ERROR`: Fallos controlados que requieren atención.

### Checklist para el Agente AI antes de entregar:
- [ ] ¿He aplicado `type hints` en todas las firmas de funciones?
- [ ] ¿He verificado que no hay lógica de negocio en el archivo `app.py` (debe estar en `/services`)?
- [ ] ¿He añadido un test unitario básico para la lógica nueva?
- [ ] ¿He sanitizado los inputs que vienen del cliente?
- [ ] ¿El código es legible para un humano sin necesidad de comentarios excesivos?

---

**Cualquier desviación de estas reglas será considerada un "Bug de Arquitectura" y debe ser corregida prioritariamente.**
