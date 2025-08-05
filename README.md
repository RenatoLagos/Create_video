# Video Production Suite - Monorepo Simplificado

Un sistema completo para la producción automatizada de videos educativos usando IA y stock footage.

## 🏗️ Estructura del Proyecto

```
video-production-suite/
├── python-pipeline/        # Backend Python - Pipeline de procesamiento
│   ├── main.py             # Orchestrador principal
│   ├── content_*.py        # Scripts de generación de contenido
│   ├── pipeline_*.py       # Scripts de procesamiento
│   ├── venv/               # Entorno virtual Python
│   └── requirements.txt    # Dependencias Python
│
├── remotion_short_video/   # Frontend TypeScript - Renderizado de videos
│   ├── src/               # Componentes React/Remotion
│   ├── public/            # Assets estáticos
│   ├── package.json       # Dependencias Node.js
│   └── remotion.config.ts # Configuración Remotion
│
├── shared-assets/         # Recursos compartidos entre sistemas
│   ├── VideoProduction/   # Outputs del pipeline Python
│   ├── videos/            # Videos procesados
│   ├── subtitles/         # Archivos de subtítulos
│   ├── prompts/           # Prompts generados
│   └── stock-footage/     # Videos descargados
│
└── scripts/               # Scripts HTML del narrador
    └── narrator_*.html    # Scripts generados para narrador
```

## 🚀 Inicio Rápido

### 1. Configuración del Backend Python

```bash
cd python-pipeline
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuración del Frontend Remotion

```bash
cd remotion_short_video
npm install
```

### 3. Variables de Entorno

Crea un archivo `.env` en la raíz con:

```env
# API Keys para Stock Footage (gratuitas)
PEXELS_API_KEY=tu_clave_pexels
PIXABAY_API_KEY=tu_clave_pixabay

# Configuración OpenAI
OPENAI_API_KEY=tu_clave_openai
```

## 📝 Uso

### Pipeline Completo Python

```bash
cd python-pipeline
python main.py --script-id 11
```

### Renderizado con Remotion

```bash
cd remotion_short_video
npm run dev  # Desarrollo
npm run build  # Producción
```

## 🔄 Flujo de Trabajo

1. **Python Pipeline** procesa contenido y genera assets
2. **Shared Assets** almacena todos los outputs 
3. **Remotion Renderer** consume assets y genera video final

## 📚 Documentación

- [Python Pipeline](python-pipeline/README.md)
- [Remotion Renderer](remotion_short_video/README.md)
- [Getting Started](remotion_short_video/GETTING_STARTED.md)

## 🛠️ Características

- ✅ Pipeline automatizado de extremo a extremo
- ✅ Generación de contenido con IA
- ✅ Procesamiento de video inteligente
- ✅ Stock footage de múltiples fuentes
- ✅ Renderizado profesional con Remotion
- ✅ Sistema de checkpoints y recuperación
- ✅ Monorepo simplificado y eficiente