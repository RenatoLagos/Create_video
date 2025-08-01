import os
import math
import json
import requests
from pathlib import Path
import fal_client
from typing import Optional, Dict, List
from datetime import datetime
from config import VideoGenerationConfig, validate_all_paths, print_configuration_summary

# Configurar la clave API desde FAL_API_KEY si está disponible
if os.getenv("FAL_API_KEY") and not os.getenv("FAL_KEY"):
    os.environ["FAL_KEY"] = os.getenv("FAL_API_KEY")

# Modelos de video disponibles
VIDEO_MODELS = {
    # Wan 2.2 - Modelo principal recomendado para contenido educativo
    "wan": "fal-ai/wan/v2.2-5b/text-to-video",
    "wan_i2v": "fal-ai/wan/v2.2-5b/image-to-video",
    
    # Modelos alternativos
    "seedance": "fal-ai/bytedance/seedance/v1/lite/text-to-video",
    "seedance_i2v": "fal-ai/bytedance/seedance/v1/lite/image-to-video",
    "veo3": "fal-ai/veo3",
    "minimax": "fal-ai/minimax/video-01-live/text-to-video", 
    "minimax_i2v": "fal-ai/minimax/video-01/image-to-video",
    "kling": "fal-ai/kling-video/v2/master/text-to-video",
    "kling_i2v": "fal-ai/kling-video/v2/master/image-to-video"
}

# Wan 2.2 Prompt Formulas and Cinematic Controls
class WanPromptBuilder:
    """Builder class for creating optimized prompts for Wan 2.2 model"""
    
    @staticmethod
    def basic_formula(subject: str, scene: str, motion: str) -> str:
        """
        Basic Formula: Subject + Scene + Motion
        Ideal for new users or creative inspiration
        """
        return f"{subject} {scene} {motion}"
    
    @staticmethod
    def advanced_formula(
        subject: str, 
        scene: str, 
        motion: str,
        subject_desc: str = "",
        scene_desc: str = "",
        motion_desc: str = "",
        aesthetic_control: str = "",
        stylization: str = ""
    ) -> str:
        """
        Advanced Formula: Subject (Description) + Scene (Description) + Motion (Description) + Aesthetic Control + Stylization
        For experienced users wanting enhanced video quality
        """
        parts = []
        
        # Subject with description
        if subject_desc:
            parts.append(f"{subject}, {subject_desc}")
        else:
            parts.append(subject)
        
        # Scene with description  
        if scene_desc:
            parts.append(f"{scene}, {scene_desc}")
        else:
            parts.append(scene)
        
        # Motion with description
        if motion_desc:
            parts.append(f"{motion}, {motion_desc}")
        else:
            parts.append(motion)
        
        # Add aesthetic control
        if aesthetic_control:
            parts.append(aesthetic_control)
        
        # Add stylization
        if stylization:
            parts.append(stylization)
        
        return ". ".join(parts)
    
    @staticmethod
    def image_to_video_formula(motion_desc: str, camera_movement: str = "") -> str:
        """
        Image-to-Video Formula: Motion Description + Camera Movement
        For when source image already establishes subject, scene, and style
        """
        if camera_movement:
            return f"{motion_desc}. {camera_movement}"
        return motion_desc

