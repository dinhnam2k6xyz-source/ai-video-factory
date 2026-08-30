import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Dropzone } from './components/Dropzone';
import { PipelineProgress } from './components/PipelineProgress';
import { DubbingStudio } from './components/DubbingStudio';
import { ShortsGallery } from './components/ShortsGallery';
import { ContentMultiplier } from './components/ContentMultiplier';
import { PricingModal } from './components/PricingModal';
import { SettingsModal } from './components/SettingsModal';
import { TaskData, UserCredits } from './types';
import { Sparkles, Volume2, Scissors, FileText, ArrowLeft, AlertTriangle, RefreshCw } from 'lucide-react';
import { getApiUrl } from './config';

export const App: React.FC = () => {
  const [currentTask, setCurrentTask] = useState<TaskData | null>(null);
  const [activeTab, setActiveTab] = useState<'dubbing' | 'shorts' | 'content'>('dubbing');
  const [isPricingOpen, setIsPricingOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [credits, setCredits] = useState<UserCredits | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch user credit status on load
  const fetchCredits = async () => {
    try {
      const res = await fetch(getApiUrl('/api/credits/status'));
      if (res.ok) {
        const data = await res.json();
        setCredits(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchCredits();
  }, []);

  // Poll task progress (chỉ poll khi có task_id thật từ server, không poll ID tạm upload_)
  useEffect(() => {
    let interval: any;
    if (currentTask && currentTask.status === 'processing' && !currentTask.task_id.startsWith('upload_')) {
      interval = setInterval(async () => {
        try {
          const res = await fetch(getApiUrl(`/api/video/status/${currentTask.task_id}`));
          if (res.ok) {
            const data: TaskData = await res.json();
            setCurrentTask(data);
            if (data.status === 'completed' || data.status === 'failed') {
              clearInterval(interval);
              setIsLoading(false);
              fetchCredits();
            }
          }
        } catch (e) {
          console.error(e);
        }
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [currentTask]);

  const handleStartProcessing = async (params: {
    file?: File;
    url?: string;
    targetLang: string;
    sourceLang: string;
    voiceMode: string;
    primaryVoiceId: string;
    customPrompt: string;
  }) => {
    setIsLoading(true);

    if (params.file) {
      const file = params.file;
      const uploadId = `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;
      const tempId = `upload_${uploadId}`;
      
      setCurrentTask({
        task_id: tempId,
        status: 'processing',
        progress: 3,
        stage: 'uploading',
        message: 'Đang kết nối & tăng tốc tải lên đa luồng (0%)...'
      });

      // Tối ưu chunk size theo dung lượng file (5MB - 8MB)
      const CHUNK_SIZE = file.size > 50 * 1024 * 1024 ? 8 * 1024 * 1024 : 5 * 1024 * 1024;
      const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
      const CONCURRENCY = 3; // Tải song song 3 luồng cùng lúc -> Tăng tốc 300% - 500%

      let completedChunks = 0;
      let isAborted = false;
      let finalTaskId: string | null = null;

      const updateProgress = () => {
        const uploadPct = Math.round((completedChunks / totalChunks) * 100);
        const mbLoaded = (completedChunks * (CHUNK_SIZE / (1024 * 1024))).toFixed(1);
        const mbTotal = (file.size / (1024 * 1024)).toFixed(1);
        const pipelinePct = Math.max(3, Math.min(10, Math.round((uploadPct / 100) * 10)));

        setCurrentTask({
          task_id: tempId,
          status: 'processing',
          progress: pipelinePct,
          stage: 'uploading',
          message: `⚡ Đang tải siêu tốc (3 luồng song song): ${uploadPct}% (${Math.min(Number(mbLoaded), Number(mbTotal)).toFixed(1)}MB / ${mbTotal}MB)...`
        });
      };

      const uploadSingleChunk = async (index: number) => {
        if (isAborted) return;
        const start = index * CHUNK_SIZE;
        const end = Math.min(file.size, start + CHUNK_SIZE);
        const chunk = file.slice(start, end);

        const formData = new FormData();
        formData.append('chunk', chunk, file.name);
        formData.append('upload_id', uploadId);
        formData.append('chunk_index', String(index));
        formData.append('total_chunks', String(totalChunks));
        formData.append('filename', file.name);
        formData.append('target_lang', params.targetLang || 'vi');
        formData.append('source_lang', params.sourceLang || 'auto');
        formData.append('voice_mode', params.voiceMode || 'solo');
        formData.append('primary_voice_id', params.primaryVoiceId || 'capcut_serious_man');
        formData.append('custom_prompt', params.customPrompt || '');

        const res = await fetch(getApiUrl('/api/video/upload-chunk'), {
          method: 'POST',
          body: formData
        });

        if (!res.ok) {
          throw new Error(`Lỗi tải phần ${index + 1} (${res.status})`);
        }

        const resData = await res.json();
        completedChunks++;
        updateProgress();

        if (resData.completed && resData.task_id) {
          finalTaskId = resData.task_id;
        }
      };

      const runParallelUpload = async () => {
        try {
          const queue = Array.from({ length: totalChunks }, (_, i) => i);
          const workers = Array.from({ length: Math.min(CONCURRENCY, totalChunks) }, async () => {
            while (queue.length > 0 && !isAborted) {
              const chunkIdx = queue.shift();
              if (chunkIdx !== undefined) {
                await uploadSingleChunk(chunkIdx);
              }
            }
          });

          await Promise.all(workers);

          if (!isAborted) {
            const taskId = finalTaskId || uploadId.slice(0, 8);
            setCurrentTask({
              task_id: taskId,
              status: 'processing',
              progress: 10,
              stage: 'media_info',
              message: 'Tải lên hoàn tất! Đang phân tích video & audio...'
            });
          }
        } catch (err: any) {
          isAborted = true;
          setCurrentTask({
            task_id: tempId,
            status: 'failed',
            progress: 0,
            stage: 'error',
            message: err.message || 'Lỗi tải video lên máy chủ.'
          });
          setIsLoading(false);
        }
      };

      runParallelUpload();

    } else if (params.url) {
      const tempId = `url_${Date.now().toString().slice(-4)}`;
      setCurrentTask({
        task_id: tempId,
        status: 'processing',
        progress: 5,
        stage: 'downloading',
        message: 'Đang kết nối và tải video từ URL...'
      });

      try {
        const res = await fetch(getApiUrl('/api/video/process-url'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            video_url: params.url,
            target_lang: params.targetLang,
            source_lang: params.sourceLang,
            voice_mode: params.voiceMode,
            primary_voice_id: params.primaryVoiceId,
            custom_prompt: params.customPrompt
          })
        });
        const data = await res.json();
        if (data.task_id) {
          setCurrentTask({
            task_id: data.task_id,
            status: 'processing',
            progress: 8,
            stage: 'downloading',
            message: 'Đang tải video từ YouTube/TikTok...'
          });
        }
      } catch (e) {
        console.error(e);
        setCurrentTask({
          task_id: tempId,
          status: 'failed',
          progress: 0,
          stage: 'error',
          message: 'Lỗi kết nối tải video từ URL'
        });
        setIsLoading(false);
      }
    }
  };

  const handleUpgradeTier = async (tier: string) => {
    try {
      await fetch(getApiUrl('/api/credits/upgrade'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier })
      });
      fetchCredits();
    } catch (e) {
      console.error(e);
    }
  };

  const handleReset = () => {
    setCurrentTask(null);
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#090c13] text-slate-100 selection:bg-purple-600 selection:text-white">
      {/* Header */}
      <Header
        credits={credits}
        onOpenPricing={() => setIsPricingOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onReset={handleReset}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8">
        
        {/* State 1: Video Input & Dropzone */}
        {!currentTask && (
          <div>
            {/* Hero Section */}
            <div className="text-center max-w-3xl mx-auto my-8 sm:my-12">
              <div className="inline-flex items-center gap-2 bg-gradient-to-r from-purple-500/10 via-indigo-500/10 to-pink-500/10 border border-purple-500/30 px-4 py-1.5 rounded-full text-xs font-bold text-purple-300 mb-4 shadow-lg shadow-purple-500/10">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span>NỀN TẢNG SẢN XUẤT VIDEO TỰ ĐỘNG BẰNG AI</span>
              </div>
              <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white leading-tight sm:leading-tight">
                1 Video Đầu Vào → <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-amber-300 bg-clip-text text-transparent">Hàng Chục Ấn Phẩm Đa Kênh</span>
              </h1>
              <p className="text-sm sm:text-base text-slate-400 mt-4 leading-relaxed max-w-2xl mx-auto">
                Tự động tách lời thoại, dịch thuật, lồng tiếng đa vai chuẩn thời gian (Timing Sync), giữ nhạc nền và cắt Shorts 9:16 kèm phụ đề Karaoke nổi bật.
              </p>
            </div>

            <Dropzone onStartProcessing={handleStartProcessing} isLoading={isLoading} />
          </div>
        )}

        {/* State 2: Processing Progress */}
        {currentTask && currentTask.status === 'processing' && (
          <PipelineProgress task={currentTask} />
        )}

        {/* State 3: Error State */}
        {currentTask && currentTask.status === 'failed' && (
          <div className="max-w-2xl mx-auto my-12 bg-red-950/20 border border-red-500/40 rounded-3xl p-8 text-center shadow-2xl relative overflow-hidden">
            <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400 mx-auto mb-4">
              <AlertTriangle className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Đã Xảy Ra Sự Cố Khi Xử Lý</h3>
            <p className="text-sm text-red-300 mb-6 bg-red-950/60 p-4 rounded-xl font-mono text-left overflow-x-auto text-xs leading-relaxed border border-red-900/50">
              {currentTask.message || "Không thể hoàn tất quy trình xử lý video."}
            </p>
            <button
              onClick={handleReset}
              className="bg-slate-800 hover:bg-slate-700 text-white font-bold px-6 py-2.5 rounded-xl border border-slate-700 transition-all hover:scale-105"
            >
              Quay Lại & Thử Lại
            </button>
          </div>
        )}

        {/* State 4: Completed Results Studio */}
        {currentTask && currentTask.status === 'completed' && (
          <div className="space-y-6">
            
            {/* Top Navigation & Back Button */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-[#111625] border border-slate-800 rounded-2xl p-4 shadow-xl">
              <div className="flex items-center gap-3">
                <button
                  onClick={handleReset}
                  className="flex items-center gap-2 text-xs font-bold bg-slate-900 hover:bg-slate-800 text-slate-300 px-3 py-2 rounded-xl border border-slate-800 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Xử Lý Video Mới</span>
                </button>
                <div className="h-5 w-[1px] bg-slate-800 hidden sm:block"></div>
                <span className="text-xs text-slate-400">
                  Mã tác vụ: <span className="font-mono text-purple-300 font-bold">{currentTask.task_id}</span>
                </span>
              </div>

              {/* Studio Tabs */}
              <div className="flex items-center gap-1.5 bg-slate-950 p-1.5 rounded-xl border border-slate-800 w-full sm:w-auto">
                <button
                  onClick={() => setActiveTab('dubbing')}
                  className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                    activeTab === 'dubbing'
                      ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Volume2 className="w-3.5 h-3.5" />
                  <span>🎙️ Lồng Tiếng Đa Vai</span>
                </button>

                <button
                  onClick={() => setActiveTab('shorts')}
                  className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                    activeTab === 'shorts'
                      ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Scissors className="w-3.5 h-3.5" />
                  <span>✂️ Auto Shorts 9:16</span>
                </button>

                <button
                  onClick={() => setActiveTab('content')}
                  className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                    activeTab === 'content'
                      ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>💎 1 Video → 10 Content</span>
                </button>
              </div>
            </div>

            {/* Tab Contents */}
            {activeTab === 'dubbing' && (
              <DubbingStudio task={currentTask} />
            )}

            {activeTab === 'shorts' && (
              <ShortsGallery
                shorts={(currentTask.data && currentTask.data.shorts) || []}
                zipUrl={currentTask.data && currentTask.data.zip_download_url}
              />
            )}

            {activeTab === 'content' && (
              <ContentMultiplier
                content={(currentTask.data && currentTask.data.content_pack) || {
                  titles: [],
                  captions: [],
                  hashtags: [],
                  thumbnail_concepts: [],
                  blog_post: "",
                  key_takeaways: []
                }}
              />
            )}

          </div>
        )}

      </main>

      {/* Pricing Modal */}
      <PricingModal
        isOpen={isPricingOpen}
        onClose={() => setIsPricingOpen(false)}
        credits={credits}
        onUpgradeTier={handleUpgradeTier}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        AI Video Factory Engine © 2026 • Tự động hóa video marketing và phân phối đa nền tảng
      </footer>
    </div>
  );
};
