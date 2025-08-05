# Python Pipeline - Backend de Procesamiento

Pipeline automatizado de generación y procesamiento de contenido de video usando IA y APIs de stock footage.

## 🏗️ Arquitectura

```
python-pipeline/
├── main.py                              # Orchestrador principal
├── content_01_generate_transcriptwriter.py   # Generación de scripts
├── content_02_analyze_scripts_video_prompts.py # Análisis y prompts
├── content_03_generate_narrator_scripts.py    # Scripts HTML
├── pipeline_01_generate_transcription.py      # Transcripción Whisper
├── pipeline_02_cut_silence.py                 # Corte de silencios
├── pipeline_03_generate_subtitles.py          # Subtítulos optimizados
├── pipeline_04_synchronize_script.py          # Sincronización SRT
├── pipeline_05_generate_segmented_prompts.py  # Prompts segmentados
├── generate_search_keywords.py                # Keywords para stock
├── search_stock_footage.py                    # Descarga de videos
├── config.py                                  # Configuración central
├── requirements.txt                           # Dependencias
├── venv/                                      # Entorno virtual
└── utils/                                     # Utilidades
```

## 🚀 Inicio Rápido

### 1. Configuración del Entorno

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Activar entorno (macOS/Linux)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Variables de Entorno

Crea un archivo `.env` en la raíz del monorepo:

```env
# API Keys para Stock Footage (GRATUITAS)
PEXELS_API_KEY=tu_clave_pexels
PIXABAY_API_KEY=tu_clave_pixabay

# OpenAI (opcional)
OPENAI_API_KEY=tu_clave_openai
```

### 3. Ejecución

```bash
# Pipeline completo
python main.py --script-id 11

# Con parámetros personalizados
python main.py --script-id 11 --min-duration 15 --max-duration 25

# Reiniciar desde el principio
python main.py --script-id 11 --force-restart

# Limpiar todo y empezar
python main.py --script-id 11 --reset
```

## 📋 Pipeline de 10 Pasos

### FASE 1: GENERACIÓN DE CONTENIDO
1. **content_01** - Genera script desde topic usando IA
2. **content_02** - Analiza script y genera prompts de video
3. **content_03** - Genera script HTML para narrador

### FASE 2: PROCESAMIENTO DE VIDEO  
4. **pipeline_01** - Genera transcripción SRT con Whisper
5. **pipeline_02** - Remueve silencios del video
6. **pipeline_03** - Genera subtítulos finales optimizados

### FASE 3: SINCRONIZACIÓN Y PROMPTS
7. **pipeline_04** - Sincroniza script con timestamps SRT
8. **pipeline_05** - Genera prompts segmentados para video

### FASE 4: OBTENCIÓN DE VIDEOS
9. **generate_search_keywords** - Extrae keywords para stock footage
10. **search_stock_footage** - Busca y descarga videos (Pexels/Pixabay)

## ⚙️ Configuración

### config.py
Archivo central con todas las configuraciones:
- Rutas de directorios
- Configuración de modelos IA
- Parámetros de procesamiento de video
- Configuración de APIs

### Sistema de Checkpoints
- Guarda progreso automáticamente
- Retoma desde donde falló
- Archivos en `../shared-assets/VideoProduction/00_checkpoints/`

### Sistema de Limpieza
- **Por defecto**: Limpia otros scripts, preserva el actual
- **--skip-cleanup**: No limpia nada
- **--reset**: Limpia TODO (incluyendo script actual)

## 🔧 Scripts Individuales

Cada script puede ejecutarse independientemente:

```bash
# Generar contenido
python content_01_generate_transcriptwriter.py --topic-id 11
python content_02_analyze_scripts_video_prompts.py --script-id 11
python content_03_generate_narrator_scripts.py --script-id 11

# Procesamiento de video
python pipeline_01_generate_transcription.py
python pipeline_02_cut_silence.py
python pipeline_03_generate_subtitles.py

# Sincronización
python pipeline_04_synchronize_script.py --script-id 11
python pipeline_05_generate_segmented_prompts.py --script-id 11

# Stock footage
python generate_search_keywords.py --script-id 11
python search_stock_footage.py --script-id 11 --max-videos 50
```

## 📁 Outputs

Todos los outputs se guardan en `../shared-assets/VideoProduction/`:

```
VideoProduction/
├── 01_ContentGeneration/      # Scripts generados
├── 02_AudioProcessing/        # (reservado para futuro)
├── 03_VideoProcessing/        # Videos y subtítulos procesados
├── 04_VideoGeneration/        # Prompts segmentados
├── 05_StockFootage/          # Videos descargados
└── 00_checkpoints/           # Puntos de recuperación
```

## 🛠️ Dependencias Principales

- **OpenAI/Pydantic-AI**: Generación de contenido con IA
- **Whisper**: Transcripción y subtítulos de audio
- **MoviePy**: Procesamiento de video (cortes, concatenación)
- **Requests**: APIs de stock footage
- **Pathlib**: Manejo de archivos y directorios
- **Python-dotenv**: Variables de entorno

## 🔍 Solución de Problemas

### Error: "Scripts faltantes"
- Ejecuta desde el directorio `python-pipeline/`
- Verifica que todos los archivos `*.py` estén presentes

### Error: "API keys no encontradas"
- Crea archivo `.env` en la raíz del monorepo
- Obtén claves gratuitas de Pexels y Pixabay

### Error: "Virtual environment no encontrado"
- Ejecuta `python -m venv venv`
- Activa el entorno antes de usar el pipeline

### Error: "Video input no encontrado"
- Coloca video en `VideoProduction/02_VideoRecording/recorded_video.mp4`
- O ajusta rutas en `config.py`

## 📚 Más Información

- [Configuración completa](../README.md)
- [Remotion Renderer](../remotion-renderer/README.md)
- [Scripts de automatización](../scripts/)