# Cinematic Controls for Educational Content
class CinematicControls:
    """Cinematic control templates optimized for educational Spanish content"""
    
    LIGHTING = {
        "natural_warm": "warm natural lighting, golden hour glow",
        "professional": "professional studio lighting, even illumination",
        "classroom": "bright classroom lighting, clear visibility",
        "cozy": "soft warm lighting, inviting atmosphere"
    }
    
    SHOT_SIZES = {
        "extreme_closeup": "extreme close-up shot",
        "closeup": "close-up shot", 
        "medium_closeup": "medium close-up shot",
        "medium": "medium shot",
        "medium_wide": "medium wide shot",
        "wide": "wide shot"
    }
    
    CAMERA_ANGLES = {
        "eye_level": "eye-level angle",
        "slightly_low": "slightly low angle",
        "slightly_high": "slightly high angle",
        "over_shoulder": "over-the-shoulder angle"
    }
    
    CAMERA_MOVEMENTS = {
        "static": "static shot, fixed camera",
        "slow_zoom_in": "slow zoom in",
        "slow_zoom_out": "slow zoom out", 
        "gentle_pan_left": "gentle pan left",
        "gentle_pan_right": "gentle pan right",
        "dolly_in": "dolly in movement",
        "dolly_out": "dolly out movement"
    }
    
    EDUCATIONAL_STYLES = {
        "professional": "professional educational style, clean and modern",
        "friendly": "friendly educational style, approachable and warm",
        "cultural": "cultural educational style, authentic Spanish atmosphere",
        "modern_classroom": "modern classroom aesthetic, contemporary design"
    }

# Educational Spanish Content Helpers
class SpanishEducationHelper:
    """Helper class for creating Spanish educational video prompts"""
    
    @staticmethod
    def create_pronunciation_prompt(
        word: str,
        phonetic: str,
        context: str = "classroom",
        emphasis: str = "mouth_focus"
    ) -> str:
        """Create prompts for pronunciation videos"""
        
        base_subjects = {
            "mouth_focus": f"Close-up of a Spanish teacher's mouth clearly pronouncing '{word}'",
            "teacher_full": f"Professional Spanish teacher demonstrating pronunciation of '{word}'",
            "split_screen": f"Split screen showing teacher and phonetic text '{phonetic}'"
        }
        
        contexts = {
            "classroom": "in a modern classroom setting with whiteboard",
            "studio": "in a professional recording studio with clean background",
            "cultural": "with Spanish cultural elements in the background",
            "home_office": "in a welcoming home office setup"
        }
        
        subject = base_subjects.get(emphasis, base_subjects["mouth_focus"])
        scene = contexts.get(context, contexts["classroom"])
        motion = f"speaking clearly and slowly, emphasizing the pronunciation of '{word}'"
        
        aesthetic = f"{CinematicControls.LIGHTING['professional']}, {CinematicControls.SHOT_SIZES['closeup']}"
        style = CinematicControls.EDUCATIONAL_STYLES['professional']
        
        return WanPromptBuilder.advanced_formula(
            subject=subject,
            scene=scene, 
            motion=motion,
            aesthetic_control=aesthetic,
            stylization=style
        )
    
    @staticmethod
    def create_cultural_context_prompt(
        topic: str,
        setting: str = "spain",
        activity: str = "daily_life"
    ) -> str:
        """Create prompts for cultural context videos"""
        
        settings = {
            "spain": "authentic Spanish street or plaza with traditional architecture",
            "restaurant": "cozy Spanish restaurant with traditional decor",
            "market": "vibrant Spanish market with fresh produce and local vendors",
            "home": "traditional Spanish home interior with cultural elements"
        }
        
        activities = {
            "daily_life": "people engaging in typical daily activities",
            "dining": "people enjoying a meal together in Spanish style",
            "shopping": "locals shopping and interacting with vendors",
            "conversation": "friendly conversation between Spanish speakers"
        }
        
        subject = f"Spanish people in their natural environment"
        scene = settings.get(setting, settings["spain"])
        motion = activities.get(activity, activities["daily_life"])
        
        aesthetic = f"{CinematicControls.LIGHTING['natural_warm']}, {CinematicControls.SHOT_SIZES['medium_wide']}"
        style = CinematicControls.EDUCATIONAL_STYLES['cultural']
        
        return WanPromptBuilder.advanced_formula(
            subject=subject,
            scene=scene,
            motion=motion,
            aesthetic_control=aesthetic,
            stylization=style
        )
    
    @staticmethod
    def create_grammar_demonstration_prompt(
        grammar_point: str,
        visual_aid: str = "text_overlay"
    ) -> str:
        """Create prompts for grammar demonstration videos"""
        
        visual_aids = {
            "text_overlay": "with animated text overlays showing grammar examples",
            "whiteboard": "using a whiteboard to illustrate grammar concepts",
            "digital_screen": "with digital graphics explaining grammar rules",
            "props": "using physical props to demonstrate grammar concepts"
        }
        
        subject = f"Professional Spanish teacher explaining {grammar_point}"
        scene = "in a modern educational setting"
        motion = f"demonstrating and explaining {grammar_point} clearly {visual_aids.get(visual_aid, visual_aids['text_overlay'])}"
        
        aesthetic = f"{CinematicControls.LIGHTING['classroom']}, {CinematicControls.SHOT_SIZES['medium']}"
        style = CinematicControls.EDUCATIONAL_STYLES['modern_classroom']
        
        return WanPromptBuilder.advanced_formula(
            subject=subject,
            scene=scene,
            motion=motion,
            aesthetic_control=aesthetic,
            stylization=style
        )

