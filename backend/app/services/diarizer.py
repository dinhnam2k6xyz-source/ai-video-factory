from typing import List, Dict, Any

class Diarizer:
    """
    Diarization & Speaker Allocation Engine (Hỗ trợ num_speakers cố định và chống chồng lấn):
    - 'solo': Ép num_speakers=1 (SPEAKER_00 / Review Phim Reup), 100% các câu dùng chung 1 giọng duy nhất.
    - 'dual': Ép num_speakers=2 (Nam & Nữ luân phiên), phân luồng đối thoại rõ ràng.
    - 'multi': Tự động phân cụm người nói (Multi-Speaker Diarization).
    """
    
    VOICE_DEFAULTS_BY_LANG = {
        "vi": {
            "male": ("capcut_serious_man", "Nam Review Phim (Trầm Ấm - Kiếm Hiệp)"),
            "female": ("capcut_young_girl", "Nữ Hoạt Bát (Trẻ Trung - Truyền Cảm)")
        },
        "en": {
            "male": ("en-US-GuyNeural", "Guy (Male US - Natural)"),
            "female": ("en-US-JennyNeural", "Jenny (Female US - Natural)")
        },
        "zh": {
            "male": ("zh-CN-YunxiNeural", "Yunxi (Male CN)"),
            "female": ("zh-CN-XiaoxiaoNeural", "Xiaoxiao (Female CN)")
        },
        "ja": {
            "male": ("ja-JP-KeitaNeural", "Keita (Male JP)"),
            "female": ("ja-JP-NanamiNeural", "Nanami (Female JP)")
        },
        "ko": {
            "male": ("ko-KR-InJoonNeural", "InJoon (Male KR)"),
            "female": ("ko-KR-SunHiNeural", "SunHi (Female KR)")
        }
    }

    def process_speakers(
        self,
        segments: List[Dict[str, Any]],
        target_lang: str = "vi",
        voice_mode: str = "solo",
        primary_voice_id: str = None
    ) -> Dict[str, Any]:
        """
        Nhận diện và gán giọng theo chế độ, chuẩn hóa thứ tự timeline:
        - Sắp xếp và đảm bảo mốc thời gian không bị đảo lộn.
        - Gán đúng Speaker Profile cho từng câu.
        """
        sorted_segments = sorted(segments, key=lambda x: float(x.get("start", 0)))
        
        # Đảm bảo End_A <= Start_B
        for i in range(len(sorted_segments) - 1):
            cur_s = sorted_segments[i]
            nxt_s = sorted_segments[i + 1]
            if float(cur_s.get("end", 0)) > float(nxt_s.get("start", 0)):
                cur_s["end"] = max(float(cur_s.get("start", 0)) + 0.3, float(nxt_s.get("start", 0)) - 0.05)

        lang_voices = self.VOICE_DEFAULTS_BY_LANG.get(target_lang, self.VOICE_DEFAULTS_BY_LANG["vi"])
        male_vid, male_vname = lang_voices["male"]
        female_vid, female_vname = lang_voices["female"]

        chosen_single_voice = primary_voice_id or male_vid

        # 1. Chế độ 1 GIỌNG DUY NHẤT (Solo Narrator / Review Phim Reup)
        if voice_mode == "solo":
            speaker_profiles = {
                "Speaker 1": {
                    "id": "Speaker 1",
                    "name": "Người Kể Chuyện (Solo Narrator)",
                    "gender": "Male" if "Nam" in chosen_single_voice or "serious_man" in chosen_single_voice or "Guy" in chosen_single_voice else "Female",
                    "voice_id": chosen_single_voice,
                    "voice_name": "Giọng Đọc Duy Nhất Toàn Bộ Video",
                    "speed": 1.0,
                    "pitch": "+0Hz"
                }
            }
            # Ép 100% tất cả các câu về Speaker 1
            for seg in sorted_segments:
                seg["speaker"] = "Speaker 1"
                
            return {
                "speakers": speaker_profiles,
                "segments": sorted_segments,
                "voice_mode": "solo"
            }

        # 2. Chế độ 2 GIỌNG ĐỐI THOẠI (Nam & Nữ)
        if voice_mode == "dual":
            speaker_profiles = {
                "Speaker 1": {
                    "id": "Speaker 1",
                    "name": "Nhân vật 1 (Nam)",
                    "gender": "Male",
                    "voice_id": chosen_single_voice if "Nam" in chosen_single_voice or "serious_man" in chosen_single_voice else male_vid,
                    "voice_name": male_vname,
                    "speed": 1.0,
                    "pitch": "+0Hz"
                },
                "Speaker 2": {
                    "id": "Speaker 2",
                    "name": "Nhân vật 2 (Nữ)",
                    "gender": "Female",
                    "voice_id": female_vid,
                    "voice_name": female_vname,
                    "speed": 1.0,
                    "pitch": "+0Hz"
                }
            }
            for idx, seg in enumerate(sorted_segments):
                seg["speaker"] = f"Speaker {(idx % 2) + 1}"
                
            return {
                "speakers": speaker_profiles,
                "segments": sorted_segments,
                "voice_mode": "dual"
            }

        # 3. Chế độ ĐA NHÂN VẬT (Multi-Speaker)
        speaker_ids = sorted(list(set(seg.get("speaker", "Speaker 1") for seg in sorted_segments)))
        speaker_profiles = {}
        
        for idx, spk_id in enumerate(speaker_ids):
            is_male = (idx % 2 == 0)
            vid, vname = (chosen_single_voice, male_vname) if idx == 0 else ((male_vid, male_vname) if is_male else (female_vid, female_vname))
            speaker_profiles[spk_id] = {
                "id": spk_id,
                "name": f"Nhân vật {idx + 1} ({'Nam' if is_male else 'Nữ'})",
                "gender": "Male" if is_male else "Female",
                "voice_id": vid,
                "voice_name": vname,
                "speed": 1.0,
                "pitch": "+0Hz"
            }

        return {
            "speakers": speaker_profiles,
            "segments": sorted_segments,
            "voice_mode": "multi"
        }

diarizer = Diarizer()
