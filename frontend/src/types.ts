export interface SpeakerProfile {
  id: string;
  name: string;
  gender: string;
  voice_id: string;
  voice_name: string;
  speed: number;
  pitch: string;
}

export interface Segment {
  id: number;
  start: number;
  end: number;
  text: string;
  translated_text?: string;
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
  reason: string;
  video_url: string;
}

export interface ThumbnailConcept {
  text: string;
  visual_idea: string;
}

export interface ContentPack {
  titles: string[];
  captions: string[];
  hashtags: string[];
  thumbnail_concepts: ThumbnailConcept[];
  blog_post: string;
  key_takeaways: string[];
  transcript?: string;
}

export interface TaskData {
  task_id: string;
  status: 'init' | 'processing' | 'completed' | 'failed';
  progress: number;
  stage: string;
  message: string;
  data?: {
    media_info?: { duration: number; width: number; height: number; fps: number };
    speakers?: Record<string, SpeakerProfile>;
    segments?: Segment[];
    full_video_url?: string;
    shorts?: ShortClip[];
    content_pack?: ContentPack;
    zip_download_url?: string;
  };
}

export interface VoiceOption {
  id: string;
  name: string;
  gender: string;
}

export interface TierInfo {
  name: string;
  price: string;
  credits: number;
  max_resolution: string;
  watermark: boolean;
  features: string[];
}

export interface UserCredits {
  current_tier: string;
  remaining_credits: number;
  used_credits: number;
  total_videos_processed: number;
  total_shorts_generated: number;
  tier_info: TierInfo;
  all_tiers: Record<string, TierInfo>;
}
