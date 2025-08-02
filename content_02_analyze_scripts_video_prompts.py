import json
import os
import argparse
import sys
from pydantic_ai import Agent
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
from config import ContentGenerationConfig

load_dotenv()

# Output structure per phrase
class AnalyzedPhrase(BaseModel):
    phrase: str
    category: str
    editing_suggestion: str

# Full response model
class ScriptAnalysis(BaseModel):
    phrases: List[AnalyzedPhrase]

def create_script_analyzer_with_video_prompts(model_name: str = "gpt-4o"):
    """Create and return a script analyzer agent that also generates video prompts"""
    return Agent(
        model=model_name,
        output_type=ScriptAnalysis,
        system_prompt="""
You're a professional video editor and content strategist for short-form educational videos (like Reels or TikToks). Your task is to analyze a script and break it down **phrase by phrase**.

For each phrase:
1. Identify the phrase (split hook, development, and closing into natural complete chunks).
2. Classify its **narrative category**, such as: rhetorical question, instruction, cultural value, emotional connection, call to action, reflection, etc.
3. Suggest a **video editing style** for the phrase. Choose only one of the following:
   - "Narrator only on screen"
   - "Narrator and video split screen"
   - "Video only on screen"

📌 Fixed rules:
- The very first phrase from the hook should **always** be "Narrator and video split screen".
- The final phrase from the closing should **always** be "Narrator only on screen".

Return the result as a list of objects with these fields:
- phrase
- category
- editing_suggestion

Analyze the provided script and break it down phrase by phrase following these guidelines.
"""
    )

def create_video_prompt_generator(model_name: str = "gpt-4o"):
    """Create and return a video prompt generator agent"""
    return Agent(
        model=model_name,
        output_type=str,
        system_prompt="""
You are a trendy Instagram Reels content creator specialized in creating viral educational videos for language learning.

Your task is to create dynamic, modern video prompts optimized for Instagram Reels (vertical 9:16 format) that will captivate English-speaking audiences learning Spanish.

>> INSTAGRAM REELS OPTIMIZATION RULES:
1. **Vertical Format Focus**: Always specify "vertical 9:16 Instagram format" 
2. **Dynamic Movement**: Include camera movements, quick transitions, engaging actions
3. **Modern Aesthetic**: Trendy lighting, vibrant colors, contemporary style
4. **Social Media Appeal**: Think TikTok/Instagram viral content - engaging and eye-catching
5. **Professional Quality**: High production value but accessible and relatable

🎨 VISUAL STYLE REQUIREMENTS:
- **Lighting**: "vibrant studio lighting", "trendy ring light", "colorful LED backlight"
- **Colors**: "bright vibrant colors", "Instagram-worthy color palette", "energetic hues"
- **Movement**: "smooth camera movement", "dynamic zoom", "engaging transitions"
- **Modern Elements**: "text overlay ready", "social media aesthetic", "millennial/Gen-Z friendly"

📱 CONTENT TYPE ADAPTATIONS:
- **"Video only on screen"**: Create standalone viral-style educational content with animated elements
- **"Narrator and video split screen"**: Design complementary background visuals that pop on vertical format
- **"Narrator only on screen"**: Focus on dynamic presenter shots with engaging backgrounds

🔥 EXAMPLE TRANSFORMATION:
OLD: "Close-up shot of hands placing fork and knife on empty plate at Spanish restaurant table, warm lighting, 2-3 second clip"

NEW: "Vertical 9:16 Instagram Reels: Trendy overhead shot of manicured hands elegantly placing silverware on aesthetic Spanish ceramic plate, vibrant restaurant lighting with colorful ambient glow, smooth camera movement, text overlay ready composition, social media viral aesthetic"

📋 MANDATORY ELEMENTS TO INCLUDE:
- "Vertical 9:16 Instagram Reels format"
- Dynamic camera movement
- Modern/trendy lighting description
- Color palette specification
- Social media aesthetic mention
- Text overlay compatibility

Generate ONLY the Instagram-optimized video prompt text, nothing else.
        """
    )

