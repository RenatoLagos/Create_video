#!/usr/bin/env python3
import json
import sys
import argparse
from datetime import datetime
import os
from config import ContentGenerationConfig

def load_script_data(json_file_path):
    """Carga los datos del archivo JSON de script analizado"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"[ERROR] Error: No se encontró el archivo {json_file_path}")
        return None
    except json.JSONDecodeError:
        print(f"[ERROR] Error: El archivo {json_file_path} no es un JSON válido")
        return None

def parse_script_to_phrases(script_data):
    """Convierte el script en frases individuales"""
    script = script_data.get('original_script', {})
    hook = script.get('hook', '')
    development = script.get('development', '')
    closing = script.get('closing', '')
    
    phrases = []
    
    # Agregar hook como frase
    if hook:
        phrases.append(hook)
    
    # Dividir development en frases más pequeñas
    if development:
        # Dividir por 👉 o por puntos si es muy largo
        if '👉' in development:
            parts = development.split('👉')
            for i, part in enumerate(parts):
                if part.strip():
                    if i == 0:
                        phrases.append(part.strip())
                    else:
                        phrases.append(f"👉{part.strip()}")
        else:
            phrases.append(development)
    
    # Agregar closing como frase
    if closing:
        phrases.append(closing)
    
    return phrases

def generate_narrator_script(script_data, script_id):
    """Genera el guión HTML para un script específico"""
    
    topic = script_data.get('topic', 'Sin título')
    category = script_data.get('category', 'Sin categoría')
    
    script_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Guión Script ID {script_id}</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 30px;
            line-height: 1.8;
            background-color: white;
            color: #333;
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.8em;
        }}
        .info {{
            text-align: center;
            margin-bottom: 50px;
            color: #666;
            font-size: 1em;
        }}
        .info p {{
            margin: 5px 0;
        }}
        .phrase {{
            margin: 25px 0;
            font-size: 1.2em;
        }}
        .narrator-instruction {{
            font-size: 1.5em;
            margin-right: 10px;
        }}
        .phrase-text {{
            display: inline;
            color: #333;
        }}
        .timestamp {{
            text-align: center;
            color: #888;
            font-size: 0.9em;
            margin-top: 60px;
            border-top: 1px solid #eee;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <h1>>> Script ID {script_id}</h1>
    
    <div class="info">
        <p><strong>ID:</strong> {script_id}</p>
        <p><strong>CATEGORÍA:</strong> {category}</p>
        <p><strong>TEMA:</strong> {topic}</p>
    </div>

"""
    
    # Obtener las frases parseadas
    phrases = parse_script_to_phrases(script_data)
    
    for phrase_text in phrases:
        script_content += f"""    <div class="phrase">
        <span class="narrator-instruction"></span><span class="phrase-text">"{phrase_text}"</span>
    </div>

"""
    
    script_content += f"""    <div class="timestamp">
        Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>"""
    
    return script_content

def save_narrator_script(content, output_file):
    """Guarda el guión en un archivo HTML"""
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    except Exception as e:
        print(f"[ERROR] Error al guardar el archivo {output_file}: {e}")
        return False

def generate_single_narrator_script(script_id: int, input_file: str = None, output_file: str = None):
    """
    Genera el guión del locutor para un script específico por ID
    
    Args:
        script_id: ID del script a procesar (obligatorio)
        input_file: Archivo JSON de entrada (opcional)
        output_file: Archivo HTML de salida (opcional)
    """
    try:
        # Determinar archivo de entrada
        if input_file is None:
            base_dir = os.path.dirname(str(ContentGenerationConfig.ANALYZED_SCRIPTS_FILE))
            input_file = os.path.join(base_dir, f"analyzed_script_id_{script_id}.json")
        
        # Determinar archivo de salida
        if output_file is None:
            scripts_dir = str(ContentGenerationConfig.NARRATOR_SCRIPTS_DIR)
            output_file = os.path.join(scripts_dir, f"narrator_script_id_{script_id}.html")
        
        print(">> NARRATOR SCRIPT GENERATOR - SINGLE SCRIPT MODE")
        print("=" * 55)
        print(f">> Target Script ID: {script_id}")
        print(f">> Input: {input_file}")
        print(f">> Output: {output_file}")
        print()
        
        # Verificar si el archivo de entrada existe
        if not os.path.exists(input_file):
            print(f"[ERROR] Input file not found: {input_file}")
            print(f"Make sure you've run content_02_analyze_scripts_video_prompts.py --script-id {script_id} first")
            return False
        
        # Crear carpeta de salida si no existe
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Cargar datos del script
        print(f">> Loading analyzed script data...")
        script_data = load_script_data(input_file)
        
        if script_data is None:
            return False
        
        # Validar que el ID coincida
        script_id_in_file = script_data.get('id')
        if script_id_in_file != script_id:
            print(f"[ERROR] Script ID mismatch! Expected {script_id}, found {script_id_in_file}")
            return False
        
        topic = script_data.get('topic', 'Sin título')
        category = script_data.get('category', 'Sin categoría')
        status = script_data.get('status', 'unknown')
        
        # Verificar que el script sea válido
        if status != 'success':
            print(f"[ERROR] Script {script_id} has status '{status}' - cannot generate narrator script")
            return False
        
        print(f"[OK] Loaded script: {topic}")
        print(f">> Category: {category}")
        
        # Generar el guión HTML
        print(f">> Generating narrator script...")
        narrator_script = generate_narrator_script(script_data, script_id)
        
        # Guardar el archivo
        print(f">> Saving HTML file...")
        if save_narrator_script(narrator_script, output_file):
            print(f"[OK] Narrator script generated successfully!")
            print(f">> Saved to: {output_file}")
            print(f">> Topic: {topic}")
            print(f">> Category: {category}")
            return True
        else:
            print(f"[ERROR] Failed to save narrator script")
            return False
                
    except Exception as e:
        print(f"[ERROR] Error generating narrator script for ID {script_id}: {str(e)}")
        return False

def main():
    """Función principal"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate narrator script for a specific script ID')
    parser.add_argument('--script-id', type=int, required=True,
                       help='Script ID to process (required, range: 1-60)')
    parser.add_argument('--input-file', type=str, help='Input analyzed script JSON file (optional)')
    parser.add_argument('--output-file', type=str, help='Output HTML file (optional)')
    
    args = parser.parse_args()
    
    # Validate script ID range
    if args.script_id < 1 or args.script_id > 60:
        print(f"[ERROR] Invalid script ID: {args.script_id}")
        print("Valid range: 1-60")
        sys.exit(1)
    
    # Generate narrator script
    success = generate_single_narrator_script(
        script_id=args.script_id,
        input_file=args.input_file,
        output_file=args.output_file
    )
    
    if success:
        print("\n[OK] SUCCESS! Narrator script generated successfully")
    else:
        print("\n[ERROR] FAILED! Could not generate narrator script")
        sys.exit(1)

if __name__ == "__main__":
    main() 