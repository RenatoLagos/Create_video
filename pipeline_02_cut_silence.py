#!/usr/bin/env python3
"""
Script para remover silencios de video basándose en transcripción SRT
Detecta gaps entre subtítulos y remueve esos segmentos del video
"""

import os
import sys
import re
import glob
from datetime import datetime, timedelta
from pathlib import Path
from moviepy.editor import VideoFileClip, concatenate_videoclips
from config import SilenceCutConfig, validate_all_paths, print_configuration_summary

def find_video_file_flexible():
    """
    Verifica que el archivo de video existe en la ubicación esperada
    """
    video_path = SilenceCutConfig.VIDEO_INPUT_PATH
    
    if video_path.exists():
        print(f"[OK] Archivo de video encontrado: {video_path}")
        return str(video_path)
    else:
        print(f"[ERROR] No se encontró el archivo de video: {video_path}")
        return None

def parse_srt_time(time_str):
    """
    Convierte tiempo SRT (HH:MM:SS,mmm) a segundos
    """
    # Reemplazar coma por punto para milisegundos
    time_str = time_str.replace(',', '.')
    
    # Parsear formato HH:MM:SS.mmm
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

def parse_srt_file(srt_path):
    """
    Parsea archivo SRT y extrae los timestamps
    """
    if not os.path.exists(srt_path):
        raise FileNotFoundError(f"Archivo SRT no encontrado: {srt_path}")
    
    segments = []
    
    with open(srt_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Dividir por bloques de subtítulos
    blocks = re.split(r'\n\s*\n', content.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            # Línea 1: número de subtítulo
            # Línea 2: timestamps
            # Línea 3+: texto
            
            timestamp_line = lines[1]
            if ' --> ' in timestamp_line:
                start_str, end_str = timestamp_line.split(' --> ')
                
                try:
                    start_time = parse_srt_time(start_str.strip())
                    end_time = parse_srt_time(end_str.strip())
                    text = ' '.join(lines[2:]).strip()
                    
                    segments.append({
                        'start': start_time,
                        'end': end_time,
                        'text': text
                    })
                except Exception as e:
                    if SilenceCutConfig.VERBOSE:
                        print(f"WARNING: Error parseando timestamp '{timestamp_line}': {e}")
                    continue
    
    # Ordenar por tiempo de inicio
    segments.sort(key=lambda x: x['start'])
    
    if SilenceCutConfig.VERBOSE:
        print(f">> Parseados {len(segments)} segmentos del archivo SRT")
    
    return segments

def detect_speech_segments(srt_segments):
    """
    Detecta segmentos con habla basándose en los subtítulos
    Agrega buffers y fusiona segmentos cercanos
    """
    if not srt_segments:
        return []
    
    speech_segments = []
    
    for segment in srt_segments:
        # Agregar buffers
        start_with_buffer = max(0, segment['start'] - SilenceCutConfig.BUFFER_BEFORE)
        end_with_buffer = segment['end'] + SilenceCutConfig.BUFFER_AFTER
        
        speech_segments.append({
            'start': start_with_buffer,
            'end': end_with_buffer,
            'original_start': segment['start'],
            'original_end': segment['end'],
            'text': segment['text']
        })
    
    # Fusionar segmentos que se superponen o están muy cerca
    merged_segments = []
    current_segment = speech_segments[0].copy()
    
    for next_segment in speech_segments[1:]:
        # Si hay superposición o gap muy pequeño, fusionar
        if next_segment['start'] <= current_segment['end'] + 0.1:
            # Fusionar
            current_segment['end'] = max(current_segment['end'], next_segment['end'])
            current_segment['text'] += ' | ' + next_segment['text']
        else:
            # Agregar el segmento actual y empezar uno nuevo
            merged_segments.append(current_segment)
            current_segment = next_segment.copy()
    
    # Agregar el último segmento
    merged_segments.append(current_segment)
    
    if SilenceCutConfig.VERBOSE:
        print(f">> Detectados {len(merged_segments)} segmentos de habla (después de fusionar)")
        total_speech_time = sum(seg['end'] - seg['start'] for seg in merged_segments)
        print(f">> Tiempo total de habla: {total_speech_time:.2f} segundos")
    
    return merged_segments

def cut_video_segments(video_path, speech_segments, output_path):
    """
    Corta el video manteniendo solo los segmentos con habla
    """
    if SilenceCutConfig.VERBOSE:
        print(">> Cargando video original...")
    
    # Cargar video
    video = VideoFileClip(video_path)
    original_duration = video.duration
    
    if SilenceCutConfig.VERBOSE:
        print(f">> Duración original: {original_duration:.2f} segundos")
    
    # Crear clips para cada segmento de habla
    clips = []
    
    for i, segment in enumerate(speech_segments):
        start_time = segment['start']
        end_time = min(segment['end'], original_duration)  # No exceder duración del video
        
        if start_time >= original_duration:
            if SilenceCutConfig.VERBOSE:
                print(f"WARNING: Segmento {i+1} excede duración del video, omitiendo")
            continue
        
        if end_time <= start_time:
            if SilenceCutConfig.VERBOSE:
                print(f"WARNING: Segmento {i+1} tiene duración inválida, omitiendo")
            continue
        
        if SilenceCutConfig.VERBOSE:
            print(f">> Cortando segmento {i+1}: {start_time:.2f}s - {end_time:.2f}s ({end_time-start_time:.2f}s)")
        
        # Crear subclip
        try:
            clip = video.subclip(start_time, end_time)
            clips.append(clip)
        except Exception as e:
            print(f"[ERROR] Error cortando segmento {i+1}: {e}")
            continue
    
    if not clips:
        raise ValueError("No se pudieron crear clips válidos")
    
    if SilenceCutConfig.VERBOSE:
        print(f">> Concatenando {len(clips)} clips...")
    
    # Obtener resolución original del video
    original_size = video.size  # (width, height)
    original_fps = video.fps
    
    if SilenceCutConfig.VERBOSE:
        print(f">> Resolución original: {original_size[0]}x{original_size[1]} @ {original_fps:.2f} fps")
    
    # Asegurar que todos los clips tengan la misma resolución
    clips_resized = []
    for i, clip in enumerate(clips):
        if clip.size != original_size:
            if SilenceCutConfig.VERBOSE:
                print(f">> Redimensionando clip {i+1} de {clip.size} a {original_size}")
            clip_resized = clip.resize(original_size)
            clips_resized.append(clip_resized)
        else:
            clips_resized.append(clip)
    
    # Concatenar clips con la misma resolución
    final_video = concatenate_videoclips(clips_resized, method="compose")
    
    # Crear directorio de salida si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if SilenceCutConfig.VERBOSE:
        print(f">> Guardando video sin silencios...")
        print(f">> Ruta de salida: {output_path}")
        print(f">> Resolución final: {final_video.size[0]}x{final_video.size[1]} @ {final_video.fps:.2f} fps")
    
    # Guardar video final preservando resolución y aspect ratio
    final_video.write_videofile(
        output_path,
        codec=SilenceCutConfig.VIDEO_CODEC,
        audio_codec=SilenceCutConfig.AUDIO_CODEC,
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        verbose=SilenceCutConfig.MOVIEPY_VERBOSE,
        ffmpeg_params=[
            '-crf', str(SilenceCutConfig.CRF_VALUE), 
            '-preset', SilenceCutConfig.PRESET,
            '-vf', f'scale={original_size[0]}:{original_size[1]}:flags=lanczos',  # Forzar resolución original
            '-aspect', f'{original_size[0]}:{original_size[1]}'  # Preservar aspect ratio
        ]
    )
    
    # Liberar memoria
    video.close()
    final_video.close()
    for clip in clips:
        clip.close()
    for clip in clips_resized:
        if clip not in clips:  # Solo cerrar clips que fueron redimensionados
            clip.close()
    
    final_duration = sum(seg['end'] - seg['start'] for seg in speech_segments if seg['start'] < original_duration)
    time_saved = original_duration - final_duration
    percentage_saved = (time_saved / original_duration) * 100 if original_duration > 0 else 0
    
    return {
        'original_duration': original_duration,
        'final_duration': final_duration,
        'time_saved': time_saved,
        'percentage_saved': percentage_saved
    }

def main():
    print(">> CORTADOR DE SILENCIOS BASADO EN SRT")
    print("=" * 50)
    
    # Validar configuración
    config_errors = validate_all_paths()
    if config_errors:
        print("[ERROR] ERRORES DE CONFIGURACIÓN:")
        for error in config_errors:
            print(f"  - {error}")
        print(">> Revisa el archivo config.py")
        sys.exit(1)
    
    # Mostrar configuración si está habilitado
    if SilenceCutConfig.VERBOSE:
        print_configuration_summary()
        print()
    
    try:
        # Paso 0: Encontrar archivo de video (flexible)
        print(">> Paso 0: Buscando archivo de video...")
        video_file = find_video_file_flexible()
        if not video_file:
            print("[ERROR] No se encontró ningún archivo MP4")
            sys.exit(1)
        
        # Paso 1: Parsear archivo SRT
        print(">> Paso 1: Parseando archivo SRT...")
        srt_path = SilenceCutConfig.SRT_INPUT_PATH
        print(f">> Usando archivo SRT: {srt_path}")
        srt_segments = parse_srt_file(str(srt_path))
        
        if not srt_segments:
            print("[ERROR] No se encontraron segmentos válidos en el archivo SRT")
            sys.exit(1)
        
        # Paso 2: Detectar segmentos de habla
        print(">> Paso 2: Detectando segmentos de habla...")
        speech_segments = detect_speech_segments(srt_segments)
        
        if not speech_segments:
            print("[ERROR] No se detectaron segmentos de habla")
            sys.exit(1)
        
        # Paso 3: Cortar video
        print(">> Paso 3: Cortando video...")
        # Nombre único estándar para el pipeline
        output_filename = "video_no_silence.mp4"
        output_path = str(SilenceCutConfig.OUTPUT_DIRECTORY / output_filename)
        
        result = cut_video_segments(video_file, speech_segments, output_path)
        
        print("\n" + "=" * 50)
        print("[OK] PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 50)
        print(f">> Video guardado en: {output_path}")
        print(f">> Duración original: {result['original_duration']:.2f}s")
        print(f">> Duración final: {result['final_duration']:.2f}s")
        print(f">> Tiempo ahorrado: {result['time_saved']:.2f}s ({result['percentage_saved']:.1f}%)")
        
    except Exception as e:
        print(f"[ERROR] Error durante el procesamiento: {str(e)}")
        if SilenceCutConfig.VERBOSE:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()