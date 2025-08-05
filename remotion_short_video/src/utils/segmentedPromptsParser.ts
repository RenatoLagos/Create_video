/**
 * Parser for segmented_prompts JSON files
 * Maps editing suggestions to layout types and creates timeline
 */

export interface SegmentTiming {
  start_time: number;
  end_time: number;
  duration: number;
}

export interface Segment {
  segment_number: number;
  timing: SegmentTiming;
  original_prompt: string;
  editing_suggestion: string;
  adapted_prompt: string;
  narrative_focus: string;
  original_context: string;
}

export interface Phrase {
  phrase_number: number;
  phrase: string;
  category: string;
  editing_suggestion: string;
  video_prompt: string | null;
  timing: {
    start_time: number;
    end_time: number;
    duration: number;
    matched_text: string;
    similarity_score: number;
    method: string;
  };
  segmentation: {
    needs_segmentation: boolean;
    original_duration: number;
    total_segments?: number;
    reason?: string;
    segments?: Segment[];
  };
}

export interface SegmentedPromptsData {
  id: number;
  category: string;
  topic: string;
  original_script: {
    hook: string;
    development: string;
    closing: string;
  };
  analysis: {
    total_phrases: number;
    phrases_with_video_prompts: Phrase[];
  };
  summary: {
    editing_breakdown: {
      narrator_only: number;
      narrator_and_video: number;
      video_only: number;
    };
  };
  status: string;
  synchronization: {
    synchronized_at: string;
    method: string;
    similarity_threshold: number;
    total_phrases: number;
    matched_phrases: number;
    unmatched_phrases: number;
  };
  segmentation_summary: {
    script_id: number;
    total_phrases: number;
    phrases_segmented: number;
    phrases_not_segmented: number;
    total_segments_created: number;
    average_segments_per_phrase: number;
    segmentation_rules_used: {
      max_segment_duration: number;
      min_segment_duration: number;
      prefer_equal_segments: boolean;
      minimum_duration_to_segment: number;
    };
    processed_at: string;
  };
}

export type LayoutType = 'center' | 'bottom' | 'circle';

export interface TimelineSegment {
  startTime: number;
  endTime: number;
  duration: number;
  layout: LayoutType;
  editingSuggestion: string;
  phraseNumber: number;
  segmentNumber?: number;
  phrase: string;
  videoPrompt: string | null;
  adaptedPrompt?: string;
}

/**
 * Maps editing suggestions to layout types
 */
export function getLayoutFromEditingSuggestion(editingSuggestion: string): LayoutType {
  switch (editingSuggestion) {
    case 'Video only on screen':
      return 'circle';
    case 'Narrator and video split screen':
      return 'bottom';
    case 'Narrator only on screen':
      return 'center';
    default:
      console.warn(`Unknown editing suggestion: ${editingSuggestion}, defaulting to center`);
      return 'center';
  }
}

/**
 * Parses segmented prompts JSON and creates timeline
 */
export function parseSegmentedPrompts(data: SegmentedPromptsData): TimelineSegment[] {
  const timeline: TimelineSegment[] = [];

  data.analysis.phrases_with_video_prompts.forEach((phrase) => {
    if (phrase.segmentation.needs_segmentation && phrase.segmentation.segments) {
      // Handle segmented phrases
      phrase.segmentation.segments.forEach((segment) => {
        timeline.push({
          startTime: segment.timing.start_time,
          endTime: segment.timing.end_time,
          duration: segment.timing.duration,
          layout: getLayoutFromEditingSuggestion(segment.editing_suggestion),
          editingSuggestion: segment.editing_suggestion,
          phraseNumber: phrase.phrase_number,
          segmentNumber: segment.segment_number,
          phrase: phrase.phrase,
          videoPrompt: phrase.video_prompt,
          adaptedPrompt: segment.adapted_prompt
        });
      });
    } else {
      // Handle non-segmented phrases
      timeline.push({
        startTime: phrase.timing.start_time,
        endTime: phrase.timing.end_time,
        duration: phrase.timing.duration,
        layout: getLayoutFromEditingSuggestion(phrase.editing_suggestion),
        editingSuggestion: phrase.editing_suggestion,
        phraseNumber: phrase.phrase_number,
        phrase: phrase.phrase,
        videoPrompt: phrase.video_prompt
      });
    }
  });

  // Sort timeline by start time
  timeline.sort((a, b) => a.startTime - b.startTime);

  return timeline;
}

/**
 * Gets the active timeline segment for a given time
 */
export function getActiveSegment(timeline: TimelineSegment[], currentTime: number): TimelineSegment | null {
  return timeline.find(segment => 
    currentTime >= segment.startTime && currentTime <= segment.endTime
  ) || null;
}

/**
 * Load and parse segmented prompts from JSON file
 */
export async function loadSegmentedPrompts(jsonFile: string): Promise<TimelineSegment[]> {
  try {
    // In Remotion, we need to fetch from staticFile
    const response = await fetch(jsonFile);
    const data: SegmentedPromptsData = await response.json();
    return parseSegmentedPrompts(data);
  } catch (error) {
    console.error('Error loading segmented prompts:', error);
    return [];
  }
}

/**
 * Debug function to log timeline
 */
export function logTimeline(timeline: TimelineSegment[]): void {
  console.log('📺 Video Timeline:');
  timeline.forEach((segment, index) => {
    console.log(
      `${index + 1}. ${segment.startTime}s - ${segment.endTime}s: "${segment.editingSuggestion}" → ${segment.layout.toUpperCase()}`
    );
  });
}