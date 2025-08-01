#!/usr/bin/env python3
"""
Script para generar subtítulos SRT de alta calidad usando OpenAI Whisper
Optimizado específicamente para la creación de archivos de subtítulos
"""

import os
import glob
import sys
import whisper
import textwrap
from pathlib import Path
from datetime import datetime
from config import SubtitlesConfig, validate_all_paths, print_configuration_summary

def find_video_file(video_path):
    """
    Busca archivos MP4 en la ruta especificada
    Valida que hay exactamente un archivo MP4
    """
    # Convertir ruta absoluta a relativa si es necesario
    if not os.path.exists(video_path):
        print(f"❌ Error: La ruta {video_path} no existe")
        return None
    
    # Buscar archivos MP4
    mp4_files = glob.glob(os.path.join(video_path, "*.mp4"))
    
    if len(mp4_files) == 0:
        print(f"❌ Error: No se encontraron archivos MP4 en {video_path}")
        return None
    elif len(mp4_files) > 1:
        print(f"❌ Error: Se encontraron {len(mp4_files)} archivos MP4 en {video_path}")
        print("Solo debe haber exactamente 1 archivo MP4.")
        print("Archivos encontrados:")
        for file in mp4_files:
            print(f"  - {os.path.basename(file)}")
        return None
    
    video_file = mp4_files[0]
    print(f"✅ Archivo de video encontrado: {os.path.basename(video_file)}")
    return video_file

def load_whisper_model(model_size=SubtitlesConfig.WHISPER_MODEL):
    """
    Carga el modelo Whisper
    """
    print(f"🔄 Cargando modelo Whisper '{model_size}'...")
    try:
        model = whisper.load_model(model_size)
        print("✅ Modelo cargado exitosamente")
        return model
    except Exception as e:
        print(f"❌ Error cargando modelo: {str(e)}")
        print(f"💡 Intentando con modelo '{SubtitlesConfig.FALLBACK_MODEL}' como respaldo...")
        try:
            model = whisper.load_model(SubtitlesConfig.FALLBACK_MODEL)
            print(f"✅ Modelo {SubtitlesConfig.FALLBACK_MODEL} cargado exitosamente")
            return model
        except Exception as e2:
            print(f"❌ Error cargando modelo {SubtitlesConfig.FALLBACK_MODEL}: {str(e2)}")
            return None

def generate_transcription(model, video_file):
    """
    Genera la transcripción usando Whisper
    """
    print("🔄 Generando transcripción para subtítulos...")
    print("⏳ Esto puede tomar varios minutos dependiendo del tamaño del video...")
    
    # Mostrar configuración actual
    if SubtitlesConfig.VERBOSE:
        print(f"⚙️  Configuración: Modelo={SubtitlesConfig.WHISPER_MODEL}, Idioma={SubtitlesConfig.LANGUAGE}, Temp={SubtitlesConfig.TEMPERATURE}")
    
    try:
        # Transcribir con configuración desde config.py
        transcribe_options = {
            'language': SubtitlesConfig.LANGUAGE if SubtitlesConfig.LANGUAGE != 'auto' else None,
            'task': 'transcribe',
            'verbose': SubtitlesConfig.WHISPER_VERBOSE,
            'word_timestamps': SubtitlesConfig.WORD_TIMESTAMPS,
            'temperature': SubtitlesConfig.TEMPERATURE,
            'best_of': SubtitlesConfig.BEST_OF,
            'beam_size': SubtitlesConfig.BEAM_SIZE,
        }
        
        result = model.transcribe(video_file, **transcribe_options)
        
        print("✅ Transcripción completada exitosamente")
        return result
    except Exception as e:
        print(f"❌ Error durante la transcripción: {str(e)}")
        return None

def split_text_for_subtitles(text, max_chars=SubtitlesConfig.MAX_CHARS_PER_LINE):
    """
    Divide el texto en líneas adecuadas para subtítulos
    """
    # Usar textwrap para dividir el texto respetando palabras
    lines = textwrap.fill(text, width=max_chars).split('\n')
    
    # Limitar al número máximo de líneas
    if len(lines) > SubtitlesConfig.MAX_LINES_PER_SUBTITLE:
        lines = lines[:SubtitlesConfig.MAX_LINES_PER_SUBTITLE]
    
    return lines

