import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import threading
import time

# 音声再生用（pygameを優先、なければwinsound）
try:
    import pygame
    pygame.mixer.init()
    AUDIO_BACKEND = "pygame"
except ImportError:
    try:
        import winsound
        AUDIO_BACKEND = "winsound"
    except ImportError:
        AUDIO_BACKEND = None


class SkitPlayer:
    """コント再生プレイヤーウィンドウ"""

    def __init__(self, parent=None, audio_dir=None, skit_text=None):
        self.parent = parent
        self.audio_dir = audio_dir
        self.skit_text = skit_text
        self.audio_files = []
        self.current_index = 0
        self.is_playing = False
        self.play_thread = None

        # ウィンドウ作成
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()

        self.window.title("コント再生プレイヤー")
        self.window.geometry("800x600")
        self.window.configure(bg="#1a1a2e")

        self.setup_ui()

        # 音声ファイルがあれば読み込み
        if audio_dir:
            self.load_audio_files(audio_dir)

    def setup_ui(self):
        """UIを構築"""
        # 上部: 立ち絵エリア（後で実装用のプレースホルダー）
        self.character_frame = tk.Frame(self.window, bg="#1a1a2e", height=300)
        self.character_frame.pack(fill=tk.X, padx=20, pady=20)
        self.character_frame.pack_propagate(False)

        # 立ち絵プレースホルダー（左右に配置）
        self.char_a_label = tk.Label(
            self.character_frame,
            text="【キャラA】\n立ち絵エリア",
            bg="#2a2a4e",
            fg="#888888",
            font=("Arial", 14),
            width=20,
            height=10
        )
        self.char_a_label.pack(side=tk.LEFT, padx=20, pady=10)

        self.char_b_label = tk.Label(
            self.character_frame,
            text="【キャラB】\n立ち絵エリア",
            bg="#2a2a4e",
            fg="#888888",
            font=("Arial", 14),
            width=20,
            height=10
        )
        self.char_b_label.pack(side=tk.RIGHT, padx=20, pady=10)

        # 中央: 字幕エリア
        self.subtitle_frame = tk.Frame(self.window, bg="#000000", height=120)
        self.subtitle_frame.pack(fill=tk.X, padx=20, pady=10)
        self.subtitle_frame.pack_propagate(False)

        self.speaker_label = tk.Label(
            self.subtitle_frame,
            text="",
            bg="#000000",
            fg="#ffcc00",
            font=("Arial", 16, "bold")
        )
        self.speaker_label.pack(pady=(10, 5))

        self.subtitle_label = tk.Label(
            self.subtitle_frame,
            text="再生ボタンを押してください",
            bg="#000000",
            fg="#ffffff",
            font=("Arial", 20),
            wraplength=700
        )
        self.subtitle_label.pack(pady=5)

        # 下部: コントロールパネル
        control_frame = tk.Frame(self.window, bg="#1a1a2e")
        control_frame.pack(fill=tk.X, padx=20, pady=10)

        # ボタン
        btn_frame = tk.Frame(control_frame, bg="#1a1a2e")
        btn_frame.pack(pady=10)

        self.load_btn = tk.Button(
            btn_frame,
            text="フォルダ読込",
            command=self.browse_folder,
            bg="#4a9eff",
            fg="white",
            font=("Arial", 12),
            width=12
        )
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.play_btn = tk.Button(
            btn_frame,
            text="▶ 再生",
            command=self.toggle_play,
            bg="#4aff9f",
            fg="black",
            font=("Arial", 12),
            width=12
        )
        self.play_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(
            btn_frame,
            text="■ 停止",
            command=self.stop_playback,
            bg="#ff4a4a",
            fg="white",
            font=("Arial", 12),
            width=12
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.prev_btn = tk.Button(
            btn_frame,
            text="◀ 前へ",
            command=self.prev_line,
            bg="#666666",
            fg="white",
            font=("Arial", 12),
            width=8
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = tk.Button(
            btn_frame,
            text="次へ ▶",
            command=self.next_line,
            bg="#666666",
            fg="white",
            font=("Arial", 12),
            width=8
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)

        # 進捗表示
        self.progress_label = tk.Label(
            control_frame,
            text="0 / 0",
            bg="#1a1a2e",
            fg="#888888",
            font=("Arial", 12)
        )
        self.progress_label.pack(pady=5)

        # セリフリスト
        list_frame = tk.Frame(self.window, bg="#1a1a2e")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(
            list_frame,
            text="セリフ一覧:",
            bg="#1a1a2e",
            fg="white",
            font=("Arial", 11)
        ).pack(anchor="w")

        self.line_listbox = tk.Listbox(
            list_frame,
            bg="#2a2a4e",
            fg="white",
            font=("Arial", 11),
            selectbackground="#4a9eff",
            height=8
        )
        self.line_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.line_listbox.bind('<<ListboxSelect>>', self.on_line_select)

    def browse_folder(self):
        """フォルダを選択して音声ファイルを読み込む"""
        folder = filedialog.askdirectory(title="音声フォルダを選択")
        if folder:
            self.load_audio_files(folder)

    def load_audio_files(self, folder):
        """音声ファイルを読み込む"""
        self.audio_dir = folder
        self.audio_files = []

        # wavファイルを番号順にソート
        files = [f for f in os.listdir(folder) if f.endswith('.wav')]
        files.sort()

        for filename in files:
            filepath = os.path.join(folder, filename)
            # ファイル名からキャラクター名とテキストを推測
            # 形式: 001_ずんだもん.wav
            match = re.match(r'(\d+)_(.+)\.wav', filename)
            if match:
                index = int(match.group(1))
                character = match.group(2)
                self.audio_files.append({
                    'file': filepath,
                    'character': character,
                    'text': f"（セリフ {index + 1}）",  # テキストは後で設定可能
                    'index': index
                })

        self.current_index = 0
        self.update_line_list()
        self.update_display()
        self.progress_label.config(text=f"0 / {len(self.audio_files)}")

    def set_skit_text(self, skit_text):
        """コントテキストを設定してセリフを紐付け"""
        if not skit_text:
            return

        lines = skit_text.strip().split('\n')
        line_index = 0

        for line in lines:
            match = re.match(r'^(.+?)[:：]\s*(.+)$', line)
            if match and line_index < len(self.audio_files):
                self.audio_files[line_index]['text'] = match.group(2).strip()
                line_index += 1

        self.update_line_list()

    def update_line_list(self):
        """セリフリストを更新"""
        self.line_listbox.delete(0, tk.END)
        for i, audio in enumerate(self.audio_files):
            display = f"{audio['character']}: {audio['text'][:30]}..."
            self.line_listbox.insert(tk.END, display)

    def update_display(self):
        """字幕表示を更新"""
        if not self.audio_files:
            self.speaker_label.config(text="")
            self.subtitle_label.config(text="音声ファイルがありません")
            return

        if 0 <= self.current_index < len(self.audio_files):
            audio = self.audio_files[self.current_index]
            self.speaker_label.config(text=audio['character'])
            self.subtitle_label.config(text=audio['text'])
            self.progress_label.config(
                text=f"{self.current_index + 1} / {len(self.audio_files)}"
            )

            # リストボックスの選択を更新
            self.line_listbox.selection_clear(0, tk.END)
            self.line_listbox.selection_set(self.current_index)
            self.line_listbox.see(self.current_index)

            # キャラクターハイライト（立ち絵実装時に使用）
            self.highlight_character(audio['character'])

    def highlight_character(self, character):
        """話しているキャラクターをハイライト"""
        # 立ち絵実装時にここで画像を切り替え
        if "ずんだもん" in character or "A" in character:
            self.char_a_label.config(bg="#4a4a8e", fg="#ffffff")
            self.char_b_label.config(bg="#2a2a4e", fg="#888888")
        elif "四国めたん" in character or "B" in character:
            self.char_a_label.config(bg="#2a2a4e", fg="#888888")
            self.char_b_label.config(bg="#4a4a8e", fg="#ffffff")
        else:
            self.char_a_label.config(bg="#2a2a4e", fg="#888888")
            self.char_b_label.config(bg="#2a2a4e", fg="#888888")

    def play_audio(self, filepath):
        """音声を再生"""
        if AUDIO_BACKEND == "pygame":
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                if not self.is_playing:
                    pygame.mixer.music.stop()
                    return False
        elif AUDIO_BACKEND == "winsound":
            import winsound
            winsound.PlaySound(filepath, winsound.SND_FILENAME)
        else:
            # 音声再生ライブラリがない場合は待機のみ
            time.sleep(1)
        return True

    def toggle_play(self):
        """再生/一時停止を切り替え"""
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback()

    def start_playback(self):
        """再生開始"""
        if not self.audio_files:
            messagebox.showwarning("警告", "音声ファイルがありません")
            return

        self.is_playing = True
        self.play_btn.config(text="⏸ 一時停止", bg="#ffcc00", fg="black")
        self.play_thread = threading.Thread(target=self.playback_loop, daemon=True)
        self.play_thread.start()

    def pause_playback(self):
        """一時停止"""
        self.is_playing = False
        self.play_btn.config(text="▶ 再生", bg="#4aff9f", fg="black")
        if AUDIO_BACKEND == "pygame":
            pygame.mixer.music.stop()

    def stop_playback(self):
        """停止してリセット"""
        self.is_playing = False
        self.play_btn.config(text="▶ 再生", bg="#4aff9f", fg="black")
        self.current_index = 0
        if AUDIO_BACKEND == "pygame":
            pygame.mixer.music.stop()
        self.update_display()

    def playback_loop(self):
        """再生ループ"""
        while self.is_playing and self.current_index < len(self.audio_files):
            audio = self.audio_files[self.current_index]

            # UIを更新（メインスレッドで）
            self.window.after(0, self.update_display)

            # 音声再生
            if not self.play_audio(audio['file']):
                break  # 停止された

            # 次のセリフへ
            self.current_index += 1
            time.sleep(0.3)  # セリフ間の間隔

        # 再生終了
        self.window.after(0, self.on_playback_finished)

    def on_playback_finished(self):
        """再生終了時の処理"""
        self.is_playing = False
        self.play_btn.config(text="▶ 再生", bg="#4aff9f", fg="black")
        if self.current_index >= len(self.audio_files):
            self.current_index = 0
            self.update_display()

    def prev_line(self):
        """前のセリフへ"""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()

    def next_line(self):
        """次のセリフへ"""
        if self.current_index < len(self.audio_files) - 1:
            self.current_index += 1
            self.update_display()

    def on_line_select(self, event):
        """リストからセリフを選択"""
        selection = self.line_listbox.curselection()
        if selection:
            self.current_index = selection[0]
            self.update_display()

    def run(self):
        """ウィンドウを実行（スタンドアロン時）"""
        self.window.mainloop()


# スタンドアロン実行用
if __name__ == "__main__":
    player = SkitPlayer()
    player.run()
