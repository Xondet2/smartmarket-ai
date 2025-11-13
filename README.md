# DBVision

Aplicación full-stack para análisis de productos de e-commerce con IA, análisis de sentimientos, web scraping y comparación de precios.

## Características

- **Análisis de Sentimientos con IA**: Analiza reseñas de clientes usando transformers de Hugging Face
- **Web Scraping**: Extrae información de productos y reseñas de múltiples plataformas (Amazon, eBay, MercadoLibre)
- **Comparación de Precios**: Compara precios entre diferentes plataformas de e-commerce
- **Dashboard Interactivo**: UI moderna en React con visualización de datos en tiempo real
- **Autenticación**: Sistema de login con JWT y contraseñas hasheadas
- **Base de Datos**: SQLite para desarrollo local, migración fácil a PostgreSQL para producción

## Stack Tecnológico

### Frontend
- React 19 con Next.js 15
- TailwindCSS v4
- Recharts para visualización
- shadcn/ui components

### Backend
- FastAPI
- SQLAlchemy ORM
- BeautifulSoup para scraping
- Transformers (Hugging Face) para IA
- bcrypt para seguridad
- JWT para autenticación

---

## Instalación Local

### Prerrequisitos
- Node.js 18+ y npm
- Python 3.9+
- Conexión a internet

### 1. Backend

\`\`\`bash
py -3.12 -m venv .venv
.venv\Scripts\activate
cd backend
pip install -r requirements.txt
pip install pydantic[email]
uvicorn main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

El API estará disponible en `http://localhost:8000`

### 2. Frontend

\`\`\`bash
npm install
npm run dev
\`\`\`

La aplicación estará en `http://localhost:3000`



## Despliegue en Producción

### Opción 1: Frontend en Vercel + Backend en Railway

#### A. Desplegar Backend en Railway

1. **Crear cuenta en Railway.app**

2. **Crear nuevo proyecto desde GitHub**
   - Conecta tu repositorio
   - Railway detectará automáticamente que es Python

3. **Configurar variables de entorno en Railway:**

\`\`\`env
DATABASE_URL=postgresql://...  (Railway lo provee automáticamente)
ALLOWED_ORIGINS=https://tu-dominio.vercel.app
PORT=8000
SECRET_KEY=tu-clave-secreta-muy-segura-aqui
\`\`\`

4. **Configurar comando de inicio:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

5. **Railway generará una URL pública** como: `https://tu-app.railway.app`

#### B. Desplegar Frontend en Vercel

1. **Conectar repositorio a Vercel**

2. **Configurar proyecto:**
   - Framework Preset: Next.js
   - Root Directory: `.` (raíz del proyecto)
   - Build Command: `npm run build`
   - Output Directory: `.next`

3. **Variables de entorno en Vercel:**

\`\`\`env
NEXT_PUBLIC_API_URL=https://tu-app.railway.app
\`\`\`

4. **Deploy** - Vercel construirá y desplegará automáticamente

---

### Opción 2: Frontend en Vercel + Backend en Render

#### A. Desplegar Backend en Render

1. **Crear cuenta en Render.com**

2. **Crear nuevo Web Service**
   - Conecta tu repositorio
   - Selecciona Python

3. **Configuración:**
   - Name: `smartmarket-backend`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Variables de entorno:**

\`\`\`env
DATABASE_URL=postgresql://...  (Render lo provee si agregas PostgreSQL)
ALLOWED_ORIGINS=https://tu-dominio.vercel.app
SECRET_KEY=tu-clave-secreta-muy-segura-aqui
PYTHON_VERSION=3.11.0
\`\`\`

5. **Agregar PostgreSQL Database:**
   - En el dashboard de Render, crea una nueva PostgreSQL database
   - Render automáticamente conectará `DATABASE_URL`

#### B. Desplegar Frontend en Vercel
(Mismo proceso que Opción 1B)

---

## Configuración de Base de Datos para Producción

### Migración de SQLite a PostgreSQL

El código ya está preparado para usar PostgreSQL automáticamente cuando detecta `DATABASE_URL`.

**En `backend/database/db_config.py`:**
\`\`\`python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smartmarket.db")

# Automáticamente convierte postgres:// a postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
\`\`\`

**Las tablas se crean automáticamente** al iniciar el servidor gracias a:
\`\`\`python
@app.on_event("startup")
def startup_event():
    init_db()  # Crea todas las tablas
\`\`\`

No necesitas ejecutar migraciones manualmente.

---

## Variables de Entorno Requeridas

### Backend (Producción)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | URL de PostgreSQL | `postgresql://user:pass@host:5432/db` |
| `ALLOWED_ORIGINS` | Dominios permitidos para CORS | `https://miapp.vercel.app` |
| `SECRET_KEY` | Clave para JWT tokens | `tu-clave-secreta-256-bits` |
| `PORT` | Puerto del servidor | `8000` |

