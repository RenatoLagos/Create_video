#!/usr/bin/env python3
"""
GENERATE SEARCH KEYWORDS - Transformador de Scripts a Keywords para APIs
Convierte los scripts generados por content_01 en keywords simples para búsqueda en APIs de stock footage.

Input: script_id_X.json (salida de content_01_generate_transcriptwriter.py)
Output: search_keywords_id_X.json (keywords optimizados para Pexels/Pixabay APIs)
"""

import json
import re
import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Set
from config import ContentGenerationConfig


def extract_keywords_from_text(text: str) -> Set[str]:
    """
    Extrae keywords relevantes de un texto para búsqueda de stock footage
    """
    keywords = set()
    
    # Convertir a minúsculas y limpiar
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)  # Remover puntuación
    words = text.split()
    
    # Keywords de interés específico para video stock
    video_keywords = {
        # Personas y emociones
        'people', 'person', 'man', 'woman', 'face', 'smile', 'happy', 'sad', 
        'confused', 'embarrassed', 'thinking', 'talking', 'speaking',
        
        # Acciones comunes
        'eating', 'drinking', 'walking', 'sitting', 'standing', 'looking', 
        'pointing', 'gesturing', 'writing', 'reading', 'cooking', 'working',
        
        # Lugares
        'restaurant', 'office', 'home', 'kitchen', 'street', 'park', 'beach',
        'cafe', 'bar', 'market', 'store', 'hospital', 'school', 'airport',
        
        # Objetos
        'food', 'drink', 'coffee', 'phone', 'book', 'computer', 'car', 'money',
        'bag', 'clothes', 'table', 'chair', 'door', 'window', 'hands', 'eyes',
        
        # Situaciones
        'meeting', 'conversation', 'shopping', 'travel', 'business', 'family',
        'friends', 'party', 'celebration', 'mistake', 'learning', 'teaching'
    }
    
    # Buscar keywords relevantes en el texto
    for word in words:
        if word in video_keywords:
            keywords.add(word)
    
    # Agregar palabras clave específicas según el contexto
    if any(w in text for w in ['pregnant', 'pregnancy', 'embarazada']):
        keywords.update(['pregnant', 'woman', 'belly', 'happy'])
    
    if any(w in text for w in ['embarrassed', 'shame', 'awkward']):
        keywords.update(['embarrassed', 'face', 'red', 'awkward'])
    
    if any(w in text for w in ['restaurant', 'food', 'eating']):
        keywords.update(['restaurant', 'food', 'eating', 'dining'])
    
    if any(w in text for w in ['spanish', 'language', 'learning']):
        keywords.update(['learning', 'education', 'language', 'teaching'])
    
    return keywords


def generate_search_queries(keywords: Set[str], max_combinations: int = 10) -> List[str]:
    """
    Genera queries de búsqueda combinando keywords de manera inteligente
    """
    keywords_list = list(keywords)
    queries = []
    
    # Query principal con todas las keywords más relevantes
    if len(keywords_list) >= 3:
        main_query = ' '.join(keywords_list[:3])
        queries.append(main_query)
    
    # Queries individuales para keywords importantes
    priority_keywords = ['people', 'person', 'woman', 'man', 'restaurant', 'food', 'learning']
    for keyword in keywords_list[:5]:  # Top 5 keywords
        if keyword in priority_keywords or len(keyword) > 4:
            queries.append(keyword)
    
    # Queries combinadas (2 keywords)
    for i in range(min(len(keywords_list), 4)):
        for j in range(i+1, min(len(keywords_list), 6)):
            combined = f"{keywords_list[i]} {keywords_list[j]}"
            queries.append(combined)
            if len(queries) >= max_combinations:
                break
        if len(queries) >= max_combinations:
            break
    
    # Queries genéricas para fallback
    queries.extend([
        "people talking",
        "person thinking", 
        "restaurant dining",
        "learning education",
        "business meeting"
    ])
    
    # Remover duplicados manteniendo orden
    seen = set()
    unique_queries = []
    for query in queries:
        if query not in seen:
            seen.add(query)
            unique_queries.append(query)
    
    return unique_queries[:max_combinations]


