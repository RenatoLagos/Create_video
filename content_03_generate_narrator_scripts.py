#!/usr/bin/env python3
import json
import sys
from datetime import datetime
import os
import glob
from config import ContentGenerationConfig

def load_scripts_data(json_file_path):
    """Carga los datos del archivo JSON"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {json_file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: El archivo {json_file_path} no es un JSON válido")
        return None

def parse_script_to_phrases(script_data):
    """Convierte el script en frases individuales"""
    script = script_data.get('script', {})
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

def generate_narrator_script(script_data, script_number):
    """Genera el guión para un script específico"""
    
    topic = script_data.get('topic', 'Sin título')
    category = script_data.get('category', 'Sin categoría')
    
    script_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Guión Script {script_number}</title>
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
    <h1>🎬 Script {script_number}</h1>
    
    <div class="info">
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

def clean_previous_html_files(scripts_dir):
    """Elimina todos los archivos HTML previos de la carpeta scripts"""
    try:
        html_pattern = os.path.join(scripts_dir, "*.html")
        html_files = glob.glob(html_pattern)
        
        if html_files:
            print(f"🧹 Limpiando {len(html_files)} archivos HTML previos...")
            for html_file in html_files:
                os.remove(html_file)
                print(f"   🗑️ Eliminado: {os.path.basename(html_file)}")
            print(f"✅ Limpieza completada")
        else:
            print("ℹ️ No se encontraron archivos HTML previos para eliminar")
            
    except Exception as e:
        print(f"⚠️ Error durante la limpieza: {e}")

def save_narrator_script(content, output_file):
    """Guarda el guión en un archivo HTML"""
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    except Exception as e:
        print(f"❌ Error al guardar el archivo {output_file}: {e}")
        return False

def main():
    """Función principal"""
    
    # Crear carpeta scripts si no existe
    scripts_dir = str(ContentGenerationConfig.NARRATOR_SCRIPTS_DIR)
    if not os.path.exists(scripts_dir):
        os.makedirs(scripts_dir)
        print(f"📁 Carpeta '{scripts_dir}' creada")
    
    # Limpiar archivos HTML previos
    clean_previous_html_files(scripts_dir)
    
    # Rutas de archivos
    json_file = str(ContentGenerationConfig.GENERATED_SCRIPTS_FILE)
    
    print("🎬 Generador de Guiones para Locutor - Procesamiento Completo")
    print("=" * 70)
    
    # Cargar datos del JSON
    print(f"📖 Cargando datos desde: {json_file}")
    scripts_data = load_scripts_data(json_file)
    
    if scripts_data is None:
        return
    
    print(f"✅ Cargados {len(scripts_data)} scripts en total")
    print("🔄 Procesando todos los scripts...")
    
    # Contadores
    success_count = 0
    error_count = 0
    
    # Procesar cada script
    for i, script_data in enumerate(scripts_data):
        script_number = i + 1
        topic = script_data.get('topic', 'Sin título')
        category = script_data.get('category', 'Sin categoría')
        
        print(f"\n📝 Procesando script {script_number}/{len(scripts_data)}")
        print(f"   📂 Categoría: {category}")
        print(f"   📋 Tema: {topic}")
        
        # Generar nombre del archivo
        output_file = f"{scripts_dir}/narrator_short_script_{script_number}.html"
        
        try:
            # Generar el guión
            narrator_script = generate_narrator_script(script_data, script_number)
            
            # Guardar el archivo
            if save_narrator_script(narrator_script, output_file):
                print(f"   ✅ Guardado: {output_file}")
                success_count += 1
            else:
                print(f"   ❌ Error al guardar: {output_file}")
                error_count += 1
                
        except Exception as e:
            print(f"   ❌ Error procesando script {script_number}: {str(e)}")
            error_count += 1
    
    # Mostrar resumen final
    print("\n" + "=" * 70)
    print("🎉 ¡Proceso completado!")
    print(f"✅ Scripts generados exitosamente: {success_count}")
    print(f"❌ Errores encontrados: {error_count}")
    print(f"📁 Archivos guardados en: {scripts_dir}/")
    
    if success_count > 0:
        print(f"\n📄 Archivos generados:")
        for i in range(1, success_count + 1):
            print(f"   - narrator_short_script_{i}.html")
    
    # Mostrar estadísticas por categoría
    if success_count > 0:
        category_counts = {}
        for script in scripts_data:
            category = script.get('category', 'Sin categoría')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print(f"\n📊 Distribución por categorías:")
        for category, count in category_counts.items():
            print(f"   - {category}: {count} scripts")

if __name__ == "__main__":
    main() 