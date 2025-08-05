export interface SubtitleEntry {
  id: number;
  startTime: number;
  endTime: number;
  text: string;
}

export function parseSRT(srtContent: string): SubtitleEntry[] {
  const entries: SubtitleEntry[] = [];
  const lines = srtContent.trim().split('\n');
  
  console.log(`🔍 SRT Parser Debug (NEW):`);
  console.log(`📄 Raw content length: ${srtContent.length}`);
  console.log(`📄 Total lines: ${lines.length}`);

  let i = 0;
  while (i < lines.length) {
    // Skip empty lines
    if (!lines[i] || lines[i].trim() === '') {
      i++;
      continue;
    }

    // Parse subtitle ID
    const id = parseInt(lines[i]);
    if (isNaN(id)) {
      console.log(`⚠️ Skipping line ${i + 1}: Invalid ID "${lines[i]}"`);
      i++;
      continue;
    }

    // Parse timestamp line
    i++;
    if (i >= lines.length) break;
    
    const timeMatch = lines[i].match(/(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})/);
    if (!timeMatch) {
      console.log(`⚠️ Skipping subtitle ${id}: Invalid time format "${lines[i]}"`);
      i++;
      continue;
    }

    const startTime = parseTime(timeMatch[1], timeMatch[2], timeMatch[3], timeMatch[4]);
    const endTime = parseTime(timeMatch[5], timeMatch[6], timeMatch[7], timeMatch[8]);

    // Parse subtitle text (can be multiple lines)
    i++;
    const textLines: string[] = [];
    while (i < lines.length && lines[i].trim() !== '' && !lines[i].match(/^\d+$/)) {
      textLines.push(lines[i]);
      i++;
    }

    const text = textLines.join(' ').trim();
    
    console.log(`✅ Subtitle ${id} parsed: ${startTime}s - ${endTime}s "${text.substring(0, 30)}..."`);

    entries.push({
      id,
      startTime,
      endTime,
      text
    });
  }

  console.log(`🎯 Final result: ${entries.length} subtitle entries parsed`);
  return entries;
}

function parseTime(hours: string, minutes: string, seconds: string, milliseconds: string): number {
  return (
    parseInt(hours) * 3600 +
    parseInt(minutes) * 60 +
    parseInt(seconds) +
    parseInt(milliseconds) / 1000
  );
}

export function getCurrentSubtitle(subtitles: SubtitleEntry[], currentTime: number): string | null {
  const current = subtitles.find(
    subtitle => currentTime >= subtitle.startTime && currentTime <= subtitle.endTime
  );
  return current ? current.text : null;
} 