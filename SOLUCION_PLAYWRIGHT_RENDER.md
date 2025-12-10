# 🔧 SOLUCIÓN: Error de Playwright en Render

> **Problema**: "Failed to install browser dependencies - su: Authentication failure"

---

## 🐛 EL PROBLEMA

Playwright intenta instalar dependencias del sistema que requieren permisos de root, pero Render no permite esto en el plan gratuito.

**Error típico**:
```
Installing dependencies...
Switching to root user to install dependencies...
Password: su: Authentication failure
Failed to install browser dependencies
Error: Installation process exited with code: 1
```

---

## ✅ SOLUCIÓN IMPLEMENTADA

He actualizado los archivos de configuración con **2 soluciones alternativas**:

### 🎯 SOLUCIÓN 1: Sin Docker (Más Simple) - **RECOMENDADA**

**Archivos actualizados**:
- ✅ `build.sh` - Instala Playwright sin dependencias del sistema
- ✅ `render.yaml` - Configuración actualizada

**Qué hace**:
- Instala solo el navegador Chromium sin las dependencias del sistema
- Usa la flag `--no-shell` para evitar instalar dependencias extras
- Render ya tiene muchas dependencias pre-instaladas

**Acción requerida**:
1. Hacer commit y push de los cambios:
   ```bash
   git add build.sh render.yaml
   git commit -m "Fix: Solucionar error de Playwright en Render"
   git push origin main
   ```

2. Render re-desplegará automáticamente

---

### 🐳 SOLUCIÓN 2: Con Docker (Más Robusto)

**Archivo creado**:
- ✅ `Dockerfile` - Imagen con dependencias de Playwright pre-instaladas

**Qué hace**:
- Usa imagen oficial de Microsoft con Playwright pre-configurado
- Incluye todas las dependencias necesarias
- Más pesado pero más confiable

**Acción requerida**:
1. En Render, ve a tu Web Service → Settings
2. Cambia el **Build Command** a:
   ```
   docker build -t nexus-ai .
   ```
3. Cambia el **Start Command** a:
   ```
   docker run -p $PORT:$PORT nexus-ai
   ```
4. Guarda y re-despliega

---

## 🚀 OPCIÓN RECOMENDADA: Solución 1 (Sin Docker)

**Es más simple y funciona bien en Render.**

### Pasos a Seguir:

1. **Hacer commit de los cambios**:
   ```bash
   git add .
   git commit -m "Fix: Solucionar error de Playwright en Render"
   git push origin main
   ```

2. **Render re-desplegará automáticamente**
   - Ve a tu Web Service en Render
   - Verás que inicia un nuevo build automáticamente
   - Espera 5-10 minutos

3. **Verificar el build**:
   - Ve a la pestaña "Logs"
   - Deberías ver:
     ```
     ==> Instalando Playwright (solo navegador)...
     Chromium downloaded to ...
     ==> Build completado exitosamente
     ```

---

## 🔍 SI AÚN FALLA

### Opción A: Deshabilitar Playwright Temporalmente

Si necesitas desplegar urgentemente y no necesitas la generación de PDFs:

1. **Comentar la instalación de Playwright en `build.sh`**:
   ```bash
   # echo "==> Instalando Playwright (solo navegador)..."
   # PLAYWRIGHT_BROWSERS_PATH=0 playwright install chromium --no-shell
   ```

2. **Comentar Playwright en `requirements.txt`**:
   ```
   # playwright>=1.40.0
   ```

3. **Modificar el código que usa Playwright** (temporal):
   En `app/core/app.py`, busca el uso de Playwright y añade un try-except:
   ```python
   try:
       from playwright.sync_api import sync_playwright
       PLAYWRIGHT_AVAILABLE = True
   except ImportError:
       PLAYWRIGHT_AVAILABLE = False
   ```

### Opción B: Usar Alternativa a Playwright

Cambiar la generación de PDFs por otra librería más ligera:

1. **Instalar alternativa**:
   ```bash
   pip install weasyprint
   ```

2. **Modificar el código** para usar WeasyPrint en lugar de Playwright

---

## 📊 COMPARACIÓN DE SOLUCIONES

| Solución | Pros | Contras | Recomendado |
|----------|------|---------|-------------|
| **Sin Docker** | ✅ Más rápido<br>✅ Más simple<br>✅ Menos recursos | ⚠️ Puede fallar si faltan deps | ✅ **SÍ** |
| **Con Docker** | ✅ Más robusto<br>✅ Todas las deps incluidas | ❌ Más lento<br>❌ Más complejo | ⚠️ Si falla opción 1 |
| **Sin Playwright** | ✅ Despliegue inmediato | ❌ Sin generación de PDFs | ❌ Solo temporal |

---

## 🎯 VERIFICAR QUE FUNCIONA

Después del re-despliegue:

1. **Verificar logs**:
   ```
   ==> Instalando Playwright (solo navegador)...
   Chromium ... downloaded to /opt/render/.cache/ms-playwright/...
   ==> Build completado exitosamente
   ```

2. **Probar la aplicación**:
   - Accede a tu URL
   - Genera una historia de usuario
   - Si necesitas PDF, intenta generarlo

3. **Si hay error al generar PDF**:
   - Revisa los logs de la aplicación
   - Puede que necesites ajustar el código de Playwright

---

## 🔧 AJUSTES ADICIONALES (Si es necesario)

### Aumentar Timeout en Render

Si el build tarda mucho:

1. Ve a Settings → Build & Deploy
2. Aumenta el **Build Timeout** a 20 minutos

### Variables de Entorno Adicionales

Agrega estas variables en Render:

```env
PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
```

---

## 📝 RESUMEN

**Problema**: Playwright necesita permisos de root en Render

**Solución**: Instalar solo el navegador sin dependencias del sistema

**Acción**:
1. ✅ Archivos ya actualizados (`build.sh`, `render.yaml`)
2. ✅ Hacer commit y push
3. ✅ Render re-desplegará automáticamente
4. ✅ Verificar logs

---

## 🆘 SI NADA FUNCIONA

### Plan B: Desplegar sin Playwright

1. Comentar Playwright en `requirements.txt`
2. Comentar instalación en `build.sh`
3. Modificar código para no usar Playwright
4. Usar alternativa como WeasyPrint o reportlab

### Contactar Soporte

Si el problema persiste:
- 📧 Render Support: support@render.com
- 💬 Render Community: https://community.render.com/
- 🔍 Buscar "playwright render" en el foro

---

## ✅ CHECKLIST

- [ ] Archivos actualizados (`build.sh`, `render.yaml`)
- [ ] Commit y push realizados
- [ ] Render re-desplegando automáticamente
- [ ] Logs verificados (sin errores de Playwright)
- [ ] Build completado exitosamente
- [ ] Aplicación accesible
- [ ] Funcionalidades probadas

---

**¡Con estos cambios, el despliegue debería funcionar!** 🚀

*Última actualización: Diciembre 2025*

