import React, { useState, useEffect } from 'react';
import { CheckCircle2, Loader2, Sparkles, AlertCircle, Film, Mic, Globe, Volume2, Scissors, FileText, Clock, Zap } from 'lucide-react';
import { TaskData } from '../types';

interface PipelineProgressProps {
  task: TaskData;
}

export const PipelineProgress: React.FC<PipelineProgressProps> = ({ task }) => {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Bộ đếm thời gian thực
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m > 0 ? `${m}m ` : ''}${s}s`;
  };

  // Ước tính thời gian còn lại
  const estimateRemaining = () => {
    if (task.progress <= 5) return '~25s';
    if (task.progress >= 95) return '~3s';
    const totalEst = (elapsedSeconds / (task.progress / 100));
    const rem = Math.max(2, Math.round(totalEst - elapsedSeconds));
    return `~${rem}s`;
  };

  const steps = [
    { key: 'media_info', label: '1. Phân Tích Video & BGM', icon: Film, threshold: 20 },
    { key: 'transcription', label: '2. Whisper Bóc Sub & Diarization', icon: Mic, threshold: 35 },
    { key: 'translation', label: '3. Dịch Thuật Kịch Bản', icon: Globe, threshold: 45 },
    { key: 'tts_generation', label: '4. Lồng Tiếng AI Đa Vai', icon: Volume2, threshold: 60 },
    { key: 'audio_mixing', label: '5. Căn Timing & Hòa Âm', icon: Sparkles, threshold: 75 },
    { key: 'generate_shorts', label: '6. Tự Tạo Shorts 9:16 Viral', icon: Scissors, threshold: 85 },
    { key: 'content_generation', label: '7. Sinh 10x Content Pack', icon: FileText, threshold: 95 },
  ];

  const currentPercent = Math.min(100, Math.max(5, task.progress || 5));

  return (
    <div className="max-w-4xl mx-auto my-8 bg-[#111625] border border-purple-500/40 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-purple-600/15 rounded-full blur-3xl pointer-events-none animate-pulse"></div>
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>

      {/* Top Header: Title & Big Percentage Ticker */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6 mb-6 relative">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <div className="w-8 h-8 rounded-xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center">
              <Zap className="w-4 h-4 text-purple-400 animate-bounce" />
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
              AI Factory Đang Sản Xuất Video...
            </h2>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span>Mã tác vụ: <span className="font-mono text-purple-300 font-bold">{task.task_id}</span></span>
            <span>•</span>
            <span className="flex items-center gap-1 text-slate-300">
              <Clock className="w-3.5 h-3.5 text-purple-400" />
              Đã chạy: <strong className="text-white">{formatTime(elapsedSeconds)}</strong> (Còn lại: <strong className="text-emerald-400">{estimateRemaining()}</strong>)
            </span>
          </div>
        </div>

        {/* Big Animated Percentage Display */}
        <div className="flex items-center gap-3 bg-slate-900/90 border border-purple-500/40 px-5 py-3 rounded-2xl shadow-xl shadow-purple-950/50">
          <div className="text-right">
            <div className="text-3xl sm:text-4xl font-black bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-300 bg-clip-text text-transparent tracking-tight">
              {currentPercent}%
            </div>
            <div className="text-[10px] uppercase font-bold text-purple-300 tracking-wider">
              {task.stage ? `Giai đoạn: ${task.stage}` : 'Đang xử lý'}
            </div>
          </div>
        </div>
      </div>

      {/* Main Animated Progress Bar with Glowing Shimmer */}
      <div className="mb-6 space-y-2">
        <div className="flex items-center justify-between text-xs font-bold text-slate-400">
          <span className="flex items-center gap-1.5 text-purple-300">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
            Tiến độ hoàn thành:
          </span>
          <span className="text-white font-mono">{currentPercent} / 100%</span>
        </div>

        <div className="w-full bg-slate-950 rounded-full h-4 p-0.5 border border-slate-800/90 overflow-hidden shadow-inner relative">
          <div
            className="bg-gradient-to-r from-indigo-600 via-purple-500 to-pink-500 h-full rounded-full transition-all duration-700 ease-out relative"
            style={{ width: `${currentPercent}%` }}
          >
            {/* Shimmer animation */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
            {/* Glow Head point */}
            <div className="absolute right-0 top-0 bottom-0 w-2 bg-white rounded-full shadow-[0_0_12px_#fff]"></div>
          </div>
        </div>
      </div>

      {/* Live Status Log Message */}
      <div className="flex items-center gap-3 bg-slate-950/90 border border-slate-800 rounded-2xl px-5 py-3.5 mb-8 shadow-md">
        <Loader2 className="w-4 h-4 text-purple-400 animate-spin flex-shrink-0" />
        <span className="text-xs sm:text-sm font-semibold text-slate-200 truncate">
          {task.message || "Đang thực thi chu trình AI Video Factory..."}
        </span>
      </div>

      {/* Step Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        {steps.map((step, idx) => {
          const isDone = (task.progress || 0) >= step.threshold || task.status === 'completed';
          const isCurrent = (task.progress || 0) < step.threshold && (idx === 0 || (task.progress || 0) >= steps[idx - 1].threshold);
          const Icon = step.icon;

          return (
            <div
              key={step.key}
              className={`p-3.5 rounded-2xl border transition-all ${
                isDone
                  ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300'
                  : isCurrent
                  ? 'bg-purple-600/20 border-purple-500 text-purple-200 shadow-lg shadow-purple-600/20 scale-[1.02]'
                  : 'bg-slate-900/40 border-slate-800 text-slate-500'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className={`p-2 rounded-xl ${isDone ? 'bg-emerald-500/20 text-emerald-400' : isCurrent ? 'bg-purple-500/30 text-purple-300' : 'bg-slate-800 text-slate-500'}`}>
                  <Icon className="w-4 h-4" />
                </div>
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
                ) : (
                  <div className="w-2 h-2 rounded-full bg-slate-700"></div>
                )}
              </div>
              <div className="text-xs font-bold truncate">{step.label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
