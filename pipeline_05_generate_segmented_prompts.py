"""
Generate segmented video prompts from synchronized script data
Divides long duration phrases into 2-3 second segments with adapted prompts
"""
import json
import math
from typing import List, Tuple, Optional
from pydantic import BaseModel
from pydantic_ai import Agent
from dotenv import load_dotenv
from pathlib import Path

from config import SegmentedPromptsConfig, validate_all_paths, print_configuration_summary

load_dotenv()

# Pydantic models for structured output
class SegmentTiming(BaseModel):
    start_time: float
    end_time: float
    duration: float
    segment_number: int

class AdaptedSegment(BaseModel):
    segment_timing: SegmentTiming
    adapted_prompt: str
    narrative_focus: str  # inicio, desarrollo, cierre
    original_context: str

class SegmentedPromptResponse(BaseModel):
    segments: List[AdaptedSegment]

def calculate_segments(duration: float, start_time: float) -> List[Tuple[float, float, int]]:
    """
    Calculate optimal segments for a given duration
    Returns list of (start_time, end_time, segment_number) tuples
    """
    max_duration = SegmentedPromptsConfig.SEGMENTATION_RULES["max_segment_duration"]
    min_duration = SegmentedPromptsConfig.SEGMENTATION_RULES["min_segment_duration"]
    min_to_segment = SegmentedPromptsConfig.SEGMENTATION_RULES["minimum_duration_to_segment"]
    
    # Don't segment if duration is too short
    if duration < min_to_segment:
        return [(start_time, start_time + duration, 1)]
    
    # Calculate number of segments needed
    num_segments = math.ceil(duration / max_duration)
    
    # If only 2 segments and duration allows, make them equal
    if num_segments == 2 and SegmentedPromptsConfig.SEGMENTATION_RULES["prefer_equal_segments"]:
        segment_duration = duration / 2
    else:
        segment_duration = duration / num_segments
    
    # Ensure minimum duration
    if segment_duration < min_duration and num_segments > 1:
        num_segments = max(1, math.floor(duration / min_duration))
        segment_duration = duration / num_segments
    
    segments = []
    for i in range(num_segments):
        seg_start = start_time + (i * segment_duration)
        seg_end = seg_start + segment_duration
        segments.append((seg_start, seg_end, i + 1))
    
    return segments

def create_segment_prompt_adapter(model_name: str = SegmentedPromptsConfig.MODEL_NAME) -> Agent:
    """Create agent to adapt video prompts for specific time segments"""
    return Agent(
        model=model_name,
        output_type=SegmentedPromptResponse,
        system_prompt="""
You are a viral Instagram Reels content creator and editor specialized in creating engaging educational content for language learning.

Your task is to break down Instagram Reels video prompts into time-specific segments that create viral, engaging content optimized for vertical 9:16 format.

🎯 INSTAGRAM REELS SEGMENT OPTIMIZATION:

1. **Visual Progression**: Each segment builds excitement and engagement
2. **Viral Continuity**: Segments flow smoothly to keep viewers hooked
3. **Modern Aesthetic**: Trendy, dynamic, social media optimized
4. **Educational Value**: Informative but entertaining and shareable

🎬 SEGMENT FOCUS STRATEGY:
- **Segment 1 (inicio)**: Hook viewer with dynamic establishing shot, trendy lighting, engaging setup
- **Middle segments (desarrollo)**: Build momentum with smooth transitions, vibrant visuals, interactive elements
- **Final segment (cierre)**: Strong conclusion with memorable visual, call-to-action ready

🎨 MANDATORY STYLE ELEMENTS FOR EACH SEGMENT:
- "Vertical 9:16 Instagram Reels format"
- Dynamic camera movements (zoom, pan, tilt)
- Modern lighting ("vibrant studio lighting", "trendy LED", "colorful backlight")
- Social media aesthetic ("Instagram-worthy", "viral-ready", "engaging")
- Text overlay compatibility
- Smooth transitions between segments

📱 ENHANCED EXAMPLE:
Original: "Close-up shot of hands placing fork and knife on empty plate at Spanish restaurant, warm lighting, 2-3 second clip"
Duration: 6 seconds → 2 segments of 3s each

Segment 1 (0-3s):
- Focus: "inicio"
- Prompt: "Vertical 9:16 Instagram Reels: Dynamic establishing shot with smooth zoom-in on stylish hands approaching aesthetic Spanish ceramic plate, vibrant restaurant lighting with colorful ambient glow, trendy millennial dining aesthetic, text overlay ready composition"

Segment 2 (3-6s):
- Focus: "cierre"
- Prompt: "Vertical 9:16 Instagram Reels: Satisfying close-up of hands elegantly placing silverware in perfect position, camera holds with gentle movement, vibrant lighting creates Instagram-worthy glow, viral content aesthetic with engaging final frame"

🔥 ENHANCEMENT REQUIREMENTS:
- Transform basic prompts into Instagram viral-worthy content
- Add dynamic camera movements and modern lighting
- Include social media optimization language
- Ensure vertical format compatibility
- Make each segment independently engaging yet cohesive

For each segment, provide:
- adapted_prompt: Instagram Reels optimized video prompt
- narrative_focus: "inicio", "desarrollo", or "cierre"
- original_context: Brief explanation of the segment's role in the viral content strategy

Generate segments that create a cohesive, engaging, viral-ready Instagram Reels experience.
        """
    )

