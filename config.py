"""
Configuración unificada para el pipeline completo de generación de videos
Fusiona todas las configuraciones de las etapas 2-7 del pipeline
"""

import os
from pathlib import Path

# ===== CONFIGURACIÓN DE RUTAS BASE =====
# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent

# Directorio principal donde se almacena toda la producción de video
VIDEO_PRODUCTION_DIR = PROJECT_ROOT / "VideoProduction"

# Directorios organizados por etapas del pipeline
CONTENT_GENERATION_DIR = VIDEO_PRODUCTION_DIR / "01_ContentGeneration" 
VIDEO_RECORDING_DIR = VIDEO_PRODUCTION_DIR / "02_VideoRecording" 
VIDEO_PROCESSING_DIR = VIDEO_PRODUCTION_DIR / "03_VideoProcessing"
VIDEO_GENERATION_DIR = VIDEO_PRODUCTION_DIR / "04_VideoGeneration"

# ===== CONFIGURACIÓN DE GENERACIÓN DE CONTENIDO =====
class ContentGenerationConfig:
    # Rutas de archivos de configuración
    TOPICS_CONFIG_FILE = CONTENT_GENERATION_DIR / "01_topics_config" / "topics.json"
    CATEGORY_PROMPTS_FILE = CONTENT_GENERATION_DIR / "01_topics_config" / "category_prompts.json"
    
    # Rutas de scripts generados
    GENERATED_SCRIPTS_FILE = CONTENT_GENERATION_DIR / "02_generated_scripts" / "scripts_by_category.json"
    ANALYZED_SCRIPTS_FILE = CONTENT_GENERATION_DIR / "03_analyzed_scripts" / "scripts_with_video_prompts.json"
    
    # Rutas de scripts del narrador (HTML)
    NARRATOR_SCRIPTS_DIR = CONTENT_GENERATION_DIR / "04_narrator_scripts"
    
    # Rutas de material listo para producción
    RELEASE_MATERIAL_DIR = CONTENT_GENERATION_DIR / "05_release_material"
    
    # Configuración de generación
    DEFAULT_MIN_DURATION = 15
    DEFAULT_MAX_DURATION = 20
    DEFAULT_LIMIT_PER_CATEGORY = 4
    DEFAULT_MODEL = "gpt-4o"

# ===== ETAPA 1: CONFIGURACIÓN DE TRANSCRIPCIONES =====
class TranscriptionConfig:
    # Rutas
    VIDEO_INPUT_PATH = VIDEO_RECORDING_DIR / "recorded_video.mp4"
    OUTPUT_DIRECTORY = VIDEO_PROCESSING_DIR / "01_transcription"
    
    # Configuración de Whisper
    WHISPER_MODEL = "large-v3"
    FALLBACK_MODEL = "base"
    LANGUAGE = "en"
    
    # Configuración avanzada
    WORD_TIMESTAMPS = True
    TEMPERATURE = 0
    BEST_OF = 5
    BEAM_SIZE = 5
    
    # Archivos de salida
    GENERATE_TXT = False
    GENERATE_JSON = False
    GENERATE_SRT = True
    
    # Logging
    VERBOSE = True
    WHISPER_VERBOSE = True

# ===== ETAPA 2: CONFIGURACIÓN DE CORTE DE SILENCIOS =====
class SilenceCutConfig:
    # Rutas
    SRT_INPUT_PATH = VIDEO_PROCESSING_DIR / "01_transcription" / "original_transcription.srt"
    VIDEO_INPUT_PATH = VIDEO_RECORDING_DIR / "recorded_video.mp4"
    OUTPUT_DIRECTORY = VIDEO_PROCESSING_DIR / "02_silence_removal"
    
    # Detección de silencios
    MIN_SILENCE_DURATION = 1.0
    BUFFER_BEFORE = 0.1
    BUFFER_AFTER = 0.1
    
    # Configuración de video
    CRF_VALUE = 20
    PRESET = "medium"
    VIDEO_CODEC = "libx264"
    AUDIO_CODEC = "aac"
    
    # Logging
    VERBOSE = True
    MOVIEPY_VERBOSE = True