def process_script_to_keywords(script_id: int, input_file: str = None, output_file: str = None):
    """
    Procesa un script y genera keywords para búsqueda de stock footage
    """
    try:
        # Determinar archivo de entrada
        if input_file is None:
            base_dir = Path(ContentGenerationConfig.GENERATED_SCRIPTS_FILE).parent
            input_file = base_dir / f"script_id_{script_id}.json"
        
        # Determinar archivo de salida
        if output_file is None:
            # Crear directorio para keywords
            output_dir = Path("VideoProduction/05_StockFootage/01_search_keywords")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"search_keywords_id_{script_id}.json"
        
        print(f">> KEYWORD GENERATOR - SCRIPT ID {script_id}")
        print("=" * 50)
        print(f">> Input: {input_file}")
        print(f">> Output: {output_file}")
        print()
        
        # Verificar que el archivo existe
        if not input_file.exists():
            print(f"[ERROR] Script file not found: {input_file}")
            print(f"Make sure you've run content_01_generate_transcriptwriter.py --topic-id {script_id} first")
            return None
        
        # Cargar script
        print(">> Loading script data...")
        with open(input_file, 'r', encoding='utf-8') as f:
            script_data = json.load(f)
        
        # Validar datos
        if script_data.get('id') != script_id:
            print(f"[ERROR] Script ID mismatch! Expected {script_id}, found {script_data.get('id')}")
            return None
        
        category = script_data.get('category', 'Unknown')
        topic = script_data.get('topic', 'Unknown')
        script = script_data.get('script', {})
        
        print(f"[OK] Loaded script: {topic}")
        print(f">> Category: {category}")
        
        # Extraer text content
        hook = script.get('hook', '')
        development = script.get('development', '')
        closing = script.get('closing', '')
        
        full_text = f"{topic} {hook} {development} {closing}"
        
        print(">> Extracting keywords...")
        
        # Extraer keywords de cada sección
        topic_keywords = extract_keywords_from_text(topic)
        hook_keywords = extract_keywords_from_text(hook)
        development_keywords = extract_keywords_from_text(development)
        closing_keywords = extract_keywords_from_text(closing)
        all_keywords = extract_keywords_from_text(full_text)
        
        # Generar queries de búsqueda
        print(">> Generating search queries...")
        
        search_queries = {
            'general': generate_search_queries(all_keywords, 8),
            'topic_focused': generate_search_queries(topic_keywords, 5),
            'hook_focused': generate_search_queries(hook_keywords, 5),
            'development_focused': generate_search_queries(development_keywords, 5)
        }
        
        # Crear resultado final
        result = {
            'script_id': script_id,
            'category': category,
            'topic': topic,
            'extracted_keywords': {
                'all_keywords': sorted(list(all_keywords)),
                'topic_keywords': sorted(list(topic_keywords)),
                'hook_keywords': sorted(list(hook_keywords)),
                'development_keywords': sorted(list(development_keywords)),
                'closing_keywords': sorted(list(closing_keywords))
            },
            'search_queries': search_queries,
            'api_ready_keywords': {
                'primary_queries': search_queries['general'][:5],
                'secondary_queries': search_queries['topic_focused'][:3] + search_queries['hook_focused'][:2],
                'fallback_queries': [
                    "people conversation",
                    "person talking",
                    "business meeting",
                    "restaurant dining",
                    "learning education"
                ]
            },
            'generated_at': {
                'timestamp': str(Path(__file__).stat().st_mtime),
                'script': __file__
            }
        }
        
        # Guardar resultado
        print(f">> Saving keywords to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Mostrar resumen
        total_keywords = len(all_keywords)
        total_queries = len(search_queries['general']) + len(search_queries['topic_focused'])
        
        print(f"\n[OK] Keywords generated successfully!")
        print(f">> Summary:")
        print(f"   • Script ID: {script_id}")
        print(f"   • Topic: {topic}")
        print(f"   • Category: {category}")
        print(f"   • Total keywords extracted: {total_keywords}")
        print(f"   • Total search queries: {total_queries}")
        print(f"   • Primary queries: {len(result['api_ready_keywords']['primary_queries'])}")
        print(f"   • Output file: {output_file}")
        
        # Mostrar algunas queries como ejemplo
        print(f"\n>> Primary search queries:")
        for i, query in enumerate(result['api_ready_keywords']['primary_queries'][:3], 1):
            print(f"   {i}. \"{query}\"")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Error processing script {script_id}: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate search keywords from script for stock footage APIs',
        epilog="""
Examples:
  python generate_search_keywords.py --script-id 11
  python generate_search_keywords.py --script-id 5 --output custom_keywords.json

This script converts content_01 script output into API-ready search keywords:
  • Extracts relevant keywords from script text
  • Generates optimized search queries for stock footage
  • Creates fallback queries for better coverage
  • Outputs structured JSON ready for API consumption
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--script-id', type=int, required=True,
                       help='Script ID to process (1-60)')
    parser.add_argument('--input-file', type=str,
                       help='Input script JSON file (optional)')
    parser.add_argument('--output-file', type=str,
                       help='Output keywords JSON file (optional)')
    
    args = parser.parse_args()
    
    # Validar script ID
    if args.script_id < 1 or args.script_id > 60:
        print(f"[ERROR] Invalid script ID: {args.script_id}")
        print("Valid range: 1-60")
        sys.exit(1)
    
    # Procesar script
    try:
        result = process_script_to_keywords(
            script_id=args.script_id,
            input_file=args.input_file,
            output_file=args.output_file
        )
        
        if result:
            print("\n[OK] SUCCESS! Keywords generated successfully")
        else:
            print("\n[ERROR] FAILED! Could not generate keywords")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[ERROR] FATAL ERROR: {str(e)}")
        sys.exit(1)