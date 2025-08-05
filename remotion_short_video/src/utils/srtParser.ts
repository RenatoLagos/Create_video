export interface SubtitleEntry {
  id: number;
  startTime: number;
  endTime: number;
  text: string;
}

export function parseSRT(srtContent: string): SubtitleEntry[] {
  const entries: SubtitleEntry[] = [];
  const blocks = srtContent.trim().split('\n\n');

  for (const block of blocks) {
    const lines = block.trim().split('\n');
    if (lines.length < 3) continue;

    const id = parseInt(lines[0]);
    const timeMatch = lines[1].match(/(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})/);
    
    if (!timeMatch) continue;

    const startTime = parseTime(timeMatch[1], timeMatch[2], timeMatch[3], timeMatch[4]);
    const endTime = parseTime(timeMatch[5], timeMatch[6], timeMatch[7], timeMatch[8]);
    const text = lines.slice(2).join('\n');

    entries.push({
      id,
      startTime,
      endTime,
      text
    });
  }

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