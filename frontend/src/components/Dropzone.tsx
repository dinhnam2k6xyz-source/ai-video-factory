import React, { useState, useRef, useEffect } from 'react';
import { Upload, Link2, Sparkles, Film, ArrowRight, Wand2, CheckCircle2, Globe, Volume2, User, Users, Mic, Pause } from 'lucide-react';
import { getApiUrl, getStorageUrl } from '../config';

interface DropzoneProps {
  onStartProcessing: (params: {
    file?: File;
    url?: string;
    targetLang: string;
    sourceLang: string;
    voiceMode: string;
    primaryVoiceId: string;
    customPrompt: string;
  }) => void;
  isLoading: boolean;
}

export const Dropzone: React.FC<DropzoneProps> = ({ onStartProcessing, isLoading }) => {
  const [tab, setTab] = useState<'upload' | 'url'>('upload');
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [sourceLang, setSourceLang] = useState('auto');
  const [targetLang, setTargetLang] = useState('vi');
  const [voiceMode, setVoiceMode] = useState<'solo' | 'dual' | 'multi'>('solo');
  const [primaryVoiceId, setPrimaryVoiceId] = useState('capcut_serious_man');
  const [customPrompt, setCustomPrompt] = useState('');
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const availableVoices = [
    { id: "capcut_serious_man", name: "CapCut - Nam Review Phim Kiếm Hiệp (🔥 Trầm sâu, Điện ảnh)", tag: "CapCut Hot" },
    { id: "capcut_young_girl", name: "CapCut - Cô Gái Hoạt Bát (🔥 Trẻ trung, Vui vẻ)", tag: "CapCut Hot" },
    { id: "capcut_calm_dubbing", name: "CapCut - Kể Chuyện Trầm Lắng (🎬 Nhẹ nhàng, Cuốn hút)", tag: "CapCut Dub" },
    { id: "capcut_confident_man", name: "CapCut - Thanh Niên Tự Tin (⚡ TikTok Trend, Dứt khoát)", tag: "CapCut Trend" },
    { id: "capcut_little_sister", name: "CapCut - Cô Bé Dễ Thương (👧 Trong trẻo, Ngọt ngào)", tag: "CapCut Cute" },
    { id: "capcut_radio_host", name: "CapCut - Host Radio Đêm (📻 Ấm áp, Tâm sự)", tag: "CapCut Radio" },
    { id: "capcut_wise_old_man", name: "CapCut - Ông Lão Trầm Khàn (👴 Cổ trang, Trải nghiệm)", tag: "CapCut Cổ Trang" },
    { id: "capcut_grandma", name: "CapCut - Bà Lão Ấm Áp (👵 Chân thật, Gia đình)", tag: "CapCut Gia Đình" },
    { id: "piper:vi_VN-25hours_single-low", name: "viPiper 25Hours (💻 Local Offline CPU - Nữ)", tag: "Offline" },
    { id: "piper:vi_VN-vivos-x_low", name: "viPiper Vivos Multi (💻 Local Offline CPU - Nam/Nữ)", tag: "Offline" },
  ];

  const promptPresets = [
    "🔥 Biến video này thành 5 video TikTok hấp dẫn & giữ chân người xem",
    "🎙️ Reup lồng tiếng 1 giọng duy nhất phong cách Review Phim",
    "💡 Tạo 3 video Shorts theo phong cách kể chuyện lôi cuốn",
    "🚀 Trích xuất các đoạn cao trào triệu view kèm phụ đề Karaoke nổi bật"
  ];

  const handlePreviewVoice = async (voiceId: string) => {
    if (playingVoiceId === voiceId && audioElement) {
      audioElement.pause();
      setPlayingVoiceId(null);
      return;
    }

    try {
      const res = await fetch(getApiUrl('/api/voices/preview'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: 'Xin chào! Đây là giọng lồng tiếng của AI Video Factory.',
          voice_id: voiceId
        })
      });
      const result = await res.json();
      if (result.status === 'success' && result.audio_url) {
        if (audioElement) audioElement.pause();
        const audio = new Audio(getStorageUrl(result.audio_url));
        audio.play();
        setAudioElement(audio);
        setPlayingVoiceId(voiceId);
        audio.onended = () => setPlayingVoiceId(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith('video/')) {
        setSelectedFile(file);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (tab === 'upload' && !selectedFile) return;
    if (tab === 'url' && !videoUrl.trim()) return;

    onStartProcessing({
      file: selectedFile || undefined,
      url: tab === 'url' ? videoUrl.trim() : undefined,
      targetLang,
      sourceLang,
      voiceMode,
      primaryVoiceId,
      customPrompt
    });
  };

  return (
    <div className="max-w-4xl mx-auto my-8">
      <div className="bg-[#111625] border border-slate-800/80 rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-72 h-72 rounded-full bg-purple-600/10 blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-72 h-72 rounded-full bg-indigo-600/10 blur-3xl pointer-events-none"></div>

        {/* Header Tabs */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setTab('upload')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                tab === 'upload'
                  ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <Upload className="w-4 h-4" />
              Tải Lên Video (MP4 / MKV)
            </button>

            <button
              type="button"
              onClick={() => setTab('url')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                tab === 'url'
                  ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <Link2 className="w-4 h-4" />
              Dán Link (YouTube / TikTok / Douyin)
            </button>
          </div>

          <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400">
            <Globe className="w-3.5 h-3.5 text-purple-400" />
            <span>Hỗ trợ: Trung, Anh, Nhật, Hàn → Việt</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Main Drop Area */}
          {tab === 'upload' ? (
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
                dragOver
                  ? 'border-purple-500 bg-purple-500/10 scale-[0.99]'
                  : selectedFile
                  ? 'border-emerald-500/60 bg-emerald-500/5'
                  : 'border-slate-700/80 bg-slate-900/40 hover:border-slate-600 hover:bg-slate-900/60'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                onChange={handleFileChange}
                className="hidden"
              />
              
              {selectedFile ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-lg shadow-emerald-500/20">
                    <CheckCircle2 className="w-8 h-8" />
                  </div>
                  <div className="text-white font-bold text-lg">{selectedFile.name}</div>
                  <div className="text-xs text-slate-400">
                    Kích thước: {(selectedFile.size / (1024 * 1024)).toFixed(1)} MB • Click để chọn video khác
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-16 h-16 rounded-2xl bg-purple-600/10 border border-purple-500/20 flex items-center justify-center text-purple-400 group-hover:scale-110 transition-transform">
                    <Upload className="w-8 h-8" />
                  </div>
                  <div className="font-bold text-white text-base">
                    Kéo & thả file video vào đây hoặc <span className="text-purple-400 underline decoration-purple-400/50 underline-offset-4">duyệt từ máy</span>
                  </div>
                  <div className="text-xs text-slate-400">
                    Hỗ trợ file MP4, MOV, MKV, AVI lên đến 2GB
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6">
              <label className="block text-xs font-semibold text-slate-300 mb-2">
                Dán đường dẫn video (YouTube, TikTok, Douyin, Facebook):
              </label>
              <div className="flex items-center gap-3 bg-slate-950 border border-slate-700/80 rounded-xl px-4 py-3 focus-within:border-purple-500 transition-colors">
                <Link2 className="w-5 h-5 text-slate-400" />
                <input
                  type="url"
                  value={videoUrl}
                  onChange={(e) => setVideoUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=... hoặc https://v.douyin.com/..."
                  className="bg-transparent text-sm text-white focus:outline-none w-full placeholder:text-slate-500"
                />
              </div>
            </div>
          )}

          {/* Configuration Grid: Languages */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
              <label className="block text-xs font-semibold text-slate-300 mb-2">
                🗣️ Ngôn ngữ gốc trong video:
              </label>
              <select
                value={sourceLang}
                onChange={(e) => setSourceLang(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
              >
                <option value="auto">🌐 Tự động nhận diện (Auto-detect)</option>
                <option value="zh">🇨🇳 Tiếng Trung Quốc (Chinese)</option>
                <option value="en">🇺🇸 Tiếng Anh (English)</option>
                <option value="ja">🇯🇵 Tiếng Nhật (Japanese)</option>
                <option value="ko">🇰🇷 Tiếng Hàn (Korean)</option>
                <option value="vi">🇻🇳 Tiếng Việt (Vietnamese)</option>
              </select>
            </div>

            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
              <label className="block text-xs font-semibold text-slate-300 mb-2">
                🎯 Ngôn ngữ đích lồng tiếng:
              </label>
              <select
                value={targetLang}
                onChange={(e) => setTargetLang(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
              >
                <option value="vi">🇻🇳 Tiếng Việt (Vietnamese Standard)</option>
                <option value="en">🇺🇸 Tiếng Anh (English)</option>
                <option value="zh">🇨🇳 Tiếng Trung (Chinese)</option>
              </select>
            </div>
          </div>

          {/* Voice Mode Selector Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-white flex items-center gap-2">
                <Mic className="w-4 h-4 text-purple-400" />
                CHẾ ĐỘ GIỌNG ĐỌC KHI REUP / LỒNG TIẾNG:
              </label>
              <span className="text-[10px] bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded-md font-bold">
                Linh Hoạt 1 - 2 - Đa Giọng
              </span>
            </div>

            {/* 3 Radio Options */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div
                onClick={() => setVoiceMode('solo')}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                  voiceMode === 'solo'
                    ? 'bg-purple-600/20 border-purple-500 shadow-md shadow-purple-500/10'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <User className={`w-4 h-4 ${voiceMode === 'solo' ? 'text-purple-400' : 'text-slate-400'}`} />
                  <span className="text-xs font-bold text-white">1 Giọng Duy Nhất</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-snug">
                  Đọc toàn bộ video bằng 1 giọng duy nhất (chuẩn Review Phim / Reup)
                </p>
              </div>

              <div
                onClick={() => setVoiceMode('dual')}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                  voiceMode === 'dual'
                    ? 'bg-purple-600/20 border-purple-500 shadow-md shadow-purple-500/10'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <Users className={`w-4 h-4 ${voiceMode === 'dual' ? 'text-purple-400' : 'text-slate-400'}`} />
                  <span className="text-xs font-bold text-white">2 Giọng Đối Thoại</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-snug">
                  Chia đối thoại 2 người (1 Nam & 1 Nữ luân phiên)
                </p>
              </div>

              <div
                onClick={() => setVoiceMode('multi')}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                  voiceMode === 'multi'
                    ? 'bg-purple-600/20 border-purple-500 shadow-md shadow-purple-500/10'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <Sparkles className={`w-4 h-4 ${voiceMode === 'multi' ? 'text-purple-400' : 'text-slate-400'}`} />
                  <span className="text-xs font-bold text-white">Tự Động Đa Vai</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-snug">
                  AI tự nhận diện bao nhiêu nhân vật thì gán bấy nhiêu giọng
                </p>
              </div>
            </div>

            {/* Primary Voice Dropdown when Solo mode is active */}
            {voiceMode === 'solo' && (
              <div className="bg-slate-950/80 border border-purple-500/30 rounded-xl p-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="flex-1 w-full sm:w-auto">
                  <label className="block text-[11px] font-bold text-purple-300 mb-1.5">
                    Chọn Giọng Người Kể Chuyện Chính:
                  </label>
                  <select
                    value={primaryVoiceId}
                    onChange={(e) => setPrimaryVoiceId(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                  >
                    {availableVoices.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  type="button"
                  onClick={() => handlePreviewVoice(primaryVoiceId)}
                  className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-semibold flex items-center gap-1.5 transition-colors self-end sm:self-auto"
                >
                  {playingVoiceId === primaryVoiceId ? <Pause className="w-3.5 h-3.5 animate-pulse" /> : <Volume2 className="w-3.5 h-3.5" />}
                  <span>Nghe thử</span>
                </button>
              </div>
            )}
          </div>

          {/* AI Content Generator Prompt Bar */}
          <div className="bg-gradient-to-r from-purple-900/20 via-indigo-900/20 to-slate-900/40 border border-purple-500/30 rounded-2xl p-5 relative">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-bold uppercase tracking-wider text-purple-300">
                ✨ AI Content Generator (Tùy biến lệnh thông minh)
              </span>
            </div>
            
            <div className="relative">
              <input
                type="text"
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="Nhập yêu cầu ví dụ: 'Biến video này thành 5 video TikTok hấp dẫn' hoặc 'Tạo 3 Shorts phong cách kể chuyện'..."
                className="w-full bg-slate-950/80 border border-slate-700 rounded-xl pl-4 pr-10 py-3 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-purple-400 transition-all shadow-inner"
              />
              <Wand2 className="w-4 h-4 text-purple-400 absolute right-3.5 top-3.5 pointer-events-none" />
            </div>

            {/* Quick Prompt Presets */}
            <div className="flex flex-wrap gap-2 mt-3">
              {promptPresets.map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setCustomPrompt(preset)}
                  className="text-[11px] bg-slate-800/80 hover:bg-purple-900/40 hover:text-purple-300 text-slate-400 px-2.5 py-1 rounded-lg border border-slate-700/60 hover:border-purple-500/30 transition-colors text-left truncate max-w-full"
                >
                  {preset}
                </button>
              ))}
            </div>
          </div>

          {/* Submit CTA Button */}
          <button
            type="submit"
            disabled={isLoading || (tab === 'upload' && !selectedFile) || (tab === 'url' && !videoUrl.trim())}
            className={`w-full py-4 rounded-xl font-bold text-base flex items-center justify-center gap-3 transition-all shadow-xl ${
              isLoading || (tab === 'upload' && !selectedFile) || (tab === 'url' && !videoUrl.trim())
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                : 'bg-gradient-to-r from-purple-600 via-indigo-600 to-pink-600 hover:from-purple-500 hover:via-indigo-500 hover:to-pink-500 text-white shadow-purple-600/30 hover:shadow-purple-600/50 hover:scale-[1.01] active:scale-[0.99]'
            }`}
          >
            {isLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Đang Khởi Động AI Pipeline...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>CHẠY TOÀN BỘ AI FACTORY PIPELINE (1-CLICK)</span>
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
