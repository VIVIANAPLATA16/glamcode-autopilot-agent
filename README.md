# 🛡️ NeurAudit Sentinel

> **Inteligencia anti-corrupción en tiempo real para contratos públicos colombianos**

[![Deploy](https://img.shields.io/badge/deploy-vercel-black?logo=vercel)](https://neuraudit-sentinel.vercel.app)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/Neon-PostgreSQL-green?logo=postgresql)](https://neon.tech)
[![AWS](https://img.shields.io/badge/AWS-Aurora%20DSQL-orange?logo=amazon-aws)](https://aws.amazon.com)

---

## 🌐 Demo en vivo

**👉 https://neuraudit-sentinel.vercel.app**

---

## 🧠 ¿Qué es NeurAudit Sentinel?

NeurAudit Sentinel es una plataforma SaaS de monitoreo continuo anti-corrupción diseñada para analizar, vigilar y alertar sobre el comportamiento contractual de entidades públicas colombianas.

A diferencia de las herramientas reactivas tradicionales, Sentinel opera de forma **proactiva**: monitorea entidades en tiempo real, cruza datos de múltiples fuentes (SECOP II, Contraloría, Procuraduría) y genera alertas automáticas clasificadas por nivel de riesgo antes de que los problemas escalen.

Sentinel es el módulo de monitoreo continuo del ecosistema **NeurAudit AI**, complementando su capacidad de investigación puntual con vigilancia permanente.

---

## 🎯 Problema que resuelve

Colombia pierde aproximadamente **$50 billones de pesos anuales** en corrupción en contratación pública. Las herramientas actuales de control son:

- ❌ Reactivas — detectan el problema después del daño
- ❌ Fragmentadas — no cruzan fuentes de datos
- ❌ Inaccesibles — solo para entidades gubernamentales grandes
- ❌ Sin alertas — requieren búsqueda manual constante

**NeurAudit Sentinel resuelve esto** con monitoreo automático, alertas en tiempo real y análisis de riesgo inteligente accesible para cualquier empresa u organización.

---

## ✨ Funcionalidades

### 📊 Dashboard Ejecutivo
- KPIs en tiempo real: entidades monitoreadas, alertas activas, contratos en riesgo
- Feed de alertas recientes con nivel de criticidad
- Vista rápida de watchlist con últimas actividades

### 👁️ Watchlist Inteligente
- Agrega entidades públicas por nombre y NIT
- Clasificación por tipo: empresa, persona, entidad territorial
- Monitoreo persistente con historial de actividad
- Búsqueda y filtrado por nivel de riesgo (ALTO / MEDIO / BAJO)
- Eliminación y gestión de entidades monitoreadas

### 🚨 Centro de Alertas
- Alertas automáticas clasificadas por criticidad
- Fuentes: SECOP II, Contraloría General, Procuraduría
- Indicadores visuales con animación pulse para alertas críticas
- Filtrado por nivel y fecha

### 🔍 Módulo Investigar
- Búsqueda libre de entidades y contratos
- Análisis de riesgo por contrato
- Integración con datos de SECOP II

### ⚙️ Configuración
- Gestión de preferencias de notificación
- Configuración de umbrales de alerta
- Integraciones con fuentes de datos

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────┐
│                   USUARIO                        │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│          Next.js 16 App Router                   │
│         (Server + Client Components)             │
│                                                  │
│  /dashboard  /watchlist  /alertas  /investigar  │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│           Next.js API Routes                     │
│        (Serverless Functions - Vercel)           │
│                                                  │
│   /api/watchlist   /api/alerts   /api/test-db   │
└─────────────────┬───────────────────────────────┘
                  │
     ┌────────────┴────────────┐
     │                         │
┌────▼────────┐      ┌────────▼────────┐
│    Neon     │      │   AWS Aurora    │
│ PostgreSQL  │      │     DSQL        │
│ (principal) │      │  (escalabilidad)│
└─────────────┘      └─────────────────┘
```

---

## 🛠️ Stack tecnológico

| Capa | Tecnología | Propósito |
|------|-----------|-----------|
| Frontend | Next.js 16, React 19 | App Router, Server Components |
| Estilos | Tailwind CSS v4 | Design system completo |
| UI | v0.dev + Lucide Icons | Componentes SOC-style |
| Backend | Next.js API Routes | Serverless functions |
| Base de datos | Neon PostgreSQL | Persistencia principal |
| Cloud DB | AWS Aurora DSQL | Escalabilidad enterprise |
| Hosting | Vercel | Deploy automático |
| Animaciones | tw-animate-css | Micro-interacciones |

---

## ⚙️ Instalación y setup

### Prerequisitos

- Node.js 22+
- npm
- Cuenta en [Neon](https://neon.tech) (gratis)

### 1. Clonar el repositorio

    git clone https://github.com/VIVIANAPLATA16/neuraudit-sentinel
    cd neuraudit-sentinel

### 2. Instalar dependencias

    npm install

### 3. Variables de entorno

Crea un archivo `.env.local` en la raíz:

    DATABASE_URL=postgresql://usuario:password@host.neon.tech/neondb?sslmode=require

### 4. Inicializar base de datos

Con el servidor corriendo, visita:

    http://localhost:3000/api/setup

### 5. Ejecutar en desarrollo

    npm run dev

Abre http://localhost:3001

---

## 📊 Schema de base de datos

    -- Entidades bajo monitoreo
    CREATE TABLE watchlists (
      id          SERIAL PRIMARY KEY,
      nombre      TEXT NOT NULL,
      nit         TEXT,
      tipo        TEXT CHECK (tipo IN ('empresa', 'persona', 'entidad')),
      descripcion TEXT,
      created_at  TIMESTAMP DEFAULT NOW()
    );

    -- Alertas generadas por el sistema
    CREATE TABLE alerts (
      id           SERIAL PRIMARY KEY,
      watchlist_id INTEGER REFERENCES watchlists(id) ON DELETE CASCADE,
      titulo       TEXT NOT NULL,
      descripcion  TEXT,
      nivel        TEXT CHECK (nivel IN ('alto', 'medio', 'bajo')),
      fuente       TEXT, -- 'SECOP', 'Contraloría', 'Procuraduría'
      created_at   TIMESTAMP DEFAULT NOW()
    );

    -- Historial de investigaciones
    CREATE TABLE investigations (
      id           SERIAL PRIMARY KEY,
      watchlist_id INTEGER REFERENCES watchlists(id) ON DELETE CASCADE,
      query        TEXT NOT NULL,
      resultado    JSONB,
      created_at   TIMESTAMP DEFAULT NOW()
    );

---

## 📁 Estructura del proyecto

    neuraudit-sentinel/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx                    # Dashboard principal
    │   │   ├── layout.tsx                  # Layout global + sidebar
    │   │   ├── globals.css                 # Design tokens + Tailwind v4
    │   │   ├── watchlist/
    │   │   │   └── page.tsx                # Gestión de entidades (con DB real)
    │   │   ├── alertas/
    │   │   │   └── page.tsx                # Centro de alertas
    │   │   ├── investigar/
    │   │   │   └── page.tsx                # Búsqueda y análisis
    │   │   ├── configuracion/
    │   │   │   └── page.tsx                # Configuración
    │   │   └── api/
    │   │       ├── watchlist/
    │   │       │   ├── route.ts            # GET + POST entidades
    │   │       │   └── [id]/route.ts       # DELETE entidad
    │   │       ├── setup/route.ts          # Inicializar tablas
    │   │       └── test-db/route.ts        # Health check
    │   ├── components/
    │   │   ├── app-shell.tsx               # Shell principal + navegación
    │   │   ├── sidebar.tsx                 # Sidebar con nav activa
    │   │   ├── risk-badge.tsx              # Badge ALTO/MEDIO/BAJO
    │   │   ├── alert-feed.tsx              # Feed de alertas
    │   │   ├── kpi-card.tsx                # Tarjetas de métricas
    │   │   ├── entity-card.tsx             # Card de entidad
    │   │   ├── page-header.tsx             # Header de página
    │   │   ├── empty-state.tsx             # Estado vacío
    │   │   └── risk-gauge.tsx              # Gauge de riesgo
    │   └── lib/
    │       ├── db.ts                       # Conexión Neon PostgreSQL
    │       ├── data.ts                     # Tipos TypeScript
    │       └── utils.ts                    # cn() helper
    ├── .env.local                          # Variables de entorno (no commitear)
    ├── next.config.mjs
    ├── tailwind.config.ts
    └── package.json

---

## 🚀 Deploy en Vercel

    npm install -g vercel
    vercel

Agrega las variables de entorno en el dashboard de Vercel:
- `DATABASE_URL` — connection string de Neon

---

## 🗺️ Roadmap

- [x] Dashboard con KPIs en tiempo real
- [x] Watchlist conectada a base de datos
- [x] CRUD completo de entidades
- [x] Sistema de alertas con niveles de riesgo
- [ ] Integración API SECOP II en tiempo real
- [ ] Alertas automáticas por webhook
- [ ] Módulo de IA para scoring de riesgo
- [ ] Exportación de reportes PDF
- [ ] Notificaciones por email/Slack

---

## 🤝 Parte del ecosistema NeurAudit

| Producto | Descripción | URL |
|---------|-------------|-----|
| **NeurAudit AI** | Investigación puntual con IA | [neuraudit-web...run.app](https://neuraudit-web-986541948066.us-central1.run.app/) |
| **NeurAudit Sentinel** | Monitoreo continuo + alertas | [neuraudit-sentinel.vercel.app](https://neuraudit-sentinel.vercel.app) |

---

## 📄 Licencia

MIT © 2026 Viviana Plata

---

*Construido para la hackathon H0 — AWS + Vercel + Neon 2026*