# Función para calcular frames necesarios basado en duración
def calculate_frames_for_duration(duration_seconds: float, target_fps: int = 30) -> int:
    """
    Calcula el número de frames necesarios para una duración específica
    Mantiene los frames entre 81-121 según el schema de Wan 2.2
    """
    calculated_frames = math.ceil(duration_seconds * target_fps)
    
    # Asegurar que esté dentro del rango permitido (81-121)
    frames = max(81, min(121, calculated_frames))
    
    print(f"   📊 Duración: {duration_seconds:.1f}s | FPS: {target_fps} | Frames calculados: {calculated_frames} | Frames finales: {frames}")
    
    return frames

# Función para generar video con soporte completo para Wan 2.2 usando schema actualizado
def generate_video(
    prompt, 
    image_url=None, 
    duration=5, 
    resolution="720p", 
    fps=30, 
    model="wan",
    aspect_ratio="9:16",  # Instagram Reels formato vertical
    negative_prompt=None,
    enable_prompt_expansion=False,
    guidance_scale=3.5,
    num_inference_steps=40
):
    # Validar duración según el modelo
    if model.startswith("seedance") and duration not in [5, 10]:
        raise ValueError("Seedance: La duración debe ser 5 o 10 segundos")
    elif model.startswith("wan"):
        # Wan 2.2 supports flexible durations, typically 3-10 seconds
        if duration < 2 or duration > 15:
            raise ValueError("Wan 2.2: La duración debe estar entre 2 y 15 segundos")
    
    print(f"🚀 Iniciando generación de video...")
    print(f"📝 Prompt: {prompt}")
    print(f"⏱️ Duración: {duration}s")
    print(f"🎬 Modelo: {model}")
    
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            print(f"⏳ En progreso...")
            for log in update.logs:
                print(f"📋 {log['message']}")
        elif isinstance(update, fal_client.Queued):
            print(f"🔄 En cola, posición: {getattr(update, 'position', 'N/A')}")
        else:
            print(f"📡 Estado: {type(update).__name__}")
    
    # Determinar el endpoint
    if image_url:
        endpoint = VIDEO_MODELS.get(f"{model}_i2v", VIDEO_MODELS.get("seedance_i2v"))
    else:
        endpoint = VIDEO_MODELS.get(model, VIDEO_MODELS.get("seedance"))
    
    print(f"🎯 Endpoint: {endpoint}")
    
    # Preparar argumentos base
    arguments = {}
    
    # Añadir parámetros específicos según el modelo
    if model.startswith("wan"):
        # Wan 2.2 uses comprehensive schema parameters
        num_frames = calculate_frames_for_duration(duration, fps)
        
        # Default negative prompt for educational content
        if negative_prompt is None:
            negative_prompt = "bright colors, overexposed, static, blurred details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, malformed limbs, fused fingers, still picture, cluttered background, three legs, many people in the background, walking backwards"
        
        arguments.update({
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_frames": num_frames,
            "frames_per_second": fps,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "num_inference_steps": num_inference_steps,
            "enable_safety_checker": True,
            "enable_prompt_expansion": enable_prompt_expansion,
            "guidance_scale": guidance_scale,
            "shift": 5,
            "interpolator_model": "film",
            "num_interpolated_frames": 0,
            "adjust_fps_for_interpolation": True
        })
        
        # Remove the original prompt from arguments since it's now included above
        if "prompt" in arguments and arguments["prompt"] == prompt:
            pass  # Already set correctly
            
    elif model.startswith("seedance"):
        arguments.update({
            "duration": duration,
            "resolution": resolution,
            "fps": fps
        })
    elif model.startswith("minimax"):
        arguments["duration"] = min(duration, 6)  # MiniMax máximo 6s
    elif model.startswith("kling"):
        arguments["duration"] = min(duration, 10)  # Kling máximo 10s
    
    if image_url:
        arguments["image"] = image_url
    
    try:
        print("📤 Enviando solicitud...")
        # Realizar la llamada
        result = fal_client.subscribe(
            endpoint,
            arguments=arguments,
            with_logs=True,
            on_queue_update=on_queue_update
        )
        
        print("📥 Respuesta recibida:")
        print(f"🔍 Resultado completo: {result}")
        
        # Extraer URL del video
        video_url = None
        if result:
            if "video" in result and isinstance(result["video"], dict) and "url" in result["video"]:
                video_url = result["video"]["url"]
            elif "video" in result and isinstance(result["video"], str):
                video_url = result["video"]
            elif isinstance(result, dict):
                # Buscar URL en diferentes estructuras posibles
                for key in ["url", "video_url", "output_url"]:
                    if key in result:
                        video_url = result[key]
                        break
        
        if video_url:
            print("✅ Video generado exitosamente!")
            print(f"🔗 URL: {video_url}")
            return video_url
        else:
            print("❌ No se pudo extraer la URL del video")
            print(f"📋 Estructura de respuesta: {result}")
            return None
            
    except Exception as e:
        print(f"❌ Error durante la generación: {str(e)}")
        raise

