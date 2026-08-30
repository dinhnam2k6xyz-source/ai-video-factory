import React, { useState, useEffect } from 'react';
import { Play, Pause, Volume2, Download, User, Mic, Sparkles, Check, RefreshCw, Wand2, FileText, Globe, Layers } from 'lucide-react';
import { TaskData, SpeakerProfile } from '../types';
import { getApiUrl, getStorageUrl } from '../config';

interface DubbingStudioProps {
  task: TaskData;
}

export const DubbingStudio: React.FC<DubbingStudioProps> = ({ task }) => {
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);
  const [availableVoices, setAvailableVoices] = useState<any[]>([]);
  const [selectedVoices, setSelectedVoices] = useState<Record<string, string>>({});
  const [isRedubbing, setIsRedubbing] = useState(false);
  const [redubSuccess, setRedubSuccess] = useState(false);

  const data = task.data || {};
  const fullVideoUrl = getStorageUrl(data.full_video_url);
  const speakers = data.speakers || {};
  const segments = data.segments || [];

  // Nạp danh sách giọng đọc từ server
  useEffect(() => {
    fetch(getApiUrl('/api/voices/list'))
      .then(res => res.json())
      .then(d => {
        if (d.voices && d.voices.vi) {
          setAvailableVoices(d.voices.vi);
        }
      })
      .catch(e => console.error(e));
  }, []);

  // Khởi tạo state giọng chọn ban đầu
  useEffect(() => {
    const initialMap: Record<string, string> = {};
    Object.entries(speakers).forEach(([spkId, prof]) => {
      initialMap[spkId] = prof.voice_id;
    });
    setSelectedVoices(initialMap);
  }, [task]);

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
          text: 'Xin chào! Đây là giọng lồng tiếng AI chất lượng cao của AI Video Factory.',
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

  const handleApplyNewVoices = async () => {
    setIsRedubbing(true);
    setRedubSuccess(false);
    try {
      const res = await fetch(getApiUrl('/api/video/redub'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: task.task_id,
          speaker_voices: selectedVoices
        })
      });
      const result = await res.json();
      if (result.status === 'success') {
        task.data = result.data;
        setRedubSuccess(true);
        setTimeout(() => setRedubSuccess(false), 3000);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsRedubbing(false);
    }
  };

  // Helper format thời gian chuẩn SRT: HH:MM:SS,mmm
  const formatSrtTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    let msecs = Math.round((seconds - Math.floor(seconds)) * 1000);
    if (msecs >= 1000) msecs = 999;
    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')},${String(msecs).padStart(3, '0')}`;
  };

  // Tải xuống file SRT (Tiếng Việt / Gốc / Song Ngữ)
  const handleDownloadSrt = (mode: 'vi' | 'orig' | 'bilingual') => {
    let content = '';
    let idx = 1;
    segments.forEach((seg: any) => {
      const start = Number(seg.start) || 0;
      let end = Number(seg.end) || 0;
      if (end <= start) end = start + 1.0;
      const viText = (seg.translated_text || seg.text || '').trim();
      const origText = (seg.original_text || seg.text || '').trim();
      
      let text = viText;
      if (mode === 'orig') text = origText;
      else if (mode === 'bilingual') text = `${viText}\n${origText}`;

      if (text) {
        content += `${idx}\n${formatSrtTime(start)} --> ${formatSrtTime(end)}\n${text}\n\n`;
        idx++;
      }
    });

    const filename = mode === 'vi' ? `phu_de_tieng_viet_${task.task_id}.srt` : mode === 'orig' ? `phu_de_goc_${task.task_id}.srt` : `phu_de_song_ngu_${task.task_id}.srt`;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Tải xuống file TXT văn bản lời thoại
  const handleDownloadTxt = (mode: 'vi' | 'orig' | 'bilingual') => {
    let content = `AI VIDEO FACTORY - VĂN BẢN LỜI THOẠI & PHỤ ĐỀ\nTask ID: ${task.task_id}\nThời lượng: ${data.media_info?.duration?.toFixed(1) || 0}s\nTổng số câu: ${segments.length}\n${'='.repeat(50)}\n\n`;
    segments.forEach((seg: any) => {
      const start = Number(seg.start) || 0;
      const mins = Math.floor(start / 60);
      const secs = Math.floor(start % 60);
      const timeTag = `[${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}]`;
      const spk = seg.speaker || 'Speaker 1';
      const viText = (seg.translated_text || seg.text || '').trim();
      const origText = (seg.original_text || seg.text || '').trim();
      
      let text = viText;
      if (mode === 'orig') text = origText;
      else if (mode === 'bilingual') text = `${viText} (${origText})`;

      if (text) {
        content += `${timeTag} [${spk}]: ${text}\n\n`;
      }
    });

    const filename = mode === 'vi' ? `loi_thoai_tieng_viet_${task.task_id}.txt` : mode === 'orig' ? `loi_thoai_goc_${task.task_id}.txt` : `loi_thoai_song_ngu_${task.task_id}.txt`;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      {/* Top Banner: Video Player & Speaker Profiles */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left: Video Player */}
        <div className="lg:col-span-7 bg-[#111625] border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              Video Hoàn Chỉnh Đã Lồng Tiếng Việt & Căn Timing
            </h3>
            {/* Top Download Actions */}
            <div className="flex items-center gap-2">
              {fullVideoUrl && (
                <a
                  href={fullVideoUrl}
                  download={`full_dubbed_video_${task.task_id}.mp4`}
                  className="flex items-center gap-1.5 text-xs bg-purple-600/25 hover:bg-purple-600/40 text-purple-200 border border-purple-500/40 px-3 py-1.5 rounded-lg transition-all font-bold shadow-sm"
                >
                  <Download className="w-3.5 h-3.5" />
                  Tải Video Full (1080p)
                </a>
              )}
              {data.zip_download_url && (
                <a
                  href={getStorageUrl(data.zip_download_url)}
                  download={`ai_video_factory_${task.task_id}.zip`}
                  className="flex items-center gap-1.5 text-xs bg-emerald-600/25 hover:bg-emerald-600/40 text-emerald-200 border border-emerald-500/40 px-3 py-1.5 rounded-lg transition-all font-bold shadow-sm"
                >
                  <Download className="w-3.5 h-3.5" />
                  Tải Trọn Gói (.ZIP)
                </a>
              )}
            </div>
          </div>

          <div className="aspect-video bg-black rounded-xl overflow-hidden border border-slate-800 relative shadow-inner">
            {fullVideoUrl ? (
              <video
                key={fullVideoUrl + (redubSuccess ? '_new' : '')}
                controls
                playsInline
                src={fullVideoUrl}
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-2">
                <Volume2 className="w-8 h-8 opacity-40 animate-pulse" />
                <span className="text-xs">Đang nạp dữ liệu video...</span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Speaker Casting Profiles with Interactive Selector */}
        <div className="lg:col-span-5 bg-[#111625] border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Mic className="w-4 h-4 text-indigo-400" />
                Dàn Giọng Lồng Tiếng Đa Vai ({Object.keys(speakers).length} Nhân vật)
              </h3>
              <span className="text-[10px] bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded-md font-bold">
                Tùy Chọn Đa Dạng
              </span>
            </div>

            <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
              {Object.entries(speakers).map(([spkId, profile]) => {
                const currentVoiceId = selectedVoices[spkId] || profile.voice_id;
                return (
                  <div
                    key={spkId}
                    className="bg-slate-900/80 border border-slate-800 hover:border-purple-500/40 rounded-xl p-3.5 transition-all space-y-2.5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center font-bold text-white text-xs">
                          {spkId.replace('SPEAKER_', 'S')}
                        </div>
                        <div>
                          <div className="text-xs font-bold text-white">{profile.name || spkId}</div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            {profile.gender === 'male' ? 'Nam' : 'Nữ'} • {profile.accent || 'Miền Bắc'}
                          </div>
                        </div>
                      </div>

                      {/* Preview Button */}
                      <button
                        onClick={() => handlePreviewVoice(currentVoiceId)}
                        className="flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-purple-300 border border-slate-700 transition-colors"
                      >
                        {playingVoiceId === currentVoiceId ? (
                          <Pause className="w-3.5 h-3.5 text-purple-400 animate-pulse" />
                        ) : (
                          <Volume2 className="w-3.5 h-3.5" />
                        )}
                        <span>Nghe thử</span>
                      </button>
                    </div>

                    {/* Voice Select Dropdown */}
                    <div>
                      <select
                        value={currentVoiceId}
                        onChange={(e) => setSelectedVoices({ ...selectedVoices, [spkId]: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500"
                      >
                        {availableVoices.map((v) => (
                          <option key={v.id} value={v.id}>
                            {v.tag ? `[${v.tag}] ` : ''}{v.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action button: Apply voices */}
          <div className="mt-4 pt-3 border-t border-slate-800">
            <button
              onClick={handleApplyNewVoices}
              disabled={isRedubbing}
              className={`w-full py-2.5 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all ${
                redubSuccess
                  ? 'bg-emerald-600 text-white'
                  : isRedubbing
                  ? 'bg-slate-800 text-slate-400 cursor-wait'
                  : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-600/25'
              }`}
            >
              {isRedubbing ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Đang Render Lại Giọng Mới...</span>
                </>
              ) : redubSuccess ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>Đã Cập Nhật Giọng Mới Thành Công!</span>
                </>
              ) : (
                <>
                  <Wand2 className="w-3.5 h-3.5" />
                  <span>Áp Dụng Giọng Mới & Render Lại Lồng Tiếng</span>
                </>
              )}
            </button>
          </div>
        </div>

      </div>

      {/* 📥 Subtitle & Transcript Download Section */}
      <div className="bg-[#111625] border border-purple-500/30 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                Tải Xuống Phụ Đề & Văn Bản Lời Thoại (SRT / TXT)
              </h3>
              <p className="text-xs text-slate-400">
                Tương thích 100% với YouTube, CapCut, Adobe Premiere, DaVinci Resolve
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] bg-slate-900 border border-slate-700 text-slate-300 px-2.5 py-1 rounded-lg font-mono font-bold">
              {segments.length} Câu thoại
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* SRT Vietnamese */}
          <button
            onClick={() => handleDownloadSrt('vi')}
            className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-purple-500 hover:bg-purple-600/10 text-white transition-all group shadow-sm hover:scale-[1.02]"
          >
            <div className="flex items-center gap-2.5 text-left">
              <span className="px-2 py-1 rounded-lg bg-purple-500/20 text-purple-400 font-black text-xs font-mono">SRT</span>
              <div>
                <div className="text-xs font-bold text-slate-200 group-hover:text-purple-300">Phụ Đề Tiếng Việt</div>
                <div className="text-[10px] text-slate-400">Chuẩn .SRT có mốc giờ</div>
              </div>
            </div>
            <Download className="w-4 h-4 text-slate-400 group-hover:text-purple-400" />
          </button>

          {/* SRT Original */}
          <button
            onClick={() => handleDownloadSrt('orig')}
            className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-indigo-500 hover:bg-indigo-600/10 text-white transition-all group shadow-sm hover:scale-[1.02]"
          >
            <div className="flex items-center gap-2.5 text-left">
              <span className="px-2 py-1 rounded-lg bg-indigo-500/20 text-indigo-400 font-black text-xs font-mono">SRT</span>
              <div>
                <div className="text-xs font-bold text-slate-200 group-hover:text-indigo-300">Phụ Đề Ngôn Ngữ Gốc</div>
                <div className="text-[10px] text-slate-400">Tiếng Trung / Anh / Nhật</div>
              </div>
            </div>
            <Download className="w-4 h-4 text-slate-400 group-hover:text-indigo-400" />
          </button>

          {/* SRT Bilingual */}
          <button
            onClick={() => handleDownloadSrt('bilingual')}
            className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-emerald-500 hover:bg-emerald-600/10 text-white transition-all group shadow-sm hover:scale-[1.02]"
          >
            <div className="flex items-center gap-2.5 text-left">
              <span className="px-2 py-1 rounded-lg bg-emerald-500/20 text-emerald-400 font-black text-xs font-mono">SRT</span>
              <div>
                <div className="text-xs font-bold text-slate-200 group-hover:text-emerald-300">Phụ Đề Song Ngữ</div>
                <div className="text-[10px] text-slate-400">Việt + Gốc 2 dòng</div>
              </div>
            </div>
            <Download className="w-4 h-4 text-slate-400 group-hover:text-emerald-400" />
          </button>

          {/* TXT Transcript */}
          <button
            onClick={() => handleDownloadTxt('vi')}
            className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-amber-500 hover:bg-amber-600/10 text-white transition-all group shadow-sm hover:scale-[1.02]"
          >
            <div className="flex items-center gap-2.5 text-left">
              <span className="px-2 py-1 rounded-lg bg-amber-500/20 text-amber-400 font-black text-xs font-mono">TXT</span>
              <div>
                <div className="text-xs font-bold text-slate-200 group-hover:text-amber-300">Văn Bản Lời Thoại</div>
                <div className="text-[10px] text-slate-400">Kèm tên nhân vật & giờ</div>
              </div>
            </div>
            <Download className="w-4 h-4 text-slate-400 group-hover:text-amber-400" />
          </button>
        </div>
      </div>

      {/* Bottom: Timeline Transcript & Subtitle Editor */}
      <div className="bg-[#111625] border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            📝 Kịch Bản Dịch & Timeline Chi Tiết ({segments.length} câu thoại)
          </h3>
          <span className="text-xs text-slate-400">Tự động đồng bộ với mốc thời gian video</span>
        </div>

        <div className="space-y-2.5 max-h-[400px] overflow-y-auto pr-2">
          {segments.map((seg) => (
            <div
              key={seg.id}
              className="bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 rounded-xl p-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-[11px] font-bold text-purple-400 bg-purple-950/50 border border-purple-800/40 px-2 py-1 rounded-md">
                  {seg.start.toFixed(1)}s - {seg.end.toFixed(1)}s
                </span>
                <span className="text-[11px] font-bold text-slate-400 bg-slate-800 px-2 py-1 rounded-md">
                  {seg.speaker}
                </span>
              </div>

              <div className="flex-1 text-sm text-slate-200">
                <span className="font-semibold text-white">
                  {seg.translated_text || seg.text}
                </span>
                {seg.translated_text && seg.text !== seg.translated_text && (
                  <div className="text-xs text-slate-500 mt-0.5 italic">
                    Gốc: "{seg.text}"
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
