# Checklist de Despliegue - SmartMarket AI

## Pre-Despliegue

### 1. Código Listo
- [ ] Todo el código está commiteado en Git
- [ ] No hay console.log en producción
- [ ] No hay credenciales hardcodeadas
- [ ] `.gitignore` incluye archivos sensibles

### 2. Variables de Entorno Preparadas

#### Backend
- [ ] `DATABASE_URL` - URL de PostgreSQL
- [ ] `ALLOWED_ORIGINS` - Dominio del frontend
- [ ] `SECRET_KEY` - Clave secreta para JWT (mínimo 32 caracteres)
- [ ] `PORT` - Puerto del servidor (opcional, Railway/Render lo proveen)

#### Frontend
- [ ] `NEXT_PUBLIC_API_URL` - URL del backend desplegado

### 3. Base de Datos
- [ ] PostgreSQL database creada en Railway/Render
- [ ] `DATABASE_URL` copiada y guardada

---

## Despliegue del Backend

### Railway

1. **Crear Proyecto**
   - [ ] Ir a railway.app
   - [ ] New Project → Deploy from GitHub repo
   - [ ] Seleccionar repositorio

2. **Configurar Servicio**
   - [ ] Railway detecta Python automáticamente
   - [ ] Agregar PostgreSQL desde "New" → Database → PostgreSQL
   - [ ] Railway conecta automáticamente `DATABASE_URL`

3. **Variables de Entorno**
   - [ ] Ir a Variables
   - [ ] Agregar `ALLOWED_ORIGINS` con el dominio de Vercel
   - [ ] Agregar `SECRET_KEY` (generar con: `openssl rand -hex 32`)
   - [ ] Agregar `PORT=8000`

4. **Configurar Build**
   - [ ] Root Directory: `backend`
   - [ ] Build Command: `pip install -r requirements.txt`
   - [ ] Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

5. **Deploy**
   - [ ] Railway despliega automáticamente
   - [ ] Copiar URL generada (ej: `https://smartmarket-production.up.railway.app`)

6. **Verificar**
   - [ ] Visitar `https://tu-url.railway.app/health`
   - [ ] Visitar `https://tu-url.railway.app/api/db-status`
   - [ ] Verificar que todas las tablas existan

### Render (Alternativa)

1. **Crear Web Service**
   - [ ] Ir a render.com
   - [ ] New → Web Service
   - [ ] Conectar repositorio

2. **Configuración**
   - [ ] Name: `smartmarket-backend`
   - [ ] Root Directory: `backend`
   - [ ] Environment: Python 3
   - [ ] Build Command: `pip install -r requirements.txt`
   - [ ] Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Agregar PostgreSQL**
   - [ ] New → PostgreSQL
   - [ ] Copiar Internal Database URL
   - [ ] Agregar como variable `DATABASE_URL` en el Web Service

4. **Variables de Entorno**
   - [ ] `DATABASE_URL` (de PostgreSQL)
   - [ ] `ALLOWED_ORIGINS`
   - [ ] `SECRET_KEY`
   - [ ] `PYTHON_VERSION=3.11.0`

5. **Deploy y Verificar**
   - [ ] Render despliega automáticamente
   - [ ] Verificar endpoints de health y db-status

---

## Despliegue del Frontend

### Vercel

1. **Importar Proyecto**
   - [ ] Ir a vercel.com
   - [ ] New Project → Import Git Repository
   - [ ] Seleccionar repositorio

2. **Configurar Proyecto**
   - [ ] Framework Preset: Next.js (detectado automáticamente)
   - [ ] Root Directory: `.` (raíz)
   - [ ] Build Command: `npm run build` (default)
   - [ ] Output Directory: `.next` (default)

3. **Variables de Entorno**
   - [ ] Agregar `NEXT_PUBLIC_API_URL`
   - [ ] Valor: URL del backend de Railway/Render
   - [ ] Ejemplo: `https://smartmarket-production.up.railway.app`

4. **Deploy**
   - [ ] Click "Deploy"
   - [ ] Esperar a que termine el build
   - [ ] Vercel genera URL (ej: `https://smartmarket-ai.vercel.app`)

