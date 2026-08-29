import React, { useState } from 'react';
import { Copy, Check, Sparkles, Hash, Image, BookOpen, Layers, MessageSquare, Lightbulb } from 'lucide-react';
import { ContentPack } from '../types';

interface ContentMultiplierProps {
  content: ContentPack;
}

export const ContentMultiplier: React.FC<ContentMultiplierProps> = ({ content }) => {
  const [copiedItem, setCopiedItem] = useState<string | null>(null);

  const handleCopy = (key: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedItem(key);
    setTimeout(() => setCopiedItem(null), 2000);
  };

  const copyAllHashtags = () => {
    const text = content.hashtags.join(' ');
    handleCopy('all_hashtags', text);
  };

  return (
    <div className="space-y-8">
      {/* Overview Banner */}
      <div className="bg-gradient-to-r from-purple-900/30 via-indigo-900/30 to-pink-900/20 border border-purple-500/30 rounded-2xl p-6 shadow-xl flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <h3 className="text-lg font-bold text-white">1 VIDEO → 10 NỘI DUNG TRUYỀN THÔNG ĐA KÊNH</h3>
          </div>
          <p className="text-xs text-slate-300">
            Tự động nhân bản bài viết, hashtag, tiêu đề viral, kịch bản thumbnail cho TikTok, YouTube & Facebook
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Box 1: 10 Tiêu Đề Viral */}
        <div className="bg-[#111625] border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
            <h4 className="font-bold text-white text-sm flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              10 Tiêu Đề Tối Ưu CTR (Click-Through Rate)
            </h4>
            <span className="text-xs bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded-md font-semibold">
              {content.titles.length} Tiêu đề
            </span>
          </div>

          <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
            {content.titles.map((title, idx) => (
              <div
                key={idx}
                className="bg-slate-900/70 hover:bg-slate-900 border border-slate-800 rounded-xl p-3 flex items-center justify-between gap-3 text-xs text-slate-200 transition-colors group"
              >
                <div className="flex items-start gap-2.5 flex-1">
                  <span className="font-bold text-purple-400 flex-shrink-0">#{idx + 1}</span>
                  <span className="font-medium text-slate-100">{title}</span>
                </div>
                <button
                  onClick={() => handleCopy(`title_${idx}`, title)}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-purple-600/30 text-slate-400 hover:text-purple-300 transition-colors"
                  title="Copy tiêu đề"
                >
                  {copiedItem === `title_${idx}` ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Box 2: 10 Captions Đa Kênh */}
        <div className="bg-[#111625] border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
            <h4 className="font-bold text-white text-sm flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-indigo-400" />
              10 Đoạn Caption Chuẩn TikTok / Shorts
            </h4>
            <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-md font-semibold">
              {content.captions.length} Captions
            </span>
          </div>

          <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
            {content.captions.map((cap, idx) => (
              <div
                key={idx}
                className="bg-slate-900/70 hover:bg-slate-900 border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between gap-2.5 transition-colors"
              >
                <p className="text-xs text-slate-300 leading-relaxed">{cap}</p>
                <div className="flex justify-end">
                  <button
                    onClick={() => handleCopy(`cap_${idx}`, cap)}
                    className="flex items-center gap-1 text-[11px] bg-slate-800 hover:bg-indigo-600/30 text-slate-300 hover:text-indigo-300 px-2.5 py-1 rounded-lg transition-colors border border-slate-700/60"
                  >
                    {copiedItem === `cap_${idx}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    <span>Copy Caption</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Box 3 & 4: Hashtags & Thumbnail Concepts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Hashtags Tag Cloud */}
        <div className="bg-[#111625] border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
            <h4 className="font-bold text-white text-sm flex items-center gap-2">
              <Hash className="w-4 h-4 text-pink-400" />
              30 Hashtags Tối Ưu Thuật Toán Phân Phối
            </h4>
            <button
              onClick={copyAllHashtags}
              className="flex items-center gap-1.5 text-xs bg-pink-500/20 hover:bg-pink-500/30 text-pink-300 border border-pink-500/30 px-3 py-1 rounded-lg transition-colors font-semibold"
            >
              {copiedItem === 'all_hashtags' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>Copy Tất Cả Hashtags</span>
            </button>
          </div>

          <div className="flex flex-wrap gap-2 max-h-[220px] overflow-y-auto">
            {content.hashtags.map((tag, idx) => (
              <span
                key={idx}
                onClick={() => handleCopy(`tag_${idx}`, tag)}
                className="text-xs bg-slate-900 hover:bg-pink-950 border border-slate-800 hover:border-pink-500/40 text-slate-300 hover:text-pink-300 px-3 py-1.5 rounded-lg cursor-pointer transition-all"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Thumbnail Visual Concepts */}
        <div className="bg-[#111625] border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
            <h4 className="font-bold text-white text-sm flex items-center gap-2">
              <Image className="w-4 h-4 text-amber-400" />
              Ý Tưởng Thiết Kế Thumbnail Thu Hút
            </h4>
          </div>

          <div className="space-y-3 max-h-[220px] overflow-y-auto pr-1">
            {content.thumbnail_concepts.map((concept, idx) => (
              <div
                key={idx}
                className="bg-slate-900/80 border border-slate-800 rounded-xl p-3 text-xs space-y-1.5"
              >
                <div className="font-bold text-amber-400 flex items-center gap-1.5">
                  <Lightbulb className="w-3.5 h-3.5" />
                  <span>Dòng chữ chính: "{concept.text}"</span>
                </div>
                <p className="text-slate-400 text-[11px] leading-snug">{concept.visual_idea}</p>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Box 5: Long-form SEO Blog Post / Facebook Article */}
      <div className="bg-[#111625] border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-4">
          <h4 className="font-bold text-white text-base flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-emerald-400" />
            Bài Viết Tóm Tắt Chi Tiết (Facebook / Blog / Newsletter)
          </h4>
          <button
            onClick={() => handleCopy('blog_post', content.blog_post)}
            className="flex items-center gap-1.5 text-xs bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 px-3 py-1.5 rounded-lg transition-colors font-semibold"
          >
            {copiedItem === 'blog_post' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>Copy Toàn Bộ Bài Viết</span>
          </button>
        </div>

        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-5 text-sm text-slate-300 leading-relaxed whitespace-pre-line max-h-[300px] overflow-y-auto">
          {content.blog_post}
        </div>
      </div>
    </div>
  );
};
