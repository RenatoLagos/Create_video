#!/usr/bin/env python3
"""
Script para sincronizar guión planificado con timestamps reales del video
Empareja frases del script con segmentos del SRT usando similitud de texto
"""

import os
import sys
import json
import re
import difflib
from datetime import datetime
from config import SynchronizationConfig, validate_all_paths, print_configuration_summary

def parse_srt_time(time_str):
    """
    Convierte tiempo SRT (HH:MM:SS,mmm) a segundos
    """
    time_str = time_str.replace(',', '.')
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds

def parse_srt_file(srt_path):
    """
    Parsea archivo SRT y extrae los segmentos con timestamps
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
                        'duration': end_time - start_time,
                        'text': text
                    })
                except Exception as e:
                    if SynchronizationConfig.VERBOSE:
                        print(f"⚠️  Error parseando timestamp '{timestamp_line}': {e}")
                    continue
    
    if SynchronizationConfig.VERBOSE:
        print(f"📄 Parseados {len(segments)} segmentos del archivo SRT")
        if segments:
            print(f"🔍 Primer segmento: \"{segments[0]['text'][:60]}...\"")
            print(f"⏱️  Timing: {segments[0]['start']:.1f}s - {segments[0]['end']:.1f}s")
    
    return segments

def load_script_json(json_path):
    """
    Carga el archivo JSON del script planificado
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Archivo JSON no encontrado: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as file:
        script_data = json.load(file)
    
    if SynchronizationConfig.VERBOSE:
        phrases = script_data.get('analysis', {}).get('phrases_with_video_prompts', [])
        print(f"📋 Cargadas {len(phrases)} frases del script planificado")
    
    return script_data

def clean_text_for_comparison(text):
    """
    Limpia el texto para mejorar la comparación
    """
    # Convertir a minúsculas
    text = text.lower()
    # Remover emojis y caracteres especiales
    text = re.sub(r'[🗣️🎯]+', '', text)
    # Remover puntuación
    text = re.sub(r'[^\w\s]', ' ', text)
    # Normalizar espacios
    text = ' '.join(text.split())
    return text

def calculate_text_similarity(text1, text2):
    """
    Calcula la similitud entre dos textos usando difflib
    """
    clean_text1 = clean_text_for_comparison(text1)
    clean_text2 = clean_text_for_comparison(text2)
    
    # Usar SequenceMatcher para calcular similitud
    similarity = difflib.SequenceMatcher(None, clean_text1, clean_text2).ratio()
    return similarity

def synchronize_by_similarity(script_phrases, srt_segments):
    """
    Sincroniza frases usando similitud de texto
    """
    synchronized_phrases = []
    used_segments = set()
    
    for phrase in script_phrases:
        phrase_text = phrase['phrase']
        best_match = None
        best_similarity = 0
        best_segment_idx = -1
        
        for i, segment in enumerate(srt_segments):
            if i in used_segments:
                continue
                
            similarity = calculate_text_similarity(phrase_text, segment['text'])
            
            if similarity > best_similarity and similarity >= SynchronizationConfig.SIMILARITY_THRESHOLD:
                best_similarity = similarity
                best_match = segment
                best_segment_idx = i
        
        if best_match:
            used_segments.add(best_segment_idx)
            
            # Agregar timing information
            phrase_with_timing = phrase.copy()
            phrase_with_timing['timing'] = {
                'start_time': best_match['start'],
                'end_time': best_match['end'],
                'duration': best_match['duration'],
                'matched_text': best_match['text'],
                'similarity_score': best_similarity
            }
            
            if SynchronizationConfig.SHOW_TEXT_COMPARISON and SynchronizationConfig.VERBOSE:
                print(f"✅ Emparejado (similitud: {best_similarity:.2f}):")
                print(f"   Script: \"{phrase_text[:50]}...\"")
                print(f"   SRT:    \"{best_match['text'][:50]}...\"")
            
            synchronized_phrases.append(phrase_with_timing)
        else:
            # Sin coincidencia encontrada
            phrase_with_timing = phrase.copy()
            phrase_with_timing['timing'] = {
                'start_time': None,
                'end_time': None,
                'duration': None,
                'matched_text': None,
                'similarity_score': 0,
                'status': 'no_match'
            }
            
            if SynchronizationConfig.VERBOSE:
                print(f"❌ Sin coincidencia para: \"{phrase_text[:50]}...\"")
            
            synchronized_phrases.append(phrase_with_timing)
    
    return synchronized_phrases

def synchronize_by_order(script_phrases, srt_segments):
    """
    Sincroniza frases por orden secuencial
    """
    synchronized_phrases = []
    
    for i, phrase in enumerate(script_phrases):
        if i < len(srt_segments):
            segment = srt_segments[i]
            
            phrase_with_timing = phrase.copy()
            phrase_with_timing['timing'] = {
                'start_time': segment['start'],
                'end_time': segment['end'],
                'duration': segment['duration'],
                'matched_text': segment['text'],
                'similarity_score': calculate_text_similarity(phrase['phrase'], segment['text']),
                'method': 'order'
            }
            
            synchronized_phrases.append(phrase_with_timing)
        else:
            # Más frases que segmentos
            phrase_with_timing = phrase.copy()
            phrase_with_timing['timing'] = {
                'start_time': None,
                'end_time': None,
                'duration': None,
                'matched_text': None,
                'similarity_score': 0,
                'status': 'no_segment'
            }
            
            synchronized_phrases.append(phrase_with_timing)
    
    return synchronized_phrases

