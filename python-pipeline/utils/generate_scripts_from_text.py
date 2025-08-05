from pydantic import BaseModel
from pydantic_ai import Agent
from dotenv import load_dotenv
import os
import json


load_dotenv()


class TextScriptInput(BaseModel):
    content: str
    script_type: str
    min_duration: int
    max_duration: int


class ScriptVideo(BaseModel):
    hook: str
    development: str
    closing: str


def read_text_file(file_path: str) -> str:
    """Read and return the content of a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ Successfully read text file: {file_path}")
        return content
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        raise
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        raise


def create_script_agent(model_name: str):
    """Create and return a script agent with unified prompt"""
    
    system_prompt = """
    Eres un guionista especializado en videos científicos cortos (30-50 segundos) que domina la psicología del engagement y storytelling avanzado.

    🧠 PRINCIPIOS FUNDAMENTALES DE HOOKS:
    El Hook es la apertura crítica de 3-5 segundos que representa el 20% del esfuerzo que impulsa el 80% del rendimiento.
    
    OBJETIVO: Crear un curiosity loop que haga imposible que el espectador deje de mirar.
    CLAVE PSICOLÓGICA: Contraste — mostrar una nueva perspectiva (B) que difiere de la creencia inicial (A).

    🎭 FORMATOS DE HOOK (usa uno):
    1. Fortune Teller: Muestra cómo el futuro puede cambiar (ideal para innovación)
    2. Investigator: Revela un "secreto" o hallazgo
    3. Contrarian: Afirmación provocadora contra la opinión común

    📏 ESTRUCTURA PARA VIDEO DE 30-50 SEGUNDOS:

    1. HOOK (3-5 segundos):
    - Usa uno de los 3 formatos
    - Crea contraste inmediato
    - Genera curiosity loop
    - Debe ser impactante y directo

    2. DEVELOPMENT (20-35 segundos):
    - Contenido educativo principal conciso
    - Integra 1-2 RE-HOOKS para mantener engagement:
      * "Pero..."
      * "Sin embargo..."
      * "Por otro lado..."
      * "O eso era lo que pensaban..."
      * "Aquí viene lo interesante..."
      * "Pero los científicos descubrieron algo más..."
      * "Sin embargo, la realidad era diferente..."
      * "Por otro lado, las evidencias mostraban..."
    - Usa analogías simples y directas
    - Mantén ritmo acelerado por la duración corta

    3. CLOSING (5-10 segundos):
    - Incluye un POV (reflexión sobre implicaciones futuras)
    - Termina con UNA de estas 2 opciones:
      a) Una pregunta interesante
      b) Una broma

    IMPORTANTE: Mantén equilibrio entre rigor científico y narrativa cautivadora en formato ultra-conciso.
    """
    
    return Agent(
        model=model_name,
        output_type=ScriptVideo,
        system_prompt=system_prompt
    )


def generate_scripts_from_text(
    text_file_path: str, 
    model_name: str, 
    output_json: str = "json/scripts_from_text.json",
    min_duration: int = 30,
    max_duration: int = 50
):
    """
    Generate script from a text file using unified format
    
    Args:
        text_file_path: Path to the text file
        model_name: The model name to use
        output_json: Output JSON file path
        min_duration: Minimum video duration in seconds
        max_duration: Maximum video duration in seconds
    """
    try:
        # Read the text file
        print(f"Reading text file: {text_file_path}")
        text_content = read_text_file(text_file_path)
        
        # Extract title from the content (first meaningful line)
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        title = "Untitled"
        for line in lines:
            if len(line) > 20 and not line.startswith(('Skip to', 'ScienceDaily', 'Your source')):
                title = line
                break
        
        print(f"Detected title: {title}")
        
        results = []
        
        print(f"\nGenerating scientific script...")
        
        try:
            # Create agent with unified format
            agent = create_script_agent(model_name)
            
            # Create parameters
            parameters = TextScriptInput(
                content=text_content,
                script_type="scientific",
                min_duration=min_duration,
                max_duration=max_duration
            )
            
            # Create user message
            user_message = f"""
            Basándote en el siguiente contenido, crea un guión de video científico que dure entre {min_duration} y {max_duration} segundos:

            CONTENIDO:
            {text_content[:2000]}...  # Limitar para evitar tokens excesivos

            Requisitos específicos:
            - Duración: {min_duration}-{max_duration} segundos
            - Debe ser atractivo y mantener la atención del espectador
            - Aplica todos los principios de hooks y re-hooks especificados
            
            Proporciona el guión en el formato requerido con hook, development y closing.
            """
            
            # Generate script
            result = agent.run_sync(user_message)
            
            # Create JSON entry
            script_entry = {
                "source_file": text_file_path,
                "title": title,
                "script_type": "scientific",
                "duration_range": f"{min_duration}-{max_duration} seconds",
                "script": {
                    "hook": result.output.hook,
                    "development": result.output.development,
                    "closing": result.output.closing
                }
            }
            
            results.append(script_entry)
            print(f"✅ Scientific script generated successfully")
            
        except Exception as e:
            print(f"❌ Error generating scientific script: {str(e)}")
            # Add error entry
            error_entry = {
                "source_file": text_file_path,
                "title": title,
                "script_type": "scientific",
                "duration_range": f"{min_duration}-{max_duration} seconds",
                "script": {
                    "hook": f"Error: {str(e)}",
                    "development": "",
                    "closing": ""
                },
                "error": str(e)
            }
            results.append(error_entry)
        
        # Save results to JSON
        os.makedirs(os.path.dirname(output_json), exist_ok=True)
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Results saved to: {output_json}")
        print(f"📊 Total scripts generated: {len([r for r in results if 'error' not in r])}")
        print(f"❌ Errors encountered: {len([r for r in results if 'error' in r])}")
        
        # Show summary
        print(f"\n📈 Generated scripts:")
        for result in results:
            if 'error' not in result:
                print(f"  - {result['script_type'].capitalize()} script: ✅")
            else:
                print(f"  - {result['script_type'].capitalize()} script: ❌")
        
        return results
        
    except Exception as e:
        print(f"❌ Error processing text file: {str(e)}")
        raise


if __name__ == "__main__":
    # Model configuration
    MODEL = "gpt-4o"
    
    # Path to the text file
    text_file_path = "../scraper/test.txt"
    
    # Check if file exists
    if not os.path.exists(text_file_path):
        print(f"❌ File not found: {text_file_path}")
        print("Please make sure the text file exists in the specified path")
    else:
        # Generate scientific script from the text
        try:
            generate_scripts_from_text(
                text_file_path=text_file_path,
                model_name=MODEL,
                output_json="../json/output/scripts_from_text.json",
                min_duration=30,
                max_duration=50
            )
        except Exception as e:
            print(f"❌ Failed to generate scripts: {str(e)}") 