def optimize_subtitle_timing(segments):
    """
    Optimiza el timing de los subtítulos para mejor legibilidad
    """
    optimized_segments = []
    
    for i, segment in enumerate(segments):
        start_time = segment.get('start', 0)
        end_time = segment.get('end', 0)
        text = segment.get('text', '').strip()
        
        if not text:
            continue
        
        # Calcular duración actual
        duration = end_time - start_time
        
        # Aplicar duración máxima si es necesario
        if duration > SubtitlesConfig.MAX_SUBTITLE_DURATION:
            end_time = start_time + SubtitlesConfig.MAX_SUBTITLE_DURATION
        
        # Asegurar gap mínimo con el siguiente subtítulo
        if i < len(segments) - 1:
            next_start = segments[i + 1].get('start', float('inf'))
            if end_time + SubtitlesConfig.MIN_GAP_BETWEEN_SUBTITLES > next_start:
                end_time = max(start_time + 1.0, next_start - SubtitlesConfig.MIN_GAP_BETWEEN_SUBTITLES)
        
        optimized_segments.append({
            'start': start_time,
            'end': end_time,
            'text': text
        })
    
    return optimized_segments

def format_time_srt(seconds):
    """
    Convierte segundos a formato SRT (HH:MM:SS,mmm)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

def save_subtitles_srt(result, video_file, output_dir):
    """
    Guarda los subtítulos en formato SRT optimizado
    """
    video_name = os.path.splitext(os.path.basename(video_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Nombre único estándar para el pipeline
    srt_file = os.path.join(output_dir, "clean_subtitles.srt")
    
    # Optimizar timing de segmentos
    segments = result.get('segments', [])
    optimized_segments = optimize_subtitle_timing(segments)
    
    subtitle_count = 0
    
    with open(srt_file, 'w', encoding='utf-8') as f:
        for segment in optimized_segments:
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text']
            
            # Dividir texto en líneas apropiadas para subtítulos
            lines = split_text_for_subtitles(text)
            
            # Crear subtítulo
            subtitle_count += 1
            start_time_str = format_time_srt(start_time)
            end_time_str = format_time_srt(end_time)
            
            f.write(f"{subtitle_count}\n")
            f.write(f"{start_time_str} --> {end_time_str}\n")
            
            # Escribir líneas de texto
            for line in lines:
                f.write(f"{line}\n")
            f.write("\n")  # Línea en blanco entre subtítulos
    
    print(f"🎬 Subtítulos SRT guardados: {srt_file}")
    print(f"📊 Total de subtítulos generados: {subtitle_count}")
    
    # Calcular estadísticas
    total_duration = max([seg['end'] for seg in optimized_segments]) if optimized_segments else 0
    avg_duration = sum([seg['end'] - seg['start'] for seg in optimized_segments]) / len(optimized_segments) if optimized_segments else 0
    
    if SubtitlesConfig.VERBOSE:
        print(f"📏 Duración total del video: {total_duration:.2f} segundos")
        print(f"⏱️  Duración promedio por subtítulo: {avg_duration:.2f} segundos")
    
    return srt_file

def main():
    print("🎬 GENERADOR DE SUBTÍTULOS SRT DE ALTA CALIDAD")
    print("=" * 55)
    
    # Validar configuración
    config_errors = validate_all_paths()
    if config_errors:
        print("❌ ERRORES DE CONFIGURACIÓN:")
        for error in config_errors:
            print(f"  - {error}")
        print("🔧 Revisa el archivo config.py")
        sys.exit(1)
    
    # Mostrar configuración si está habilitado
    if SubtitlesConfig.VERBOSE:
        print_configuration_summary()
        print()
    
    # Configuración de rutas desde config.py
    video_input_path = SubtitlesConfig.VIDEO_INPUT_PATH
    output_dir = SubtitlesConfig.OUTPUT_DIRECTORY
    
    # Paso 1: Buscar archivo de video
    video_file_path = video_input_path / "video_no_silence.mp4"
    if not video_file_path.exists():
        print(f"❌ Error: No se encontró el archivo de video: {video_file_path}")
        sys.exit(1)
    print(f"✅ Archivo de video encontrado: {video_file_path}")
    video_file = str(video_file_path)
    
    # Paso 2: Cargar modelo Whisper
    model = load_whisper_model()  # Usa configuración de config.py
    if not model:
        sys.exit(1)
    
    # Paso 3: Generar transcripción
    result = generate_transcription(model, video_file)
    if not result:
        sys.exit(1)
    
    # Paso 4: Guardar subtítulos SRT
    srt_file = save_subtitles_srt(result, video_file, output_dir)
    
    print("\n" + "=" * 55)
    print("🎉 GENERACIÓN DE SUBTÍTULOS COMPLETADA EXITOSAMENTE")
    print("=" * 55)
    print(f"📁 Archivo guardado en: {os.path.dirname(srt_file)}/")
    print(f"🎬 Archivo SRT: {os.path.basename(srt_file)}")
    
    # Mostrar preview del texto
    preview = result['text'][:200] + "..." if len(result['text']) > 200 else result['text']
    print(f"\n📝 Preview del contenido:")
    print(f'"{preview}"')
    
    print(f"\n💡 El archivo SRT está listo para usar con reproductores de video")
    print(f"📍 Ubicación: {srt_file}")

if __name__ == "__main__":
    main()