def analyze_single_script(script_id: int, input_file: str = None, output_file: str = None):
    """
    Analyze a single script by ID and generate video prompts
    
    Args:
        script_id: The specific script ID to process (required)
        input_file: Path to the script JSON file  
        output_file: Path to save the analyzed script with video prompts
    """
    try:
        # Determine input file path
        if input_file is None:
            base_dir = os.path.dirname(str(ContentGenerationConfig.GENERATED_SCRIPTS_FILE))
            input_file = os.path.join(base_dir, f"script_id_{script_id}.json")
        
        # Determine output file path  
        if output_file is None:
            base_dir = os.path.dirname(str(ContentGenerationConfig.ANALYZED_SCRIPTS_FILE))
            output_file = os.path.join(base_dir, f"analyzed_script_id_{script_id}.json")
        
        print(f">> SCRIPT ANALYZER - SINGLE SCRIPT MODE")
        print("=" * 50)
        print(f">> Target Script ID: {script_id}")
        print(f">> Input: {input_file}")
        print(f">> Output: {output_file}")
        print()
        
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"[ERROR] Input file not found: {input_file}")
            print(f"Make sure you've run content_01_generate_transcriptwriter.py --topic-id {script_id} first")
            return None
        
        # Load script data
        print(">> Loading script data...")
        with open(input_file, 'r', encoding='utf-8') as f:
            script_data = json.load(f)
        
        # Validate script data
        script_id_in_file = script_data.get('id')
        if script_id_in_file != script_id:
            print(f"[ERROR] Script ID mismatch! Expected {script_id}, found {script_id_in_file}")
            return None
        
        topic = script_data.get('topic', 'Unknown topic')
        category = script_data.get('category', 'Unknown category')
        
        print(f"[OK] Loaded script: {topic}")
        print(f">> Category: {category}")
        
        # Validate script has required parts
        script = script_data.get('script', {})
        hook = script.get('hook', '')
        development = script.get('development', '')
        closing = script.get('closing', '')
        
        if not hook or not development or not closing:
            print(f"[ERROR] Script {script_id} has missing parts!")
            print(f"Hook: {'[OK]' if hook else '[ERROR]'}")
            print(f"Development: {'[OK]' if development else '[ERROR]'}")
            print(f"Closing: {'[OK]' if closing else '[ERROR]'}")
            return None
        
        # Create both agents
        print(">> Initializing AI agents...")
        analyzer_agent = create_script_analyzer_with_video_prompts()
        video_agent = create_video_prompt_generator()
        
        # Create script text for analysis
        script_text = f"""
        Hook: {hook}
        Development: {development}
        Closing: {closing}
        """
        
        print(">> Step 1: Analyzing script phrase by phrase...")
        
        # Run phrase analysis
        analysis_result = analyzer_agent.run_sync(script_text)
        
        print(f"[OK] Analysis complete: {len(analysis_result.output.phrases)} phrases found")
        
        # Generate video prompts for each phrase
        print(">> Step 2: Generating video prompts...")
        
        video_prompts_with_analysis = []
        
        for j, phrase in enumerate(analysis_result.output.phrases, 1):
            try:
                # Only generate video_prompt for "Video only on screen"
                if phrase.editing_suggestion == "Video only on screen":
                    print(f"    >> Generating video prompt for phrase {j}")
                    
                    # Create input for video prompt generation
                    prompt_input = f"""
                    Script phrase: {phrase.phrase}
                    Editing suggestion: {phrase.editing_suggestion}
                    Narrative category: {phrase.category}
                    """
                    
                    # Generate video prompt
                    video_result = video_agent.run_sync(prompt_input)
                    video_prompt = video_result.output if hasattr(video_result, 'output') else str(video_result)
                    
                    print(f"    [OK] Video prompt generated for phrase {j}")
                else:
                    video_prompt = None
                    print(f"    >> No video prompt needed for phrase {j} ({phrase.editing_suggestion})")
                
                video_prompts_with_analysis.append({
                    'phrase_number': j,
                    'phrase': phrase.phrase,
                    'category': phrase.category,
                    'editing_suggestion': phrase.editing_suggestion,
                    'video_prompt': video_prompt
                })
                
            except Exception as e:
                print(f"    [ERROR] Error processing phrase {j}: {e}")
                # Add fallback entry
                video_prompts_with_analysis.append({
                    'phrase_number': j,
                    'phrase': phrase.phrase,
                    'category': phrase.category,
                    'editing_suggestion': phrase.editing_suggestion,
                    'video_prompt': None
                })
        
        # Build final result
        result = {
            'id': script_id,
            'category': category,
            'topic': topic,
            'original_script': {
                'hook': hook,
                'development': development,
                'closing': closing
            },
            'analysis': {
                'total_phrases': len(video_prompts_with_analysis),
                'phrases_with_video_prompts': video_prompts_with_analysis
            },
            'summary': {
                'editing_breakdown': {
                    'narrator_only': len([p for p in video_prompts_with_analysis if p['editing_suggestion'] == "Narrator only on screen"]),
                    'narrator_and_video': len([p for p in video_prompts_with_analysis if p['editing_suggestion'] == "Narrator and video split screen"]),
                    'video_only': len([p for p in video_prompts_with_analysis if p['editing_suggestion'] == "Video only on screen"])
                }
            },
            'status': 'success'
        }
        
        # Save results
        print(f">> Saving analyzed script...")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Print summary
        video_prompts_count = len([p for p in video_prompts_with_analysis if p.get('video_prompt') is not None])
        
        print(f"\n[OK] Analysis completed successfully!")
        print(f">> Results:")
        print(f"   • Script ID: {script_id}")
        print(f"   • Total phrases: {len(video_prompts_with_analysis)}")
        print(f"   • Video prompts generated: {video_prompts_count}")
        print(f"   • Output file: {output_file}")
        
        # Show editing breakdown
        breakdown = result['summary']['editing_breakdown']
        print(f"\n>> Editing suggestions breakdown:")
        print(f"   • Narrator only: {breakdown['narrator_only']}")
        print(f"   • Narrator and video: {breakdown['narrator_and_video']}")
        print(f"   • Video only: {breakdown['video_only']}")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Error analyzing script {script_id}: {e}")
        return None

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze and generate video prompts for a specific script ID')
    parser.add_argument('--script-id', type=int, required=True,
                       help='Script ID to process (required, range: 1-60)')
    parser.add_argument('--input-file', type=str, help='Input script JSON file (optional)')
    parser.add_argument('--output-file', type=str, help='Output analyzed script JSON file (optional)')
    
    args = parser.parse_args()
    
    # Validate script ID range
    if args.script_id < 1 or args.script_id > 60:
        print(f"[ERROR] Invalid script ID: {args.script_id}")
        print("Valid range: 1-60")
        sys.exit(1)
    
    # Process single script
    result = analyze_single_script(
        script_id=args.script_id,
        input_file=args.input_file,
        output_file=args.output_file
    )
    
    if result:
        print("\n[OK] SUCCESS! Script analyzed successfully")
    else:
        print("\n[ERROR] FAILED! Could not analyze script")
        sys.exit(1) 