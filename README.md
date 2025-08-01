# 🎬 VIDEO PRODUCTION PIPELINE

## 🎯 NUEVA ESTRUCTURA ORGANIZADA POR ETAPAS

```
Create_video/
├── 📄 config.py                                    # ✨ Configuración centralizada renovada
├── 📄 requirements.txt                             # Dependencias del proyecto
├── 📁 utils/                                       # Utilidades del proyecto
├── 📁 scripts/                                     # Scripts HTML del narrador
│
├── 🎬 SCRIPTS DE GENERACIÓN DE CONTENIDO:
├── 📄 content_01_generate_transcriptwriter.py      # Generar scripts desde temas
├── 📄 content_02_analyze_scripts_video_prompts.py  # Analizar scripts y crear prompts
├── 📄 content_03_generate_narrator_scripts.py      # Generar scripts HTML del narrador
├── 📄 content_04_release_material.py               # Extraer material para producción
│
├── 🔧 SCRIPTS DEL PIPELINE DE VIDEO:
├── 📄 pipeline_01_generate_transcription.py        # Etapa 1: Transcripción original
├── 📄 pipeline_02_cut_silence.py                   # Etapa 2: Remover silencios
├── 📄 pipeline_03_generate_subtitles.py            # Etapa 3: Subtítulos limpios
├── 📄 pipeline_04_synchronize_script.py            # Etapa 4: Sincronizar con timestamps
├── 📄 pipeline_05_generate_segmented_prompts.py    # Etapa 5: Segmentar prompts
├── 📄 pipeline_06_generate_videos.py               # Etapa 6: Generar videos AI
├── 📄 pipeline_07_batch_video_generator.py         # Etapa 6: Generación en lotes
│
├── 📁 VideoProduction/                             # 🎯 NUEVA ESTRUCTURA ORGANIZADA
│   ├── 📁 01_ContentGeneration/                    # Generación de contenido
│   │   ├── 📁 01_topics_config/                    # Configuración de temas
│   │   │   ├── 📄 category_prompts.json            # Prompts por categoría
│   │   │   └── 📄 topics.json                      # Lista de temas
│   │   ├── 📁 02_generated_scripts/                # Scripts generados
│   │   │   └── 📄 scripts_by_category.json         # Scripts organizados
│   │   ├── 📁 03_analyzed_scripts/                 # Scripts analizados
│   │   │   └── 📄 scripts_with_video_prompts.json  # Con prompts de video
│   │   ├── 📁 04_narrator_scripts/                 # Scripts HTML del narrador
│   │   └── 📁 05_release_material/                 # Material extraído
│   │       ├── 📄 script_XX_data.json              # Datos del script
│   │       └── 📄 narrator_short_script_XX.html    # Script HTML
│   │
│   ├── 📁 02_VideoRecording/                       # Video grabado
│   │   └── 📄 recorded_video.mp4                   # Video original
│   │
│   ├── 📁 03_VideoProcessing/                      # Procesamiento de video
│   │   ├── 📁 01_transcription/                    # Transcripción original
│   │   │   └── 📄 original_transcription.srt       # Transcripción base
│   │   ├── 📁 02_silence_removal/                  # Remoción de silencios
│   │   │   └── 📄 video_no_silence.mp4             # Video sin silencios
│   │   ├── 📁 03_subtitles/                        # Subtítulos limpios
│   │   │   └── 📄 clean_subtitles.srt              # Subtítulos optimizados
│   │   └── 📁 04_synchronization/                  # Sincronización
│   │       └── 📄 synchronized_script.json         # Script sincronizado
│   │
│   └── 📁 04_VideoGeneration/                      # Generación AI de videos
│       ├── 📁 01_segmented_prompts/                # Prompts segmentados
│       │   └── 📄 segmented_prompts.json           # Prompts por segmento
│       └── 📁 02_generated_videos/                 # Videos generados
│           ├── 📁 metadata/                        # Metadatos
│           │   └── 📄 generated_videos_metadata.json
│           └── 📁 videos/                          # Videos MP4
│               ├── 📄 phrase_01_segment_01.mp4     # Videos por segmento
│               └── 📄 phrase_XX_segment_XX.mp4     # ...
│
├── 📁 9_remotion_edit_video/                       # ⚠️ NO MODIFICADO
└── 📁 10_generate_descriptions/                    # ⚠️ NO MODIFICADO
```

