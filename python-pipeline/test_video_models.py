#!/usr/bin/env python3
"""
TEST VIDEO MODELS - Script rápido para testear modelos de generación de video
Ejecuta solo la fracción necesaria del pipeline:

1. content_01_generate_transcriptwriter.py - Genera script desde topic
2. content_02_analyze_scripts_video_prompts.py - Genera prompts de video
3. Convierte formato para run_pipeline_generate_video.py
4. run_pipeline_generate_video.py - Genera videos con IA

Ideal para testear diferentes modelos sin procesar audio/video del narrador.
"""

import subprocess
import sys
import argparse
import time
import os
import json
from datetime import datetime
from pathlib import Path


def run_command_quiet(command: list, step_name: str, step_number: int, total_steps: int) -> bool:
    """Ejecuta un comando mostrando información esencial y errores detallados"""
    print(f"\n[{step_number}/{total_steps}] {step_name}...")
    
    try:
        start_time = time.time()
        
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
        
        # Mostrar output si existe
        if result.stdout.strip():
            print(result.stdout.strip())
        
        print(f"[OK] Completado en {duration:.1f}s")
        return True
        
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"[ERROR] FAILED después de {duration:.1f}s")
        print(f"Exit Code: {e.returncode}")
        
        if e.stdout and e.stdout.strip():
            print(f"\n>> Stdout:")
            print(e.stdout.strip())
        
        if e.stderr and e.stderr.strip():
            print(f"\n>> Error Details:")
            print(e.stderr.strip())
        
        print(f"\n>> Failed Command:")
        print(f"   {' '.join(command)}")
        
        return False
    
    except Exception as e:
        print(f"[ERROR] Error inesperado: {str(e)}")
        print(f">> Command: {' '.join(command)}")
        return False


