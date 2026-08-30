import asyncio
import os
import json
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional
import subprocess

from app.core.config import settings
from app.core.credit_manager import credit_manager
from app.services.audio_extractor import audio_extractor
from app.services.transcriber import transcriber
from app.services.diarizer import diarizer
from app.services.translator import translator
from app.services.tts_engine import tts_engine
from app.services.timing_aligner import timing_aligner
from app.services.highlight_detector import highlight_detector
from app.services.smart_cropper import smart_cropper
from app.services.subtitle_generator import subtitle_generator
from app.services.content_generator import content_generator

class VideoFactoryPipeline:
    """
    AI Video Factory V2 Master Pipeline:
    - Kế thừa kiến trúc tối ưu từ autodub-local, VideoLingo và video-dubbing-system
    - Single-Pass Audio Decode & Direct Video Muxing (Tối đa tốc độ)
    - Rebuild Speaker Utterances (Gộp câu ngắt đoạn, đọc mượt mà tự nhiên)
    - In-Memory Timeline Engine & Strict Overlap Checker (Chống chồng giọng 100%)
    - Checkpointing & Fast Re-Dubbing (Lưu tiến trình, đổi giọng trong 2s)
    """
    
    def __init__(self):
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        task = self.active_tasks.get(task_id)
        if task:
            return task
        # Thử nạp từ checkpoint đĩa nếu server vừa restart
        ckpt_file = settings.OUTPUTS_DIR / task_id / "checkpoint.json"
        if ckpt_file.exists():
            try:
                with open(ckpt_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {
                        "task_id": task_id,
                        "status": "completed",
                        "progress": 100,
                        "stage": "completed",
                        "message": "Đã khôi phục tác vụ từ Checkpoint!",
                        "data": data
                    }
            except Exception:
                pass
        return {"status": "not_found"}

    def update_task_progress(self, task_id: str, progress: int, stage: str, message: str, data: Dict[str, Any] = None):
        if task_id in self.active_tasks:
            self.active_tasks[task_id].update({
                "progress": progress,
                "stage": stage,
                "message": message,
                "data": data or self.active_tasks[task_id].get("data", {})
            })

    async def run_pipeline(
        self,
        task_id: str,
        video_path: str,
        target_lang: str = "vi",
        source_lang: str = "auto",
        voice_mode: str = "solo",
        primary_voice_id: str = "vi-VN-NamMinhNeural_cinema",
        custom_prompt: str = None,
        speaker_voice_map: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Chạy toàn bộ pipeline xử lý video tự động V2
        """
        task_temp_dir = settings.TEMP_DIR / task_id
        task_out_dir = settings.OUTPUTS_DIR / task_id
        task_temp_dir.mkdir(parents=True, exist_ok=True)
        task_out_dir.mkdir(parents=True, exist_ok=True)

        self.active_tasks[task_id] = {
            "task_id": task_id,
            "status": "processing",
            "progress": 5,
            "stage": "init",
            "message": "Đang khởi tạo tác vụ và kiểm tra định dạng video...",
            "data": {}
        }

        try:
            # 1. Phân tích thông tin Media
            self.update_task_progress(task_id, 10, "media_info", "Đang trích xuất thông tin video (fps, độ dài, phân giải)...")
            media_info = audio_extractor.get_media_info(video_path)
            duration = media_info.get("duration", 60.0)
            
            # Trừ credit
            credit_manager.deduct_credits(round(duration / 60.0, 2))

            # 2. Tách Vocal & Lọc sạch tiếng cho ASR (Bỏ qua BGM nếu ở chế độ Solo)
            self.update_task_progress(task_id, 20, "audio_separation", "Đang trích xuất và lọc sạch âm thanh giọng nói cho AI...")
            need_bgm = (voice_mode != "solo")
            vocals_path, bgm_path = audio_extractor.separate_vocals_and_bgm(video_path, task_temp_dir, need_bgm=need_bgm)

            # 3. Whisper Speech-to-Text & Rebuild Speaker Utterances (autodub-local style)
            self.update_task_progress(task_id, 35, "transcription", "Đang nhận diện giọng nói và gộp câu thoại hoàn chỉnh...")
            raw_segments = transcriber.transcribe(vocals_path, source_lang=source_lang)
            diar_result = diarizer.process_speakers(
                raw_segments,
                target_lang=target_lang,
                voice_mode=voice_mode,
                primary_voice_id=primary_voice_id
            )
            speaker_profiles = diar_result["speakers"]
            segments = diar_result["segments"]
            
            # Ghi đè giọng đọc nếu user có cấu hình trước
            if speaker_voice_map:
                for spk, v_id in speaker_voice_map.items():
                    if spk in speaker_profiles:
                        speaker_profiles[spk]["voice_id"] = v_id

            # 4. Dịch thuật theo ngữ cảnh & đo độ dài câu (VideoLingo style)
            self.update_task_progress(task_id, 45, "translation", f"Đang dịch kịch bản sang ngôn ngữ đích ({target_lang})...")
            translated_segments = translator.translate_segments(segments, target_lang=target_lang, source_lang=source_lang)

            # 5. Sinh Giọng Đọc AI Đa Vai (TTS) Siêu Tốc (12 Parallel Streams)
            self.update_task_progress(task_id, 55, "tts_generation", f"Đang lồng tiếng AI {len(translated_segments)} câu thoại...")
            
            def on_tts_progress(completed: int, total: int):
                pct = 55 + int((completed / max(1, total)) * 15)
                self.update_task_progress(
                    task_id,
                    min(70, pct),
                    "tts_generation",
                    f"Đang lồng tiếng AI ({completed}/{total} câu thoại)..."
                )

            tts_segments = await tts_engine.generate_segment_audios(
                translated_segments,
                speaker_profiles,
                task_temp_dir,
                progress_callback=on_tts_progress
            )

            # 6. Căn Timing In-Memory & Mix Nhạc Nền (video-dubbing-system style)
            self.update_task_progress(task_id, 65, "audio_mixing", "Đang co giãn tốc độ giọng nói và hòa âm chuẩn xác trong RAM...")
            full_dub_voice = timing_aligner.build_full_dub_track(tts_segments, duration, task_temp_dir)
            mixed_audio_path = str(task_temp_dir / "final_mixed_audio.aac")
            # Tắt tiếng gốc (bgm_volume=0.0) để đảm bảo 100% âm thanh phát ra là tiếng dịch chuẩn
            timing_aligner.mix_dub_with_bgm(full_dub_voice, bgm_path, mixed_audio_path, bgm_volume=0.0, voice_volume=1.4)

            # 7. Render Video Full Đã Lồng Tiếng & Burn Phụ Đề Đã Dịch (Single-Pass Ultrafast)
            self.update_task_progress(task_id, 75, "render_full_video", "Đang lồng tiếng và chèn phụ đề đã dịch vào Video Full siêu tốc...")
            full_dubbed_video = str(task_out_dir / "full_dubbed_video.mp4")
            full_dubbed_clean = str(task_out_dir / "full_dubbed_video_clean.mp4")
            full_ass_path = str(task_temp_dir / "full_subtitles.ass")

            # 7a. Sinh phụ đề Cinema
            subtitle_generator.generate_ass_subtitles(tts_segments, full_ass_path, is_vertical=False, style_mode="cinema")
            clean_ass = full_ass_path.replace("\\", "/").replace(":", "\\:")

            # 7b. Single-Pass Direct Video Mux & Subtitle Burn
            render_cmd = [
                "ffmpeg", "-y",
                "-threads", "0",
                "-i", video_path,
                "-i", mixed_audio_path,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-vf", f"ass='{clean_ass}'",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "ultrafast",
                "-tune", "fastdecode",
                "-crf", "21",
                "-c:a", "aac",
                "-ar", "44100",
                "-ac", "2",
                "-b:a", "192k",
                "-disposition:a:0", "default",
                "-movflags", "+faststart",
                "-shortest",
                full_dubbed_video
            ]
            try:
                subprocess.run(render_cmd, capture_output=True, check=True)
            except Exception as e:
                print(f"[Pipeline] Single-pass burn error: {e}, using remux fallback...")
                fallback_cmd = [
                    "ffmpeg", "-y", "-threads", "0",
                    "-i", video_path, "-i", mixed_audio_path,
                    "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy",
                    "-c:a", "aac", "-ar", "44100", "-ac", "2",
                    "-disposition:a:0", "default",
                    "-movflags", "+faststart", "-shortest",
                    full_dubbed_video
                ]
                subprocess.run(fallback_cmd, capture_output=True, check=True)

            # 8. Tự Tạo Shorts 9:16 & Cắt Highlights Song Song (Multithreaded Parallel Render)
            self.update_task_progress(task_id, 85, "generate_shorts", "Đang phân tích đoạn viral, crop 9:16 và burn phụ đề Karaoke song song...")
            highlights = highlight_detector.detect_highlights(tts_segments, duration, user_prompt=custom_prompt)
            
            def render_single_short(h: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                try:
                    s_id = h["id"]
                    s_start = h["start_time"]
                    s_end = h["end_time"]
                    
                    short_segs = [s for s in tts_segments if s["start"] >= s_start and s["end"] <= s_end]
                    if not short_segs:
                        short_segs = [{"start": s_start, "end": s_end, "text": h["title"]}]
                        
                    short_ass = str(task_temp_dir / f"short_{s_id}.ass")
                    subtitle_generator.generate_ass_subtitles(short_segs, short_ass, offset_start=s_start, is_vertical=True, style_mode="karaoke")
                    
                    final_short_path = str(task_out_dir / f"short_viral_{s_id}.mp4")
                    face_center = smart_cropper.detect_face_centers(full_dubbed_video, s_start, s_end, sample_interval_sec=1.0)
                    
                    ok = smart_cropper.crop_and_burn_short(
                        full_dubbed_video, s_start, s_end, short_ass, final_short_path,
                        center_x_ratio=face_center, crf=21, preset="ultrafast"
                    )
                    if ok:
                        h["video_url"] = f"/storage/outputs/{task_id}/short_viral_{s_id}.mp4"
                        return h
                except Exception as ex:
                    print(f"[Pipeline] Short render error: {ex}")
                return None

            from concurrent.futures import ThreadPoolExecutor
            generated_shorts = []
            with ThreadPoolExecutor(max_workers=3) as executor:
                results = list(executor.map(render_single_short, highlights))
                for res in results:
                    if res:
                        generated_shorts.append(res)
                        credit_manager.add_shorts_count(1)

            # 9. Xuất file phụ đề SRT / TXT
            srt_vi_path = str(task_out_dir / "subtitles_vi.srt")
            srt_orig_path = str(task_out_dir / "subtitles_original.srt")
            srt_bilingual_path = str(task_out_dir / "subtitles_bilingual.srt")
            txt_vi_path = str(task_out_dir / "transcript_vi.txt")
            txt_orig_path = str(task_out_dir / "transcript_original.txt")

            subtitle_generator.generate_srt(tts_segments, srt_vi_path, mode="translated")
            subtitle_generator.generate_srt(tts_segments, srt_orig_path, mode="original")
            subtitle_generator.generate_srt(tts_segments, srt_bilingual_path, mode="bilingual")
            subtitle_generator.generate_txt(tts_segments, txt_vi_path, mode="translated")
            subtitle_generator.generate_txt(tts_segments, txt_orig_path, mode="original")

            # 10. Tạo 1 Video -> 10 Content Multiplier
            self.update_task_progress(task_id, 95, "content_generation", "Đang sinh trọn bộ 10 Tiêu đề, Captions, 30 Hashtags, Thumbnail concept...")
            content_pack = content_generator.generate_10x_content(tts_segments, custom_prompt=custom_prompt)

            # 11. Đóng gói ZIP tải về
            zip_filename = f"ai_video_factory_{task_id}.zip"
            zip_path = task_out_dir / zip_filename
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.exists(full_dubbed_video):
                    zipf.write(full_dubbed_video, arcname="full_dubbed_video.mp4")
                if os.path.exists(srt_vi_path):
                    zipf.write(srt_vi_path, arcname="subtitles/subtitles_vi.srt")
                if os.path.exists(srt_orig_path):
                    zipf.write(srt_orig_path, arcname="subtitles/subtitles_original.srt")
                if os.path.exists(srt_bilingual_path):
                    zipf.write(srt_bilingual_path, arcname="subtitles/subtitles_bilingual.srt")
                if os.path.exists(txt_vi_path):
                    zipf.write(txt_vi_path, arcname="subtitles/transcript_vi.txt")
                if os.path.exists(txt_orig_path):
                    zipf.write(txt_orig_path, arcname="subtitles/transcript_original.txt")
                for s in generated_shorts:
                    s_file = task_out_dir / f"short_viral_{s['id']}.mp4"
                    if s_file.exists():
                        zipf.write(s_file, arcname=f"shorts/short_viral_{s['id']}.mp4")
                content_json_str = json.dumps(content_pack, ensure_ascii=False, indent=2)
                zipf.writestr("1_video_10_content.json", content_json_str)

            result_data = {
                "task_id": task_id,
                "media_info": media_info,
                "speakers": speaker_profiles,
                "segments": tts_segments,
                "full_video_url": f"/storage/outputs/{task_id}/full_dubbed_video.mp4",
                "subtitles": {
                    "srt_vi": f"/storage/outputs/{task_id}/subtitles_vi.srt",
                    "srt_orig": f"/storage/outputs/{task_id}/subtitles_original.srt",
                    "srt_bilingual": f"/storage/outputs/{task_id}/subtitles_bilingual.srt",
                    "txt_vi": f"/storage/outputs/{task_id}/transcript_vi.txt",
                    "txt_orig": f"/storage/outputs/{task_id}/transcript_original.txt"
                },
                "shorts": generated_shorts,
                "content_pack": content_pack,
                "zip_download_url": f"/storage/outputs/{task_id}/{zip_filename}"
            }

            # 12. Lưu Checkpoint vĩnh viễn để hỗ trợ Resume & Re-dub tức thì
            ckpt_path = task_out_dir / "checkpoint.json"
            with open(ckpt_path, "w", encoding="utf-8") as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            self.active_tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "stage": "completed",
                "message": "Hoàn tất xử lý toàn bộ quy trình V2!",
                "data": result_data
            })
            return result_data

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.active_tasks[task_id].update({
                "status": "failed",
                "progress": 0,
                "stage": "error",
                "message": f"Lỗi trong quá trình xử lý: {str(e)}"
            })
            raise e

    async def re_dub(self, task_id: str, speaker_voice_map: Dict[str, str]) -> Dict[str, Any]:
        """
        Fast Re-Dubbing (Khôi phục từ Checkpoint và sinh giọng mới trong 2-3 giây):
        - Bỏ qua toàn bộ bước giải mã, Whisper và dịch thuật!
        - Tái sử dụng segments đã dịch, chỉ render lại TTS và muxing!
        """
        task = self.active_tasks.get(task_id)
        task_data = task.get("data") if task else None
        
        task_out_dir = settings.OUTPUTS_DIR / task_id
        task_temp_dir = settings.TEMP_DIR / task_id
        task_temp_dir.mkdir(parents=True, exist_ok=True)

        if not task_data:
            ckpt_file = task_out_dir / "checkpoint.json"
            if ckpt_file.exists():
                with open(ckpt_file, "r", encoding="utf-8") as f:
                    task_data = json.load(f)
            else:
                raise ValueError("Task không tồn tại hoặc chưa có checkpoint")

        video_path = str(settings.UPLOADS_DIR / f"{task_id}.mp4")
        if not os.path.exists(video_path):
            files = list(settings.UPLOADS_DIR.glob(f"{task_id}.*"))
            if files:
                video_path = str(files[0])

        speaker_profiles = task_data.get("speakers", {})
        for spk, v_id in speaker_voice_map.items():
            if spk in speaker_profiles:
                speaker_profiles[spk]["voice_id"] = v_id
                for lang_voices in settings.AVAILABLE_VOICES.values():
                    for v in lang_voices:
                        if v["id"] == v_id:
                            speaker_profiles[spk]["voice_name"] = v["name"]
                            break

        segments = task_data.get("segments", [])
        duration = task_data.get("media_info", {}).get("duration", 60.0)

        # 1. Sinh lại TTS với giọng mới siêu tốc (12 parallel streams)
        tts_segments = await tts_engine.generate_segment_audios(segments, speaker_profiles, task_temp_dir)

        # 2. Ghép dub track mới trong RAM
        full_dub_voice = timing_aligner.build_full_dub_track(tts_segments, duration, task_temp_dir)
        mixed_audio_path = str(task_temp_dir / "final_mixed_audio.aac")
        bgm_path = str(task_temp_dir / "bgm.wav")
        timing_aligner.mix_dub_with_bgm(full_dub_voice, bgm_path, mixed_audio_path, bgm_volume=0.0, voice_volume=1.4)

        # 3. Remux video full & burn phụ đề
        full_dubbed_video = str(task_out_dir / "full_dubbed_video.mp4")
        full_ass_path = str(task_temp_dir / "full_subtitles.ass")
        subtitle_generator.generate_ass_subtitles(tts_segments, full_ass_path, is_vertical=False, style_mode="cinema")
        clean_ass = full_ass_path.replace("\\", "/").replace(":", "\\:")

        render_cmd = [
            "ffmpeg", "-y",
            "-threads", "0",
            "-i", video_path,
            "-i", mixed_audio_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-vf", f"ass='{clean_ass}'",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            "-tune", "fastdecode",
            "-crf", "21",
            "-c:a", "aac",
            "-ar", "44100",
            "-ac", "2",
            "-b:a", "192k",
            "-disposition:a:0", "default",
            "-movflags", "+faststart",
            "-shortest",
            full_dubbed_video
        ]
        try:
            subprocess.run(render_cmd, capture_output=True, check=True)
        except Exception:
            fallback_cmd = [
                "ffmpeg", "-y", "-threads", "0",
                "-i", video_path, "-i", mixed_audio_path,
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy",
                "-c:a", "aac", "-ar", "44100", "-ac", "2",
                "-disposition:a:0", "default",
                "-movflags", "+faststart", "-shortest",
                full_dubbed_video
            ]
            subprocess.run(fallback_cmd, capture_output=True, check=True)

        task_data["speakers"] = speaker_profiles
        task_data["segments"] = tts_segments
        
        # Cập nhật Checkpoint
        ckpt_path = task_out_dir / "checkpoint.json"
        with open(ckpt_path, "w", encoding="utf-8") as f:
            json.dump(task_data, f, ensure_ascii=False, indent=2)

        if task_id in self.active_tasks:
            self.active_tasks[task_id]["data"] = task_data
        return task_data

pipeline = VideoFactoryPipeline()
