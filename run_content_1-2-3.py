#!/usr/bin/env python3
"""
Script maestro para ejecutar el pipeline completo de generación de contenido
Ejecuta en secuencia: content_01 -> content_02 -> content_03 para un ID específico
"""

import subprocess
import sys
import argparse
import time
import os
from datetime import datetime


def run_command(command: list, step_name: str, step_number: int, total_steps: int) -> bool:
    """Ejecuta un comando con output mínimo"""
    print(f"  [{step_number}/{total_steps}] {step_name}...", end=" ")
    
    try:
        start_time = time.time()
        
        result = subprocess.run(
            command,
            check=True,
            capture_output=False,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=os.environ.copy()
        )
        
        duration = time.time() - start_time
        print(f"OK ({duration:.1f}s)")
        return True
        
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"FAILED ({duration:.1f}s)")
        
        print(f"    Exit code: {e.returncode}")
        
        return False
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False


def run_content_pipeline(script_id: int, model: str = None, min_duration: int = None, max_duration: int = None, verbose: bool = False) -> bool:
    """
    Ejecuta el pipeline completo de contenido para un script ID específico
    
    Args:
        script_id: ID del script a procesar (1-60)
        model: Modelo a usar (opcional)
        min_duration: Duración mínima en segundos (opcional)
        max_duration: Duración máxima en segundos (opcional)
        verbose: Mostrar output detallado
    
    Returns:
        bool: True si todo el pipeline fue exitoso
    """
    
    print(f">> Generando contenido para Script ID {script_id}...")
    
    pipeline_start_time = time.time()
    
    # Definir los pasos del pipeline
    steps = [
        {
            "name": "Generate Script",
            "script": "content_01_generate_transcriptwriter.py",
            "description": "Generating video script from topic"
        },
        {
            "name": "Analyze Script & Generate Video Prompts", 
            "script": "content_02_analyze_scripts_video_prompts.py",
            "description": "Analyzing script and generating video prompts"
        },
        {
            "name": "Generate Narrator Script",
            "script": "content_03_generate_narrator_scripts.py", 
            "description": "Generating HTML narrator script"
        }
    ]
    
    # Ejecutar cada paso
    for i, step in enumerate(steps, 1):
        # Construir comando base con parámetro correcto
        if step["script"] == "content_01_generate_transcriptwriter.py":
            # content_01 usa --topic-id
            command = [sys.executable, step["script"], "--topic-id", str(script_id)]
        else:
            # content_02 y content_03 usan --script-id
            command = [sys.executable, step["script"], "--script-id", str(script_id)]
        
        # Agregar parámetros opcionales solo para el primer script
        if i == 1:  # content_01_generate_transcriptwriter.py
            if model:
                command.extend(["--model", model])
            if min_duration:
                command.extend(["--min-duration", str(min_duration)])
            if max_duration:
                command.extend(["--max-duration", str(max_duration)])
        
        # Ejecutar el paso
        success = run_command(command, step["name"], i, len(steps))
        
        if not success:
            print(f"[ERROR] Falló en paso {i}: {step['name']}")
            return False
    
    # Pipeline completado exitosamente
    total_duration = time.time() - pipeline_start_time
    print(f"[OK] Contenido generado exitosamente ({total_duration:.1f}s)")
    
    return True


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Run complete content generation pipeline for a specific script ID',
        epilog="""
Examples:
  python run_content_pipeline.py --script-id 5
  python run_content_pipeline.py --script-id 10 --model gpt-4o --min-duration 20 --max-duration 30
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--script-id', type=int, required=True,
                       help='Script ID to process (required, range: 1-60)')
    parser.add_argument('--model', type=str, 
                       help='Model to use for generation (optional)')
    parser.add_argument('--min-duration', type=int,
                       help='Minimum video duration in seconds (optional)')
    parser.add_argument('--max-duration', type=int, 
                       help='Maximum video duration in seconds (optional)')
    parser.add_argument('--verbose', action='store_true',
                       help='Show verbose output (optional)')
    
    args = parser.parse_args()
    
    # Validar rango de script ID
    if args.script_id < 1 or args.script_id > 60:
        print(f"[ERROR] Invalid script ID: {args.script_id}")
        print("Valid range: 1-60")
        sys.exit(1)
    
    # Ejecutar pipeline
    success = run_content_pipeline(
        script_id=args.script_id,
        model=args.model,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        verbose=args.verbose
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()