def convert_analyzed_to_segmented_format(script_id: int):
    """
    Convierte el formato de analyzed_script a segmented_prompts sin segmentación real
    para compatibilidad con run_pipeline_generate_video.py
    """
    
    print(f"\n[CONVERT] Convirtiendo formato analyzed_script → segmented_prompts...")
    
    try:
        # Rutas de archivos
        from config import ContentGenerationConfig, VideoGenerationConfig
        
        analyzed_file = Path(ContentGenerationConfig.ANALYZED_SCRIPTS_FILE).parent / f"analyzed_script_id_{script_id}.json"
        segmented_output_dir = VideoGenerationConfig.OUTPUT_DIR.parent / "01_segmented_prompts"
        segmented_output_dir.mkdir(parents=True, exist_ok=True)
        segmented_file = segmented_output_dir / f"segmented_prompts_id_{script_id}.json"
        
        # Cargar archivo analyzed
        if not analyzed_file.exists():
            print(f"[ERROR] Archivo analyzed no encontrado: {analyzed_file}")
            return False
        
        with open(analyzed_file, 'r', encoding='utf-8') as f:
            analyzed_data = json.load(f)
        
        # Convertir formato
        phrases_analyzed = analyzed_data.get('analysis', {}).get('phrases_with_video_prompts', [])
        
        # Añadir campos de segmentación con needs_segmentation=False
        for phrase in phrases_analyzed:
            phrase['segmentation'] = {
                'needs_segmentation': False,
                'reason': 'No segmentation for video model testing',
                'original_duration': 3.0  # Duración por defecto
            }
        
        # Crear estructura compatible
        segmented_data = {
            **analyzed_data,  # Mantener todos los campos originales
            'conversion_info': {
                'converted_from': str(analyzed_file),
                'conversion_type': 'analyzed_to_segmented_for_testing',
                'converted_at': datetime.now().isoformat(),
                'script_id': script_id
            }
        }
        
        # Guardar archivo convertido
        with open(segmented_file, 'w', encoding='utf-8') as f:
            json.dump(segmented_data, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Conversión completada:")
        print(f"   Input: {analyzed_file}")
        print(f"   Output: {segmented_file}")
        print(f"   Frases procesadas: {len(phrases_analyzed)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en conversión: {e}")
        return False


def test_video_model(script_id: int, model: str = "wan", fps: int = 30, 
                    min_duration: int = None, max_duration: int = None) -> bool:
    """
    Ejecuta el pipeline de testing rápido para modelos de video
    """
    
    print("=" * 70)
    print(">> TEST VIDEO MODELS - PIPELINE RÁPIDO")
    print("=" * 70)
    print(f"Script ID: {script_id}")
    print(f"Modelo IA: {model}")
    print(f"FPS: {fps}")
    if min_duration:
        print(f"Duración mínima: {min_duration}s")
    if max_duration:
        print(f"Duración máxima: {max_duration}s")
    print(f"Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    pipeline_start_time = time.time()
    
    # Definir pasos del pipeline de testing
    steps = [
        # PASO 1: Generar script
        {
            "name": "Generar Script desde Topic",
            "script": "content_01_generate_transcriptwriter.py",
            "params": ["--topic-id", str(script_id)],
            "optional_params": [
                ("--min-duration", str(min_duration)) if min_duration else None,
                ("--max-duration", str(max_duration)) if max_duration else None
            ]
        },
        
        # PASO 2: Generar prompts de video
        {
            "name": "Analizar Script y Generar Prompts de Video",
            "script": "content_02_analyze_scripts_video_prompts.py",
            "params": ["--script-id", str(script_id)],
            "optional_params": []
        }
    ]
    
    # Ejecutar pasos 1 y 2
    for i, step in enumerate(steps, 1):
        command = [sys.executable, step["script"]] + step["params"]
        
        # Agregar parámetros opcionales
        for optional_param in step["optional_params"]:
            if optional_param:
                command.extend(optional_param)
        
        success = run_command_quiet(
            command=command,
            step_name=step["name"],
            step_number=i,
            total_steps=4  # 2 scripts + 1 conversión + 1 generación de video
        )
        
        if not success:
            print(f"\n[ERROR] PIPELINE FALLÓ EN PASO {i}")
            return False
    
    # PASO 3: Convertir formato
    success = convert_analyzed_to_segmented_format(script_id)
    if not success:
        print(f"\n[ERROR] PIPELINE FALLÓ EN CONVERSIÓN")
        return False
    
    print(f"[3/4] Conversión de formato... [OK] Completado")
    
    # PASO 4: Generar videos
    video_command = [
        sys.executable, "run_pipeline_generate_video.py",
        "--input", f"VideoProduction/04_VideoGeneration/01_segmented_prompts/segmented_prompts_id_{script_id}.json",
        "--model", model,
        "--fps", str(fps)
    ]
    
    success = run_command_quiet(
        command=video_command,
        step_name="Generar Videos con Inteligencia Artificial",
        step_number=4,
        total_steps=4
    )
    
    if not success:
        print(f"\n[ERROR] PIPELINE FALLÓ EN GENERACIÓN DE VIDEOS")
        return False
    
    # Pipeline completado
    pipeline_end_time = time.time()
    total_duration = pipeline_end_time - pipeline_start_time
    
    print(f"\n" + "=" * 70)
    print(f"[OK] TEST COMPLETADO EXITOSAMENTE!")
    print(f"=" * 70)
    print(f"Script ID: {script_id}")
    print(f"Modelo probado: {model}")
    print(f"Duración total: {total_duration:.1f}s ({total_duration/60:.1f} min)")
    print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n>> Archivos generados:")
    print(f"   - Script: script_id_{script_id}.json")
    print(f"   - Prompts: analyzed_script_id_{script_id}.json")
    print(f"   - Prompts convertidos: segmented_prompts_id_{script_id}.json")
    print(f"   - Videos: VideoProduction/04_VideoGeneration/02_generated_videos/videos/")
    
    return True


def validate_prerequisites():
    """Valida que todos los scripts necesarios existan"""
    
    required_scripts = [
        "content_01_generate_transcriptwriter.py",
        "content_02_analyze_scripts_video_prompts.py",
        "run_pipeline_generate_video.py",
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


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Test rápido de modelos de generación de video',
        epilog="""
Ejemplos:
  python test_video_models.py --script-id 11
  python test_video_models.py --script-id 5 --model wan --fps 24
  python test_video_models.py --script-id 7 --model minimax --min-duration 20
  python test_video_models.py --script-id 11 --model kling --fps 30

Este script ejecuta solo los pasos necesarios para testear modelos:
  1. Generación de script desde topic
  2. Análisis y generación de prompts de video
  3. Conversión de formato (analyzed → segmented)
  4. Generación de videos con IA

NO incluye: procesamiento de audio/video del narrador, sincronización
IDEAL PARA: testear diferentes modelos de IA rápidamente
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
    
    args = parser.parse_args()
    
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
    
    # Ejecutar pipeline de testing
    try:
        success = test_video_model(
            script_id=args.script_id,
            model=args.model,
            fps=args.fps,
            min_duration=args.min_duration,
            max_duration=args.max_duration
        )
        
        if success:
            print(f"\n[OK] TEST COMPLETADO!")
            print(f"   Videos generados para Script ID {args.script_id} con modelo {args.model}")
            sys.exit(0)
        else:
            print(f"\n[ERROR] Test falló")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n[STOP] Test interrumpido por el usuario (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()