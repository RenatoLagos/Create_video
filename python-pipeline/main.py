#!/usr/bin/env python3
"""
MAIN.PY - PIPELINE COMPLETO DE PRODUCCIÓN DE VIDEO
Ejecuta directamente todos los scripts individuales en secuencia:

FASE 1: GENERACIÓN DE CONTENIDO
1. content_01_generate_transcriptwriter.py - Genera script desde topic
2. content_02_analyze_scripts_video_prompts.py - Analiza script y genera prompts
3. content_03_generate_narrator_scripts.py - Genera script HTML del narrador

FASE 2: PROCESAMIENTO DE VIDEO  
4. pipeline_01_generate_transcription.py - Genera transcripción SRT
5. pipeline_02_cut_silence.py - Remueve silencios del video
6. pipeline_03_generate_subtitles.py - Genera subtítulos finales optimizados

FASE 3: SINCRONIZACIÓN Y PROMPTS
7. pipeline_04_synchronize_script.py - Sincroniza script con timestamps SRT
8. pipeline_05_generate_segmented_prompts.py - Genera prompts segmentados

FASE 4: OBTENCIÓN DE VIDEOS
9. generate_search_keywords.py - Extrae keywords para búsqueda de stock footage
10. search_stock_footage.py - Busca y descarga videos de Pexels/Pixabay
"""

import subprocess
import sys
import argparse
import time
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


def clean_project_directories(script_id: int, clean_all: bool = False):
    """
    Limpia las carpetas de inputs y outputs para mantener orden en cada proyecto
    
    Args:
        script_id: ID del script a procesar
        clean_all: Si True, limpia TODO (modo --reset). Si False, elimina todo EXCEPTO archivos del script_id específico
    """
    
    print(f">> Limpiando carpetas del proyecto...")
    
    # Definir carpetas a limpiar
    directories_to_clean = [
        # Contenido generado
        "VideoProduction/01_ContentGeneration/02_generated_scripts",
        "VideoProduction/01_ContentGeneration/03_analyzed_scripts", 
        "VideoProduction/01_ContentGeneration/04_narrator_scripts",
        "VideoProduction/01_ContentGeneration/05_release_material",
        
        # Procesamiento de audio/video
        "VideoProduction/02_AudioProcessing",
        "VideoProduction/03_VideoProcessing",
        
        # Generación de videos (IA - si existe)
        "VideoProduction/04_VideoGeneration",
        
        # Stock footage
        "VideoProduction/05_StockFootage/01_search_keywords",
        "VideoProduction/05_StockFootage/02_downloaded_videos",
        
        # Checkpoints
        "VideoProduction/00_checkpoints"
    ]
    
    cleaned_count = 0
    
    for dir_path in directories_to_clean:
        dir_path = Path(dir_path)
        
        if not dir_path.exists():
            continue
            
        try:
            if clean_all:
                # Limpiar toda la carpeta
                if dir_path.exists() and any(dir_path.iterdir()):
                    shutil.rmtree(dir_path)
                    dir_path.mkdir(parents=True, exist_ok=True)
                    cleaned_count += 1
                    print(f"   ✅ Limpiada: {dir_path}")
            else:
                # Eliminar todo EXCEPTO archivos del script_id actual y archivos de configuración
                current_script_patterns = [
                    f"script_id_{script_id}",
                    f"_id_{script_id}",
                    f"script_{script_id}_",
                ]
                
                protected_files = {
                    "topics.json", 
                    "category_prompts.json",
                    "config.py",
                    ".env",
                    ".gitignore"
                }
                
                files_removed = 0
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        file_name = file_path.name
                        
                        # Verificar si es del script actual
                        is_current_script = any(pattern in file_name for pattern in current_script_patterns)
                        
                        # Verificar si es archivo de configuración protegido
                        is_protected = file_name in protected_files
                        
                        # Eliminar solo si NO es del script actual y NO está protegido
                        if not is_current_script and not is_protected:
                            try:
                                file_path.unlink()
                                files_removed += 1
                            except Exception as e:
                                print(f"   ⚠️  Error eliminando {file_path}: {e}")
                    
                    elif file_path.is_dir() and file_path != dir_path:
                        # Verificar si la carpeta está relacionada con el script actual
                        dir_name = file_path.name
                        is_current_script_dir = any(pattern in dir_name for pattern in current_script_patterns)
                        
                        # Si la carpeta no es del script actual y está vacía, eliminarla
                        if not is_current_script_dir:
                            try:
                                if not any(file_path.iterdir()):
                                    file_path.rmdir()
                                    files_removed += 1
                            except Exception:
                                pass  # Ignorar errores al eliminar carpetas

                if files_removed > 0:
                    cleaned_count += 1
                    print(f"   ✅ Limpiada: {dir_path} ({files_removed} archivos)")
                    
        except Exception as e:
            print(f"   ⚠️  Error limpiando {dir_path}: {e}")
    
    # Limpiar archivos temporales en la raíz (estos siempre se pueden eliminar)
    root_files_to_clean = [
        f"video_no_silence.mp4",
        f"clean_subtitles.srt", 
        f"transcription.srt",
        f"video_with_silence.mp4"
    ]
    
    for file_name in root_files_to_clean:
        file_path = Path(file_name)
        if file_path.exists():
            try:
                file_path.unlink()
                cleaned_count += 1
                print(f"   ✅ Eliminado: {file_name}")
            except Exception as e:
                print(f"   ⚠️  Error eliminando {file_name}: {e}")
    
    if cleaned_count > 0:
        print(f"[OK] Limpieza completada: {cleaned_count} ubicaciones procesadas")
    else:
        print(f"[INFO] No había archivos para limpiar")


