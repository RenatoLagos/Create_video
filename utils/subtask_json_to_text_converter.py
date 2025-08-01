import json
import os

def convert_json_to_text(json_file_path, output_file_path):
    """
    Convierte el archivo JSON a un archivo de texto con la estructura especificada
    """
    try:
        # Leer el archivo JSON
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Crear el contenido del archivo de texto
        content = []
        current_category = None
        
        for item in data:
            # Verificar si el item tiene error
            if 'error' in item:
                continue
                
            category = item.get('category', '')
            topic = item.get('topic', '')
            script = item.get('script', {})
            
            # Si es una nueva categoría, agregar H1
            if category != current_category:
                if current_category is not None:  # No agregar línea vacía antes del primer H1
                    content.append('')  # Línea vacía antes de nueva categoría
                content.append(f'# {category}')
                content.append('')  # Línea vacía después del H1
                current_category = category
            
            # Agregar H2 para el topic
            content.append(f'## {topic}')
            content.append('')  # Línea vacía después del H2
            
            # Agregar el contenido del script
            hook = script.get('hook', '')
            development = script.get('development', '')
            closing = script.get('closing', '')
            
            # Agregar hook
            if hook:
                content.append(hook)
                content.append('')  # Línea vacía después del hook
            
            # Agregar development
            if development:
                # Reemplazar \n\n con líneas vacías reales
                development_lines = development.replace('\\n\\n', '\n\n').replace('\\n', '\n')
                content.append(development_lines)
                content.append('')  # Línea vacía después del development
            
            # Agregar closing
            if closing:
                content.append(closing)
                content.append('')  # Línea vacía después del closing
        
        # Escribir el archivo de texto
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write('\n'.join(content))
        
        print(f"✅ Archivo convertido exitosamente: {output_file_path}")
        print(f"📊 Se procesaron {len([item for item in data if 'error' not in item])} elementos")
        
    except FileNotFoundError:
        print(f"❌ Error: No se pudo encontrar el archivo {json_file_path}")
    except json.JSONDecodeError:
        print(f"❌ Error: El archivo {json_file_path} no es un JSON válido")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

def main():
    # Rutas de archivos
    json_file = "json/generated_scripts_by_category.json"
    output_dir = "scripts"
    output_file = os.path.join(output_dir, "scripts_content.txt")
    
    # Crear la carpeta scripts si no existe
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 Carpeta '{output_dir}' creada")
    
    # Verificar si el archivo JSON existe
    if not os.path.exists(json_file):
        print(f"❌ El archivo {json_file} no existe")
        return
    
    # Convertir el archivo
    convert_json_to_text(json_file, output_file)

if __name__ == "__main__":
    main() 