import requests
import json
import logging
import os
from datetime import datetime

VOICEVOX_BASE_URL = "http://localhost:50021"

# ログ設定
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, "voicevox_debug.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# キャラクターIDマッピング
SPEAKER_IDS = {
    "ずんだもん": 3,
    "四国めたん": 2,
    "春日部つむぎ": 8,
}

class VoicevoxAPI:
    def __init__(self, base_url=VOICEVOX_BASE_URL):
        self.base_url = base_url
        logger.info(f"VoicevoxAPI initialized: base_url={base_url}")

    def is_available(self):
        """VOICEVOXが起動しているか確認"""
        try:
            logger.debug(f"Checking VOICEVOX availability: {self.base_url}/version")
            response = requests.get(f"{self.base_url}/version", timeout=2)
            logger.info(f"VOICEVOX version check: status={response.status_code}, body={response.text[:100]}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"VOICEVOX not available: {e}")
            return False

    def get_audio_query(self, text, speaker_id):
        """音声合成用のクエリを生成"""
        try:
            url = f"{self.base_url}/audio_query"
            params = {"text": text, "speaker": speaker_id}
            logger.info(f"[audio_query] URL: {url}")
            logger.info(f"[audio_query] params: {params}")
            logger.debug(f"[audio_query] text: {text[:50]}...")

            response = requests.post(url, params=params, timeout=30)

            logger.info(f"[audio_query] status: {response.status_code}")
            logger.debug(f"[audio_query] headers: {dict(response.headers)}")

            if response.status_code == 200:
                query = response.json()
                logger.info(f"[audio_query] SUCCESS - query keys: {list(query.keys())}")
                return {"success": True, "query": query}
            else:
                logger.error(f"[audio_query] FAILED - status: {response.status_code}, body: {response.text[:200]}")
                return {"success": False, "error": f"Status {response.status_code}: {response.text[:100]}"}
        except Exception as e:
            logger.exception(f"[audio_query] EXCEPTION: {e}")
            return {"success": False, "error": str(e)}

    def synthesize(self, query, speaker_id):
        """音声を合成"""
        try:
            url = f"{self.base_url}/synthesis"
            params = {"speaker": speaker_id}
            data = json.dumps(query)

            logger.info(f"[synthesis] URL: {url}")
            logger.info(f"[synthesis] params: {params}")
            logger.debug(f"[synthesis] query data length: {len(data)} bytes")

            response = requests.post(url, params=params, data=data, timeout=60)

            logger.info(f"[synthesis] status: {response.status_code}")
            logger.debug(f"[synthesis] headers: {dict(response.headers)}")

            if response.status_code == 200:
                content_length = len(response.content)
                logger.info(f"[synthesis] SUCCESS - audio size: {content_length} bytes")
                return {"success": True, "audio": response.content}
            else:
                logger.error(f"[synthesis] FAILED - status: {response.status_code}, body: {response.text[:200]}")
                return {"success": False, "error": f"Status {response.status_code}: {response.text[:100]}"}
        except Exception as e:
            logger.exception(f"[synthesis] EXCEPTION: {e}")
            return {"success": False, "error": str(e)}

    def text_to_speech(self, text, character_name):
        """テキストから音声を生成"""
        logger.info(f"[text_to_speech] character: {character_name}, text: {text[:30]}...")

        speaker_id = SPEAKER_IDS.get(character_name)
        if speaker_id is None:
            logger.error(f"[text_to_speech] Unknown character: {character_name}")
            return {"success": False, "error": f"Unknown character: {character_name}"}

        logger.info(f"[text_to_speech] speaker_id: {speaker_id}")

        # クエリ生成
        query_result = self.get_audio_query(text, speaker_id)
        if not query_result["success"]:
            return query_result

        # 音声合成
        return self.synthesize(query_result["query"], speaker_id)

    def generate_skit_audio(self, skit_text, output_dir, char_mapping=None):
        """コント全体の音声を生成

        Args:
            skit_text: コントのテキスト
            output_dir: 出力ディレクトリ
            char_mapping: キャラクター名のマッピング（例: {"A": "ずんだもん", "B": "四国めたん"}）
        """
        import re

        logger.info(f"[generate_skit_audio] START - output_dir: {output_dir}")
        logger.info(f"[generate_skit_audio] char_mapping: {char_mapping}")
        logger.debug(f"[generate_skit_audio] skit_text:\n{skit_text[:500]}...")

        os.makedirs(output_dir, exist_ok=True)

        # セリフをパース（キャラ名: セリフ の形式）
        lines = skit_text.strip().split("\n")
        logger.info(f"[generate_skit_audio] Total lines: {len(lines)}")

        audio_files = []

        for i, line in enumerate(lines):
            logger.debug(f"[generate_skit_audio] Line {i}: {line[:50]}...")

            # キャラ名: セリフ の形式をパース
            match = re.match(r'^(.+?)[:：]\s*(.+)$', line)
            if not match:
                logger.debug(f"[generate_skit_audio] Line {i}: No match, skipping")
                continue

            character = match.group(1).strip()
            text = match.group(2).strip()

            logger.info(f"[generate_skit_audio] Line {i}: character={character}, text={text[:30]}...")

            # キャラクターマッピングを適用
            if char_mapping and character in char_mapping:
                mapped_character = char_mapping[character]
                logger.info(f"[generate_skit_audio] Line {i}: Mapping '{character}' -> '{mapped_character}'")
                character = mapped_character

            if character not in SPEAKER_IDS:
                logger.warning(f"[generate_skit_audio] Line {i}: Unknown character '{character}', skipping")
                continue

            # 音声生成
            result = self.text_to_speech(text, character)
            if not result["success"]:
                logger.error(f"[generate_skit_audio] Line {i}: FAILED - {result['error']}")
                return {"success": False, "error": f"Line {i+1}: {result['error']}"}

            # ファイル保存
            filename = f"{i:03d}_{character}.wav"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(result["audio"])

            logger.info(f"[generate_skit_audio] Line {i}: Saved to {filepath}")

            audio_files.append({
                "file": filepath,
                "character": character,
                "text": text
            })

        # セリフ情報をJSONファイルとして保存
        import json
        skit_info_path = os.path.join(output_dir, "skit_info.json")
        skit_info = []
        for audio in audio_files:
            skit_info.append({
                "file": os.path.basename(audio["file"]),
                "character": audio["character"],
                "text": audio["text"]
            })
        with open(skit_info_path, "w", encoding="utf-8") as f:
            json.dump(skit_info, f, ensure_ascii=False, indent=2)
        logger.info(f"[generate_skit_audio] Saved skit info to {skit_info_path}")

        logger.info(f"[generate_skit_audio] COMPLETE - {len(audio_files)} files generated")
        return {"success": True, "files": audio_files}