# Función para calcular costo estimado
def estimate_cost(duration_sec, resolution="720p", fps=24, model="wan"):
    if model.startswith("wan"):
        # Wan 2.2 pricing: approximately $0.15-0.25 per video depending on duration
        base_cost = 0.15
        duration_factor = max(1.0, duration_sec / 5.0)  # Scale with duration
        return round(base_cost * duration_factor, 4)
    elif model.startswith("seedance"):
        # Tarifa fija por video de 5s: USD 0.18
        factor = duration_sec / 5.0
        return round(0.18 * factor, 4)
    elif model.startswith("minimax"):
        # MiniMax aproximadamente $0.20 por video
        return 0.20
    elif model.startswith("kling"):
        # Kling aproximadamente $0.25 por 5s
        factor = duration_sec / 5.0
        return round(0.25 * factor, 4)
    else:
        # Cálculo genérico por tokens
        res_dims = {"480p": (852, 480), "720p": (1280, 720), "1080p": (1920, 1080)}
        w, h = res_dims.get(resolution, (1280, 720))
        tokens = (w * h * fps * duration_sec) / 1024 / 1e6
        return round(tokens * 1.80, 4)

# Función para listar modelos disponibles
def list_models():
    print("🎬 Modelos de video disponibles:")
    for key, endpoint in VIDEO_MODELS.items():
        print(f"  - {key}: {endpoint}")