def synchronize_hybrid(script_phrases, srt_segments):
    """
    Método híbrido: primero por similitud, luego por orden para frases sin coincidencia
    """
    # Primero intentar por similitud
    synchronized_phrases = synchronize_by_similarity(script_phrases, srt_segments)
    
    # Para frases sin coincidencia, intentar asignación por orden
    unmatched_phrases = [p for p in synchronized_phrases if p['timing'].get('status') == 'no_match']
    used_segments = set()
    
    # Identificar segmentos ya usados
    for phrase in synchronized_phrases:
        if phrase['timing']['matched_text']:
            for i, segment in enumerate(srt_segments):
                if segment['text'] == phrase['timing']['matched_text']:
                    used_segments.add(i)
                    break
    
    # Asignar segmentos restantes por orden
    available_segments = [s for i, s in enumerate(srt_segments) if i not in used_segments]
    
    unmatched_count = 0
    for phrase in synchronized_phrases:
        if phrase['timing'].get('status') == 'no_match' and unmatched_count < len(available_segments):
            segment = available_segments[unmatched_count]
            
            phrase['timing'] = {
                'start_time': segment['start'],
                'end_time': segment['end'],
                'duration': segment['duration'],
                'matched_text': segment['text'],
                'similarity_score': calculate_text_similarity(phrase['phrase'], segment['text']),
                'method': 'hybrid_order'
            }
            
            unmatched_count += 1
    
    return synchronized_phrases

def save_synchronized_script(script_data, synchronized_phrases, output_path):
    """
    Guarda el script sincronizado con timestamps
    """
    # Crear copia del script original
    synchronized_script = script_data.copy()
    
    # Reemplazar frases con las sincronizadas
    synchronized_script['analysis']['phrases_with_video_prompts'] = synchronized_phrases
    
    # Agregar metadata de sincronización
    synchronized_script['synchronization'] = {
        'synchronized_at': datetime.now().isoformat(),
        'method': SynchronizationConfig.SYNC_METHOD,
        'similarity_threshold': SynchronizationConfig.SIMILARITY_THRESHOLD,
        'total_phrases': len(synchronized_phrases),
        'matched_phrases': len([p for p in synchronized_phrases if p['timing']['start_time'] is not None]),
        'unmatched_phrases': len([p for p in synchronized_phrases if p['timing']['start_time'] is None])
    }
    
    # Crear directorio de salida si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Guardar archivo sincronizado
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(synchronized_script, f, ensure_ascii=False, indent=2)
    
    if SynchronizationConfig.VERBOSE:
        print(f"💾 Script sincronizado guardado: {output_path}")
    
    return synchronized_script

def main():
    print("🔄 SINCRONIZADOR DE SCRIPT CON TIMESTAMPS")
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
    if SynchronizationConfig.VERBOSE:
        print_configuration_summary()
        print()
    
    try:
        # Paso 1: Cargar script JSON
        print("📋 Paso 1: Cargando script planificado...")
        script_path = SynchronizationConfig.SCRIPT_JSON_PATH
        print(f"🔍 Usando archivo script: {script_path}")
        script_data = load_script_json(str(script_path))
        script_phrases = script_data['analysis']['phrases_with_video_prompts']
        
        # Paso 2: Parsear archivo SRT
        print("📄 Paso 2: Parseando archivo SRT...")
        srt_path = SynchronizationConfig.SRT_INPUT_PATH
        print(f"🔍 Usando archivo SRT: {srt_path}")
        srt_segments = parse_srt_file(str(srt_path))
        
        # Paso 3: Sincronizar según método configurado
        print(f"🔄 Paso 3: Sincronizando usando método '{SynchronizationConfig.SYNC_METHOD}'...")
        
        if SynchronizationConfig.SYNC_METHOD == "similarity":
            synchronized_phrases = synchronize_by_similarity(script_phrases, srt_segments)
        elif SynchronizationConfig.SYNC_METHOD == "order":
            synchronized_phrases = synchronize_by_order(script_phrases, srt_segments)
        elif SynchronizationConfig.SYNC_METHOD == "hybrid":
            synchronized_phrases = synchronize_hybrid(script_phrases, srt_segments)
        
        # Paso 4: Guardar resultado
        print("💾 Paso 4: Guardando script sincronizado...")
        # Nombre único estándar para el pipeline
        output_filename = "synchronized_script.json"
        output_path = SynchronizationConfig.OUTPUT_DIRECTORY / output_filename
        
        result = save_synchronized_script(script_data, synchronized_phrases, output_path)
        
        print("\n" + "=" * 50)
        print("🎉 SINCRONIZACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 50)
        print(f"📁 Archivo guardado en: {output_path}")
        
        # Estadísticas
        sync_info = result['synchronization']
        print(f"📊 Estadísticas:")
        print(f"   Total de frases: {sync_info['total_phrases']}")
        print(f"   Frases emparejadas: {sync_info['matched_phrases']}")
        print(f"   Frases sin emparejar: {sync_info['unmatched_phrases']}")
        print(f"   Método usado: {sync_info['method']}")
        
        if sync_info['matched_phrases'] > 0:
            success_rate = (sync_info['matched_phrases'] / sync_info['total_phrases']) * 100
            print(f"   Tasa de éxito: {success_rate:.1f}%")
        
    except Exception as e:
        print(f"❌ Error durante la sincronización: {str(e)}")
        if SynchronizationConfig.VERBOSE:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()