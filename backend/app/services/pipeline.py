import asyncio
import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, Callable, List
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
    """Master Pipeline điều phối toàn bộ chu trình xử lý video từ đầu đến cuối"""
    
    def __init__(self):
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        return self.active_tasks.get(task_id, {"status": "not_found"})

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
        Chạy toàn bộ pipeline xử lý video tự động
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

            # 2. Tách Vocal & Nhạc nền (BGM)
            self.update_task_progress(task_id, 20, "audio_separation", "Đang tách dải âm thanh giọng nói và nhạc nền (BGM)...")
            vocals_path, bgm_path = audio_extractor.separate_vocals_and_bgm(video_path, task_temp_dir)

            # 3. Whisper Speech-to-Text & Diarization
            self.update_task_progress(task_id, 35, "transcription", "Đang nhận diện giọng nói và phân loại nhân vật thoại...")
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

            # 4. Dịch thuật theo ngữ cảnh & đo độ dài câu
            self.update_task_progress(task_id, 45, "translation", f"Đang dịch kịch bản sang ngôn ngữ đích ({target_lang})...")
            translated_segments = translator.translate_segments(segments, target_lang=target_lang, source_lang=source_lang)

            # 5. Sinh Giọng Đọc AI Đa Vai (TTS) Siêu Tốc
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

            # 6. Căn Timing Tự Động & Mix Nhạc Nền (Loại bỏ hoàn toàn giọng gốc)
            self.update_task_progress(task_id, 65, "audio_mixing", "Đang co giãn tốc độ giọng nói và hòa âm chuẩn xác...")
            full_dub_voice = timing_aligner.build_full_dub_track(tts_segments, duration, task_temp_dir)
            mixed_audio_path = str(task_temp_dir / "final_mixed_audio.aac")
            # Tắt tiếng gốc (bgm_volume=0.0) để đảm bảo 100% âm thanh phát ra là tiếng dịch chuẩn
            timing_aligner.mix_dub_with_bgm(full_dub_voice, bgm_path, mixed_audio_path, bgm_volume=0.0, voice_volume=1.4)

            # 7. Render Video Full Đã Lồng Tiếng
            self.update_task_progress(task_id, 75, "render_full_video", "Đang render Video Full lồng tiếng mới...")
            full_dubbed_video = str(task_out_dir / "full_dubbed_video.mp4")
            full_ass_path = str(task_temp_dir / "full_subtitles.ass")
            subtitle_generator.generate_ass_subtitles(tts_segments, full_ass_path, is_vertical=False)
            
            # Ghép video hình ảnh gốc với audio lồng tiếng mới
            remux_cmd = [
                "ffmpeg", "-y",
                "-threads", "0",
                "-i", video_path,
                "-i", mixed_audio_path,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "copy",
                "-c:a", "aac",
                "-movflags", "+faststart",
                "-shortest",
                full_dubbed_video
            ]
            subprocess.run(remux_cmd, capture_output=True, check=True)

            # 8. Tự Tạo Shorts 9:16 & Cắt Highlights
            self.update_task_progress(task_id, 85, "generate_shorts", "Đang phân tích đoạn viral, crop 9:16 và burn phụ đề Karaoke...")
            highlights = highlight_detector.detect_highlights(tts_segments, duration, user_prompt=custom_prompt)
            
            generated_shorts = []
            for h in highlights:
                s_id = h["id"]
                s_start = h["start_time"]
                s_end = h["end_time"]
                
                # 8a. Nhận diện mặt và Crop 9:16
                cropped_short = str(task_temp_dir / f"short_{s_id}_cropped.mp4")
                face_center = smart_cropper.detect_face_centers(full_dubbed_video, s_start, s_end)
                smart_cropper.crop_to_shorts(full_dubbed_video, s_start, s_end, cropped_short, center_x_ratio=face_center)
                
                # 8b. Lọc segments trong khoảng thời gian của short và tạo phụ đề động
                short_segs = [s for s in tts_segments if s["start"] >= s_start and s["end"] <= s_end]
                if not short_segs:
                    short_segs = [{"start": s_start, "end": s_end, "text": h["title"]}]
                    
                short_ass = str(task_temp_dir / f"short_{s_id}.ass")
                subtitle_generator.generate_ass_subtitles(short_segs, short_ass, offset_start=s_start, is_vertical=True)
                
                # 8c. Burn Subtitle vào Short
                final_short_path = str(task_out_dir / f"short_viral_{s_id}.mp4")
                subtitle_generator.burn_subtitles(cropped_short, short_ass, final_short_path)
                
                h["video_url"] = f"/storage/outputs/{task_id}/short_viral_{s_id}.mp4"
                generated_shorts.append(h)
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
                # Ghi file JSON nội dung
                import json
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

            # Tự động dọn dẹp các file audio/video thô trung gian để tiết kiệm dung lượng ổ đĩa
            try:
                if task_temp_dir.exists():
                    shutil.rmtree(task_temp_dir, ignore_errors=True)
            except Exception:
                pass

            self.active_tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "stage": "completed",
                "message": "Hoàn tất xử lý toàn bộ quy trình!",
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
        """Đổi giọng đọc mới cho các nhân vật và render lại video thành phẩm trong 3-5 giây"""
        task = self.active_tasks.get(task_id)
        if not task or not task.get("data"):
            raise ValueError("Task không tồn tại hoặc chưa hoàn thành")

        task_data = task["data"]
        task_temp_dir = settings.TEMP_DIR / task_id
        task_out_dir = settings.OUTPUTS_DIR / task_id
        video_path = str(settings.UPLOADS_DIR / f"{task_id}.mp4")
        if not os.path.exists(video_path):
            files = list(settings.UPLOADS_DIR.glob(f"{task_id}.*"))
            if files:
                video_path = str(files[0])

        speaker_profiles = task_data.get("speakers", {})
        for spk, v_id in speaker_voice_map.items():
            if spk in speaker_profiles:
                speaker_profiles[spk]["voice_id"] = v_id
                # Tìm tên giọng
                for lang_voices in settings.AVAILABLE_VOICES.values():
                    for v in lang_voices:
                        if v["id"] == v_id:
                            speaker_profiles[spk]["voice_name"] = v["name"]
                            break

        segments = task_data.get("segments", [])
        duration = task_data.get("media_info", {}).get("duration", 60.0)

        # 1. Sinh lại TTS với giọng mới
        tts_segments = await tts_engine.generate_segment_audios(segments, speaker_profiles, task_temp_dir)

        # 2. Ghép dub track mới
        full_dub_voice = timing_aligner.build_full_dub_track(tts_segments, duration, task_temp_dir)
        mixed_audio_path = str(task_temp_dir / "final_mixed_audio.aac")
        bgm_path = str(task_temp_dir / "bgm.wav")
        timing_aligner.mix_dub_with_bgm(full_dub_voice, bgm_path, mixed_audio_path, bgm_volume=0.0, voice_volume=1.4)

        # 3. Remux video full
        full_dubbed_video = str(task_out_dir / "full_dubbed_video.mp4")
        remux_cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", mixed_audio_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            full_dubbed_video
        ]
        subprocess.run(remux_cmd, capture_output=True, check=True)

        task_data["speakers"] = speaker_profiles
        task_data["segments"] = tts_segments
        self.active_tasks[task_id]["data"] = task_data
        return task_data

pipeline = VideoFactoryPipeline()
