#!/usr/bin/env python3
"""
Script para generar transcripciones de alta calidad usando OpenAI Whisper
Replica la calidad de transcripción de Adobe Premiere Pro
"""

import os
import glob
import json
import sys
import whisper
from pathlib import Path
from datetime import datetime
from config import TranscriptionConfig, validate_all_paths, print_configuration_summary

def find_video_file(video_path):
    """
    Busca archivos MP4 en la ruta especificada
    Valida que hay exactamente un archivo MP4
    Renombra el archivo a 'video.mp4' para estandarizar el pipeline
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
    
    original_video_file = mp4_files[0]
    original_name = os.path.basename(original_video_file)
    print(f"✅ Archivo de video encontrado: {original_name}")
    
    # Renombrar a nombre estándar para el pipeline
    standard_video_file = os.path.join(video_path, "video.mp4")
    
    if original_video_file != standard_video_file:
        try:
            # Si ya existe video.mp4, eliminarlo primero
            if os.path.exists(standard_video_file):
                os.remove(standard_video_file)
                print(f"🗑️  Archivo anterior 'video.mp4' eliminado")
            
            # Renombrar archivo
            os.rename(original_video_file, standard_video_file)
            print(f"🔄 Archivo renombrado: '{original_name}' → 'video.mp4'")
        except Exception as e:
            print(f"❌ Error renombrando archivo: {str(e)}")
            return original_video_file  # Usar archivo original si falla el renombrado
    else:
        print(f"✅ El archivo ya tiene el nombre estándar: video.mp4")
    
    return standard_video_file

def load_whisper_model(model_size=TranscriptionConfig.WHISPER_MODEL):
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
        print(f"💡 Intentando con modelo '{TranscriptionConfig.FALLBACK_MODEL}' como respaldo...")
        try:
            model = whisper.load_model(TranscriptionConfig.FALLBACK_MODEL)
            print(f"✅ Modelo {TranscriptionConfig.FALLBACK_MODEL} cargado exitosamente")
            return model
        except Exception as e2:
            print(f"❌ Error cargando modelo {TranscriptionConfig.FALLBACK_MODEL}: {str(e2)}")
            return None

def generate_transcription(model, video_file):
    """
    Genera la transcripción usando Whisper
    """
    print("🔄 Generando transcripción...")
    print("⏳ Esto puede tomar varios minutos dependiendo del tamaño del video...")
    
    # Mostrar configuración actual
    if TranscriptionConfig.VERBOSE:
        print(f"⚙️  Configuración: Modelo={TranscriptionConfig.WHISPER_MODEL}, Idioma={TranscriptionConfig.LANGUAGE}, Temp={TranscriptionConfig.TEMPERATURE}")
    
    try:
        # Transcribir con configuración desde config.py
        transcribe_options = {
            'language': TranscriptionConfig.LANGUAGE if TranscriptionConfig.LANGUAGE != 'auto' else None,
            'task': 'transcribe',
            'verbose': TranscriptionConfig.WHISPER_VERBOSE,
            'word_timestamps': TranscriptionConfig.WORD_TIMESTAMPS,
            'temperature': TranscriptionConfig.TEMPERATURE,
            'best_of': TranscriptionConfig.BEST_OF,
            'beam_size': TranscriptionConfig.BEAM_SIZE,
        }
        
        result = model.transcribe(video_file, **transcribe_options)
        
        print("✅ Transcripción completada exitosamente")
        return result
    except Exception as e:
        print(f"❌ Error durante la transcripción: {str(e)}")
        return None

def save_transcription(result, video_file, output_dir):
    """
    Guarda la transcripción en múltiples formatos según configuración
    """
    video_name = os.path.splitext(os.path.basename(video_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    saved_files = []
    
    # 1. Texto plano (.txt)
    if TranscriptionConfig.GENERATE_TXT:
        txt_file = os.path.join(output_dir, f"{video_name}_transcription.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(result['text'])
        print(f"📄 Transcripción guardada: {txt_file}")
        saved_files.append(txt_file)
    
    # 2. JSON con timestamps (.json)
    if TranscriptionConfig.GENERATE_JSON:
        json_file = os.path.join(output_dir, f"{video_name}_transcription_detailed.json")
        transcription_data = {
            'video_file': os.path.basename(video_file),
            'generated_at': datetime.now().isoformat(),
            'language': result.get('language', TranscriptionConfig.LANGUAGE),
            'duration': len(result.get('segments', [])),
            'full_text': result['text'],
            'segments': []
        }
        
        # Agregar segmentos con timestamps
        for segment in result.get('segments', []):
            transcription_data['segments'].append({
                'id': segment.get('id'),
                'start': round(segment.get('start', 0), 2),
                'end': round(segment.get('end', 0), 2),
                'text': segment.get('text', '').strip(),
                'words': segment.get('words', []) if 'words' in segment else []
            })
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(transcription_data, f, ensure_ascii=False, indent=2)
        print(f"📋 Transcripción detallada guardada: {json_file}")
        saved_files.append(json_file)
    
    # 3. Formato SRT para subtítulos (.srt)
    if TranscriptionConfig.GENERATE_SRT:
        # Nombre único para el pipeline
        srt_file = os.path.join(output_dir, "original_transcription.srt")
        with open(srt_file, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(result.get('segments', []), 1):
                start_time = format_time_srt(segment.get('start', 0))
                end_time = format_time_srt(segment.get('end', 0))
                text = segment.get('text', '').strip()
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
        print(f"🎬 Subtítulos guardados: {srt_file}")
        saved_files.append(srt_file)
    
    return saved_files

def format_time_srt(seconds):
    """
    Convierte segundos a formato SRT (HH:MM:SS,mmm)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