def process_phrase_segments(phrase_data: dict, adapter_agent: Agent) -> dict:
    """Process a single phrase and generate segments if needed"""
    timing = phrase_data.get('timing', {})
    duration = timing.get('duration', 0)
    start_time = timing.get('start_time', 0)
    original_prompt = phrase_data.get('video_prompt')
    editing_suggestion = phrase_data.get('editing_suggestion')
    
    # Only process if we have a video prompt and it needs segmentation
    if not original_prompt or duration < SegmentedPromptsConfig.SEGMENTATION_RULES["minimum_duration_to_segment"]:
        return {
            **phrase_data,
            'segmentation': {
                'needs_segmentation': False,
                'reason': 'Duration too short or no video prompt' if not original_prompt else 'Duration < 4s',
                'original_duration': duration
            }
        }
    
    # Calculate segments
    segments = calculate_segments(duration, start_time)
    
    if len(segments) == 1:
        return {
            **phrase_data,
            'segmentation': {
                'needs_segmentation': False,
                'reason': 'Single segment sufficient',
                'original_duration': duration
            }
        }
    
    print(f"    🔪 Segmenting into {len(segments)} parts (duration: {duration:.1f}s)")
    
    try:
        # Create input for segment adaptation
        segment_timings = []
        for seg_start, seg_end, seg_num in segments:
            segment_timings.append({
                'segment_number': seg_num,
                'start_time': seg_start,
                'end_time': seg_end,
                'duration': seg_end - seg_start
            })
        
        adapter_input = f"""
Original video prompt: {original_prompt}
Editing suggestion: {editing_suggestion}
Original duration: {duration} seconds
Total segments needed: {len(segments)}

Segment timings:
{json.dumps(segment_timings, indent=2)}

Generate adapted prompts for each segment that work together as a cohesive sequence.
        """
        
        # Generate adapted segments
        result = adapter_agent.run_sync(adapter_input)
        adapted_segments = result.output.segments
        
        # Build segmentation data
        segmentation_data = {
            'needs_segmentation': True,
            'original_duration': duration,
            'total_segments': len(segments),
            'segments': []
        }
        
        for i, (seg_start, seg_end, seg_num) in enumerate(segments):
            segment_data = {
                'segment_number': seg_num,
                'timing': {
                    'start_time': seg_start,
                    'end_time': seg_end,
                    'duration': seg_end - seg_start
                },
                'original_prompt': original_prompt,
                'editing_suggestion': editing_suggestion
            }
            
            # Add adapted prompt if available
            if i < len(adapted_segments):
                adapted_seg = adapted_segments[i]
                segment_data.update({
                    'adapted_prompt': adapted_seg.adapted_prompt,
                    'narrative_focus': adapted_seg.narrative_focus,
                    'original_context': adapted_seg.original_context
                })
            else:
                # Fallback if AI didn't generate enough segments
                segment_data.update({
                    'adapted_prompt': f"{original_prompt} (segment {seg_num}/{len(segments)})",
                    'narrative_focus': "desarrollo",
                    'original_context': f"Segment {seg_num} of original prompt"
                })
            
            segmentation_data['segments'].append(segment_data)
        
        return {
            **phrase_data,
            'segmentation': segmentation_data
        }
        
    except Exception as e:
        print(f"    ❌ Error segmenting phrase: {e}")
        return {
            **phrase_data,
            'segmentation': {
                'needs_segmentation': False,
                'reason': f'Error during segmentation: {str(e)}',
                'original_duration': duration,
                'error': str(e)
            }
        }