class CheckpointManager:
    """Maneja los checkpoints para retomar pipeline desde donde se quedó"""
    
    def __init__(self, script_id: int):
        self.script_id = script_id
        self.checkpoint_dir = Path("VideoProduction/00_checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / f"checkpoint_script_id_{script_id}.json"
    
    def save_checkpoint(self, step_number: int, step_name: str, parameters: dict = None):
        """Guarda checkpoint después de completar un paso"""
        checkpoint_data = {
            "script_id": self.script_id,
            "last_completed_step": step_number,
            "step_name": step_name,
            "completed_steps": list(range(1, step_number + 1)),
            "timestamp": datetime.now().isoformat(),
            "parameters": parameters or {}
        }
        
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
    
    def load_checkpoint(self):
        """Carga checkpoint existente si existe"""
        if not self.checkpoint_file.exists():
            return None
        
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Error cargando checkpoint: {e}")
            return None
    
    def clear_checkpoint(self):
        """Elimina checkpoint al completar pipeline exitosamente"""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
    
    def get_resume_step(self):
        """Obtiene el número de paso desde donde retomar"""
        checkpoint = self.load_checkpoint()
        if checkpoint:
            return checkpoint.get("last_completed_step", 0) + 1
        return 1
    
    def show_checkpoint_status(self, total_steps: int):
        """Muestra estado del checkpoint si existe"""
        checkpoint = self.load_checkpoint()
        if not checkpoint:
            return False
        
        print(f"\n>> CHECKPOINT ENCONTRADO para Script ID {self.script_id}")
        print(f"   Última ejecución: {checkpoint.get('timestamp', 'Unknown')}")
        print(f"   Último paso completado: {checkpoint.get('last_completed_step', 0)}/{total_steps}")
        print(f"   Último paso: {checkpoint.get('step_name', 'Unknown')}")
        print(f"   Pasos completados: {len(checkpoint.get('completed_steps', []))}/{total_steps}")
        
        # Verificar si los parámetros son compatibles
        if checkpoint.get('parameters'):
            print(f"   Parámetros usados: {checkpoint['parameters']}")
        
        return True


def run_command_quiet(command: list, step_name: str, step_number: int, total_steps: int) -> bool:
    """
    Ejecuta un comando mostrando información esencial y errores detallados
    """
    print(f"\n[{step_number}/{total_steps}] {step_name}...")
    
    try:
        start_time = time.time()
        
        # Ejecutar el comando capturando output para mejor trazabilidad de errores
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Mostrar output si existe (para debug)
        if result.stdout.strip():
            print(result.stdout.strip())
        
        print(f"[OK] Completado en {duration:.1f}s")
        return True
        
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"[ERROR] FAILED después de {duration:.1f}s")
        print(f"Exit Code: {e.returncode}")
        
        # Mostrar output estándar si existe
        if e.stdout and e.stdout.strip():
            print(f"\n>> Stdout:")
            print(e.stdout.strip())
        
        # Mostrar errores detallados
        if e.stderr and e.stderr.strip():
            print(f"\n>> Error Details:")
            print(e.stderr.strip())
        
        # Mostrar comando que falló para debug
        print(f"\n>> Failed Command:")
        print(f"   {' '.join(command)}")
        
        return False
    
    except Exception as e:
        print(f"[ERROR] Error inesperado: {str(e)}")
        print(f">> Command: {' '.join(command)}")
        return False


