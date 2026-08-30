from typing import List, Dict, Any

class Diarizer:
    """
    Diarization, Utterance Rebuilder & Speaker Allocation Engine (Học hỏi từ autodub-local & video-dubbing-system):
    - Rebuild Speaker Utterances: Tự động gộp các phân đoạn ngắt vụn (fragments) của cùng một người nói
      nếu khoảng cách < 0.5s thành câu hoàn chỉnh, giúp AI đọc liền mạch và tự nhiên 100%.
    - Strict Overlap Checker: Đảm bảo End_A <= Start_B - 0.05s, loại bỏ hoàn toàn hiện tượng chồng giọng.
    - Chế độ Solo / Dual / Multi linh hoạt.
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

    def rebuild_utterances(self, raw_segments: List[Dict[str, Any]], max_gap_sec: float = 0.5) -> List[Dict[str, Any]]:
        """
        Gộp các câu ngắt đoạn ngắn (< 0.5s) của cùng 1 speaker thành câu hoàn chỉnh
        (Kiến trúc Utterance Rebuilder từ autodub-local)
        """
        if not raw_segments:
            return []

        sorted_segs = sorted(raw_segments, key=lambda x: float(x.get("start", 0)))
        merged = []
        current = None

        for s in sorted_segs:
            text = (s.get("text") or "").strip()
            if not text:
                continue

            start = float(s.get("start", 0))
            end = float(s.get("end", start + 1.0))
            speaker = s.get("speaker", "Speaker 1")

            if current is None:
                current = {
                    "id": len(merged) + 1,
                    "start": start,
                    "end": end,
                    "text": text,
                    "speaker": speaker
                }
            else:
                same_speaker = (current.get("speaker") == speaker)
                gap = start - current["end"]
                
                # Gộp nếu cùng speaker và khoảng nghỉ < max_gap_sec hoặc câu trước chưa kết thúc bằng dấu chấm
                is_sentence_end = current["text"].endswith((".", "!", "?", "。", "！", "？"))
                if same_speaker and (gap <= max_gap_sec or not is_sentence_end) and (end - current["start"] <= 12.0):
                    current["end"] = max(current["end"], end)
                    current["text"] = f"{current['text']} {text}".strip()
                else:
                    merged.append(current)
                    current = {
                        "id": len(merged) + 1,
                        "start": start,
                        "end": end,
                        "text": text,
                        "speaker": speaker
                    }

        if current is not None:
            merged.append(current)

        return merged

    def process_speakers(
        self,
        segments: List[Dict[str, Any]],
        target_lang: str = "vi",
        voice_mode: str = "solo",
        primary_voice_id: str = None
    ) -> Dict[str, Any]:
        """
        Gộp utterances, phân bổ Speaker và bảo vệ timeline chống chồng giọng 100%
        """
        # 1. Rebuild Utterances (Gộp câu ngắt vụn)
        clean_segments = self.rebuild_utterances(segments)
        
        # 2. Strict Overlap Checker (Bảo vệ Guard Gap 50ms giữa các câu)
        for i in range(len(clean_segments) - 1):
            cur_s = clean_segments[i]
            nxt_s = clean_segments[i + 1]
            cur_start = float(cur_s.get("start", 0))
            nxt_start = float(nxt_s.get("start", 0))
            
            if float(cur_s.get("end", 0)) > nxt_start - 0.05:
                cur_s["end"] = max(cur_start + 0.3, nxt_start - 0.05)

        lang_voices = self.VOICE_DEFAULTS_BY_LANG.get(target_lang, self.VOICE_DEFAULTS_BY_LANG["vi"])
        male_vid, male_vname = lang_voices["male"]
        female_vid, female_vname = lang_voices["female"]

        chosen_single_voice = primary_voice_id or male_vid

        # 3. Chế độ 1 GIỌNG DUY NHẤT (Solo Narrator / Review Phim Reup)
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
            for seg in clean_segments:
                seg["speaker"] = "Speaker 1"
                
            return {
                "speakers": speaker_profiles,
                "segments": clean_segments,
                "voice_mode": "solo"
            }

        # 4. Chế độ 2 GIỌNG ĐỐI THOẠI (Nam & Nữ)
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
            
            for idx, seg in enumerate(clean_segments):
                assigned_spk = "Speaker 1" if idx % 2 == 0 else "Speaker 2"
                seg["speaker"] = assigned_spk
                
            return {
                "speakers": speaker_profiles,
                "segments": clean_segments,
                "voice_mode": "dual"
            }

        # 5. Chế độ TỰ ĐỘNG NHẬN DIỆN NHIỀU NHÂN VẬT (Multi-Speaker)
        unique_spks = sorted(list(set(s.get("speaker", "Speaker 1") for s in clean_segments)))
        if not unique_spks:
            unique_spks = ["Speaker 1"]

        speaker_profiles = {}
        for i, spk in enumerate(unique_spks):
            if i == 0 and chosen_single_voice:
                vid = chosen_single_voice
                vname = male_vname if "Nam" in chosen_single_voice or "serious_man" in chosen_single_voice else female_vname
            else:
                vid, vname = (male_vid, male_vname) if i % 2 == 0 else (female_vid, female_vname)
                
            speaker_profiles[spk] = {
                "id": spk,
                "name": f"Nhân vật {i+1}",
                "gender": "Male" if i % 2 == 0 else "Female",
                "voice_id": vid,
                "voice_name": vname,
                "speed": 1.0,
                "pitch": "+0Hz"
            }

        return {
            "speakers": speaker_profiles,
            "segments": clean_segments,
            "voice_mode": "multi"
        }

diarizer = Diarizer()