# Función especializada para generar videos educativos de español
def generate_educational_spanish_video(
    content_type: str,
    word_or_topic: str = "",
    phonetic: str = "",
    context: str = "classroom",
    emphasis: str = "mouth_focus",
    setting: str = "spain",
    activity: str = "daily_life",
    grammar_point: str = "",
    visual_aid: str = "text_overlay",
    duration: int = 3,
    model: str = "wan"
) -> Optional[str]:
    """
    Generate educational Spanish videos using optimized prompts for different content types
    
    Args:
        content_type: "pronunciation", "cultural", or "grammar"
        word_or_topic: The word to pronounce or topic to cover
        phonetic: Phonetic transcription (for pronunciation)
        context: Setting context (classroom, studio, cultural, home_office)
        emphasis: Focus type (mouth_focus, teacher_full, split_screen)
        setting: Cultural setting (spain, restaurant, market, home)
        activity: Cultural activity (daily_life, dining, shopping, conversation)
        grammar_point: Grammar concept to explain
        visual_aid: Visual aid type (text_overlay, whiteboard, digital_screen, props)
        duration: Video duration in seconds
        model: AI model to use
    
    Returns:
        URL of generated video or None if failed
    """
    
    print(f"🎓 Generando video educativo de español: {content_type}")
    
    # Generate appropriate prompt based on content type
    if content_type == "pronunciation":
        if not word_or_topic:
            raise ValueError("Para pronunciación, 'word_or_topic' es requerido")
        
        prompt = SpanishEducationHelper.create_pronunciation_prompt(
            word=word_or_topic,
            phonetic=phonetic or f"[{word_or_topic}]",
            context=context,
            emphasis=emphasis
        )
        
    elif content_type == "cultural":
        prompt = SpanishEducationHelper.create_cultural_context_prompt(
            topic=word_or_topic or "Spanish culture",
            setting=setting,
            activity=activity
        )
        
    elif content_type == "grammar":
        prompt = SpanishEducationHelper.create_grammar_demonstration_prompt(
            grammar_point=grammar_point or word_or_topic or "Spanish grammar",
            visual_aid=visual_aid
        )
        
    else:
        raise ValueError("content_type debe ser 'pronunciation', 'cultural', o 'grammar'")
    
    print(f"📝 Prompt generado: {prompt[:100]}...")
    
    try:
        # Generate the video
        video_url = generate_video(
            prompt=prompt,
            duration=duration,
            model=model
        )
        
        if video_url:
            print(f"✅ Video educativo generado exitosamente!")
            print(f"🎯 Tipo: {content_type}")
            print(f"📚 Tema: {word_or_topic or grammar_point}")
            print(f"🔗 URL: {video_url}")
            
            # Calculate and show cost
            cost = estimate_cost(duration, model=model)
            print(f"💰 Costo estimado: USD {cost}")
            
        return video_url
        
    except Exception as e:
        print(f"❌ Error generando video educativo: {e}")
        return None

# Función para descargar video desde URL
def download_video(video_url: str, output_path: str) -> bool:
    """
    Descarga un video desde una URL y lo guarda en el path especificado
    """
    try:
        print(f"   📥 Descargando video...")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"   ✅ Video guardado en: {output_path}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error descargando video: {e}")
        return False