## 🔄 FLUJO COMPLETO DEL PIPELINE

### 📝 **FASE 1: GENERACIÓN DE CONTENIDO**
| Script | Función | Input | Output |
|--------|---------|--------|--------|
| `content_01_generate_transcriptwriter.py` | Generar scripts desde temas | `topics.json`, `category_prompts.json` | `scripts_by_category.json` |
| `content_02_analyze_scripts_video_prompts.py` | Analizar scripts y crear prompts | `scripts_by_category.json` | `scripts_with_video_prompts.json` |
| `content_03_generate_narrator_scripts.py` | Generar scripts HTML del narrador | `scripts_by_category.json` | Archivos HTML del narrador |
| `content_04_release_material.py` | Extraer material específico | Scripts analizados | Material en `05_release_material/` |

### 🎥 **FASE 2: PROCESAMIENTO DE VIDEO**
| Etapa | Script | Input | Output | Ubicación |
|-------|--------|--------|--------|-----------|
| **1** | `pipeline_01_generate_transcription.py` | `recorded_video.mp4` | `original_transcription.srt` | `03_VideoProcessing/01_transcription/` |
| **2** | `pipeline_02_cut_silence.py` | Video + transcripción | `video_no_silence.mp4` | `03_VideoProcessing/02_silence_removal/` |
| **3** | `pipeline_03_generate_subtitles.py` | Video sin silencios | `clean_subtitles.srt` | `03_VideoProcessing/03_subtitles/` |
| **4** | `pipeline_04_synchronize_script.py` | Script + subtítulos | `synchronized_script.json` | `03_VideoProcessing/04_synchronization/` |

### 🤖 **FASE 3: GENERACIÓN DE VIDEOS AI**
| Etapa | Script | Input | Output | Ubicación |
|-------|--------|--------|--------|-----------|
| **5** | `pipeline_05_generate_segmented_prompts.py` | Script sincronizado | `segmented_prompts.json` | `04_VideoGeneration/01_segmented_prompts/` |
| **6** | `pipeline_06_generate_videos.py` | Prompts segmentados | Videos MP4 + metadatos | `04_VideoGeneration/02_generated_videos/` |
| **6b** | `pipeline_07_batch_video_generator.py` | Prompts segmentados | Generación en lotes | `04_VideoGeneration/02_generated_videos/` |

## ⚙️ CONFIGURACIÓN CENTRALIZADA RENOVADA

El archivo `config.py` ha sido **completamente rediseñado** con configuraciones organizadas por etapas:

### 🎯 **Configuraciones por Etapa:**

- **`ContentGenerationConfig`** - Rutas y configuración para generación de contenido
  - Archivos de configuración de temas y categorías
  - Rutas de scripts generados y analizados
  - Configuración de HTML del narrador y material de release

- **`TranscriptionConfig`** - Configuración de Whisper y transcripciones
  - Modelos de Whisper (large-v3, fallback)
  - Configuración de idioma y parámetros de calidad
  - Rutas de input/output organizadas

- **`SilenceCutConfig`** - Configuración de remoción de silencios
  - Parámetros de detección de silencios
  - Configuración de codecs y calidad de video
  - Buffers antes y después del habla

- **`SubtitlesConfig`** - Configuración de subtítulos optimizados
  - Configuración de formato y timing
  - Máxima duración y caracteres por línea
  - Gaps entre subtítulos

- **`SynchronizationConfig`** - Configuración de sincronización
  - Métodos de sincronización (similarity, order, hybrid)
  - Threshold de similitud de texto
  - Rutas de scripts y subtítulos

- **`SegmentedPromptsConfig`** - Configuración de segmentación de prompts
  - Duración máxima y mínima de segmentos
  - Configuración del modelo AI (GPT-4o)
  - Reglas de segmentación para videos

- **`VideoGenerationConfig`** - Configuración de generación de videos AI
  - Modelos disponibles (Wan 2.2, Seedance, etc.)
  - Configuración de FPS, resolución y aspect ratio
  - Rutas de metadatos y videos generados

### 🛠️ **Funciones de Utilidad:**
- `validate_all_paths()` - Validación automática de todas las rutas
- `print_configuration_summary()` - Resumen visual de la configuración
- `apply_quality_profile()` - Perfiles de calidad (fast, balanced, high)

## 📦 INSTALACIÓN

