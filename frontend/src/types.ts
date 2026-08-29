export interface SpeakerProfile {
  id: string;
  name: string;
  gender: string;
  voice_id: string;
  voice_name: string;
  speed: number;
  pitch: string;
  accent?: string;
}

export interface Segment {
  id: number;
  start: number;
  end: number;
  text: string;
  translated_text?: string;
  original_text?: string;
  speaker: string;
  voice_id?: string;
  tts_audio_path?: string;
  words?: { word: string; start: number; end: number }[];
}

export interface ShortClip {
  id: number;
  title: string;
  start_time: number;
  end_time: number;
  duration: number;
  viral_score: number;
  hook: string;
  reason?: string;
  video_url: string;
}

export interface ContentPack {
  titles: string[];
  captions: string[];
  hashtags: string[];
  thumbnail_ideas?: any[];
  thumbnail_concepts?: any[];
  blog_post: string;
  key_takeaways?: string[];
}

export interface TaskData {
  task_id: string;
  status: 'processing' | 'completed' | 'failed';
  progress: number;
  stage: string;
  message: string;
  data?: {
    media_info?: {
      duration: number;
      width: number;
      height: number;
    };
    speakers?: Record<string, SpeakerProfile>;
    segments?: Segment[];
    full_video_url?: string;
    subtitles?: {
      srt_vi?: string;
      srt_orig?: string;
      srt_bilingual?: string;
      txt_vi?: string;
      txt_orig?: string;
    };
    shorts?: ShortClip[];
    content_pack?: ContentPack;
    zip_download_url?: string;
  };
}

export interface UserCredits {
  plan?: 'FREE' | 'PRO_99K' | 'PRO_199K' | 'BUSINESS_499K';
  plan_name?: string;
  price_vnd?: number;
  minutes_used?: number;
  minutes_total?: number;
  minutes_remaining?: number;
  videos_processed?: number;
  shorts_created?: number;
  features?: string[];
  remaining_credits?: number;
  current_tier?: string;
  all_tiers?: any;
}