### Frontend (Producción)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | URL del backend | `https://miapp.railway.app` |

---

## Comandos Útiles

### Desarrollo Local

\`\`\`bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend
npm run dev

# Ver logs del backend
# Los logs aparecen en la terminal donde ejecutaste uvicorn

# Verificar estado de la base de datos
curl http://localhost:8000/api/db-status
\`\`\`

### Producción

\`\`\`bash
# Build del frontend
npm run build

# Iniciar frontend en producción
npm start

# Backend en producción (Railway/Render lo hacen automáticamente)
cd backend
uvicorn main:app --host 0.0.0.0 --port $PORT
\`\`\`

---

## Estructura del Proyecto

\`\`\`
SmartMarketAI/
├── app/                    # Frontend Next.js
│   ├── page.tsx           # Página principal
│   ├── login/             # Página de login
│   ├── register/          # Página de registro
│   └── globals.css        # Estilos globales
├── components/            # Componentes React
│   ├── search-bar.tsx
│   ├── analysis-results.tsx
│   ├── auth-provider.tsx
│   └── ...
├── lib/                   # Servicios y utilidades
│   ├── api.ts            # Cliente de API
│   ├── auth.ts           # Servicio de autenticación
│   └── hooks/            # Custom hooks
├── backend/              # Backend FastAPI
│   ├── main.py          # Punto de entrada
│   ├── routes/          # Endpoints de la API
│   ├── services/        # Lógica de negocio
│   ├── database/        # Modelos y configuración
│   └── utils/           # Utilidades
└── public/              # Archivos estáticos
\`\`\`

---

## Solución de Problemas

### Backend no inicia

\`\`\`bash
# Verifica que las dependencias estén instaladas
pip install -r requirements.txt

# Verifica que el puerto 8000 no esté en uso
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows
\`\`\`

### Frontend no conecta con Backend

1. Verifica que `NEXT_PUBLIC_API_URL` esté configurado correctamente
2. Verifica que el backend esté corriendo
3. Revisa la consola del navegador para errores de CORS
4. Asegúrate de que `ALLOWED_ORIGINS` en el backend incluya tu dominio

### Error de Base de Datos en Producción

1. Verifica que `DATABASE_URL` esté configurado
2. Visita `https://tu-backend.com/api/db-status` para verificar las tablas
3. Revisa los logs del servidor para errores de conexión

### Error de Autenticación

1. Verifica que `SECRET_KEY` esté configurado en producción
2. Limpia el localStorage del navegador
3. Verifica que el token JWT no haya expirado (24 horas por defecto)

---

## Documentación de la API

Una vez el backend esté corriendo:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Seguridad

- Las contraseñas se hashean con bcrypt (12 rounds)
- Los tokens JWT expiran en 24 horas
- CORS está configurado para permitir solo dominios específicos
- Las variables sensibles se manejan con variables de entorno
- SQL injection protegido por SQLAlchemy ORM


