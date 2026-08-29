import React from 'react';
import { Sparkles, Video, Zap, Settings } from 'lucide-react';
import { UserCredits } from '../types';

interface HeaderProps {
  credits: UserCredits | null;
  onOpenPricing: () => void;
  onOpenSettings: () => void;
  onReset: () => void;
}

export const Header: React.FC<HeaderProps> = ({ credits, onOpenPricing, onOpenSettings, onReset }) => {
  return (
    <header className="border-b border-slate-800/80 bg-[#0d121f]/90 backdrop-blur-md sticky top-0 z-50 px-6 py-4 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Logo & Brand */}
        <div className="flex items-center gap-3 cursor-pointer group" onClick={onReset}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/25 group-hover:scale-105 transition-transform">
            <Video className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                AI VIDEO FACTORY
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
                PRO ENGINE
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">1 Video → Multi Dubbing + Auto Shorts + 10x Content</p>
          </div>
        </div>

        {/* Right Action: Credits & Settings */}
        <div className="flex items-center gap-3">
          {credits && (
            <div className="hidden sm:flex items-center gap-3 bg-slate-900/90 border border-slate-800 rounded-xl px-4 py-2">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400 fill-amber-400 animate-pulse" />
                <span className="text-xs text-slate-400">Số dư Credit:</span>
                <span className="text-sm font-bold text-white">
                  {typeof credits.remaining_credits === 'number' ? credits.remaining_credits.toFixed(1) : credits.remaining_credits} phút
                </span>
              </div>
              <div className="h-4 w-[1px] bg-slate-700"></div>
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold text-emerald-400 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/20">
                  {credits.current_tier}
                </span>
              </div>
            </div>
          )}

          <button
            onClick={onOpenSettings}
            className="p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 transition-colors flex items-center gap-1.5 text-xs font-medium"
            title="Cài đặt API Key & Dịch vụ"
          >
            <Settings className="w-4 h-4 text-purple-400" />
            <span className="hidden sm:inline">Cài Đặt</span>
          </button>

          <button
            onClick={onOpenPricing}
            className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-lg shadow-purple-600/30 hover:shadow-purple-600/50 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Nâng Cấp Gói</span>
          </button>
        </div>

      </div>
    </header>
  );
};
