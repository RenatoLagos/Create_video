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
import argparse
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
                        print(f">>  Error parseando timestamp '{timestamp_line}': {e}")
                    continue
    
    if SynchronizationConfig.VERBOSE:
        print(f">> Parseados {len(segments)} segmentos del archivo SRT")
        if segments:
            print(f">> Primer segmento: \"{segments[0]['text'][:60]}...\"")
            print(f"Time:  Timing: {segments[0]['start']:.1f}s - {segments[0]['end']:.1f}s")
    
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
        print(f">> Cargadas {len(phrases)} frases del script planificado")
    
    return script_data

def clean_text_for_comparison(text):
    """
    Limpia el texto para mejorar la comparación
    """
    # Convertir a minúsculas
    text = text.lower()
    # Remover emojis y caracteres especiales
    text = re.sub(r'[^\w\s]', '', text)
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
                print(f"[OK] Emparejado (similitud: {best_similarity:.2f}):")
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
                print(f"[ERROR] Sin coincidencia para: \"{phrase_text[:50]}...\"")
            
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
        print(f">> Script sincronizado guardado: {output_path}")
    
    return synchronized_script

def synchronize_single_script(script_id: int, input_file: str = None, output_file: str = None, srt_file: str = None):
    """
    Sincroniza un script específico por ID con timestamps del SRT
    
    Args:
        script_id: ID del script a sincronizar (obligatorio)
        input_file: Archivo JSON del script analizado (opcional)
        output_file: Archivo JSON de salida sincronizado (opcional)
        srt_file: Archivo SRT con timestamps (opcional)
    """
    try:
        # Determinar archivo de entrada
        if input_file is None:
            base_dir = "VideoProduction/01_ContentGeneration/03_analyzed_scripts"
            input_file = os.path.join(base_dir, f"analyzed_script_id_{script_id}.json")
        
        # Determinar archivo de salida
        if output_file is None:
            output_dir = SynchronizationConfig.OUTPUT_DIRECTORY
            output_file = output_dir / f"synchronized_script_id_{script_id}.json"
        
        # Determinar archivo SRT
        if srt_file is None:
            srt_file = str(SynchronizationConfig.SRT_INPUT_PATH)
        
        print(">> SCRIPT SYNCHRONIZER - SINGLE SCRIPT MODE")
        print("=" * 55)
        print(f">> Target Script ID: {script_id}")
        print(f">> Input: {input_file}")
        print(f">> SRT File: {srt_file}")
        print(f">> Output: {output_file}")
        print(f">> Method: {SynchronizationConfig.SYNC_METHOD}")
        print()
        
        # Verificar que el archivo de entrada existe
        if not os.path.exists(input_file):
            print(f"[ERROR] Input file not found: {input_file}")
            print(f"Make sure you've run content_02_analyze_scripts_video_prompts.py --script-id {script_id} first")
            return None
        
        # Verificar que el archivo SRT existe
        if not os.path.exists(srt_file):
            print(f"[ERROR] SRT file not found: {srt_file}")
            print("Make sure the SRT file exists in the configured path")
            return None
        
        # Paso 1: Cargar script JSON
        print(">> Step 1: Loading analyzed script...")
        script_data = load_script_json(input_file)
        
        # Validar que el ID coincida
        script_id_in_file = script_data.get('id')
        if script_id_in_file != script_id:
            print(f"[ERROR] Script ID mismatch! Expected {script_id}, found {script_id_in_file}")
            return None
        
        script_phrases = script_data['analysis']['phrases_with_video_prompts']
        topic = script_data.get('topic', 'Unknown')
        
        print(f"[OK] Loaded script: {topic}")
        print(f">> Found {len(script_phrases)} phrases to synchronize")
        
        # Paso 2: Parsear archivo SRT
        print(">> Step 2: Parsing SRT file...")
        srt_segments = parse_srt_file(srt_file)
        
        print(f"[OK] Found {len(srt_segments)} SRT segments")
        
        # Paso 3: Sincronizar según método configurado
        print(f">> Step 3: Synchronizing using '{SynchronizationConfig.SYNC_METHOD}' method...")
        
        if SynchronizationConfig.SYNC_METHOD == "similarity":
            synchronized_phrases = synchronize_by_similarity(script_phrases, srt_segments)
        elif SynchronizationConfig.SYNC_METHOD == "order":
            synchronized_phrases = synchronize_by_order(script_phrases, srt_segments)
        elif SynchronizationConfig.SYNC_METHOD == "hybrid":
            synchronized_phrases = synchronize_hybrid(script_phrases, srt_segments)
        else:
            print(f"[ERROR] Unknown synchronization method: {SynchronizationConfig.SYNC_METHOD}")
            return None
        
        # Paso 4: Guardar resultado
        print(">> Step 4: Saving synchronized script...")
        
        result = save_synchronized_script(script_data, synchronized_phrases, output_file)
        
        print(f"\n[OK] SYNCHRONIZATION COMPLETED SUCCESSFULLY!")
        print("=" * 55)
        print(f">> File saved: {output_file}")
        
        # Estadísticas
        sync_info = result['synchronization']
        print(f">> Statistics:")
        print(f"   • Script ID: {script_id}")
        print(f"   • Topic: {topic}")
        print(f"   • Total phrases: {sync_info['total_phrases']}")
        print(f"   • Matched phrases: {sync_info['matched_phrases']}")
        print(f"   • Unmatched phrases: {sync_info['unmatched_phrases']}")
        print(f"   • Method used: {sync_info['method']}")
        
        if sync_info['matched_phrases'] > 0:
            success_rate = (sync_info['matched_phrases'] / sync_info['total_phrases']) * 100
            print(f"   • Success rate: {success_rate:.1f}%")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Error synchronizing script {script_id}: {str(e)}")
        if SynchronizationConfig.VERBOSE:
            import traceback
            traceback.print_exc()
        return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Synchronize script with SRT timestamps for a specific script ID')
    parser.add_argument('--script-id', type=int, required=True,
                       help='Script ID to synchronize (required, range: 1-60)')
    parser.add_argument('--input-file', type=str, help='Input analyzed script JSON file (optional)')
    parser.add_argument('--output-file', type=str, help='Output synchronized script JSON file (optional)')
    parser.add_argument('--srt-file', type=str, help='Input SRT file with timestamps (optional)')
    
    args = parser.parse_args()
    
    # Validate script ID range
    if args.script_id < 1 or args.script_id > 60:
        print(f"[ERROR] Invalid script ID: {args.script_id}")
        print("Valid range: 1-60")
        sys.exit(1)
    
    # Process single script synchronization
    result = synchronize_single_script(
        script_id=args.script_id,
        input_file=args.input_file,
        output_file=args.output_file,
        srt_file=args.srt_file
    )
    
    if result:
        print("\n[OK] SUCCESS! Script synchronized successfully")
    else:
        print("\n[ERROR] FAILED! Could not synchronize script")
        sys.exit(1)

if __name__ == "__main__":
    main()