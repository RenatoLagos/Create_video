from pydantic import BaseModel
from pydantic_ai import Agent
from dotenv import load_dotenv
import os
import json
from config import ContentGenerationConfig


load_dotenv()


class ScriptInput(BaseModel):
    topic: str
    min_duration: int
    max_duration: int


class ScriptVideo(BaseModel):
    hook: str
    development: str
    closing: str


def load_category_prompts(prompts_file: str = None) -> dict:
    """Load category prompts from JSON file"""
    if prompts_file is None:
        prompts_file = str(ContentGenerationConfig.CATEGORY_PROMPTS_FILE)
    
    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)
        
        # Extract and join prompt arrays into strings for each category
        category_prompts = {}
        for category, data in prompts_data.items():
            prompt_data = data.get('prompt', [])
            if isinstance(prompt_data, list):
                # Join array elements with newlines
                category_prompts[category] = '\n'.join(prompt_data)
            else:
                # Handle old string format as fallback
                category_prompts[category] = prompt_data
        
        print(f"✅ Loaded {len(category_prompts)} category prompts from {prompts_file}")
        return category_prompts
        
    except FileNotFoundError:
        print(f"❌ Prompts file not found: {prompts_file}")
        print("Using default fallback prompt...")
        return {"default": "You are an expert AI video scriptwriter creating engaging content for Spanish learners."}
    except Exception as e:
        print(f"❌ Error loading prompts: {str(e)}")
        return {"default": "You are an expert AI video scriptwriter creating engaging content for Spanish learners."}


def show_available_categories(prompts_file: str = None):
    """Show available categories and their descriptions"""
    if prompts_file is None:
        prompts_file = str(ContentGenerationConfig.CATEGORY_PROMPTS_FILE)
    
    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)
        
        print(f"\n📋 Available Categories ({len(prompts_data)}):")
        print("=" * 50)
        
        for category, data in prompts_data.items():
            description = data.get('description', 'No description available')
            style = data.get('style', 'No style defined')
            print(f"🎯 {category}")
            print(f"   📝 Description: {description}")
            print(f"   🎭 Style: {style}")
            print()
            
    except FileNotFoundError:
        print(f"❌ Prompts file not found: {prompts_file}")
    except Exception as e:
        print(f"❌ Error reading prompts file: {str(e)}")


def get_system_prompt(category: str, category_prompts: dict) -> str:
    """Get the appropriate system prompt for a given category"""
    return category_prompts.get(category, category_prompts.get("Quick Travel Phrases", category_prompts.get("default", "")))


def create_scriptwriter_agent(model_name: str, category: str = "Quick Travel Phrases", category_prompts: dict = None):
    """Create and return a scriptwriter agent with the specified model and category-specific prompt"""
    if category_prompts is None:
        category_prompts = load_category_prompts()
    
    system_prompt = get_system_prompt(category, category_prompts)
    
    return Agent(
        model=model_name,
        input_type=ScriptInput,
        output_type=ScriptVideo,
        system_prompt=system_prompt
    )


