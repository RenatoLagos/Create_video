#!/usr/bin/env python3
"""
SEARCH STOCK FOOTAGE - Buscador de Videos en APIs
Busca videos en Pexels y Pixabay APIs usando keywords generados por generate_search_keywords.py

Input: search_keywords_id_X.json  
Output: Videos descargados en carpetas separadas por API
"""

import os
import json
import requests
import argparse
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import hashlib
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


class PexelsAPI:
    """Cliente para Pexels Videos API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/videos/search"
        self.headers = {"Authorization": api_key}
        self.rate_limit_delay = 1  # 1 segundo entre requests
    
    def search_videos(self, query: str, per_page: int = 10) -> Dict:
        """Busca videos en Pexels"""
        params = {
            "query": query,
            "per_page": per_page,
            "size": "medium"  # Tamaño medio para mejor rendimiento
        }
        
        try:
            print(f"    [PEXELS] Searching: \"{query}\"...")
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            videos_found = len(data.get('videos', []))
            print(f"    [PEXELS] Found {videos_found} videos")
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"    [PEXELS ERROR] {str(e)}")
            return {"videos": []}
    
    def download_video(self, video_url: str, output_path: str, max_size_mb: int = 50) -> bool:
        """Descarga un video desde Pexels"""
        try:
            # Hacer request con stream para verificar size
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            # Verificar tamaño del archivo
            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > max_size_mb:
                    print(f"        [SKIP] Video too large: {size_mb:.1f}MB")
                    return False
            
            # Descargar archivo
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True
            
        except Exception as e:
            print(f"        [ERROR] Download failed: {str(e)}")
            return False


class PixabayAPI:
    """Cliente para Pixabay Videos API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://pixabay.com/api/videos/"
        self.rate_limit_delay = 1  # 1 segundo entre requests  
    
    def search_videos(self, query: str, per_page: int = 20, video_type: str = "film") -> Dict:
        """Busca videos en Pixabay"""
        params = {
            "key": self.api_key,
            "q": query,
            "per_page": per_page,
            "video_type": video_type,  # film para contenido cinematográfico
            "safesearch": "true"
        }
        
        try:
            print(f"    [PIXABAY] Searching: \"{query}\"...")
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            videos_found = len(data.get('hits', []))
            print(f"    [PIXABAY] Found {videos_found} videos")
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"    [PIXABAY ERROR] {str(e)}")
            return {"hits": []}
    
    def download_video(self, video_url: str, output_path: str, max_size_mb: int = 50) -> bool:
        """Descarga un video desde Pixabay"""
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            # Verificar tamaño si está disponible
            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > max_size_mb:
                    print(f"        [SKIP] Video too large: {size_mb:.1f}MB")
                    return False
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True
            
        except Exception as e:
            print(f"        [ERROR] Download failed: {str(e)}")
            return False


def generate_filename(query: str, video_id: str, api_source: str) -> str:
    """Genera nombre de archivo único para el video"""
    # Limpiar query para filename
    clean_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
    clean_query = clean_query.replace(' ', '_')[:30]  # Limitar longitud
    
    return f"{api_source}_{clean_query}_{video_id}.mp4"


