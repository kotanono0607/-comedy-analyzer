import requests
import json

VOICEVOX_BASE_URL = "http://localhost:50021"

# キャラクターIDマッピング
SPEAKER_IDS = {
    "ずんだもん": 3,
    "四国めたん": 2,
    "春日部つむぎ": 8,
}

class VoicevoxAPI:
    def __init__(self, base_url=VOICEVOX_BASE_URL):
        self.base_url = base_url

    def is_available(self):
        """VOICEVOXが起動しているか確認"""
        try:
            response = requests.get(f"{self.base_url}/version", timeout=2)
            return response.status_code == 200
        except:
            return False

    def get_audio_query(self, text, speaker_id):
        """音声合成用のクエリを生成"""
        try:
            response = requests.post(
                f"{self.base_url}/audio_query",
                params={"text": text, "speaker": speaker_id},
                timeout=30
            )
            if response.status_code == 200:
                return {"success": True, "query": response.json()}
            else:
                return {"success": False, "error": f"Status {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def synthesize(self, query, speaker_id):
        """音声を合成"""
        try:
            response = requests.post(
                f"{self.base_url}/synthesis",
                params={"speaker": speaker_id},
                headers={"Content-Type": "application/json"},
                data=json.dumps(query),
                timeout=60
            )
            if response.status_code == 200:
                return {"success": True, "audio": response.content}
            else:
                return {"success": False, "error": f"Status {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def text_to_speech(self, text, character_name):
        """テキストから音声を生成"""
        speaker_id = SPEAKER_IDS.get(character_name)
        if speaker_id is None:
            return {"success": False, "error": f"Unknown character: {character_name}"}

        # クエリ生成
        query_result = self.get_audio_query(text, speaker_id)
        if not query_result["success"]:
            return query_result

        # 音声合成
        return self.synthesize(query_result["query"], speaker_id)

    def generate_skit_audio(self, skit_text, output_dir):
        """コント全体の音声を生成"""
        import os
        import re

        os.makedirs(output_dir, exist_ok=True)

        # セリフをパース（キャラ名: セリフ の形式）
        lines = skit_text.strip().split("\n")
        audio_files = []

        for i, line in enumerate(lines):
            # キャラ名: セリフ の形式をパース
            match = re.match(r'^(.+?)[:：]\s*(.+)$', line)
            if not match:
                continue

            character = match.group(1).strip()
            text = match.group(2).strip()

            if character not in SPEAKER_IDS:
                continue

            # 音声生成
            result = self.text_to_speech(text, character)
            if not result["success"]:
                return {"success": False, "error": f"Line {i+1}: {result['error']}"}

            # ファイル保存
            filename = f"{i:03d}_{character}.wav"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(result["audio"])

            audio_files.append({
                "file": filepath,
                "character": character,
                "text": text
            })

        return {"success": True, "files": audio_files}