# ===== ETAPA 3: CONFIGURACIÓN DE SUBTÍTULOS =====
class SubtitlesConfig:
    # Rutas
    VIDEO_INPUT_PATH = VIDEO_PROCESSING_DIR / "02_silence_removal"
    OUTPUT_DIRECTORY = VIDEO_PROCESSING_DIR / "03_subtitles"
    
    # Configuración de Whisper (igual que transcripción)
    WHISPER_MODEL = "large-v3"
    FALLBACK_MODEL = "base"
    LANGUAGE = "en"
    WORD_TIMESTAMPS = True
    TEMPERATURE = 0
    BEST_OF = 5
    BEAM_SIZE = 5
    
    # Configuración de subtítulos
    MAX_SUBTITLE_DURATION = 6.0
    MAX_CHARS_PER_LINE = 42
    MAX_LINES_PER_SUBTITLE = 2
    MIN_GAP_BETWEEN_SUBTITLES = 0.3
    
    # Logging
    VERBOSE = True
    WHISPER_VERBOSE = True

# ===== ETAPA 4: CONFIGURACIÓN DE SINCRONIZACIÓN =====
class SynchronizationConfig:
    # Rutas
    SCRIPT_JSON_PATH = CONTENT_GENERATION_DIR / "05_release_material" / "script_11_data.json"
    SRT_INPUT_PATH = VIDEO_PROCESSING_DIR / "03_subtitles" / "clean_subtitles.srt"
    OUTPUT_DIRECTORY = VIDEO_PROCESSING_DIR / "04_synchronization"
    
    # Configuración de sincronización
    SIMILARITY_THRESHOLD = 0.6
    SYNC_METHOD = "hybrid"  # 'similarity', 'order', 'hybrid'
    
    # Logging
    VERBOSE = True
    SHOW_TEXT_COMPARISON = True

# ===== ETAPA 5: CONFIGURACIÓN DE PROMPTS SEGMENTADOS =====
class SegmentedPromptsConfig:
    # Rutas
    INPUT_FILE = VIDEO_PROCESSING_DIR / "04_synchronization" / "synchronized_script.json"
    OUTPUT_DIR = VIDEO_GENERATION_DIR / "01_segmented_prompts"
    OUTPUT_FILENAME = "segmented_prompts.json"
    
    # Configuración de tiempo
    MAX_SEGMENT_DURATION = 3.0
    MIN_SEGMENT_DURATION = 2.0
    
    # Configuración de AI
    MODEL_NAME = "gpt-4o"
    
    # Configuración de procesamiento
    VERBOSE_LOGGING = True
    CREATE_OUTPUT_DIR = True
    
    # Reglas de segmentación
    SEGMENTATION_RULES = {
        "max_segment_duration": MAX_SEGMENT_DURATION,
        "min_segment_duration": MIN_SEGMENT_DURATION,
        "prefer_equal_segments": True,
        "minimum_duration_to_segment": 4.0
    }

# ===== ETAPA 6: CONFIGURACIÓN DE GENERACIÓN DE VIDEO =====
class VideoGenerationConfig:
    # Rutas
    INPUT_FILE = VIDEO_GENERATION_DIR / "01_segmented_prompts" / "segmented_prompts.json"
    OUTPUT_DIR = VIDEO_GENERATION_DIR / "02_generated_videos" / "videos"
    METADATA_DIR = VIDEO_GENERATION_DIR / "02_generated_videos" / "metadata"
    METADATA_FILE = "generated_videos_metadata.json"
    
    # Modelos de video disponibles
    VIDEO_MODELS = {
        "wan": "fal-ai/wan/v2.2-5b/text-to-video",
        "wan_i2v": "fal-ai/wan/v2.2-5b/image-to-video",
        "seedance": "fal-ai/bytedance/seedance/v1/lite/text-to-video",
        "seedance_i2v": "fal-ai/bytedance/seedance/v1/lite/image-to-video",
        "veo3": "fal-ai/veo3",
        "minimax": "fal-ai/minimax/video-01-live/text-to-video",
        "minimax_i2v": "fal-ai/minimax/video-01/image-to-video",
        "kling": "fal-ai/kling-video/v2/master/text-to-video",
        "kling_i2v": "fal-ai/kling-video/v2/master/image-to-video"
    }
    
    # Configuración por defecto
    DEFAULT_MODEL = "wan"
    DEFAULT_DURATION = 3
    DEFAULT_ASPECT_RATIO = "9:16"
    
    # Configuración de procesamiento
    VERBOSE = True
    PARALLEL_PROCESSING = True
    MAX_RETRIES = 3