def generate_segmented_prompts(input_file: str = None, output_file: str = None):
    """
    Main function to generate segmented video prompts
    """
    try:
        # Use config paths if not provided
        input_path = input_file or SegmentedPromptsConfig.INPUT_FILE
        output_path = output_file or (SegmentedPromptsConfig.OUTPUT_DIR / SegmentedPromptsConfig.OUTPUT_FILENAME)
        
        print("🚀 Starting segmented prompt generation...")
        print(f"📖 Input: {input_path}")
        print(f"💾 Output: {output_path}")
        
        # Validate paths and ensure output directory
        config_errors = validate_all_paths()
        if config_errors:
            print("❌ ERRORES DE CONFIGURACIÓN:")
            for error in config_errors:
                print(f"  - {error}")
            return
        
        # Load synchronized script data
        print(f"\n📖 Loading synchronized script data...")
        with open(input_path, 'r', encoding='utf-8') as f:
            script_data = json.load(f)
        
        print(f"✅ Loaded script: {script_data.get('topic', 'Unknown topic')}")
        
        # Create adapter agent
        print("🤖 Initializing segment adapter agent...")
        adapter_agent = create_segment_prompt_adapter()
        
        # Process phrases
        phrases = script_data.get('analysis', {}).get('phrases_with_video_prompts', [])
        print(f"🎬 Processing {len(phrases)} phrases...")
        
        processed_phrases = []
        total_segments_created = 0
        phrases_segmented = 0
        
        for i, phrase in enumerate(phrases, 1):
            print(f"\n🎭 Processing phrase {i}/{len(phrases)}: {phrase.get('phrase', '')[:50]}...")
            
            processed_phrase = process_phrase_segments(phrase, adapter_agent)
            processed_phrases.append(processed_phrase)
            
            # Count segments created
            segmentation = processed_phrase.get('segmentation', {})
            if segmentation.get('needs_segmentation', False):
                segments_count = len(segmentation.get('segments', []))
                total_segments_created += segments_count
                phrases_segmented += 1
                print(f"    ✅ Created {segments_count} segments")
            else:
                print(f"    ➡️ No segmentation needed: {segmentation.get('reason', 'Unknown')}")
        
        # Build final output
        output_data = {
            **script_data,
            'analysis': {
                **script_data.get('analysis', {}),
                'phrases_with_video_prompts': processed_phrases
            },
            'segmentation_summary': {
                'total_phrases': len(phrases),
                'phrases_segmented': phrases_segmented,
                'phrases_not_segmented': len(phrases) - phrases_segmented,
                'total_segments_created': total_segments_created,
                'average_segments_per_phrase': total_segments_created / phrases_segmented if phrases_segmented > 0 else 0,
                'segmentation_rules_used': SegmentedPromptsConfig.SEGMENTATION_RULES,
                'processed_at': str(Path(__file__).name)
            }
        }
        
        # Save results
        print(f"\n💾 Saving segmented prompts to: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"\n🎉 Segmentation completed!")
        print(f"📊 Summary:")
        print(f"   • Total phrases: {len(phrases)}")
        print(f"   • Phrases segmented: {phrases_segmented}")
        print(f"   • Phrases not segmented: {len(phrases) - phrases_segmented}")
        print(f"   • Total segments created: {total_segments_created}")
        print(f"   • Average segments per phrase: {total_segments_created / phrases_segmented:.1f}" if phrases_segmented > 0 else "   • Average segments per phrase: 0")
        print(f"   • Output file: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    generate_segmented_prompts()