import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import threading
import time
import json

# 画像処理用
try:
    from PIL import Image, ImageTk, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

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

# 立ち絵設定ファイルパス
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHARACTER_CONFIG_PATH = os.path.join(SCRIPT_DIR, "character_images.json")


class SkitPlayer:
    """コント再生プレイヤーウィンドウ"""

    # デフォルトのキャラクターマッピング
    CHARACTER_MAPPING = {
        "ずんだもん": "A",
        "四国めたん": "B",
        "春日部つむぎ": "A",
    }

    def __init__(self, parent=None, audio_dir=None, skit_text=None):
        self.parent = parent
        self.audio_dir = audio_dir
        self.skit_text = skit_text
        self.audio_files = []
        self.current_index = 0
        self.is_playing = False
        self.play_thread = None

        # 立ち絵画像
        self.char_a_image = None
        self.char_b_image = None
        self.char_a_photo = None
        self.char_b_photo = None
        self.char_a_photo_dim = None
        self.char_b_photo_dim = None

        # ウィンドウ作成
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()

        self.window.title("コント再生プレイヤー")
        self.window.geometry("900x700")
        self.window.configure(bg="#1a1a2e")

        # 立ち絵設定を読み込み
        self.load_character_config()

        self.setup_ui()

        # 音声ファイルがあれば読み込み
        if audio_dir:
            self.load_audio_files(audio_dir)

    def load_character_config(self):
        """立ち絵設定を読み込む"""
        self.char_images = {"A": None, "B": None}
        if os.path.exists(CHARACTER_CONFIG_PATH):
            try:
                with open(CHARACTER_CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.char_images = config.get("images", {"A": None, "B": None})
            except:
                pass

    def save_character_config(self):
        """立ち絵設定を保存"""
        config = {"images": self.char_images}
        with open(CHARACTER_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def setup_ui(self):
        """UIを構築"""
        # 上部: 立ち絵エリア
        self.character_frame = tk.Frame(self.window, bg="#1a1a2e", height=350)
        self.character_frame.pack(fill=tk.X, padx=20, pady=10)
        self.character_frame.pack_propagate(False)

        # キャラA立ち絵（左）
        char_a_container = tk.Frame(self.character_frame, bg="#1a1a2e")
        char_a_container.pack(side=tk.LEFT, padx=10, pady=5)

        self.char_a_label = tk.Label(
            char_a_container,
            text="【キャラA】\nクリックで\n立ち絵設定",
            bg="#2a2a4e",
            fg="#888888",
            font=("Arial", 12),
            width=25,
            height=15,
            cursor="hand2"
        )
        self.char_a_label.pack()
        self.char_a_label.bind("<Button-1>", lambda e: self.select_character_image("A"))

        tk.Label(char_a_container, text="キャラA", bg="#1a1a2e", fg="#ffcc00", font=("Arial", 11, "bold")).pack(pady=2)

        # キャラB立ち絵（右）
        char_b_container = tk.Frame(self.character_frame, bg="#1a1a2e")
        char_b_container.pack(side=tk.RIGHT, padx=10, pady=5)

        self.char_b_label = tk.Label(
            char_b_container,
            text="【キャラB】\nクリックで\n立ち絵設定",
            bg="#2a2a4e",
            fg="#888888",
            font=("Arial", 12),
            width=25,
            height=15,
            cursor="hand2"
        )
        self.char_b_label.pack()
        self.char_b_label.bind("<Button-1>", lambda e: self.select_character_image("B"))

        tk.Label(char_b_container, text="キャラB", bg="#1a1a2e", fg="#00ccff", font=("Arial", 11, "bold")).pack(pady=2)

        # 立ち絵を読み込んで表示
        self.load_and_display_images()

        # 中央: 字幕エリア
        self.subtitle_frame = tk.Frame(self.window, bg="#000000", height=100)
        self.subtitle_frame.pack(fill=tk.X, padx=20, pady=10)
        self.subtitle_frame.pack_propagate(False)

        self.speaker_label = tk.Label(
            self.subtitle_frame,
            text="",
            bg="#000000",
            fg="#ffcc00",
            font=("Arial", 14, "bold")
        )
        self.speaker_label.pack(pady=(10, 5))

        self.subtitle_label = tk.Label(
            self.subtitle_frame,
            text="再生ボタンを押してください",
            bg="#000000",
            fg="#ffffff",
            font=("Arial", 18),
            wraplength=800
        )
        self.subtitle_label.pack(pady=5)

        # 下部: コントロールパネル
        control_frame = tk.Frame(self.window, bg="#1a1a2e")
        control_frame.pack(fill=tk.X, padx=20, pady=5)

        # ボタン
        btn_frame = tk.Frame(control_frame, bg="#1a1a2e")
        btn_frame.pack(pady=5)

        self.load_btn = tk.Button(
            btn_frame,
            text="フォルダ読込",
            command=self.browse_folder,
            bg="#4a9eff",
            fg="white",
            font=("Arial", 11),
            width=10
        )
        self.load_btn.pack(side=tk.LEFT, padx=3)

        self.play_btn = tk.Button(
            btn_frame,
            text="▶ 再生",
            command=self.toggle_play,
            bg="#4aff9f",
            fg="black",
            font=("Arial", 11),
            width=10
        )
        self.play_btn.pack(side=tk.LEFT, padx=3)

        self.stop_btn = tk.Button(
            btn_frame,
            text="■ 停止",
            command=self.stop_playback,
            bg="#ff4a4a",
            fg="white",
            font=("Arial", 11),
            width=10
        )
        self.stop_btn.pack(side=tk.LEFT, padx=3)

        self.prev_btn = tk.Button(
            btn_frame,
            text="◀ 前",
            command=self.prev_line,
            bg="#666666",
            fg="white",
            font=("Arial", 11),
            width=6
        )
        self.prev_btn.pack(side=tk.LEFT, padx=3)

        self.next_btn = tk.Button(
            btn_frame,
            text="次 ▶",
            command=self.next_line,
            bg="#666666",
            fg="white",
            font=("Arial", 11),
            width=6
        )
        self.next_btn.pack(side=tk.LEFT, padx=3)

        # 進捗表示
        self.progress_label = tk.Label(
            control_frame,
            text="0 / 0",
            bg="#1a1a2e",
            fg="#888888",
            font=("Arial", 11)
        )
        self.progress_label.pack(pady=3)

        # セリフリスト
        list_frame = tk.Frame(self.window, bg="#1a1a2e")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        tk.Label(
            list_frame,
            text="セリフ一覧:",
            bg="#1a1a2e",
            fg="white",
            font=("Arial", 10)
        ).pack(anchor="w")

        self.line_listbox = tk.Listbox(
            list_frame,
            bg="#2a2a4e",
            fg="white",
            font=("Arial", 10),
            selectbackground="#4a9eff",
            height=6
        )
        self.line_listbox.pack(fill=tk.BOTH, expand=True, pady=3)
        self.line_listbox.bind('<<ListboxSelect>>', self.on_line_select)

    def select_character_image(self, char_id):
        """立ち絵画像を選択"""
        if not PIL_AVAILABLE:
            messagebox.showwarning("警告", "立ち絵機能にはPillowが必要です。\npip install Pillow")
            return

        filepath = filedialog.askopenfilename(
            title=f"キャラ{char_id}の立ち絵を選択",
            filetypes=[("画像ファイル", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if filepath:
            self.char_images[char_id] = filepath
            self.save_character_config()
            self.load_and_display_images()

    def load_and_display_images(self):
        """立ち絵画像を読み込んで表示"""
        if not PIL_AVAILABLE:
            return

        # キャラA
        if self.char_images.get("A") and os.path.exists(self.char_images["A"]):
            try:
                img = Image.open(self.char_images["A"])
                img = self.resize_image(img, 200, 280)
                self.char_a_image = img
                self.char_a_photo = ImageTk.PhotoImage(img)
                # 暗いバージョンも作成
                enhancer = ImageEnhance.Brightness(img)
                dim_img = enhancer.enhance(0.4)
                self.char_a_photo_dim = ImageTk.PhotoImage(dim_img)
                self.char_a_label.config(image=self.char_a_photo, text="", width=200, height=280)
            except Exception as e:
                print(f"キャラA画像読み込みエラー: {e}")

        # キャラB
        if self.char_images.get("B") and os.path.exists(self.char_images["B"]):
            try:
                img = Image.open(self.char_images["B"])
                img = self.resize_image(img, 200, 280)
                self.char_b_image = img
                self.char_b_photo = ImageTk.PhotoImage(img)
                # 暗いバージョンも作成
                enhancer = ImageEnhance.Brightness(img)
                dim_img = enhancer.enhance(0.4)
                self.char_b_photo_dim = ImageTk.PhotoImage(dim_img)
                self.char_b_label.config(image=self.char_b_photo, text="", width=200, height=280)
            except Exception as e:
                print(f"キャラB画像読み込みエラー: {e}")

    def resize_image(self, img, max_width, max_height):
        """画像をリサイズ（アスペクト比を維持）"""
        ratio = min(max_width / img.width, max_height / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        return img.resize(new_size, Image.Resampling.LANCZOS)

    def browse_folder(self):
        """フォルダを選択して音声ファイルを読み込む"""
        folder = filedialog.askdirectory(title="音声フォルダを選択")
        if folder:
            self.load_audio_files(folder)

    def load_audio_files(self, folder):
        """音声ファイルを読み込む"""
        self.audio_dir = folder
        self.audio_files = []

        # skit_info.jsonがあれば読み込む
        skit_info_path = os.path.join(folder, "skit_info.json")
        if os.path.exists(skit_info_path):
            try:
                with open(skit_info_path, "r", encoding="utf-8") as f:
                    skit_info = json.load(f)
                for i, info in enumerate(skit_info):
                    filepath = os.path.join(folder, info["file"])
                    if os.path.exists(filepath):
                        self.audio_files.append({
                            'file': filepath,
                            'character': info["character"],
                            'text': info["text"],
                            'index': i
                        })
            except Exception as e:
                print(f"skit_info.json読み込みエラー: {e}")

        # JSONがない場合はファイル名から推測
        if not self.audio_files:
            files = [f for f in os.listdir(folder) if f.endswith('.wav')]
            files.sort()

            for filename in files:
                filepath = os.path.join(folder, filename)
                match = re.match(r'(\d+)_(.+)\.wav', filename)
                if match:
                    index = int(match.group(1))
                    character = match.group(2)
                    self.audio_files.append({
                        'file': filepath,
                        'character': character,
                        'text': f"（セリフ {index + 1}）",
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
            display = f"{audio['character']}: {audio['text'][:40]}..."
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

            # キャラクターハイライト
            self.highlight_character(audio['character'])

    def get_character_side(self, character):
        """キャラクター名からA/Bを判定"""
        # マッピングを確認
        if character in self.CHARACTER_MAPPING:
            return self.CHARACTER_MAPPING[character]
        # ファイル名の偶数/奇数で判定（フォールバック）
        if self.current_index % 2 == 0:
            return "A"
        return "B"

    def highlight_character(self, character):
        """話しているキャラクターをハイライト（明るく表示）"""
        side = self.get_character_side(character)

        if PIL_AVAILABLE:
            # 立ち絵がある場合は明るさで切り替え
            if side == "A":
                if self.char_a_photo:
                    self.char_a_label.config(image=self.char_a_photo)
                else:
                    self.char_a_label.config(bg="#4a4a8e", fg="#ffffff")
                if self.char_b_photo_dim:
                    self.char_b_label.config(image=self.char_b_photo_dim)
                else:
                    self.char_b_label.config(bg="#2a2a4e", fg="#888888")
            else:
                if self.char_a_photo_dim:
                    self.char_a_label.config(image=self.char_a_photo_dim)
                else:
                    self.char_a_label.config(bg="#2a2a4e", fg="#888888")
                if self.char_b_photo:
                    self.char_b_label.config(image=self.char_b_photo)
                else:
                    self.char_b_label.config(bg="#4a4a8e", fg="#ffffff")
        else:
            # 立ち絵がない場合は背景色で切り替え
            if side == "A":
                self.char_a_label.config(bg="#4a4a8e", fg="#ffffff")
                self.char_b_label.config(bg="#2a2a4e", fg="#888888")
            else:
                self.char_a_label.config(bg="#2a2a4e", fg="#888888")
                self.char_b_label.config(bg="#4a4a8e", fg="#ffffff")

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