def run_main_pipeline(script_id: int, model: str = "wan", fps: int = 30, 
                     min_duration: int = None, max_duration: int = None, 
                     force_restart: bool = False, skip_cleanup: bool = False, reset: bool = False) -> bool:
    """
    Ejecuta el pipeline completo de producción de video ejecutando directamente
    todos los scripts individuales con soporte para checkpoints
    """
    
    # Crear manager de checkpoints
    checkpoint_manager = CheckpointManager(script_id)
    
    # Parámetros para verificar compatibilidad
    current_parameters = {
        "model": model,
        "fps": fps,
        "min_duration": min_duration,
        "max_duration": max_duration
    }
    
    print("=" * 70)
    print(">> PIPELINE PRINCIPAL DE PRODUCCIÓN DE VIDEO")
    print("=" * 70)
    print(f"Script ID: {script_id}")
    print(f"Modelo IA: {model}")
    print(f"FPS: {fps}")
    if min_duration:
        print(f"Duración mínima: {min_duration}s")
    if max_duration:
        print(f"Duración máxima: {max_duration}s")
    if force_restart:
        print(f"Modo: REINICIO FORZADO")
    if reset:
        print(f"Modo: RESET COMPLETO (limpia TODO)")
    print(f"Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    pipeline_start_time = time.time()
    
    # Definir todos los pasos del pipeline
    steps = [
        # ============= FASE 1: GENERACIÓN DE CONTENIDO =============
        {
            "name": "Generar Script desde Topic",
            "script": "content_01_generate_transcriptwriter.py",
            "params": ["--topic-id", str(script_id)],
            "optional_params": [
                ("--model", model) if model != "wan" else None,
                ("--min-duration", str(min_duration)) if min_duration else None,
                ("--max-duration", str(max_duration)) if max_duration else None
            ],
            "phase": "CONTENIDO"
        },
        {
            "name": "Analizar Script y Generar Prompts de Video",
            "script": "content_02_analyze_scripts_video_prompts.py",
            "params": ["--script-id", str(script_id)],
            "optional_params": [],
            "phase": "CONTENIDO"
        },
        {
            "name": "Generar Script HTML del Narrador",
            "script": "content_03_generate_narrator_scripts.py",
            "params": ["--script-id", str(script_id)],
            "optional_params": [],
            "phase": "CONTENIDO"
        },
        
        # ============= FASE 2: PROCESAMIENTO DE VIDEO =============
        {
            "name": "Generar Transcripción con Whisper",
            "script": "pipeline_01_generate_transcription.py",
            "params": [],
            "optional_params": [],
            "phase": "PROCESAMIENTO"
        },
        {
            "name": "Remover Silencios del Video",
            "script": "pipeline_02_cut_silence.py", 
            "params": [],
            "optional_params": [],
            "phase": "PROCESAMIENTO"
        },
        {
            "name": "Generar Subtítulos Finales Optimizados",
            "script": "pipeline_03_generate_subtitles.py",
            "params": [],
            "optional_params": [],
            "phase": "PROCESAMIENTO"
        },
        
        # ============= FASE 3: SINCRONIZACIÓN Y PROMPTS =============
        {
            "name": "Sincronizar Script con Timestamps SRT",
            "script": "pipeline_04_synchronize_script.py",
            "params": ["--script-id", str(script_id)],
            "optional_params": [],
            "phase": "SINCRONIZACIÓN"
        },
        {
            "name": "Generar Prompts Segmentados",
            "script": "pipeline_05_generate_segmented_prompts.py",
            "params": ["--script-id", str(script_id)],
            "optional_params": [],
            "phase": "SINCRONIZACIÓN"
        },
        
        # ============= FASE 4: OBTENCIÓN DE VIDEOS =============
        {
            "name": "Extraer Keywords para Búsqueda de Stock Footage",
            "script": "generate_search_keywords.py",
            "params": ["--script-id", str(script_id)],
            "optional_params": [],
            "phase": "STOCK FOOTAGE"
        },
        {
            "name": "Buscar y Descargar Videos de Stock Footage",
            "script": "search_stock_footage.py",
            "params": ["--script-id", str(script_id), "--max-videos", "50"],
            "optional_params": [],
            "phase": "STOCK FOOTAGE"
        }
    ]
    
    # Determinar desde qué paso empezar
    start_step = 1
    should_clean = True  # Por defecto, limpiar
    
    if reset:
        # Modo RESET: siempre limpiar TODO y empezar desde cero
        checkpoint_manager.clear_checkpoint()
        should_clean = True
        print(f"\n[INFO] Modo RESET: limpiando TODO y reiniciando desde paso 1")
    elif not force_restart:
        # Verificar si hay checkpoint
        has_checkpoint = checkpoint_manager.show_checkpoint_status(len(steps))
        if has_checkpoint:
            start_step = checkpoint_manager.get_resume_step()
            should_clean = False  # No limpiar si resumimos desde checkpoint
            if start_step <= len(steps):
                print(f"\n[INFO] Retomando desde paso {start_step}")
            else:
                print(f"\n[INFO] Pipeline ya completado según checkpoint")
                checkpoint_manager.clear_checkpoint()
                return True
    else:
        # Forzar reinicio - limpiar checkpoint existente
        checkpoint_manager.clear_checkpoint()
        print(f"\n[INFO] Reiniciando pipeline desde el paso 1")
    
    # Limpiar carpetas del proyecto si es necesario
    if reset:
        # RESET siempre limpia, incluso si skip_cleanup está presente
        print()
        clean_project_directories(script_id=script_id, clean_all=True)
        print()
    elif should_clean and not skip_cleanup:
        print()
        # Limpieza normal: solo otros scripts
        clean_project_directories(script_id=script_id, clean_all=False)
        print()
    elif skip_cleanup:
        print(f"\n[INFO] Omitiendo limpieza de carpetas (--skip-cleanup)")
        print()
    
    # Ejecutar cada paso
    current_phase = None
    for i, step in enumerate(steps, 1):
        # Saltar pasos ya completados
        if i < start_step:
            continue
        # Mostrar encabezado de fase si cambió
        if step["phase"] != current_phase:
            current_phase = step["phase"]
            print(f"\n{'='*20} FASE: {current_phase} {'='*20}")
        
        # Construir comando completo
        command = [sys.executable, step["script"]] + step["params"]
        
        # Agregar parámetros opcionales
        for optional_param in step["optional_params"]:
            if optional_param:  # Solo si no es None
                command.extend(optional_param)
        
        # Ejecutar el paso
        success = run_command_quiet(
            command=command,
            step_name=step["name"],
            step_number=i,
            total_steps=len(steps)
        )
        
        if success:
            # Guardar checkpoint después de paso exitoso
            checkpoint_manager.save_checkpoint(
                step_number=i,
                step_name=step["name"],
                parameters=current_parameters
            )
        else:
            pipeline_end_time = time.time()
            total_duration = pipeline_end_time - pipeline_start_time
            
            print(f"\n" + "=" * 70)
            print(f"[ERROR] PIPELINE FALLÓ EN PASO {i}")
            print(f"=" * 70)
            print(f"Paso fallido: {step['name']}")
            print(f"Script: {step['script']}")
            print(f"Fase: {step['phase']}")
            print(f"Tiempo transcurrido: {total_duration:.1f}s")
            print(f"Script ID: {script_id}")
            
            print(f"\n>> Solución de problemas:")
            print(f"   - Revisa la configuración en config.py")
            print(f"   - Verifica que todos los archivos de entrada existan")
            print(f"   - Ejecuta el script fallido individualmente:")
            print(f"     {' '.join(command)}")
            
            return False
    
    # Pipeline completado exitosamente
    pipeline_end_time = time.time()
    total_duration = pipeline_end_time - pipeline_start_time
    
    # Limpiar checkpoint al completar exitosamente
    checkpoint_manager.clear_checkpoint()
    
    print(f"\n" + "=" * 70)
    print(f"[OK] PIPELINE COMPLETADO EXITOSAMENTE!")
    print(f"=" * 70)
    print(f"Script ID: {script_id}")
    print(f"Duración total: {total_duration:.1f}s ({total_duration/60:.1f} min)")
    print(f"Pasos completados: {len(steps)}/{len(steps)}")
    print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n>> Archivos generados:")
    print(f"   - Scripts: script_id_{script_id}.json, analyzed_script_id_{script_id}.json")
    print(f"   - Narrador: narrator_script_id_{script_id}.html")
    print(f"   - Video procesado: video_no_silence.mp4")
    print(f"   - Subtítulos: clean_subtitles.srt")
    print(f"   - Prompts: segmented_prompts_id_{script_id}.json")
    print(f"   - Keywords: search_keywords_id_{script_id}.json")
    print(f"   - Videos Stock: VideoProduction/05_StockFootage/02_downloaded_videos/script_id_{script_id}/")
    
    print(f"\n[INFO] Checkpoint limpiado - Pipeline completado")
    
    return True


def validate_prerequisites():
    """Valida que todos los scripts necesarios existan"""
    
    required_scripts = [
        # Scripts de contenido
        "content_01_generate_transcriptwriter.py",
        "content_02_analyze_scripts_video_prompts.py",
        "content_03_generate_narrator_scripts.py",
        # Scripts de pipeline
        "pipeline_01_generate_transcription.py",
        "pipeline_02_cut_silence.py", 
        "pipeline_03_generate_subtitles.py",
        "pipeline_04_synchronize_script.py",
        "pipeline_05_generate_segmented_prompts.py",
        # Scripts de stock footage
        "generate_search_keywords.py",
        "search_stock_footage.py",
        # Configuración
        "config.py"
    ]
    
    missing_scripts = []
    for script in required_scripts:
        if not os.path.exists(script):
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"[ERROR] Scripts faltantes:")
        for script in missing_scripts:
            print(f"   - {script}")
        return False
    
    return True