# Función principal para procesar segmented_prompts.json y generar videos
def process_segmented_prompts_and_generate_videos(
    input_file: str = None,
    output_dir: str = None,
    target_fps: int = 30,
    model: str = "wan"
):
    """
    Procesa el archivo segmented_prompts.json y genera videos para cada prompt
    """
    
    # Usar rutas de configuración si no se proporcionan
    if input_file is None:
        input_file = str(VideoGenerationConfig.INPUT_FILE)
    if output_dir is None:
        output_dir = str(VideoGenerationConfig.OUTPUT_DIR)
    
    print("🎬 Iniciando procesamiento de prompts segmentados...")
    print(f"📖 Input: {input_file}")
    print(f"💾 Output: {output_dir}")
    
    # Validar configuración
    config_errors = validate_all_paths()
    if config_errors:
        print("❌ ERRORES DE CONFIGURACIÓN:")
        for error in config_errors:
            print(f"  - {error}")
        return []
    
    # Crear directorio de salida
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Cargar datos de segmentación
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        phrases = data.get('analysis', {}).get('phrases_with_video_prompts', [])
        print(f"🎭 Encontradas {len(phrases)} frases para procesar")
        
        generated_videos = []
        total_cost = 0.0
        
        for phrase in phrases:
            phrase_num = phrase.get('phrase_number', 0)
            phrase_text = phrase.get('phrase', '')
            editing_suggestion = phrase.get('editing_suggestion', '')
            segmentation = phrase.get('segmentation', {})
            
            print(f"\n🎬 Procesando Frase {phrase_num}: {phrase_text[:50]}...")
            print(f"   📝 Sugerencia de edición: {editing_suggestion}")
            
            # Solo procesar si la sugerencia NO es "Narrator only on screen"
            if editing_suggestion == "Narrator only on screen":
                print(f"   ⏭️ Saltando - Solo narrador en pantalla")
                continue
            
            prompts_to_generate = []
            
            # Determinar qué prompts generar
            if segmentation.get('needs_segmentation', False):
                # Usar prompts segmentados
                segments = segmentation.get('segments', [])
                print(f"   🔪 Frase segmentada en {len(segments)} partes")
                
                for segment in segments:
                    prompts_to_generate.append({
                        'prompt': segment.get('adapted_prompt', ''),
                        'duration': segment.get('timing', {}).get('duration', 3.0),
                        'segment_number': segment.get('segment_number', 1),
                        'narrative_focus': segment.get('narrative_focus', 'desarrollo'),
                        'is_segmented': True
                    })
            else:
                # Usar prompt original
                original_prompt = phrase.get('video_prompt', '')
                if original_prompt:
                    prompts_to_generate.append({
                        'prompt': original_prompt,
                        'duration': phrase.get('timing', {}).get('duration', 3.0),
                        'segment_number': 1,
                        'narrative_focus': 'completo',
                        'is_segmented': False
                    })
                else:
                    print(f"   ⚠️ No se encontró video_prompt para la frase {phrase_num}")
                    continue
            
            # Generar videos para cada prompt
            for i, prompt_data in enumerate(prompts_to_generate, 1):
                prompt_text = prompt_data['prompt'].strip('"')
                duration = round(prompt_data['duration'])  # Redondear duración
                segment_num = prompt_data['segment_number']
                
                if not prompt_text:
                    print(f"   ⚠️ Prompt vacío para segmento {segment_num}")
                    continue
                
                print(f"\n   🎥 Generando video {i}/{len(prompts_to_generate)} (Segmento {segment_num})")
                print(f"   ⏱️ Duración objetivo: {duration}s")
                print(f"   📝 Prompt: {prompt_text[:100]}...")
                
                try:
                    # Generar video
                    video_url = generate_video(
                        prompt=prompt_text,
                        duration=duration,
                        fps=target_fps,
                        model=model,
                        aspect_ratio="9:16",  # Instagram Reels formato vertical
                        resolution="720p"
                    )
                    
                    if video_url:
                        # Crear nombre de archivo
                        filename = f"phrase_{phrase_num:02d}_segment_{segment_num:02d}.mp4"
                        video_path = output_path / filename
                        
                        # Descargar video
                        if download_video(video_url, str(video_path)):
                            # Calcular costo
                            cost = estimate_cost(duration, model=model)
                            total_cost += cost
                            
                            # Agregar información del video generado
                            video_info = {
                                'phrase_number': phrase_num,
                                'segment_number': segment_num,
                                'phrase_text': phrase_text,
                                'editing_suggestion': editing_suggestion,
                                'prompt_used': prompt_text,
                                'duration_seconds': duration,
                                'target_fps': target_fps,
                                'is_segmented': prompt_data['is_segmented'],
                                'narrative_focus': prompt_data['narrative_focus'],
                                'video_filename': filename,
                                'video_path': str(video_path),
                                'video_url': video_url,
                                'cost_usd': cost,
                                'generated_at': datetime.now().isoformat(),
                                'model_used': model,
                                'generation_parameters': {
                                    'frames_per_second': target_fps,
                                    'resolution': "720p",
                                    'aspect_ratio': "9:16",  # Instagram Reels formato vertical
                                    'num_frames': calculate_frames_for_duration(duration, target_fps)
                                }
                            }
                            
                            generated_videos.append(video_info)
                            
                            print(f"   ✅ Video generado exitosamente: {filename}")
                            print(f"   💰 Costo: ${cost:.4f}")
                        else:
                            print(f"   ❌ Error descargando video para frase {phrase_num}, segmento {segment_num}")
                    else:
                        print(f"   ❌ Error generando video para frase {phrase_num}, segmento {segment_num}")
                        
                except Exception as e:
                    print(f"   ❌ Error procesando frase {phrase_num}, segmento {segment_num}: {e}")
                    continue
        
        # Guardar JSON con información de videos generados
        metadata_dir = VideoGenerationConfig.METADATA_DIR
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = metadata_dir / VideoGenerationConfig.METADATA_FILE
        metadata = {
            'total_videos_generated': len(generated_videos),
            'total_cost_usd': round(total_cost, 4),
            'generation_summary': {
                'input_file': input_file,
                'output_directory': output_dir,
                'target_fps': target_fps,
                'model_used': model,
                'generated_at': datetime.now().isoformat()
            },
            'videos': generated_videos
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Resumen final
        print(f"\n🎉 Procesamiento completado!")
        print(f"📊 Resumen:")
        print(f"   • Videos generados: {len(generated_videos)}")
        print(f"   • Costo total: ${total_cost:.4f} USD")
        print(f"   • Directorio de salida: {output_dir}")
        print(f"   • Archivo de metadatos: {metadata_file}")
        
        return generated_videos
        
    except Exception as e:
        print(f"❌ Error procesando archivo: {e}")
        return []

# --- Ejecución de prueba ---
if __name__ == "__main__":
    print("🎥 Generador de Video con fal.ai")
    print("=" * 40)
    
    # Mostrar modelos disponibles
    list_models()
    print()
    
    # Configuración para contenido educativo de español
    print("\n🎓 Ejemplo de contenido educativo de español:")
    
    # Ejemplo 1: Prompt optimizado con Wan 2.2 para pronunciación
    pronunciation_prompt = SpanishEducationHelper.create_pronunciation_prompt(
        word="jamón",
        phonetic="ha-MON",
        context="classroom",
        emphasis="mouth_focus"
    )
    
    print(f"\n📝 Prompt de pronunciación generado:")
    print(f"   {pronunciation_prompt}")
    
    # Ejemplo 2: Prompt básico usando fórmula básica
    basic_prompt = WanPromptBuilder.basic_formula(
        subject="Spanish teacher explaining pronunciation",
        scene="in a modern classroom",
        motion="speaking clearly and demonstrating mouth movements"
    )
    
    print(f"\n📝 Prompt básico generado:")
    print(f"   {basic_prompt}")
    
    # Configuración para la prueba
    model = "wan"  # Modelo principal recomendado
    duration = 3  # Ideal para contenido educativo corto
    
    # Usar el prompt de pronunciación para la prueba
    prompt = pronunciation_prompt
    
    try:
        # Procesar archivo de prompts segmentados y generar videos
        print(f"\n🎬 Procesando prompts segmentados y generando videos...")
        
        generated_videos = process_segmented_prompts_and_generate_videos(
            target_fps=30,
            model="wan"
        )
        
        if generated_videos:
            print(f"\n🎉 ¡Proceso completado exitosamente!")
            print(f"📹 Videos generados: {len(generated_videos)}")
            
            # Mostrar resumen de los primeros videos
            print(f"\n📋 Primeros videos generados:")
            for video in generated_videos[:3]:
                print(f"   • {video['video_filename']} - Frase {video['phrase_number']} - ${video['cost_usd']:.4f}")
                
            if len(generated_videos) > 3:
                print(f"   • ... y {len(generated_videos) - 3} videos más")
        
        # Ejemplo alternativo con función educativa individual
        print(f"\n" + "="*50)
        print(f"🎓 Ejemplo adicional - Video educativo individual:")
        
        educational_url = generate_educational_spanish_video(
            content_type="pronunciation",
            word_or_topic="hola",
            phonetic="OH-la",
            context="studio",
            emphasis="mouth_focus",
            duration=3
        )
        
        if educational_url:
            print(f"\n✨ Video educativo generado: {educational_url}")
        
    except Exception as e:
        print(f"💥 Error: {e}")
