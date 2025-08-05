#!/usr/bin/env python3
"""
TEST STOCK FOOTAGE - Script completo para probar stock footage
Ejecuta el flujo completo: Script → Keywords → Búsqueda APIs → Videos descargados

Flujo:
1. content_01_generate_transcriptwriter.py - Genera script desde topic  
2. generate_search_keywords.py - Extrae keywords del script
3. search_stock_footage.py - Busca y descarga videos de Pexels/Pixabay

Ideal para probar stock footage como alternativa a generación con IA.
"""

import subprocess
import sys
import argparse
import time
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


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


def test_stock_footage_pipeline(
    script_id: int,
    pexels_api_key: str = None,
    pixabay_api_key: str = None,
    max_videos: int = 50,
    min_duration: int = None,
    max_duration: int = None
) -> bool:
    """
    Ejecuta el pipeline completo de testing con stock footage
    """
    
    print("=" * 70)
    print(">> TEST STOCK FOOTAGE - PIPELINE COMPLETO")
    print("=" * 70)
    print(f"Script ID: {script_id}")
    print(f"Max videos: {max_videos}")
    if pexels_api_key:
        print(f"Pexels API: ✅ Disponible")
    else:
        print(f"Pexels API: ❌ No disponible")
    if pixabay_api_key:
        print(f"Pixabay API: ✅ Disponible")
    else:
        print(f"Pixabay API: ❌ No disponible")
    if min_duration:
        print(f"Duración mínima: {min_duration}s")
    if max_duration:
        print(f"Duración máxima: {max_duration}s")
    print(f"Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    pipeline_start_time = time.time()
    
    # Definir pasos del pipeline
    steps = []
    
    # PASO 1: Generar script (solo si no existe)
    script_file = Path(f"VideoProduction/01_ContentGeneration/02_generated_scripts/script_id_{script_id}.json")
    if not script_file.exists():
        step_1_params = ["--topic-id", str(script_id)]
        if min_duration:
            step_1_params.extend(["--min-duration", str(min_duration)])
        if max_duration:
            step_1_params.extend(["--max-duration", str(max_duration)])
        
        steps.append({
            "name": "Generar Script desde Topic",
            "script": "content_01_generate_transcriptwriter.py",
            "params": step_1_params
        })
    else:
        print(f"\n[SKIP] Script ya existe: {script_file}")
    
    # PASO 2: Generar keywords
    steps.append({
        "name": "Extraer Keywords para Búsqueda API",
        "script": "generate_search_keywords.py", 
        "params": ["--script-id", str(script_id)]
    })
    
    # PASO 3: Buscar y descargar videos
    search_params = ["--script-id", str(script_id), "--max-videos", str(max_videos)]
    if pexels_api_key:
        search_params.extend(["--pexels-key", pexels_api_key])
    if pixabay_api_key:
        search_params.extend(["--pixabay-key", pixabay_api_key])
    
    steps.append({
        "name": "Buscar y Descargar Videos de Stock Footage",
        "script": "search_stock_footage.py",
        "params": search_params
    })
    
    # Ejecutar pasos
    for i, step in enumerate(steps, 1):
        command = [sys.executable, step["script"]] + step["params"]
        
        success = run_command_quiet(
            command=command,
            step_name=step["name"],
            step_number=i,
            total_steps=len(steps)
        )
        
        if not success:
            print(f"\n[ERROR] PIPELINE FALLÓ EN PASO {i}")
            return False
    
    # Pipeline completado
    pipeline_end_time = time.time()
    total_duration = pipeline_end_time - pipeline_start_time
    
    print(f"\n" + "=" * 70)
    print(f"[OK] STOCK FOOTAGE TEST COMPLETADO!")
    print(f"=" * 70)
    print(f"Script ID: {script_id}")
    print(f"Duración total: {total_duration:.1f}s ({total_duration/60:.1f} min)")
    print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n>> Archivos generados:")
    print(f"   - Script: script_id_{script_id}.json")
    print(f"   - Keywords: search_keywords_id_{script_id}.json")
    print(f"   - Videos: VideoProduction/05_StockFootage/02_downloaded_videos/script_id_{script_id}/")
    print(f"     • Pexels: VideoProduction/05_StockFootage/02_downloaded_videos/script_id_{script_id}/pexels/")
    print(f"     • Pixabay: VideoProduction/05_StockFootage/02_downloaded_videos/script_id_{script_id}/pixabay/")
    
    # Mostrar estadísticas si hay archivo de resultados
    results_file = Path(f"VideoProduction/05_StockFootage/02_downloaded_videos/script_id_{script_id}/search_results_{script_id}.json")
    if results_file.exists():
        try:
            import json
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            summary = results.get('summary', {})
            print(f"\n>> Estadísticas de búsqueda:")
            print(f"   • Videos encontrados: {summary.get('total_videos_found', 0)}")
            print(f"   • Videos descargados: {summary.get('total_videos_downloaded', 0)}")
            print(f"   • Pexels: {summary.get('pexels_videos', 0)} videos")
            print(f"   • Pixabay: {summary.get('pixabay_videos', 0)} videos")
            
        except Exception:
            pass  # No mostrar error si no se puede leer stats
    
    return True


def validate_prerequisites():
    """Valida que todos los scripts necesarios existan"""
    
    required_scripts = [
        "content_01_generate_transcriptwriter.py",
        "generate_search_keywords.py",
        "search_stock_footage.py",
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
        description='Test completo de stock footage como alternativa a generación de video con IA',
        epilog="""
Ejemplos:
  python test_stock_footage.py --script-id 11
  python test_stock_footage.py --script-id 5 --max-videos 80
  python test_stock_footage.py --script-id 7 --pexels-key YOUR_KEY --pixabay-key YOUR_KEY

API Keys:
  Configura las claves en archivo .env en la raíz del proyecto:
    PEXELS_API_KEY=tu_clave_pexels
    PIXABAY_API_KEY=tu_clave_pixabay
  
  O pásalas como argumentos:
    --pexels-key TU_CLAVE_PEXELS
    --pixabay-key TU_CLAVE_PIXABAY

Obtener API Keys GRATIS:
  • Pexels: https://www.pexels.com/api/new/
  • Pixabay: https://pixabay.com/api/docs/

Este script ejecuta automáticamente:
  1. Generación de script desde topic
  2. Extracción de keywords para búsqueda
  3. Búsqueda y descarga de videos de stock footage

VENTAJAS vs Generación con IA:
  ✅ Más rápido (descarga vs generación)
  ✅ Más económico (APIs gratuitas vs costos IA)
  ✅ Videos reales profesionales
  ✅ Sin límites de duración
  ✅ Mayor variedad disponible
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--script-id', type=int, required=True,
                       help='ID del script a procesar (1-60)')
    parser.add_argument('--pexels-key', type=str,
                       help='Pexels API key (o usar PEXELS_API_KEY env var)')
    parser.add_argument('--pixabay-key', type=str, 
                       help='Pixabay API key (o usar PIXABAY_API_KEY env var)')
    parser.add_argument('--max-videos', type=int, default=50,
                       help='Máximo total de videos a descargar (default: 50)')
    parser.add_argument('--min-duration', type=int,
                       help='Duración mínima del script en segundos (opcional)')
    parser.add_argument('--max-duration', type=int,
                       help='Duración máxima del script en segundos (opcional)')
    
    args = parser.parse_args()
    
    # Validar script ID
    if args.script_id < 1 or args.script_id > 60:
        print(f"[ERROR] Script ID inválido: {args.script_id}")
        print("Rango válido: 1-60")
        sys.exit(1)
    
    # Obtener API keys
    pexels_key = args.pexels_key or os.getenv('PEXELS_API_KEY')
    pixabay_key = args.pixabay_key or os.getenv('PIXABAY_API_KEY')
    
    if not pexels_key and not pixabay_key:
        print("[ERROR] No se proporcionaron claves de API!")
        print("\n📋 Para obtener claves API GRATUITAS:")
        print("• Pexels API: https://www.pexels.com/api/new/")
        print("• Pixabay API: https://pixabay.com/api/docs/")
        print("\n💡 Configura las claves en archivo .env:")
        print("PEXELS_API_KEY=tu_clave_pexels")
        print("PIXABAY_API_KEY=tu_clave_pixabay")
        print("\nO usa los argumentos:")
        print("--pexels-key TU_CLAVE --pixabay-key TU_CLAVE")
        sys.exit(1)
    
    # Validar prerequisites
    print(">> Verificando prerequisites...")
    if not validate_prerequisites():
        print("[ERROR] Faltan scripts necesarios!")
        sys.exit(1)
    
    print("[OK] Todos los scripts están disponibles")
    
    # Ejecutar pipeline de stock footage
    try:
        success = test_stock_footage_pipeline(
            script_id=args.script_id,
            pexels_api_key=pexels_key,
            pixabay_api_key=pixabay_key,
            max_videos=args.max_videos,
            min_duration=args.min_duration,
            max_duration=args.max_duration
        )
        
        if success:
            print(f"\n[OK] TEST DE STOCK FOOTAGE COMPLETADO!")
            print(f"   Videos descargados para Script ID {args.script_id}")
            print(f"   Revisa las carpetas pexels/ y pixabay/ para comparar resultados")
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