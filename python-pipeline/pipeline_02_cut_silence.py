#!/usr/bin/env python3
"""
Script para remover silencios de video basándose en transcripción SRT
Detecta gaps entre subtítulos y remueve esos segmentos del video
Incluye detección y manejo de rotación de video
"""

import os
import sys
import re
import glob
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
from moviepy.editor import VideoFileClip, concatenate_videoclips
from config import SilenceCutConfig, validate_all_paths, print_configuration_summary

def get_video_rotation(video_path):
    """
    Detecta la rotación del video usando ffprobe
    Busca rotación tanto en tags como en side_data (Display Matrix)
    """
    try:
        # Usar ffprobe para obtener metadata completo incluyendo side_data
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            streams = data.get('streams', [])
            
            # Buscar el stream de video
            video_stream = None
            for stream in streams:
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if video_stream:
                rotation = 0
                width = video_stream.get('width', 0)
                height = video_stream.get('height', 0)
                
                # Método 1: Buscar rotación en tags
                if 'tags' in video_stream and 'rotate' in video_stream['tags']:
                    rotation = int(video_stream['tags']['rotate'])
                    print(f">> Rotación encontrada en tags: {rotation}°")
                
                # Método 2: Buscar rotación en side_data_list (Display Matrix)
                elif 'side_data_list' in video_stream:
                    for side_data in video_stream['side_data_list']:
                        if side_data.get('side_data_type') == 'Display Matrix':
                            if 'rotation' in side_data:
                                rotation = int(float(side_data['rotation']))
                                print(f">> Rotación encontrada en Display Matrix: {rotation}°")
                                break
                
                # Normalizar rotación (convertir valores negativos)
                if rotation < 0:
                    rotation = 360 + rotation
                
                return {
                    'rotation': rotation,
                    'original_width': width,
                    'original_height': height,
                    'needs_rotation': rotation in [90, 270]
                }
    
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f">> Error con ffprobe: {e}")
        # Si ffprobe falla, usar método alternativo con MoviePy
        try:
            video = VideoFileClip(str(video_path))
            rotation = getattr(video.reader, 'rotation', 0) if hasattr(video.reader, 'rotation') else 0
            width, height = video.size
            video.close()
            
            return {
                'rotation': rotation,
                'original_width': width,
                'original_height': height,
                'needs_rotation': rotation in [90, 270]
            }
        except Exception as e2:
            print(f">> Error con MoviePy: {e2}")
            pass
    
    # Fallback: no rotation detected
    return {
        'rotation': 0,
        'original_width': 0,
        'original_height': 0,
        'needs_rotation': False
    }

def apply_rotation_if_needed(video_clip, rotation_info):
    """
    Corrige la orientación del video basándose en su metadata de rotación
    Para videos con rotación -90°, transponemos las dimensiones en lugar de rotar
    """
    if not rotation_info['needs_rotation']:
        return video_clip
    
    rotation = rotation_info['rotation']
    
    if rotation == 270:  # Video tiene -90° en Display Matrix
        # En lugar de rotar, transponemos las dimensiones manteniendo aspect ratio correcto
        print(">> Transponiendo dimensiones de 1280x720 a 720x1280 (sin rotación)")
        print(">> Esto corrige el metadata de rotación -90° cambiando las dimensiones físicas")
        
        # Redimensionar a las dimensiones correctas (720x1280) manteniendo contenido sin rotar
        corrected_video = video_clip.resize((720, 1280))
        return corrected_video
        
    elif rotation == 90:
        # Video está rotado 90°, transponemos y ajustamos
        print(">> Transponiendo dimensiones para corrección 90°")
        corrected_video = video_clip.resize((720, 1280))
        return corrected_video
        
    elif rotation == 180:
        # Video está rotado 180°, aplicamos rotación
        print(">> Aplicando corrección: 180°")
        return video_clip.rotate(180)
    
    return video_clip

