import React, { useState, useEffect } from 'react';
import { Play, Pause, Volume2, Download, User, Mic, Sparkles, Check, RefreshCw, Wand2 } from 'lucide-react';
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
            {fullVideoUrl && (
              <a
                href={fullVideoUrl}
                download="full_dubbed_video.mp4"
                className="flex items-center gap-1.5 text-xs bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 px-3 py-1.5 rounded-lg transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                Tải Video Full (1080p)
              </a>
            )}
          </div>

          <div className="aspect-video bg-black rounded-xl overflow-hidden border border-slate-800 relative shadow-inner">
            {fullVideoUrl ? (
              <video
                key={fullVideoUrl + (redubSuccess ? '_new' : '')}
                controls
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
                      <div className="flex items-center gap-2.5">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs ${
                          profile.gender === 'Female'
                            ? 'bg-pink-500/20 text-pink-300 border border-pink-500/30'
                            : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                        }`}>
                          {profile.name.includes('1') ? '👨' : profile.name.includes('2') ? '👩' : '👤'}
                        </div>
                        <div>
                          <div className="text-xs font-bold text-white">{profile.name} ({spkId})</div>
                        </div>
                      </div>

                      <button
                        onClick={() => handlePreviewVoice(currentVoiceId)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-purple-600/30 text-slate-300 hover:text-purple-300 border border-slate-700 transition-colors flex items-center gap-1 text-[11px]"
                        title="Nghe thử giọng"
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
