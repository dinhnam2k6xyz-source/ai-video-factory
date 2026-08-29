import React, { useState, useEffect } from 'react';
import { X, Settings, Key, CheckCircle2, ShieldCheck, Cpu, Sparkles, ExternalLink, Save, RefreshCw } from 'lucide-react';
import { getApiUrl } from '../config';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [geminiKey, setGeminiKey] = useState('');
  const [capcutUrl, setCapcutUrl] = useState('');
  const [customTtsUrl, setCustomTtsUrl] = useState('');
  const [settingsData, setSettingsData] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetch(getApiUrl('/api/settings/'))
        .then(res => res.json())
        .then(d => {
          setSettingsData(d);
          if (d.capcut_tts_url) setCapcutUrl(d.capcut_tts_url);
          if (d.custom_tts_url) setCustomTtsUrl(d.custom_tts_url);
        })
        .catch(e => console.error(e));
    }
  }, [isOpen]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSavedSuccess(false);

    try {
      const res = await fetch(getApiUrl('/api/settings/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          gemini_api_key: geminiKey || undefined,
          capcut_tts_url: capcutUrl,
          custom_tts_url: customTtsUrl
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setSavedSuccess(true);
        setTimeout(() => setSavedSuccess(false), 3000);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-[#111625] border border-slate-800 rounded-3xl w-full max-w-2xl overflow-hidden shadow-2xl relative">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Cấu Hình Dịch Vụ & API Key (Tùy Chọn)</h2>
              <p className="text-xs text-slate-400">Hệ thống mặc định hoạt động 100% MIỄN PHÍ vĩnh viễn không cần bất kỳ API Key nào</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          
          {/* Status of 100% Free Core Engines */}
          <div className="bg-emerald-950/30 border border-emerald-500/30 rounded-2xl p-4 space-y-3">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs uppercase tracking-wider">
              <ShieldCheck className="w-4 h-4" />
              <span>Trạng Thái Đang Chạy Miễn Phí (Zero Cost Mode - Hoạt Động Cục Bộ):</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div className="bg-slate-900/80 border border-emerald-500/20 rounded-xl p-2.5 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="text-slate-300">Whisper STT (Local Offline)</span>
              </div>
              <div className="bg-slate-900/80 border border-emerald-500/20 rounded-xl p-2.5 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="text-slate-300">Dịch thuật (Chrome Ext Free RPC)</span>
              </div>
              <div className="bg-slate-900/80 border border-emerald-500/20 rounded-xl p-2.5 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="text-slate-300">Lồng tiếng CapCut & viPiper Local</span>
              </div>
              <div className="bg-slate-900/80 border border-emerald-500/20 rounded-xl p-2.5 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="text-slate-300">Render 9:16 Shorts & Subtitle ASS</span>
              </div>
            </div>
          </div>

          {/* Optional Gemini API Key */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-white flex items-center gap-2">
                <Key className="w-4 h-4 text-purple-400" />
                Google Gemini API Key (Miễn Phí 100% - Tùy Chọn):
              </label>
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-purple-400 hover:text-purple-300 flex items-center gap-1 font-semibold underline"
              >
                <span>Lấy Key Free Tại Đây</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed">
              Google cấp gói Free Tier hoàn toàn $0 (không cần thẻ tín dụng). Nếu nhập key này, AI sẽ dịch thuật văn phong kiếm hiệp và tạo nội dung TikTok thông minh hơn nữa.
            </p>

            <input
              type="password"
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              placeholder={settingsData?.has_gemini_key ? `Đang dùng: ${settingsData.gemini_key_masked}` : 'AIzaSy... (Để trống nếu muốn dùng Free RPC)'}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-4 py-2.5 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-purple-500"
            />
          </div>

          {/* Optional CapCut / Custom TTS Server */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3">
            <label className="text-xs font-bold text-white flex items-center gap-2">
              <Cpu className="w-4 h-4 text-indigo-400" />
              CapCut TTS Server / Custom TTS Endpoint URL (Tùy Chọn):
            </label>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Nếu bạn tự dựng máy chủ từ repo GitHub (như <i>kuwacom/CapCut-TTS</i> hoặc <i>Edge-TTS-Server</i>), hãy dán URL máy chủ tại đây (ví dụ: <code className="text-purple-300">http://localhost:8080</code>).
            </p>
            <input
              type="url"
              value={capcutUrl}
              onChange={(e) => setCapcutUrl(e.target.value)}
              placeholder="http://127.0.0.1:8080 (Để trống để dùng CapCut Presets có sẵn)"
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-4 py-2.5 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-purple-500"
            />
          </div>

          {/* Footer Submit Button */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 transition-colors"
            >
              Đóng
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-600/25 transition-all"
            >
              {isSaving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              <span>{savedSuccess ? 'Đã Lưu Thành Công!' : 'Lưu Cấu Hình'}</span>
            </button>
          </div>
        </form>

      </div>
    </div>
  );
};