def process_topics_by_category_limit(file_path: str, model_name: str, output_json: str = None, min_duration: int = 15, max_duration: int = 20, limit_per_category: int = 4):
    """
    Process topics from JSON file and generate SHORT scripts with a specific limit per category
    
    Args:
        file_path: Path to the JSON file
        model_name: The model name to use for all agents
        output_json: Output JSON file path
        min_duration: Minimum video duration in seconds
        max_duration: Maximum video duration in seconds
        limit_per_category: Maximum number of scripts to generate per category
    """
    try:
        # Load category prompts first
        print("Loading category prompts...")
        category_prompts = load_category_prompts()
        
        # Read the JSON file
        print(f"Reading JSON file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            topics_data = json.load(f)
        
        # Check if data is valid
        if not isinstance(topics_data, list):
            raise ValueError("JSON file should contain a list of topic objects")
        
        # Filter out empty topics
        valid_topics = [item for item in topics_data if item.get('Topics')]
        
        # Group topics by category
        topics_by_category = {}
        for item in valid_topics:
            category = item.get('Category', 'Unknown')
            if category not in topics_by_category:
                topics_by_category[category] = []
            topics_by_category[category].append(item)
        
        # Handle None limit_per_category
        if limit_per_category is None:
            limit_per_category = len(max(topics_by_category.values(), key=len)) if topics_by_category else 4
        
        print(f"\n📊 Found topics in {len(topics_by_category)} categories:")
        for category, topics in topics_by_category.items():
            available = len(topics)
            will_process = min(available, limit_per_category)
            print(f"  - {category}: {available} available, will process {will_process}")
        
        # Initialize results list
        results = []
        
        # Keep track of agents by category to avoid recreating them
        agents_cache = {}
        
        total_to_process = sum(min(len(topics), limit_per_category) for topics in topics_by_category.values())
        processed_count = 0
        
        # Process each category
        for category, topics in topics_by_category.items():
            print(f"\n🎯 Processing category: {category}")
            
            # Limit topics for this category
            topics_to_process = topics[:limit_per_category]
            
            for item in topics_to_process:
                topic = item.get('Topics', '')
                processed_count += 1
                
                print(f"\nProcessing topic {processed_count}/{total_to_process}: {topic}")
                print(f"Category: {category}")
                
                try:
                    # Get or create agent for this category
                    if category not in agents_cache:
                        print(f"Creating new agent for category: {category}")
                        agents_cache[category] = create_scriptwriter_agent(model_name, category, category_prompts)
                    
                    agent = agents_cache[category]
                    
                    # Create parameters for the agent
                    parameters = ScriptInput(
                        topic=str(topic),
                        min_duration=min_duration,
                        max_duration=max_duration
                    )
                    
                    # Create a specific user message
                    user_message = f"""
                    Create a video script with the following specifications:
                    - Topic: {parameters.topic}
                    - Duration: between {parameters.min_duration} and {parameters.max_duration} seconds
                    - Category: {category}
                    
                    Please follow the framework outlined in the system prompt and provide the script in the required format.
                    """
                    
                    # Generate script using the category-specific agent
                    result = agent.run_sync(user_message)
                    
                    # Create JSON entry
                    script_entry = {
                        "category": category,
                        "topic": topic,
                        "script": {
                            "hook": result.output.hook,
                            "development": result.output.development,
                            "closing": result.output.closing
                        }
                    }
                    
                    results.append(script_entry)
                    print(f"✅ Script generated successfully for: {topic}")
                    
                except Exception as e:
                    print(f"❌ Error processing topic '{topic}': {str(e)}")
                    # Add error entry
                    error_entry = {
                        "category": category,
                        "topic": topic,
                        "script": {
                            "hook": f"Error: {str(e)}",
                            "development": "",
                            "closing": ""
                        },
                        "error": str(e)
                    }
                    results.append(error_entry)
        
        # Save results to JSON
        if output_json is None:
            output_json = str(ContentGenerationConfig.GENERATED_SCRIPTS_FILE)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_json), exist_ok=True)
        
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Results saved to: {output_json}")
        print(f"📊 Total scripts generated: {len([r for r in results if 'error' not in r])}")
        print(f"❌ Errors encountered: {len([r for r in results if 'error' in r])}")
        
        # Show category breakdown
        category_counts = {}
        for result in results:
            if 'error' not in result:
                cat = result['category']
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        print(f"\n📈 Scripts generated by category:")
        for cat, count in category_counts.items():
            print(f"  - {cat}: {count} scripts")
        
        return results
        
    except Exception as e:
        print(f"❌ Error processing JSON file: {str(e)}")
        raise


if __name__ == "__main__":
    # Model configuration
    MODEL = "gpt-4o"
    
    # Show available categories
    show_available_categories()
    
    # Path to the JSON file
    json_file_path = str(ContentGenerationConfig.TOPICS_CONFIG_FILE)
    
    # Check if file exists
    if not os.path.exists(json_file_path):
        print(f"❌ File not found: {json_file_path}")
        print(f"Please make sure the {json_file_path} file exists in the directory")
    else:
        # Process topics and generate SHORT scripts with category limits
        try:
            process_topics_by_category_limit(
                file_path=json_file_path,
                model_name=ContentGenerationConfig.DEFAULT_MODEL,
                min_duration=ContentGenerationConfig.DEFAULT_MIN_DURATION, 
                max_duration=ContentGenerationConfig.DEFAULT_MAX_DURATION,
                limit_per_category=ContentGenerationConfig.DEFAULT_LIMIT_PER_CATEGORY
            )
        except Exception as e:
            print(f"❌ Failed to process topics: {str(e)}") 