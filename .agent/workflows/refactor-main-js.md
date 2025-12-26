---
description: Plan de Refactorización Quirúrgica de main.js (9,217 líneas)
---

# 📋 Refactorización Quirúrgica de `static/js/main.js`

## 🎯 Manifiesto: "Opción B - Refactorización Quirúrgica (Strangler Pattern)"

En lugar de intentar una refactorización masiva y teórica, adoptamos un enfoque de **encapsulación progresiva** y **refactorización bajo demanda**. El objetivo principal es la **estabilidad del sistema** mientras se mejora la calidad del código conforme se trabaja en él.

### 🛡️ Principios Fundamentales
1. **Encapsulación Hacia Adentro**: No usamos Proxies ni inyectamos getters/setters complejos en `window`. Si `main.js` necesita una variable global (ej. `myChart`), la variable permanece físicamente en `main.js` para evitar colisiones.
2. **Inyección de Dependencias Explícita**: Los nuevos módulos no buscan cosas en `window`. Las funciones reciben lo que necesitan como argumentos (ej. `ChartModule.update(myChart, data)`).
3. **Refactorización "Just-in-Time" (Bajo Demanda)**: No refactorizamos "porque sí". Solo modularizamos una sección de `main.js` cuando necesitemos realizar una nueva tarea, mejora o corrección en esa funcionalidad específica.
4. **Strangler Pattern**: Vamos "estrangulando" el monolito pieza por pieza. Cada éxito en un módulo nuevo reduce el tamaño y la complejidad de `main.js` de forma segura.

---

## 🏗️ Arquitectura de Módulos (Target)

Mantenemos la estructura de carpetas pero el flujo de trabajo es dinámico:

```
static/js/
├── core/
│   ├── utils.js              # pendiente: Utilidades globales
│   ├── navigation.js         # pendiente: Navegación SPA
│   └── api-client.js         # Pendiente: Cliente HTTP
├── modules/
│   ├── dashboard/            # Bajo demanda
│   ├── generators/           # Bajo demanda
│   └── jira/                 # Bajo demanda
└── main.js                   # Monolito disminuyendo progresivamente
```

---

## ✅ PROGRESO REALIZADO

### FASE 1: Utilidades Core (2025-12-23)
- **Estado**: ✅ COMPLETADA
- **Logro**: Extracción de `getCsrfToken`, `getCookie` y sistema de notificaciones toast.
- **Técnica**: IIFE con exportación controlada a `window`.
- **Impacto**: Cero regresiones detectadas.

### FASE 2: Sistema de Navegación (2025-12-23)
- **Estado**: ✅ COMPLETADA
- **Logro**: Extracción de `navigateToSection` y lógica de ruteo SPA.
- **Impacto**: Mejoró la carga inicial y la organización del ruteo.

---

## 📝 Lecciones Aprendidas (Crucial)

### ❌ Lo que NO funcionó (Intento de Fase 3)
- **Variables Globales Compartidas**: Intentar mover variables de instancia de charts a un módulo y usar `Object.defineProperty` en `window` para que `main.js` "creyera" que siguen ahí. Esto rompió la sincronización y la visibilidad de los datos.
- **Refactorización masiva sin contexto**: Mover código de gráficos cuando no se estaba trabajando en gráficos causó errores difíciles de rastrear.

### ✅ Lo que SÍ funciona
- **Scripts en orden**: Cargar módulos core antes de `main.js` en `index.html`.
- **IIFE (Immediately Invoked Function Expression)**: Protege el scope interno del módulo mientras expone solo lo necesario.
- **Pasar el objeto como parámetro**: Si una función de `main.js` usa un canvas, el módulo debe recibir el canvas, no adivinar dónde está.

---

## 🚀 Metodología de Trabajo "Bajo Demanda"

Cuando se asigne una TAREA en una sección específica (ej. "Mejorar carga masiva"):

1. **Aislar**: Identificar el bloque de código en `main.js` que maneja esa tarea.
2. **Extraer**: Mover la lógica pesada (no la declaración de variables globales) a un nuevo archivo en `static/js/modules/...`.
3. **Modularizar**: Convertir la lógica en funciones puras que reciban sus dependencias.
4. **Vincular**: Reemplazar la lógica en `main.js` con llamadas al nuevo módulo.
5. **Verificar**: Probar la tarea original y asegurar que la modularización no introdujo errores.

---

**Última Actualización**: 2025-12-23 12:50  
**Estado Actual**: Estable con Fases 1-2 operativas. Adoptando enfoque Quirúrgico para el futuro.