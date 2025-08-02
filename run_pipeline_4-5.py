#!/usr/bin/env python3
"""
Script maestro para ejecutar el pipeline de procesamiento de video
Ejecuta en secuencia: pipeline_04 -> pipeline_05 para un ID específico
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


def run_video_pipeline(script_id: int, srt_file: str = None, verbose: bool = False) -> bool:
    """
    Ejecuta el pipeline completo de procesamiento de video para un script ID específico
    
    Args:
        script_id: ID del script a procesar (1-60)
        srt_file: Archivo SRT con timestamps (opcional)
        verbose: Mostrar output detallado
    
    Returns:
        bool: True si todo el pipeline fue exitoso
    """
    
    print(f">> Sincronizando script {script_id} y generando prompts...")
    
    pipeline_start_time = time.time()
    
    # Definir los pasos del pipeline
    steps = [
        {
            "name": "Synchronize Script with SRT Timestamps",
            "script": "pipeline_04_synchronize_script.py",
            "description": "Matching script phrases with SRT timestamps"
        },
        {
            "name": "Generate Segmented Video Prompts", 
            "script": "pipeline_05_generate_segmented_prompts.py",
            "description": "Creating time-segmented video prompts"
        }
    ]
    
    # Ejecutar cada paso
    for i, step in enumerate(steps, 1):
        # Construir comando base
        command = [sys.executable, step["script"], "--script-id", str(script_id)]
        
        # Agregar parámetros opcionales
        if i == 1 and srt_file:  # pipeline_04_synchronize_script.py
            command.extend(["--srt-file", srt_file])
        
        # Ejecutar el paso
        success = run_command(command, step["name"], i, len(steps))
        
        if not success:
            print(f"[ERROR] Falló en paso {i}: {step['name']}")
            return False
    
    # Pipeline completado exitosamente
    total_duration = time.time() - pipeline_start_time
    print(f"[OK] Sincronización y prompts generados exitosamente ({total_duration:.1f}s)")
    
    return True


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Run complete video processing pipeline for a specific script ID',
        epilog="""
Examples:
  python run_pipeline.py --script-id 5
  python run_pipeline.py --script-id 10 --srt-file path/to/custom.srt --verbose

Prerequisites:
  Before running this pipeline, make sure you've run:
  python run_content_pipeline.py --script-id <ID>
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--script-id', type=int, required=True,
                       help='Script ID to process (required, range: 1-60)')
    parser.add_argument('--srt-file', type=str,
                       help='Path to SRT file with timestamps (optional, uses config default)')
    parser.add_argument('--verbose', action='store_true',
                       help='Show verbose output (optional)')
    
    args = parser.parse_args()
    
    # Validar rango de script ID
    if args.script_id < 1 or args.script_id > 60:
        print(f"[ERROR] Invalid script ID: {args.script_id}")
        print("Valid range: 1-60")
        sys.exit(1)
    
    # Verificar prerequisitos
    print(">> Checking prerequisites...")
    
    # Verificar que exista el archivo analizado del content pipeline
    import os
    from config import ContentGenerationConfig
    
    base_dir = os.path.dirname(str(ContentGenerationConfig.ANALYZED_SCRIPTS_FILE))
    required_file = os.path.join(base_dir, f"analyzed_script_id_{args.script_id}.json")
    
    if not os.path.exists(required_file):
        print(f"[ERROR] Required file not found: {required_file}")
        print()
        print("[ERROR] MISSING PREREQUISITE!")
        print("Before running the video pipeline, you must run the content pipeline:")
        print(f"   python run_content_pipeline.py --script-id {args.script_id}")
        print()
        print("This will generate the required analyzed script file.")
        sys.exit(1)
    
    print(f"[OK] Found required file: {required_file}")
    print()
    
    # Ejecutar pipeline
    success = run_video_pipeline(
        script_id=args.script_id,
        srt_file=args.srt_file,
        verbose=args.verbose
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()