5. **Actualizar CORS en Backend**
   - [ ] Ir a Railway/Render
   - [ ] Actualizar `ALLOWED_ORIGINS` con la URL de Vercel
   - [ ] Ejemplo: `https://smartmarket-ai.vercel.app`
   - [ ] El backend se redesplegará automáticamente

---

## Post-Despliegue

### 1. Verificación Completa

#### Backend
- [ ] `https://tu-backend.com/health` retorna `{"status": "healthy"}`
- [ ] `https://tu-backend.com/api/db-status` muestra todas las tablas
- [ ] `https://tu-backend.com/docs` muestra Swagger UI

#### Frontend
- [ ] La página principal carga correctamente
- [ ] El indicador de backend muestra "Online"
- [ ] Puedes crear una cuenta de prueba
- [ ] Puedes hacer login
- [ ] Puedes buscar un producto
- [ ] El análisis funciona correctamente

### 2. Pruebas de Funcionalidad

- [ ] **Registro**: Crear cuenta nueva
- [ ] **Login**: Iniciar sesión con cuenta creada
- [ ] **Búsqueda por URL**: Analizar producto con URL
- [ ] **Búsqueda por nombre**: Buscar "iphone 16"
- [ ] **Análisis**: Ver resultados con gráficos
- [ ] **Historial**: Ver análisis recientes
- [ ] **Eliminar**: Borrar un análisis
- [ ] **Logout**: Cerrar sesión

### 3. Monitoreo

#### Railway
- [ ] Configurar alertas de uptime
- [ ] Revisar logs en tiempo real
- [ ] Configurar métricas de uso

#### Vercel
- [ ] Revisar Analytics
- [ ] Configurar notificaciones de deploy
- [ ] Revisar logs de errores

### 4. Optimizaciones Opcionales

- [ ] Configurar dominio personalizado en Vercel
- [ ] Configurar CDN para assets estáticos
- [ ] Habilitar compresión gzip
- [ ] Configurar rate limiting en el backend
- [ ] Agregar monitoring con Sentry
- [ ] Configurar backups automáticos de la base de datos

---

## Comandos de Emergencia

### Rollback en Vercel
\`\`\`bash
# Desde el dashboard de Vercel
# Deployments → Seleccionar deployment anterior → Promote to Production
\`\`\`

### Rollback en Railway
\`\`\`bash
# Desde el dashboard de Railway
# Deployments → Seleccionar deployment anterior → Redeploy
\`\`\`

### Ver Logs en Tiempo Real

**Railway:**
\`\`\`bash
# Instalar CLI
npm i -g @railway/cli

# Login
railway login

# Ver logs
railway logs
\`\`\`

**Render:**
\`\`\`bash
# Desde el dashboard
# Logs tab → Ver logs en tiempo real
\`\`\`

### Reiniciar Servicios

**Railway:**
- Dashboard → Service → Settings → Restart

**Render:**
- Dashboard → Service → Manual Deploy → Deploy latest commit

---

## Contactos de Soporte

- Railway: https://railway.app/help
- Render: https://render.com/docs
- Vercel: https://vercel.com/support

---

## Notas Importantes

1. **SECRET_KEY**: Nunca compartas tu SECRET_KEY. Genera una nueva para producción.
2. **DATABASE_URL**: Mantén segura la URL de tu base de datos.
3. **CORS**: Asegúrate de que ALLOWED_ORIGINS solo incluya tu dominio de producción.
4. **Backups**: Railway y Render hacen backups automáticos, pero considera backups adicionales para datos críticos.
5. **Costos**: Railway y Render tienen planes gratuitos con límites. Monitorea tu uso.

---

## Generación de SECRET_KEY

\`\`\`bash
# Opción 1: OpenSSL
openssl rand -hex 32

# Opción 2: Python
python -c "import secrets; print(secrets.token_hex(32))"

# Opción 3: Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
\`\`\`

Usa la salida como tu `SECRET_KEY` en las variables de entorno del backend.
