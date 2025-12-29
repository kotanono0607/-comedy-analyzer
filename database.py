import sqlite3
import os
from config import DATABASE_PATH

# スクリプトのディレクトリを基準にパスを解決
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Database:
    def __init__(self):
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self):
        schema_path = os.path.join(BASE_DIR, 'models', 'schema.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.conn.executescript(f.read())
        self.conn.commit()

    def add_author(self, name, channel_url=None):
        self.conn.execute("INSERT OR IGNORE INTO authors (name, channel_url) VALUES (?, ?)", (name, channel_url))
        self.conn.commit()
        result = self.conn.execute("SELECT id FROM authors WHERE name = ?", (name,)).fetchone()
        return result['id']

    def get_authors(self):
        return self.conn.execute("SELECT * FROM authors ORDER BY name").fetchall()

    def add_video(self, video_id, title, url, author_id):
        self.conn.execute("INSERT OR IGNORE INTO videos (video_id, title, url, author_id) VALUES (?, ?, ?, ?)", (video_id, title, url, author_id))
        self.conn.commit()
        result = self.conn.execute("SELECT id FROM videos WHERE video_id = ?", (video_id,)).fetchone()
        return result['id']

    def get_videos_by_author(self, author_id):
        return self.conn.execute("SELECT * FROM videos WHERE author_id = ? ORDER BY created_at DESC", (author_id,)).fetchall()

    def get_all_videos(self):
        return self.conn.execute("SELECT v.*, a.name as author_name FROM videos v LEFT JOIN authors a ON v.author_id = a.id ORDER BY v.created_at DESC").fetchall()

    def add_transcript(self, video_db_id, content):
        self.conn.execute("DELETE FROM transcripts WHERE video_id = ?", (video_db_id,))
        self.conn.execute("INSERT INTO transcripts (video_id, content) VALUES (?, ?)", (video_db_id, content))
        self.conn.commit()

    def get_transcript(self, video_db_id):
        result = self.conn.execute("SELECT * FROM transcripts WHERE video_id = ?", (video_db_id,)).fetchone()
        return result['content'] if result else None

    def add_analysis(self, video_db_id, raw_analysis):
        self.conn.execute("DELETE FROM analyses WHERE video_id = ?", (video_db_id,))
        self.conn.execute("INSERT INTO analyses (video_id, raw_analysis) VALUES (?, ?)", (video_db_id, raw_analysis))
        self.conn.commit()

    def get_analysis(self, video_db_id):
        return self.conn.execute("SELECT * FROM analyses WHERE video_id = ?", (video_db_id,)).fetchone()

    def get_analyses_by_author(self, author_id):
        return self.conn.execute("SELECT a.*, v.title, v.video_id as youtube_id FROM analyses a JOIN videos v ON a.video_id = v.id WHERE v.author_id = ? ORDER BY a.created_at DESC", (author_id,)).fetchall()

    def save_author_pattern(self, author_id, common_patterns, analysis_summary):
        self.conn.execute("DELETE FROM author_patterns WHERE author_id = ?", (author_id,))
        self.conn.execute("INSERT INTO author_patterns (author_id, common_patterns, analysis_summary) VALUES (?, ?, ?)", (author_id, common_patterns, analysis_summary))
        self.conn.commit()

    def get_author_pattern(self, author_id):
        return self.conn.execute("SELECT * FROM author_patterns WHERE author_id = ?", (author_id,)).fetchone()

    def close(self):
        self.conn.close()
