#!/usr/bin/env python3
"""
Script dedicado para procesar segmented_prompts.json y generar videos en lote
Ejecuta solo la funcionalidad de generación de videos sin ejemplos adicionales
"""

from pipeline_06_generate_videos import process_segmented_prompts_and_generate_videos
import sys
import argparse
from config import VideoGenerationConfig

def main():
    """Función principal para ejecutar la generación de videos en lote"""
    
    parser = argparse.ArgumentParser(description='Generar videos desde prompts segmentados')
    parser.add_argument('--input', 
                       default=str(VideoGenerationConfig.INPUT_FILE),
                       help='Archivo JSON de entrada con prompts segmentados')
    parser.add_argument('--output', 
                       default=str(VideoGenerationConfig.OUTPUT_DIR),
                       help='Directorio de salida para videos generados')
    parser.add_argument('--fps', type=int, default=30,
                       help='Frames por segundo objetivo (default: 30)')
    parser.add_argument('--model', default='wan',
                       help='Modelo de AI a usar (default: wan)')
    
    args = parser.parse_args()
    
    print("🎬 Generador de Videos en Lote - fal.ai")
    print("=" * 50)
    print(f"📖 Archivo de entrada: {args.input}")
    print(f"💾 Directorio de salida: {args.output}")
    print(f"🎥 FPS objetivo: {args.fps}")
    print(f"🤖 Modelo: {args.model}")
    print("=" * 50)
    
    try:
        # Ejecutar procesamiento
        generated_videos = process_segmented_prompts_and_generate_videos(
            input_file=args.input,
            output_dir=args.output,
            target_fps=args.fps,
            model=args.model
        )
        
        if generated_videos:
            print(f"\n✅ ¡Procesamiento completado exitosamente!")
            print(f"📹 Total de videos generados: {len(generated_videos)}")
            
            total_cost = sum(video['cost_usd'] for video in generated_videos)
            print(f"💰 Costo total estimado: ${total_cost:.4f} USD")
            
            # Mostrar resumen detallado
            print(f"\n📋 Videos generados:")
            for video in generated_videos:
                print(f"   • {video['video_filename']} - Frase {video['phrase_number']}, Seg {video['segment_number']} - {video['duration_seconds']}s - ${video['cost_usd']:.4f}")
            
            print(f"\n📁 Videos guardados en: {args.output}")
            print(f"📄 Metadatos guardados en: {args.output}/generated_videos_metadata.json")
            
        else:
            print(f"\n❌ No se generaron videos. Revisa el archivo de entrada y la configuración.")
            sys.exit(1)
            
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo de entrada: {args.input}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()