# ===== FUNCIONES DE UTILIDAD =====
def get_absolute_path(path):
    """Convierte cualquier path a absoluto"""
    if isinstance(path, str):
        path = Path(path)
    return path.resolve()

def ensure_directory_exists(directory):
    """Crea un directorio si no existe"""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def validate_file_exists(file_path):
    """Valida que un archivo existe"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    return True

def validate_all_paths():
    """Valida que todas las rutas críticas existen o se pueden crear"""
    errors = []
    
    # Validar directorio base de producción de video
    if not VIDEO_PRODUCTION_DIR.exists():
        errors.append(f"Directorio base de producción no existe: {VIDEO_PRODUCTION_DIR}")
    
    # Crear directorios de salida si no existen
    directories_to_create = [
        CONTENT_GENERATION_DIR,
        VIDEO_RECORDING_DIR,
        VIDEO_PROCESSING_DIR,
        VIDEO_GENERATION_DIR,
        TranscriptionConfig.OUTPUT_DIRECTORY,
        SilenceCutConfig.OUTPUT_DIRECTORY,
        SubtitlesConfig.OUTPUT_DIRECTORY,
        SynchronizationConfig.OUTPUT_DIRECTORY,
        SegmentedPromptsConfig.OUTPUT_DIR,
        VideoGenerationConfig.OUTPUT_DIR,
        VideoGenerationConfig.METADATA_DIR
    ]
    
    for directory in directories_to_create:
        try:
            ensure_directory_exists(directory)
        except Exception as e:
            errors.append(f"No se pudo crear directorio {directory}: {e}")
    
    return errors

def print_configuration_summary():
    """Imprime un resumen de la configuración actual"""
    print("🔧 CONFIGURACIÓN DEL PIPELINE DE PRODUCCIÓN DE VIDEO")
    print("=" * 60)
    print(f"📁 Directorio de producción: {VIDEO_PRODUCTION_DIR}")
    print(f"🎯 Generación de contenido: {CONTENT_GENERATION_DIR}")
    print(f"🎬 Grabación de video: {VIDEO_RECORDING_DIR}")
    print(f"⚙️  Procesamiento de video: {VIDEO_PROCESSING_DIR}")
    print(f"🤖 Generación de video AI: {VIDEO_GENERATION_DIR}")
    print(f"\n🎤 Modelo Whisper: {TranscriptionConfig.WHISPER_MODEL}")
    print(f"🎬 Codec de video: {SilenceCutConfig.VIDEO_CODEC}")
    print(f"🤖 Modelo AI: {SegmentedPromptsConfig.MODEL_NAME}")
    print(f"🎥 Modelo de video: {VideoGenerationConfig.DEFAULT_MODEL}")
    print("=" * 60)

# ===== PERFILES PREDEFINIDOS =====
def apply_quality_profile(profile="high"):
    """
    Aplica perfiles de calidad predefinidos a todo el pipeline
    
    Perfiles disponibles:
    - 'fast': Rápido pero menos preciso
    - 'balanced': Balance entre velocidad y calidad  
    - 'high': Máxima calidad (recomendado)
    """
    if profile == "fast":
        TranscriptionConfig.WHISPER_MODEL = "base"
        SubtitlesConfig.WHISPER_MODEL = "base"
        TranscriptionConfig.BEST_OF = 1
        SilenceCutConfig.CRF_VALUE = 28
        print("🚀 Perfil aplicado: RÁPIDO")
        
    elif profile == "balanced":
        TranscriptionConfig.WHISPER_MODEL = "medium"
        SubtitlesConfig.WHISPER_MODEL = "medium"
        TranscriptionConfig.BEST_OF = 3
        SilenceCutConfig.CRF_VALUE = 23
        print("⚖️  Perfil aplicado: BALANCEADO")
        
    elif profile == "high":
        TranscriptionConfig.WHISPER_MODEL = "large-v3"
        SubtitlesConfig.WHISPER_MODEL = "large-v3"
        TranscriptionConfig.BEST_OF = 5
        SilenceCutConfig.CRF_VALUE = 20
        print("💎 Perfil aplicado: ALTA CALIDAD")
        
    else:
        print(f"⚠️  Perfil '{profile}' no reconocido. Usando configuración actual.")

if __name__ == "__main__":
    # Mostrar configuración
    print_configuration_summary()
    
    # Validar configuración
    errors = validate_all_paths()
    if errors:
        print("\n❌ ERRORES DE CONFIGURACIÓN:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ Configuración válida - Todos los directorios listos")