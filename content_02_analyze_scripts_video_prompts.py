import json
import os
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

🎯 INSTAGRAM REELS OPTIMIZATION RULES:
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

def analyze_and_generate_video_prompts_from_scripts(input_file: str = None, 
                                                   output_file: str = None):
    """
    Analyze scripts phrase by phrase AND generate video prompts with editing suggestions
    """
    # Use config paths if not provided
    if input_file is None:
        input_file = str(ContentGenerationConfig.GENERATED_SCRIPTS_FILE)
    if output_file is None:
        output_file = str(ContentGenerationConfig.ANALYZED_SCRIPTS_FILE)
    
    try:
        print(f"📖 Loading scripts from: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            scripts_data = json.load(f)
        
        print(f"🚀 Found {len(scripts_data)} scripts to process")
        
        # Create both agents
        analyzer_agent = create_script_analyzer_with_video_prompts()
        video_agent = create_video_prompt_generator()
        
        results = []
        
        for i, script_data in enumerate(scripts_data):
            script_number = i + 1
            topic = script_data.get('topic', 'Sin título')
            category = script_data.get('category', 'Sin categoría')
            
            print(f"\n🎬 Processing script {script_number}: {topic}")
            
            try:
                # Extract script parts
                script = script_data.get('script', {})
                hook = script.get('hook', '')
                development = script.get('development', '')
                closing = script.get('closing', '')
                
                # Skip if script has errors or missing parts
                if 'error' in script_data or not hook or not development or not closing:
                    print(f"   ⚠️ Skipping script with missing parts or errors")
                    continue
                
                # Create script text for analysis
                script_text = f"""
                Hook: {hook}
                Development: {development}
                Closing: {closing}
                """
                
                print(f"   🔍 Step 1: Analyzing script phrase by phrase...")
                
                # Run phrase analysis
                analysis_result = analyzer_agent.run_sync(script_text)
                
                print(f"   ✅ Analysis complete: {len(analysis_result.output.phrases)} phrases found")
                
                # Now generate video prompts for each phrase
                print(f"   🎥 Step 2: Generating video prompts for each phrase...")
                
                video_prompts_with_analysis = []
                
                for j, phrase in enumerate(analysis_result.output.phrases, 1):
                    try:
                        # Solo generar video_prompt para "Video only on screen"
                        if phrase.editing_suggestion == "Video only on screen":
                            # Create input for video prompt generation
                            prompt_input = f"""
                            Script phrase: {phrase.phrase}
                            Editing suggestion: {phrase.editing_suggestion}
                            Narrative category: {phrase.category}
                            """
                            
                            # Generate video prompt
                            video_result = video_agent.run_sync(prompt_input)
                            video_prompt = video_result.output if hasattr(video_result, 'output') else str(video_result)
                            
                            print(f"      ✅ Phrase {j}/{len(analysis_result.output.phrases)} completed (with video prompt)")
                        else:
                            # No generar video_prompt para "Narrator only on screen" y "Narrator and video split screen"
                            video_prompt = None
                            print(f"      ✅ Phrase {j}/{len(analysis_result.output.phrases)} completed (no video prompt needed)")
                        
                        video_prompts_with_analysis.append({
                            'phrase_number': j,
                            'phrase': phrase.phrase,
                            'category': phrase.category,
                            'editing_suggestion': phrase.editing_suggestion,
                            'video_prompt': video_prompt
                        })
                        
                    except Exception as e:
                        print(f"      ❌ Error processing phrase {j}: {e}")
                        # Add fallback entry
                        video_prompts_with_analysis.append({
                            'phrase_number': j,
                            'phrase': phrase.phrase,
                            'category': phrase.category,
                            'editing_suggestion': phrase.editing_suggestion,
                            'video_prompt': None
                        })
                
                # Add to results with complete analysis
                results.append({
                    'script_number': script_number,
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
                })
                
                print(f"   ✅ Script {script_number} completed with {len(video_prompts_with_analysis)} video prompts")
                
            except Exception as e:
                print(f"   ❌ Error processing script {script_number}: {str(e)}")
                # Add error entry
                results.append({
                    'script_number': script_number,
                    'category': category,
                    'topic': topic,
                    'original_script': script_data.get('script', {}),
                    'analysis': None,
                    'summary': None,
                    'status': 'error',
                    'error_message': str(e)
                })
        
        # Save results
        print(f"\n💾 Saving analyzed scripts with video prompts to: {output_file}")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        successful = len([r for r in results if r['status'] == 'success'])
        failed = len(results) - successful
        total_phrases = sum(len(r.get('analysis', {}).get('phrases_with_video_prompts', [])) for r in results if r['status'] == 'success')
        total_prompts = sum(len([p for p in r.get('analysis', {}).get('phrases_with_video_prompts', []) if p.get('video_prompt') is not None]) for r in results if r['status'] == 'success')
        
        print(f"\n🎉 Analysis and video prompt generation completed!")
        print(f"📊 Results:")
        print(f"   • Scripts processed: {len(results)}")
        print(f"   • Successful: {successful}")
        print(f"   • Failed: {failed}")
        print(f"   • Total phrases analyzed: {total_phrases}")
        print(f"   • Video prompts generated: {total_prompts} (only for 'Video only on screen')")
        print(f"   • Output file: {output_file}")
        
        # Show editing breakdown summary
        if successful > 0:
            total_narrator_only = sum(r.get('summary', {}).get('editing_breakdown', {}).get('narrator_only', 0) for r in results if r['status'] == 'success')
            total_narrator_video = sum(r.get('summary', {}).get('editing_breakdown', {}).get('narrator_and_video', 0) for r in results if r['status'] == 'success')
            total_video_only = sum(r.get('summary', {}).get('editing_breakdown', {}).get('video_only', 0) for r in results if r['status'] == 'success')
            
            print(f"\n📈 Editing suggestions breakdown:")
            print(f"   • Narrator only: {total_narrator_only}")
            print(f"   • Narrator and video: {total_narrator_video}")
            print(f"   • Video only: {total_video_only}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    analyze_and_generate_video_prompts_from_scripts() 