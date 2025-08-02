#!/usr/bin/env python3
"""
Master script para ejecutar el pipeline completo de procesamiento de video:
1. pipeline_01_generate_transcription.py - Genera transcripción SRT
2. pipeline_02_cut_silence.py - Remueve silencios del video
3. pipeline_03_generate_subtitles.py - Genera subtítulos finales optimizados

Este script ejecuta los 3 pasos en secuencia, validando que cada paso
tenga los inputs necesarios del paso anterior.
"""

import subprocess
import sys
import time
import os
from datetime import datetime
from pathlib import Path


def run_pipeline_step(command, step_name, step_number, total_steps):
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


def validate_prerequisites():
    """
    Valida que los archivos de configuración y dependencias existan
    
    Returns:
        bool: True si todo está correcto, False si hay problemas
    """
    print(">> Checking prerequisites...")
    
    # Verificar que config.py existe
    if not os.path.exists("config.py"):
        print("[ERROR] config.py not found! Make sure you're in the correct directory.")
        return False
    
    # Verificar que los scripts del pipeline existen
    required_scripts = [
        "pipeline_01_generate_transcription.py",
        "pipeline_02_cut_silence.py", 
        "pipeline_03_generate_subtitles.py"
    ]
    
    for script in required_scripts:
        if not os.path.exists(script):
            print(f"[ERROR] Required script not found: {script}")
            return False
        else:
            print(f"[OK] Found required script: {script}")
    
    return True


def run_video_pipeline():
    """
    Ejecuta el pipeline completo de procesamiento de video
    
    Returns:
        bool: True si exitoso, False si falló
    """
    
    print(f">> Procesando video...")
    
    pipeline_start_time = time.time()
    
    # Definir los pasos del pipeline
    steps = [
        {
            "script": "pipeline_01_generate_transcription.py",
            "name": "Generate Transcription",
            "description": "Creates high-quality transcription using OpenAI Whisper"
        },
        {
            "script": "pipeline_02_cut_silence.py", 
            "name": "Remove Silence",
            "description": "Removes silent segments from video based on SRT"
        },
        {
            "script": "pipeline_03_generate_subtitles.py",
            "name": "Generate Clean Subtitles", 
            "description": "Creates optimized subtitles from processed video"
        }
    ]
    
    # Ejecutar cada paso
    for i, step in enumerate(steps, 1):
        command = [sys.executable, step["script"]]
        
        success = run_pipeline_step(
            command=command,
            step_name=step["name"],
            step_number=i,
            total_steps=len(steps)
        )
        
        if not success:
            print(f"[ERROR] Falló en paso {i}: {step['name']}")
            return False
    
    # Pipeline completado exitosamente
    total_duration = time.time() - pipeline_start_time
    print(f"[OK] Video procesado exitosamente ({total_duration:.1f}s)")
    
    return True


def main():
    """
    Función principal
    """
    print(">> VIDEO PROCESSING PIPELINE")
    print("=" * 60)
    print(">> Processing video through complete pipeline:")
    print("   1. Generate transcription")
    print("   2. Remove silence from video")
    print("   3. Generate clean subtitles")
    print("=" * 60)
    
    # Validar prerrequisitos
    if not validate_prerequisites():
        print("\n[ERROR] Prerequisites check failed!")
        sys.exit(1)
    
    print("[OK] All prerequisites validated")
    print()
    
    # Ejecutar pipeline
    try:
        success = run_video_pipeline()
        
        if success:
            print("\n>> Pipeline completed successfully!")
            print(">> Check the output directories specified in config.py for results")
            sys.exit(0)
        else:
            print("\n[ERROR] Pipeline failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n[ERROR] Pipeline interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()