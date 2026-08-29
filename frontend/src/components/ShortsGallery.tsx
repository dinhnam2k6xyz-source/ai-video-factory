import React from 'react';
import { Flame, Download, Sparkles, Clock, Share2, Play, Check } from 'lucide-react';
import { ShortClip } from '../types';
import { getStorageUrl } from '../config';

interface ShortsGalleryProps {
  shorts: ShortClip[];
  zipUrl?: string;
}

export const ShortsGallery: React.FC<ShortsGalleryProps> = ({ shorts, zipUrl }) => {
  const [copiedId, setCopiedId] = React.useState<number | null>(null);

  const handleCopyTitle = (id: number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Top action bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-[#111625] border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Flame className="w-5 h-5 text-amber-500 fill-amber-500 animate-bounce" />
            Danh Sách Shorts / TikTok 9:16 Tự Động Tạo ({shorts.length} Clip Viral)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Đã tự động crop 9:16 bám khuôn mặt người nói (Face Tracking) và burn phụ đề Karaoke TikTok
          </p>
        </div>

        {zipUrl && (
          <a
            href={getStorageUrl(zipUrl)}
            download="ai_video_factory_shorts_pack.zip"
            className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-lg shadow-purple-600/30 transition-all hover:scale-105"
          >
            <Download className="w-4 h-4" />
            Tải Trọn Bộ ZIP (Tất Cả Clips + Assets)
          </a>
        )}
      </div>

      {/* Shorts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {shorts.map((clip) => (
          <div
            key={clip.id}
            className="bg-[#111625] border border-slate-800 hover:border-purple-500/50 rounded-2xl p-4 shadow-xl flex flex-col justify-between transition-all group hover:shadow-purple-500/10"
          >
            {/* Header info */}
            <div>
              <div className="flex items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-1.5 bg-amber-500/15 border border-amber-500/30 text-amber-400 px-2.5 py-1 rounded-lg text-xs font-black">
                  <Flame className="w-3.5 h-3.5 fill-amber-400" />
                  <span>{clip.viral_score}/100 VIRAL</span>
                </div>
                <div className="flex items-center gap-1 text-slate-400 text-xs font-semibold bg-slate-900 px-2 py-1 rounded-md">
                  <Clock className="w-3 h-3" />
                  <span>{clip.duration}s</span>
                </div>
              </div>

              {/* 9:16 Video Player Container */}
              <div className="aspect-[9/16] max-h-[380px] mx-auto bg-black rounded-xl overflow-hidden border border-slate-800 relative mb-4 shadow-lg">
                {clip.video_url ? (
                  <video
                    controls
                    src={getStorageUrl(clip.video_url)}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-2">
                    <Play className="w-8 h-8 opacity-40" />
                    <span className="text-xs">Đang tải preview...</span>
                  </div>
                )}
              </div>

              {/* Title & Hook */}
              <div className="space-y-2">
                <h4 className="font-bold text-white text-sm line-clamp-2 leading-snug">
                  {clip.title}
                </h4>
                {clip.hook && (
                  <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-2.5 text-[11px] text-slate-300">
                    <span className="font-bold text-purple-400">🎯 Hook 3s đầu:</span> {clip.hook}
                  </div>
                )}
                {clip.reason && (
                  <div className="text-[11px] text-slate-400 italic">
                    💡 {clip.reason}
                  </div>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-slate-800">
              <a
                href={getStorageUrl(clip.video_url)}
                download={`short_viral_${clip.id}.mp4`}
                className="flex-1 flex items-center justify-center gap-1.5 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-semibold py-2 rounded-xl transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                Tải Clip
              </a>
              <button
                onClick={() => handleCopyTitle(clip.id, clip.title)}
                className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
                title="Copy tiêu đề"
              >
                {copiedId === clip.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Share2 className="w-3.5 h-3.5" />}
              </button>
            </div>

          </div>
        ))}
      </div>
    </div>
  );
};