```powershell
# Clonar el repositorio
git clone <repository-url>
cd Create_video

# Instalar dependencias
pip install -r requirements.txt

# Para usar GPU con Whisper (recomendado):
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Configurar variables de entorno para fal.ai
export FAL_API_KEY="your-fal-api-key"
```

## 🚀 USO DEL PIPELINE

### **Opción 1: Generación de Contenido Completa**
```powershell
# 1. Generar scripts desde temas
python content_01_generate_transcriptwriter.py

# 2. Analizar scripts y crear prompts de video
python content_02_analyze_scripts_video_prompts.py

# 3. Generar scripts HTML del narrador
python content_03_generate_narrator_scripts.py

# 4. Extractar material específico para producción
python content_04_release_material.py 11  # Ejemplo: script ID 11
```

### **Opción 2: Pipeline de Procesamiento de Video**
```powershell
# 1. Generar transcripción original
python pipeline_01_generate_transcription.py

# 2. Remover silencios del video
python pipeline_02_cut_silence.py

# 3. Generar subtítulos limpios
python pipeline_03_generate_subtitles.py

# 4. Sincronizar script con timestamps
python pipeline_04_synchronize_script.py

# 5. Segmentar prompts para generación
python pipeline_05_generate_segmented_prompts.py

# 6. Generar videos con IA
python pipeline_06_generate_videos.py
# O usar generación en lotes:
python pipeline_07_batch_video_generator.py --input path/to/prompts.json --output path/to/videos
```

### **Opción 3: Pipeline Completo**
```powershell
# Ejecutar todo el pipeline en orden:
python content_01_generate_transcriptwriter.py && \
python content_02_analyze_scripts_video_prompts.py && \
python content_03_generate_narrator_scripts.py && \
python content_04_release_material.py 11 && \
python pipeline_01_generate_transcription.py && \
python pipeline_02_cut_silence.py && \
python pipeline_03_generate_subtitles.py && \
python pipeline_04_synchronize_script.py && \
python pipeline_05_generate_segmented_prompts.py && \
python pipeline_06_generate_videos.py
```

## 🎯 BENEFICIOS DE LA NUEVA ESTRUCTURA

### ✅ **Organización Clara**
- **4 etapas definidas**: ContentGeneration → VideoRecording → VideoProcessing → VideoGeneration
- **Flujo lógico** fácil de seguir y entender
- **Separación clara** entre generación de contenido y procesamiento de video

### ✅ **Nombres Descriptivos**
- Archivos con nombres que **explican su función**
- **No más prefijos numéricos** confusos como "0s_", "1s_", "2s_"
- **Ubicación lógica** de cada archivo en su etapa correspondiente

### ✅ **Configuración Centralizada**
- **Una sola fuente de verdad** en `config.py`
- **Configuración por etapas** bien organizada
- **Validación automática** de rutas y configuraciones

### ✅ **Mantenimiento Simplificado**
- **Fácil localización** de archivos y funcionalidades
- **Estructura escalable** para agregar nuevas etapas
- **Documentación clara** del flujo de trabajo

### ✅ **Reutilización y Modularidad**
- **Scripts independientes** que pueden ejecutarse por separado
- **Configuraciones reutilizables** entre diferentes proyectos
- **API clara** entre etapas del pipeline

## ⚠️ NOTAS IMPORTANTES

- **VideoProduction/** reemplaza completamente a `Video/` con estructura organizada
- Las carpetas `9_remotion_edit_video/` y `10_generate_descriptions/` **no fueron modificadas**
- **Configuración centralizada** en `config.py` controla todas las rutas
- **Todos los scripts** han sido actualizados y están **libres de errores**
- **Backward compatibility** mantenida para datos existentes

## 🔧 CONFIGURACIÓN PERSONALIZADA

```python
# Ejemplo de personalización en config.py
from config import apply_quality_profile, print_configuration_summary

# Aplicar perfil de calidad
apply_quality_profile("high")  # Opciones: fast, balanced, high

# Ver configuración actual
print_configuration_summary()

# Validar rutas
from config import validate_all_paths
errors = validate_all_paths()
if errors:
    print("Errores encontrados:", errors)
```

---

**🎬 Pipeline de Producción de Video - Reorganización Completada** ✨

*Estructura optimizada para máxima claridad, mantenibilidad y escalabilidad*