def main():
    print("🎥 GENERADOR DE TRANSCRIPCIONES DE ALTA CALIDAD")
    print("=" * 50)
    
    # Validar configuración
    config_errors = validate_all_paths()
    if config_errors:
        print("❌ ERRORES DE CONFIGURACIÓN:")
        for error in config_errors:
            print(f"  - {error}")
        print("🔧 Revisa el archivo config.py")
        sys.exit(1)
    
    # Mostrar configuración si está habilitado
    if TranscriptionConfig.VERBOSE:
        print_configuration_summary()
        print()
    
    # Configuración de rutas desde config.py
    video_input_path = TranscriptionConfig.VIDEO_INPUT_PATH  
    output_dir = TranscriptionConfig.OUTPUT_DIRECTORY
    
    # Paso 1: Verificar archivo de video
    if not video_input_path.exists():
        print(f"❌ Error: No se encontró el archivo de video: {video_input_path}")
        sys.exit(1)
    print(f"✅ Archivo de video encontrado: {video_input_path}")
    video_file = str(video_input_path)
    
    # Paso 2: Cargar modelo Whisper
    model = load_whisper_model()  # Usa configuración de config.py
    if not model:
        sys.exit(1)
    
    # Paso 3: Generar transcripción
    result = generate_transcription(model, video_file)
    if not result:
        sys.exit(1)
    
    # Paso 4: Guardar resultados
    saved_files = save_transcription(result, video_file, output_dir)
    
    print("\n" + "=" * 50)
    print("🎉 TRANSCRIPCIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 50)
    print(f"📁 Archivos generados en: {os.path.basename(output_dir)}/")
    
    # Mostrar archivos generados
    for file_path in saved_files:
        file_name = os.path.basename(file_path)
        if file_name.endswith('.txt'):
            print(f"📄 Texto plano: {file_name}")
        elif file_name.endswith('.json'):
            print(f"📋 JSON detallado: {file_name}")
        elif file_name.endswith('.srt'):
            print(f"🎬 Subtítulos SRT: {file_name}")
    
    # Mostrar preview del texto
    preview = result['text'][:200] + "..." if len(result['text']) > 200 else result['text']
    print(f"\n📝 Preview del texto transcrito:")
    print(f'"{preview}"')

if __name__ == "__main__":
    main()