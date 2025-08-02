#!/usr/bin/env python3
"""
SCRIPT MAESTRO COMPLETO - PIPELINE DE PRODUCCIÓN DE VIDEO
Ejecuta todo el flujo completo en secuencia:
1. Generación de contenido (content_01 -> content_02 -> content_03)
2. Procesamiento de video (transcripción -> cortar silencios -> subtítulos)
3. Sincronización y prompts (sincronizar script -> generar prompts segmentados)
4. Generación de videos con IA
"""

import subprocess
import sys
import argparse
import time
from datetime import datetime
from pathlib import Path
import os


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


def run_complete_pipeline(script_id: int, model: str = "wan", fps: int = 30) -> bool:
    """
    Ejecuta el pipeline completo de producción de video
    """
    
    print("=" * 60)
    print(">> PIPELINE COMPLETO DE PRODUCCIÓN DE VIDEO")
    print("=" * 60)
    print(f"Script ID: {script_id}")
    print(f"Modelo IA: {model}")
    print(f"FPS: {fps}")
    print(f"Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    pipeline_start_time = time.time()
    
    # Definir todos los pasos del pipeline
    steps = [
        # FASE 1: GENERACIÓN DE CONTENIDO
        {
            "name": "Generación de Contenido",
            "command": [sys.executable, "run_content_1-2-3.py", "--script-id", str(script_id)],
            "description": "Genera script, análisis y narrador"
        },
        
        # FASE 2: PROCESAMIENTO DE VIDEO
        {
            "name": "Procesamiento de Video",
            "command": [sys.executable, "run_pipeline_1-2-3.py", "--script-id", str(script_id)],
            "description": "Transcripción, corte de silencios, subtítulos"
        },
        
        # FASE 3: SINCRONIZACIÓN Y PROMPTS
        {
            "name": "Sincronización y Prompts",
            "command": [sys.executable, "run_pipeline_4-5.py", "--script-id", str(script_id)],
            "description": "Sincroniza script y genera prompts segmentados"
        },
        
        # FASE 4: GENERACIÓN DE VIDEOS
        {
            "name": "Generación de Videos con IA",
            "command": [
                sys.executable, "run_pipeline_generate_video.py", 
                "--input", f"VideoProduction/04_VideoGeneration/01_segmented_prompts/segmented_prompts_id_{script_id}.json",
                "--model", model,
                "--fps", str(fps)
            ],
            "description": "Genera videos con inteligencia artificial"
        }
    ]
    
    # Ejecutar cada fase
    for i, step in enumerate(steps, 1):
        print(f"\n>> FASE {i}: {step['name']}")
        print(f"   {step['description']}")
        
        success = run_command_quiet(
            command=step["command"],
            step_name=step["name"],
            step_number=i,
            total_steps=len(steps)
        )
        
        if not success:
            pipeline_end_time = time.time()
            total_duration = pipeline_end_time - pipeline_start_time
            
            print(f"\n" + "=" * 60)
            print(f"[ERROR] PIPELINE FALLÓ EN FASE {i}")
            print(f"=" * 60)
            print(f"Fase fallida: {step['name']}")
            print(f"Tiempo transcurrido: {total_duration:.1f}s")
            print(f"Script ID: {script_id}")
            
            print(f"\n>> Solución de problemas:")
            print(f"   - Revisa la configuración en config.py")
            print(f"   - Verifica que todos los archivos de entrada existan")
            print(f"   - Ejecuta la fase fallida individualmente:")
            print(f"     {' '.join(step['command'])}")
            
            return False
    
    # Pipeline completado exitosamente
    pipeline_end_time = time.time()
    total_duration = pipeline_end_time - pipeline_start_time
    
    print(f"\n" + "=" * 60)
    print(f"[OK] PIPELINE COMPLETADO EXITOSAMENTE!")
    print(f"=" * 60)
    print(f"Script ID: {script_id}")
    print(f"Duración total: {total_duration:.1f}s ({total_duration/60:.1f} min)")
    print(f"Fases completadas: {len(steps)}/{len(steps)}")
    print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n>> Archivos generados:")
    print(f"   - Scripts: script_id_{script_id}.json, analyzed_script_id_{script_id}.json")
    print(f"   - Narrador: narrator_script_id_{script_id}.html")
    print(f"   - Video procesado: video_no_silence.mp4")
    print(f"   - Subtítulos: clean_subtitles.srt")
    print(f"   - Prompts: segmented_prompts_id_{script_id}.json")
    print(f"   - Videos: VideoProduction/04_VideoGeneration/02_generated_videos/videos/")
    
    return True


def validate_prerequisites():
    """Valida que todos los scripts necesarios existan"""
    
    required_scripts = [
        "run_content_1-2-3.py",
        "run_pipeline_1-2-3.py", 
        "run_pipeline_4-5.py",
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
        description='Pipeline completo de producción de video con IA',
        epilog="""
Ejemplos:
  python run_complete_pipeline.py --script-id 11
  python run_complete_pipeline.py --script-id 5 --model wan --fps 24

Este script ejecuta automáticamente:
  1. Generación de contenido (script, análisis, narrador)
  2. Procesamiento de video (transcripción, cortes, subtítulos)
  3. Sincronización y prompts segmentados
  4. Generación de videos con IA
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--script-id', type=int, required=True,
                       help='ID del script a procesar (1-60)')
    parser.add_argument('--model', default='wan',
                       help='Modelo de IA para videos (default: wan)')
    parser.add_argument('--fps', type=int, default=30,
                       help='Frames por segundo (default: 30)')
    
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
    
    # Ejecutar pipeline completo
    try:
        success = run_complete_pipeline(
            script_id=args.script_id,
            model=args.model,
            fps=args.fps
        )
        
        if success:
            print(f"\n[OK] PRODUCCIÓN COMPLETADA!")
            print(f"   Tu video para el Script ID {args.script_id} está listo")
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