def search_and_download_videos(
    script_id: int,
    keywords_file: str = None,
    pexels_api_key: str = None,
    pixabay_api_key: str = None,
    max_videos_per_query: int = 10,
    max_total_videos: int = 20
):
    """
    Busca y descarga videos usando las APIs de Pexels y Pixabay
    """
    
    # Determinar archivo de keywords
    if keywords_file is None:
        keywords_dir = Path("VideoProduction/05_StockFootage/01_search_keywords")
        keywords_file = keywords_dir / f"search_keywords_id_{script_id}.json"
    
    print(f">> STOCK FOOTAGE SEARCH - SCRIPT ID {script_id}")
    print("=" * 60)
    print(f">> Keywords file: {keywords_file}")
    print(f">> Max videos per query: {max_videos_per_query}")
    print(f">> Max total videos: {max_total_videos}")
    print()
    
    # Verificar archivo de keywords
    if not keywords_file.exists():
        print(f"[ERROR] Keywords file not found: {keywords_file}")
        print(f"Run: python generate_search_keywords.py --script-id {script_id}")
        return None
    
    # Cargar keywords
    print(">> Loading search keywords...")
    with open(keywords_file, 'r', encoding='utf-8') as f:
        keywords_data = json.load(f)
    
    # Extraer queries
    primary_queries = keywords_data.get('api_ready_keywords', {}).get('primary_queries', [])
    secondary_queries = keywords_data.get('api_ready_keywords', {}).get('secondary_queries', [])
    fallback_queries = keywords_data.get('api_ready_keywords', {}).get('fallback_queries', [])
    
    all_queries = primary_queries + secondary_queries + fallback_queries
    selected_queries = all_queries[:8]  # Limitar queries para no saturar APIs
    
    print(f"[OK] Loaded {len(selected_queries)} search queries")
    
    # Crear directorios de salida
    base_output_dir = Path("VideoProduction/05_StockFootage/02_downloaded_videos") / f"script_id_{script_id}"
    pexels_dir = base_output_dir / "pexels"
    pixabay_dir = base_output_dir / "pixabay"
    
    pexels_dir.mkdir(parents=True, exist_ok=True)
    pixabay_dir.mkdir(parents=True, exist_ok=True)
    
    # Inicializar APIs
    apis_available = []
    pexels_client = None
    pixabay_client = None
    
    if pexels_api_key:
        pexels_client = PexelsAPI(pexels_api_key)
        apis_available.append("pexels")
        print(f"[OK] Pexels API initialized")
    else:
        print(f"[WARNING] No Pexels API key provided")
    
    if pixabay_api_key:
        pixabay_client = PixabayAPI(pixabay_api_key)
        apis_available.append("pixabay")
        print(f"[OK] Pixabay API initialized")
    else:
        print(f"[WARNING] No Pixabay API key provided")
    
    if not apis_available:
        print(f"[ERROR] No API keys provided!")
        return None
    
    # Resultados de búsqueda
    results = {
        'script_id': script_id,
        'topic': keywords_data.get('topic', 'Unknown'),
        'searches_performed': [],
        'videos_downloaded': {
            'pexels': [],
            'pixabay': []
        },
        'summary': {
            'total_queries': len(selected_queries),
            'total_videos_found': 0,
            'total_videos_downloaded': 0
        }
    }
    
    downloaded_count = 0
    
    # Buscar en cada API
    for query in selected_queries:
        if downloaded_count >= max_total_videos:
            break
        
        print(f"\n>> Query: \"{query}\"")
        
        search_result = {
            'query': query,
            'pexels_results': 0,
            'pixabay_results': 0,
            'downloads_attempted': 0,
            'downloads_successful': 0
        }
        
        # PEXELS API
        if pexels_client and downloaded_count < max_total_videos:
            pexels_data = pexels_client.search_videos(query, per_page=max_videos_per_query)
            pexels_videos = pexels_data.get('videos', [])
            search_result['pexels_results'] = len(pexels_videos)
            
            for video in pexels_videos[:max_videos_per_query]:
                if downloaded_count >= max_total_videos:
                    break
                
                try:
                    video_id = str(video.get('id', 'unknown'))
                    video_files = video.get('video_files', [])
                    
                    # Buscar mejor calidad disponible (medium preferred)
                    best_video = None
                    for vf in video_files:
                        if vf.get('quality') == 'hd' and vf.get('width', 0) <= 1280:
                            best_video = vf
                            break
                    
                    if not best_video and video_files:
                        best_video = video_files[0]  # Fallback al primero disponible
                    
                    if best_video:
                        video_url = best_video.get('link', '')
                        filename = generate_filename(query, video_id, "pexels")
                        output_path = pexels_dir / filename
                        
                        search_result['downloads_attempted'] += 1
                        if pexels_client.download_video(video_url, str(output_path)):
                            downloaded_count += 1
                            search_result['downloads_successful'] += 1
                            
                            video_info = {
                                'filename': filename,
                                'video_id': video_id,
                                'query_used': query,
                                'duration': video.get('duration', 0),
                                'width': best_video.get('width', 0),
                                'height': best_video.get('height', 0),
                                'url': video.get('url', ''),
                                'user': video.get('user', {}).get('name', 'Unknown')
                            }
                            results['videos_downloaded']['pexels'].append(video_info)
                            
                            print(f"        [OK] Downloaded: {filename}")
                        
                except Exception as e:
                    print(f"        [ERROR] Processing Pexels video: {e}")
        
        # PIXABAY API
        if pixabay_client and downloaded_count < max_total_videos:
            pixabay_data = pixabay_client.search_videos(query, per_page=max_videos_per_query)
            pixabay_videos = pixabay_data.get('hits', [])
            search_result['pixabay_results'] = len(pixabay_videos)
            
            for video in pixabay_videos[:max_videos_per_query]:
                if downloaded_count >= max_total_videos:
                    break
                
                try:
                    video_id = str(video.get('id', 'unknown'))
                    video_streams = video.get('videos', {})
                    
                    # Seleccionar mejor stream (medium preferred)
                    best_stream = None
                    for size in ['medium', 'small', 'large', 'tiny']:
                        if size in video_streams:
                            best_stream = video_streams[size]
                            break
                    
                    if best_stream:
                        video_url = best_stream.get('url', '')
                        filename = generate_filename(query, video_id, "pixabay")
                        output_path = pixabay_dir / filename
                        
                        search_result['downloads_attempted'] += 1
                        if pixabay_client.download_video(video_url, str(output_path)):
                            downloaded_count += 1
                            search_result['downloads_successful'] += 1
                            
                            video_info = {
                                'filename': filename,
                                'video_id': video_id,
                                'query_used': query,
                                'duration': video.get('duration', 0),
                                'width': best_stream.get('width', 0),
                                'height': best_stream.get('height', 0),
                                'pageURL': video.get('pageURL', ''),
                                'user': video.get('user', 'Unknown'),
                                'tags': video.get('tags', '')
                            }
                            results['videos_downloaded']['pixabay'].append(video_info)
                            
                            print(f"        [OK] Downloaded: {filename}")
                        
                except Exception as e:
                    print(f"        [ERROR] Processing Pixabay video: {e}")
        
        results['searches_performed'].append(search_result)
        results['summary']['total_videos_found'] += search_result['pexels_results'] + search_result['pixabay_results']
    
    # Actualizar resumen
    results['summary']['total_videos_downloaded'] = downloaded_count
    results['summary']['pexels_videos'] = len(results['videos_downloaded']['pexels'])
    results['summary']['pixabay_videos'] = len(results['videos_downloaded']['pixabay'])
    
    # Guardar resultados
    results_file = base_output_dir / f"search_results_{script_id}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Mostrar resumen final
    print(f"\n" + "=" * 60)
    print(f"[OK] SEARCH COMPLETED!")
    print(f"=" * 60)
    print(f">> Script ID: {script_id}")
    print(f">> Topic: {results['topic']}")
    print(f">> Queries searched: {results['summary']['total_queries']}")
    print(f">> Videos found: {results['summary']['total_videos_found']}")
    print(f">> Videos downloaded: {results['summary']['total_videos_downloaded']}")
    print(f"   • Pexels: {results['summary']['pexels_videos']}")
    print(f"   • Pixabay: {results['summary']['pixabay_videos']}")
    print(f">> Results saved: {results_file}")
    print(f">> Videos location:")
    print(f"   • Pexels: {pexels_dir}")
    print(f"   • Pixabay: {pixabay_dir}")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Search and download stock footage videos from Pexels and Pixabay APIs',
        epilog="""
Examples:
  python search_stock_footage.py --script-id 11
  python search_stock_footage.py --script-id 5 --max-videos 50
  python search_stock_footage.py --script-id 7 --pexels-key YOUR_KEY --pixabay-key YOUR_KEY --max-per-query 5

API Keys:
  Create .env file in project root:
    PEXELS_API_KEY=your_pexels_key
    PIXABAY_API_KEY=your_pixabay_key
  
  Or pass directly:
    --pexels-key YOUR_PEXELS_KEY
    --pixabay-key YOUR_PIXABAY_KEY

Output structure:
  VideoProduction/05_StockFootage/02_downloaded_videos/script_id_X/
    ├── pexels/          # Pexels videos
    ├── pixabay/         # Pixabay videos  
    └── search_results_X.json  # Search metadata
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--script-id', type=int, required=True,
                       help='Script ID to process (1-60)')
    parser.add_argument('--keywords-file', type=str,
                       help='Keywords JSON file (optional)')
    parser.add_argument('--pexels-key', type=str,
                       help='Pexels API key (or use PEXELS_API_KEY env var)')
    parser.add_argument('--pixabay-key', type=str,
                       help='Pixabay API key (or use PIXABAY_API_KEY env var)')
    parser.add_argument('--max-videos', type=int, default=20,
                       help='Maximum total videos to download (default: 20)')
    parser.add_argument('--max-per-query', type=int, default=10,
                       help='Maximum videos per search query (default: 10)')
    
    args = parser.parse_args()
    
    # Validar script ID
    if args.script_id < 1 or args.script_id > 60:
        print(f"[ERROR] Invalid script ID: {args.script_id}")
        print("Valid range: 1-60")
        sys.exit(1)
    
    # Obtener API keys
    pexels_key = args.pexels_key or os.getenv('PEXELS_API_KEY')
    pixabay_key = args.pixabay_key or os.getenv('PIXABAY_API_KEY')
    
    if not pexels_key and not pixabay_key:
        print("[ERROR] No API keys provided!")
        print("Please provide at least one API key:")
        print("  1. Create .env file in project root:")
        print("     PEXELS_API_KEY=your_pexels_key")
        print("     PIXABAY_API_KEY=your_pixabay_key")
        print("  2. Or pass directly:")
        print("     --pexels-key YOUR_PEXELS_KEY")
        print("     --pixabay-key YOUR_PIXABAY_KEY")
        sys.exit(1)
    
    # Ejecutar búsqueda
    try:
        result = search_and_download_videos(
            script_id=args.script_id,
            keywords_file=args.keywords_file, 
            pexels_api_key=pexels_key,
            pixabay_api_key=pixabay_key,
            max_videos_per_query=args.max_per_query,
            max_total_videos=args.max_videos
        )
        
        if result:
            print("\n[OK] SUCCESS! Stock footage search completed")
        else:
            print("\n[ERROR] FAILED! Could not complete search")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[ERROR] FATAL ERROR: {str(e)}")
        sys.exit(1)