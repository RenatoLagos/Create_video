from pydantic import BaseModel
from pydantic_ai import Agent
from dotenv import load_dotenv
import os
import json
import argparse
import sys
import re
from config import ContentGenerationConfig


load_dotenv()


def remove_emojis(text: str) -> str:
    """
    Remove emojis from text to avoid Windows encoding issues
    
    Args:
        text: Text that may contain emojis
        
    Returns:
        Text with emojis removed
    """
    # Comprehensive pattern to match emojis and other Unicode symbols
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # geometric shapes extended
        "\U0001F800-\U0001F8FF"  # supplemental arrows-C
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F004\U0001F0CF"   # mahjong tile, playing card
        "\U0001F170-\U0001F251"  # enclosed ideographic supplement
        "]+", 
        flags=re.UNICODE
    )
    
    return emoji_pattern.sub(r'', text).strip()


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
        
        print(f"[OK] Loaded {len(category_prompts)} category prompts from {prompts_file}")
        return category_prompts
        
    except FileNotFoundError:
        print(f"[ERROR] Prompts file not found: {prompts_file}")
        print("Using default fallback prompt...")
        return {"default": "You are an expert AI video scriptwriter creating engaging content for Spanish learners."}
    except Exception as e:
        print(f"[ERROR] Error loading prompts: {str(e)}")
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
            print(f">> {category}")
            print(f"   >> Description: {description}")
            print(f"   >> Style: {style}")
            print()
            
    except FileNotFoundError:
        print(f"[ERROR] Prompts file not found: {prompts_file}")
    except Exception as e:
        print(f"[ERROR] Error reading prompts file: {str(e)}")


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
        output_type=ScriptVideo,
        system_prompt=system_prompt
    )


def process_single_topic(file_path: str, topic_id: int, model_name: str, output_json: str = None, min_duration: int = 15, max_duration: int = 20):
    """
    Process a single topic by ID and generate script
    
    Args:
        file_path: Path to the JSON file with topics
        topic_id: The specific topic ID to process (required)
        model_name: The model name to use
        output_json: Output JSON file path
        min_duration: Minimum video duration in seconds
        max_duration: Maximum video duration in seconds
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
        
        # Find the specific topic by ID
        print(f">> Searching for topic with ID: {topic_id}")
        target_topic = None
        for item in topics_data:
            if item.get('id') == topic_id:
                target_topic = item
                break
        
        if target_topic is None:
            print(f"[ERROR] Topic with ID {topic_id} not found!")
            print(f"Available IDs: {[item.get('id') for item in topics_data if item.get('id')]}")
            return None
        
        # Validate topic has required fields
        if not target_topic.get('Topics'):
            print(f"[ERROR] Topic {topic_id} has no content!")
            return None
        
        topic_text = target_topic.get('Topics', '')
        category = target_topic.get('Category', 'Unknown')
        
        print(f"[OK] Found topic {topic_id}: {topic_text}")
        print(f">> Category: {category}")
        
        # Create agent for this category
        print(f"Creating agent for category: {category}")
        agent = create_scriptwriter_agent(model_name, category, category_prompts)
        
        # Create parameters for the agent
        parameters = ScriptInput(
            topic=str(topic_text),
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
        
        print(f">> Generating script for topic {topic_id}...")
        
        # Generate script using the category-specific agent
        result = agent.run_sync(user_message)
        
        # Create JSON entry (remove emojis to avoid encoding issues)
        script_entry = {
            "id": topic_id,
            "category": category,
            "topic": topic_text,
            "script": {
                "hook": remove_emojis(result.output.hook),
                "development": remove_emojis(result.output.development),
                "closing": remove_emojis(result.output.closing)
            }
        }
        
        # Set output path with ID
        if output_json is None:
            base_dir = os.path.dirname(str(ContentGenerationConfig.GENERATED_SCRIPTS_FILE))
            output_json = os.path.join(base_dir, f"script_id_{topic_id}.json")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_json), exist_ok=True)
        
        # Save single script result
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(script_entry, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Script generated successfully!")
        print(f">> Saved to: {output_json}")
        print(f">> Topic: {topic_text}")
        print(f">> Category: {category}")
        
        return script_entry
        
    except Exception as e:
        print(f"[ERROR] Error processing topic {topic_id}: {str(e)}")
        raise


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate video script for a specific topic ID')
    parser.add_argument('--topic-id', type=int, required=True, 
                       help='Topic ID to process (required, range: 1-60)')
    parser.add_argument('--model', type=str, default=ContentGenerationConfig.DEFAULT_MODEL, 
                       help='Model to use for generation')
    parser.add_argument('--min-duration', type=int, default=ContentGenerationConfig.DEFAULT_MIN_DURATION, 
                       help='Minimum video duration in seconds')
    parser.add_argument('--max-duration', type=int, default=ContentGenerationConfig.DEFAULT_MAX_DURATION, 
                       help='Maximum video duration in seconds')
    parser.add_argument('--output', type=str, help='Output JSON file path (optional)')
    
    args = parser.parse_args()
    
    # Validate topic ID range
    if args.topic_id < 1 or args.topic_id > 60:
        print(f"[ERROR] Invalid topic ID: {args.topic_id}")
        print("Valid range: 1-60")
        sys.exit(1)
    
    print(">> VIDEO SCRIPT GENERATOR - SINGLE TOPIC MODE")
    print("=" * 50)
    print(f">> Target Topic ID: {args.topic_id}")
    print(f">> Model: {args.model}")
    print(f">> Duration: {args.min_duration}-{args.max_duration} seconds")
    print()
    
    # Path to the JSON file
    json_file_path = str(ContentGenerationConfig.TOPICS_CONFIG_FILE)
    
    # Check if file exists
    if not os.path.exists(json_file_path):
        print(f"[ERROR] File not found: {json_file_path}")
        print(f"Please make sure the topics file exists")
        sys.exit(1)
    
    # Process single topic
    try:
        result = process_single_topic(
            file_path=json_file_path,
            topic_id=args.topic_id,
            model_name=args.model,
            output_json=args.output,
            min_duration=args.min_duration, 
            max_duration=args.max_duration
        )
        
        if result:
            print("\n[OK] SUCCESS! Script generated successfully")
        else:
            print("\n[ERROR] FAILED! Could not generate script")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[ERROR] FATAL ERROR: {str(e)}")
        sys.exit(1) 