def test_rotations(video_path):
    """
    Función de prueba para probar diferentes rotaciones
    """
    print(">> MODO DE PRUEBA DE ROTACIONES")
    print(">> Generando muestras con diferentes rotaciones...")
    
    video = VideoFileClip(video_path)
    
    # Crear clips de prueba de 5 segundos
    test_clip = video.subclip(0, min(5, video.duration))
    
    rotations_to_test = [0, 90, -90, 180, -180, 270]
    
    for i, rotation in enumerate(rotations_to_test):
        output_file = f"VideoProduction/03_VideoProcessing/02_silence_removal/test_rotation_{rotation}.mp4"
        
        if rotation == 0:
            final_clip = test_clip
        else:
            final_clip = test_clip.rotate(rotation)
        
        print(f">> Generando test_{rotation}.mp4 con rotación {rotation}°")
        
        final_clip.write_videofile(
            output_file,
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            ffmpeg_params=['-crf', '23', '-preset', 'fast']
        )
        
        final_clip.close()
    
    video.close()
    test_clip.close()
    
    print(">> Archivos de prueba generados. Revisa cuál tiene la orientación correcta.")
    return rotations_to_test

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
    Detecta y maneja rotación automáticamente
    """
    if SilenceCutConfig.VERBOSE:
        print(">> Cargando video original...")
    
    # PASO 1: Detectar rotación del video
    rotation_info = get_video_rotation(video_path)
    
    if SilenceCutConfig.VERBOSE:
        print(f">> Rotación detectada: {rotation_info['rotation']}°")
        print(f">> Dimensiones técnicas: {rotation_info['original_width']}x{rotation_info['original_height']}")
        print(f">> Necesita rotación: {'Sí' if rotation_info['needs_rotation'] else 'No'}")
    
    # PASO 2: Cargar video
    video = VideoFileClip(video_path)
    original_duration = video.duration
    
    # PASO 3: Aplicar rotación si es necesario
    if rotation_info['needs_rotation']:
        if SilenceCutConfig.VERBOSE:
            print(f">> Aplicando rotación de {rotation_info['rotation']}°...")
        video = apply_rotation_if_needed(video, rotation_info)
    
    # PASO 4: Obtener resolución final (después de rotación)
    final_size = video.size  # (width, height)
    final_fps = video.fps
    final_aspect_ratio = final_size[0] / final_size[1]
    
    if SilenceCutConfig.VERBOSE:
        print(f">> Duración original: {original_duration:.2f} segundos")
        print(f">> Resolución final: {final_size[0]}x{final_size[1]} (W x H)")
        print(f">> Aspect ratio final: {final_aspect_ratio:.3f}")
        print(f">> FPS: {final_fps:.2f}")
        
        # Detectar orientación final
        if final_aspect_ratio > 1:
            orientation = "landscape (horizontal)"
        elif final_aspect_ratio < 1:
            orientation = "portrait (vertical)"
        else:
            orientation = "square (cuadrado)"
        print(f">> Orientación final: {orientation}")
    
    # Crear clips para cada segmento de habla
    clips = []
    
    for i, segment in enumerate(speech_segments):
        start_time = segment['start']
        end_time = min(segment['end'], original_duration)
        
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
        
        try:
            clip = video.subclip(start_time, end_time)
            # El clip heredará automáticamente la rotación aplicada
            clips.append(clip)
        except Exception as e:
            print(f"[ERROR] Error cortando segmento {i+1}: {e}")
            continue
    
    if not clips:
        raise ValueError("No se pudieron crear clips válidos")
    
    if SilenceCutConfig.VERBOSE:
        print(f">> Concatenando {len(clips)} clips...")
    
    # Concatenar clips
    final_video = concatenate_videoclips(clips, method="compose")
    
    # Crear directorio de salida
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if SilenceCutConfig.VERBOSE:
        final_width, final_height = final_video.size
        print(f">> Guardando video con resolución: {final_width}x{final_height}")
        print(f">> Ruta de salida: {output_path}")
    
    # Guardar video final
    final_video.write_videofile(
        output_path,
        codec=SilenceCutConfig.VIDEO_CODEC,
        audio_codec=SilenceCutConfig.AUDIO_CODEC,
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        verbose=SilenceCutConfig.MOVIEPY_VERBOSE,
        ffmpeg_params=[
            '-crf', str(SilenceCutConfig.CRF_VALUE), 
            '-preset', SilenceCutConfig.PRESET
        ]
    )
    
    # Liberar memoria
    video.close()
    final_video.close()
    for clip in clips:
        clip.close()
    
    # Calcular estadísticas
    final_duration = sum(seg['end'] - seg['start'] for seg in speech_segments if seg['start'] < original_duration)
    time_saved = original_duration - final_duration
    percentage_saved = (time_saved / original_duration) * 100 if original_duration > 0 else 0
    
    return {
        'original_duration': original_duration,
        'final_duration': final_duration,
        'time_saved': time_saved,
        'percentage_saved': percentage_saved,
        'rotation_applied': rotation_info['rotation'] if rotation_info['needs_rotation'] else 0,
        'final_resolution': final_video.size
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
        if result['rotation_applied'] != 0:
            print(f">> Rotación aplicada: {result['rotation_applied']}°")
        print(f">> Resolución final: {result['final_resolution']}")
        
    except Exception as e:
        print(f"[ERROR] Error durante el procesamiento: {str(e)}")
        if SilenceCutConfig.VERBOSE:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()