def show_all_checkpoints():
    """Muestra todos los checkpoints existentes"""
    checkpoint_dir = Path("VideoProduction/00_checkpoints")
    
    if not checkpoint_dir.exists():
        print("[INFO] No hay directorio de checkpoints")
        return
    
    checkpoint_files = list(checkpoint_dir.glob("checkpoint_script_id_*.json"))
    
    if not checkpoint_files:
        print("[INFO] No hay checkpoints guardados")
        return
    
    print(f"\n>> CHECKPOINTS EXISTENTES ({len(checkpoint_files)} encontrados)")
    print("=" * 60)
    
    for checkpoint_file in sorted(checkpoint_files):
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            script_id = data.get('script_id', 'Unknown')
            last_step = data.get('last_completed_step', 0)
            step_name = data.get('step_name', 'Unknown')
            timestamp = data.get('timestamp', 'Unknown')
            parameters = data.get('parameters', {})
            
            print(f"\nScript ID {script_id}:")
            print(f"  Último paso: {last_step} - {step_name}")
            print(f"  Fecha: {timestamp}")
            if parameters:
                print(f"  Parámetros: {parameters}")
            print(f"  Archivo: {checkpoint_file.name}")
            
        except Exception as e:
            print(f"\n[ERROR] Error leyendo {checkpoint_file.name}: {e}")
    
    print(f"\n[INFO] Para retomar: python main.py --script-id <ID>")
    print(f"[INFO] Para reiniciar: python main.py --script-id <ID> --force-restart")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Pipeline principal completo de producción de video con Stock Footage',
        epilog="""
Ejemplos:
  python main.py --script-id 11
  python main.py --script-id 5 --min-duration 20 --max-duration 30
  python main.py --script-id 7 --force-restart
  python main.py --script-id 11 --skip-cleanup
  python main.py --script-id 17 --reset
  python main.py --show-checkpoints

Requisitos:
  Crea archivo .env con tus API keys GRATUITAS:
    PEXELS_API_KEY=tu_clave_pexels
    PIXABAY_API_KEY=tu_clave_pixabay

Este script ejecuta automáticamente todos los pasos:
  1. Generación de contenido (script, análisis, narrador)
  2. Procesamiento de video (transcripción, cortes, subtítulos)  
  3. Sincronización y prompts segmentados
  4. Obtención de videos de stock footage (Pexels/Pixabay)

SISTEMA DE LIMPIEZA:
- Por defecto, limpia carpetas del proyecto antes de empezar (mantiene orden)
- Solo elimina archivos de OTROS scripts (preserva el script-id actual)
- No limpia si se resume desde checkpoint (preserva progreso)
- Usa --skip-cleanup para omitir limpieza automática
- Usa --reset para LIMPIAR TODO (incluyendo archivos del script actual)

SISTEMA DE CHECKPOINTS:
- Si el pipeline falla, automáticamente guarda el progreso
- La próxima ejecución retomará desde donde se quedó
- Usa --force-restart para ignorar checkpoints y empezar desde cero
- Los checkpoints se guardan en VideoProduction/00_checkpoints/

VENTAJAS DEL STOCK FOOTAGE:
✅ Más rápido que generación con IA
✅ Más económico (APIs gratuitas)
✅ Videos reales profesionales
✅ Mayor variedad disponible
✅ Sin límites de duración

Ejecuta directamente todos los scripts individuales sin capas intermedias.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--script-id', type=int, required=True,
                       help='ID del script a procesar (1-60)')
    parser.add_argument('--model', default='wan',
                       help='Modelo de IA para videos (default: wan)')
    parser.add_argument('--fps', type=int, default=30,
                       help='Frames por segundo (default: 30)')
    parser.add_argument('--min-duration', type=int,
                       help='Duración mínima del video en segundos (opcional)')
    parser.add_argument('--max-duration', type=int,
                       help='Duración máxima del video en segundos (opcional)')
    parser.add_argument('--force-restart', action='store_true',
                       help='Fuerza reinicio del pipeline ignorando checkpoints')
    parser.add_argument('--skip-cleanup', action='store_true',
                       help='Omite limpieza automática de carpetas del proyecto')
    parser.add_argument('--reset', action='store_true',
                       help='RESETEA TODO: limpia todas las carpetas incluyendo archivos del script actual')
    parser.add_argument('--show-checkpoints', action='store_true',
                       help='Muestra todos los checkpoints existentes y sale')
    
    args = parser.parse_args()
    
    # Mostrar checkpoints si se solicita
    if args.show_checkpoints:
        show_all_checkpoints()
        return
    
    # Validar rango de script ID
    if args.script_id < 1 or args.script_id > 60:
        print(f"[ERROR] Script ID inválido: {args.script_id}")
        print("Rango válido: 1-60")
        sys.exit(1)
    
    # Validar prerequisites
    print(">> Verificando prerequisites...")
    if not validate_prerequisites():
        print("[ERROR] Faltan scripts necesarios!")
        sys.exit(1)
    
    print("[OK] Todos los scripts están disponibles")
    
    # Validar API keys para stock footage
    print(">> Validando API keys para stock footage...")
    pexels_key = os.getenv('PEXELS_API_KEY')
    pixabay_key = os.getenv('PIXABAY_API_KEY')
    
    if not pexels_key and not pixabay_key:
        print("[ERROR] No se encontraron API keys para stock footage!")
        print("\n📝 Crea archivo .env con tus claves:")
        print("  PEXELS_API_KEY=tu_clave_pexels")
        print("  PIXABAY_API_KEY=tu_clave_pixabay")
        print("\n🔑 Obtén claves GRATUITAS en:")
        print("  • Pexels: https://www.pexels.com/api/new/")
        print("  • Pixabay: https://pixabay.com/api/docs/")
        sys.exit(1)
    
    apis_available = []
    if pexels_key:
        apis_available.append("Pexels")
    if pixabay_key:
        apis_available.append("Pixabay")
    
    print(f"[OK] APIs disponibles: {', '.join(apis_available)}")
    
    # Ejecutar pipeline completo
    try:
        success = run_main_pipeline(
            script_id=args.script_id,
            model=args.model,
            fps=args.fps,
            min_duration=args.min_duration,
            max_duration=args.max_duration,
            force_restart=args.force_restart,
            skip_cleanup=args.skip_cleanup,
            reset=args.reset
        )
        
        if success:
            print(f"\n[OK] PRODUCCIÓN COMPLETADA!")
            print(f"   Videos de stock footage para Script ID {args.script_id} descargados")
            print(f"   Revisa: VideoProduction/05_StockFootage/02_downloaded_videos/script_id_{args.script_id}/")
            sys.exit(0)
        else:
            print(f"\n[ERROR] Producción falló")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n[STOP] Pipeline interrumpido por el usuario (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()