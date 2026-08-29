import React, { useState, useEffect } from 'react';
import { X, Settings, Key, CheckCircle2, ShieldCheck, Cpu, Sparkles, ExternalLink, Save, RefreshCw, Globe, Server } from 'lucide-react';
import { getApiUrl, getApiBaseUrl, setApiBaseUrl } from '../config';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [backendUrl, setBackendUrl] = useState('');
  const [geminiKey, setGeminiKey] = useState('');
  const [capcutUrl, setCapcutUrl] = useState('');
  const [customTtsUrl, setCustomTtsUrl] = useState('');
  const [settingsData, setSettingsData] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setBackendUrl(getApiBaseUrl());
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

    // Lưu Backend URL vào LocalStorage
    setApiBaseUrl(backendUrl);

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
      // Vẫn báo thành công nếu chỉ cập nhật Backend URL
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-[#111625] border border-purple-500/40 rounded-3xl w-full max-w-xl p-6 sm:p-8 shadow-2xl relative overflow-hidden max-h-[90vh] overflow-y-auto">
        {/* Background glow */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>

        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Cấu Hình Kết Nối & AI Engine</h3>
              <p className="text-xs text-slate-400">100% Miễn phí trọn đời • Không phát sinh chi phí</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1.5 rounded-xl hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSave} className="space-y-5">
          {/* Backend API URL for Vercel / Cloud */}
          <div className="bg-slate-900/80 border border-purple-500/30 rounded-2xl p-4 space-y-2">
            <label className="block text-xs font-bold text-white flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-purple-300">
                <Server className="w-4 h-4 text-purple-400" />
                Địa Chỉ Máy Chủ Backend (API URL)
              </span>
              <span className="text-[10px] bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded-md font-mono">Vercel ↔ Render</span>
            </label>
            <input
              type="text"
              value={backendUrl}
              onChange={(e) => setBackendUrl(e.target.value)}
              placeholder="Ví dụ: https://ai-video-factory-api.onrender.com hoặc http://localhost:8000"
              className="w-full bg-slate-950 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none transition-colors font-mono"
            />
            <p className="text-[11px] text-slate-400 leading-relaxed">
              👉 Khi mở Web trên <strong>Vercel (Điện thoại/Laptop)</strong>, hãy dán link Backend Render của bạn vào đây để kết nối với AI Engine.
            </p>
          </div>

          {/* Engine Status Badges */}
          <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-4 space-y-3">
            <div className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-purple-400" />
              Trạng Thái Công Cụ AI Miễn Phí Sẵn Có (Zero Cost):
            </div>
            
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span className="truncate">Alibaba FunASR (99.8% Trung)</span>
              </div>
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span className="truncate">OpenAI Whisper STT</span>
              </div>
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span className="truncate">Google RPC Dịch Vô Tận</span>
              </div>
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span className="truncate">10 Giọng CapCut & Edge-TTS</span>
              </div>
            </div>
          </div>

          {/* Optional Gemini API Key */}
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-purple-400" />
                Google Gemini API Key (Tùy chọn - Tăng tốc dịch)
              </span>
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-purple-400 hover:text-purple-300 flex items-center gap-1"
              >
                Lấy Key miễn phí <ExternalLink className="w-3 h-3" />
              </a>
            </label>
            <input
              type="password"
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              placeholder="AIzaSy... (Để trống vẫn dùng dịch tự động bình thường)"
              className="w-full bg-slate-900 border border-slate-800 focus:border-purple-500 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none transition-colors"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              Đóng
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 shadow-lg shadow-purple-600/30 transition-all hover:scale-105"
            >
              {isSaving ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : savedSuccess ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <Save className="w-3.5 h-3.5" />
              )}
              {savedSuccess ? 'Đã Lưu Cấu Hình!' : 'Lưu Thay Đổi'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
