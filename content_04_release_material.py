#!/usr/bin/env python3
"""
4s_release_output.py
Script para extraer y organizar materiales de un script específico para producción de video.

Extrae el JSON del script y el archivo HTML correspondiente y los copia a:
C:/Users/Admin/Projects/Create_video/Video/Material/

Uso: python 4s_release_output.py [script_id]
Ejemplo: python 4s_release_output.py 11
"""

import json
import os
import shutil
import sys
from pathlib import Path
from config import ContentGenerationConfig, VIDEO_PRODUCTION_DIR

def create_directory_structure(base_path):
    """Crea la estructura de carpetas necesaria."""
    full_path = Path(base_path)
    
    # Crear carpetas Material y Results
    material_path = full_path / "Material"
    results_path = full_path / "Results"
    
    material_path.mkdir(parents=True, exist_ok=True)
    results_path.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Estructura de carpetas verificada en: {full_path}")
    return material_path, results_path

def extract_script_from_json(json_file_path, script_id):
    """Extrae el script específico del archivo JSON."""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            scripts_data = json.load(f)
        
        # Buscar el script con el ID específico
        target_script = None
        for script in scripts_data:
            if script.get('script_number') == script_id:
                target_script = script
                break
        
        if target_script is None:
            print(f"❌ Error: No se encontró el script con ID {script_id}")
            return None
        
        print(f"✅ Script {script_id} encontrado: {target_script.get('topic', 'Sin título')}")
        return target_script
        
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {json_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error al leer el JSON: {e}")
        return None

def copy_html_file(scripts_folder, script_id, destination_path):
    """Copia el archivo HTML correspondiente."""
    html_filename = f"narrator_short_script_{script_id}.html"
    source_path = Path(scripts_folder) / html_filename
    destination_file = destination_path / html_filename
    
    try:
        if source_path.exists():
            shutil.copy2(source_path, destination_file)
            print(f"✅ Archivo HTML copiado: {html_filename}")
            return True
        else:
            print(f"❌ Error: No se encontró el archivo {html_filename} en {scripts_folder}")
            return False
    except Exception as e:
        print(f"❌ Error copiando HTML: {e}")
        return False

def save_script_json(script_data, destination_path, script_id):
    """Guarda el fragmento JSON del script específico."""
    json_filename = f"script_{script_id}_data.json"
    json_file_path = destination_path / json_filename
    
    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Datos JSON guardados: {json_filename}")
        return True
    except Exception as e:
        print(f"❌ Error guardando JSON: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("❌ Uso: python 4s_release_output.py [script_id]")
        print("   Ejemplo: python 4s_release_output.py 11")
        sys.exit(1)
    
    try:
        script_id = int(sys.argv[1])
    except ValueError:
        print("❌ Error: El ID del script debe ser un número entero")
        sys.exit(1)
    
    print(f"🎬 Procesando script ID: {script_id}")
    print("=" * 50)
    
    # Rutas de archivos y carpetas
    json_file_path = ContentGenerationConfig.ANALYZED_SCRIPTS_FILE
    scripts_folder = ContentGenerationConfig.NARRATOR_SCRIPTS_DIR  
    video_base_path = VIDEO_PRODUCTION_DIR
    
    # Verificar que los archivos fuente existen
    if not json_file_path.exists():
        print(f"❌ Error: No se encontró el archivo JSON en {json_file_path}")
        sys.exit(1)
    
    if not scripts_folder.exists():
        print(f"❌ Error: No se encontró la carpeta de scripts en {scripts_folder}")
        sys.exit(1)
    
    # 1. Usar carpeta de material de la nueva estructura
    material_path = ContentGenerationConfig.RELEASE_MATERIAL_DIR
    material_path.mkdir(parents=True, exist_ok=True)
    results_path = video_base_path / "Results"
    results_path.mkdir(parents=True, exist_ok=True)
    
    # 2. Extraer datos del JSON
    script_data = extract_script_from_json(json_file_path, script_id)
    if script_data is None:
        sys.exit(1)
    
    # 3. Guardar JSON del script específico
    json_success = save_script_json(script_data, material_path, script_id)
    
    # 4. Copiar archivo HTML
    html_success = copy_html_file(scripts_folder, script_id, material_path)
    
    # Resumen final
    print("=" * 50)
    if json_success and html_success:
        print(f"🎉 ¡Proceso completado exitosamente!")
        print(f"📁 Materiales disponibles en: {material_path}")
        print(f"📁 Carpeta de resultados: {results_path}")
        print(f"📄 Archivos agregados a Material:")
        print(f"   - script_{script_id}_data.json")
        print(f"   - narrator_short_script_{script_id}.html")
    else:
        print("⚠️  El proceso se completó con algunos errores")

if __name__ == "__main__":
    main()