import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog, filedialog
from database import Database
from youtube_api import YouTubeAPI
from gemini_api import GeminiAPI
from voicevox_api import VoicevoxAPI
from player import SkitPlayer

class ComedyAnalyzer:
    VOICEVOX_CHARACTERS = {
        "ずんだもん": {
            "role": "ボケ",
            "tone": "語尾に「〜のだ」「〜なのだ」を使う。子供っぽく無邪気。",
            "example": "それはすごいのだ！ / わからないのだ… / やってみるのだ"
        },
        "四国めたん": {
            "role": "ツッコミ",
            "tone": "大人っぽく落ち着いている。丁寧語だが冷静にツッコむ。",
            "example": "それはおかしいですね / なぜそうなるんですか / 意味がわかりません"
        },
        "春日部つむぎ": {
            "role": "どちらでも",
            "tone": "明るく元気。ギャルっぽい。語尾に「〜じゃん」「〜だよね」を使う。",
            "example": "まじ？それやばくない？ / いいじゃんいいじゃん！ / ウケるんだけど"
        },
    }

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("コメディ分析ツール")
        self.root.geometry("1200x900")
        self.root.configure(bg="#2b2b2b")
        self.db = Database()
        self.yt = YouTubeAPI()
        self.gemini = GeminiAPI()
        self.voicevox = VoicevoxAPI()
        self.setup_styles()
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        self.create_analyze_tab()
        self.create_authors_tab()
        self.create_videos_tab()
        self.create_patterns_tab()
        self.status = tk.Label(self.root, text="準備完了", bg="#2b2b2b", fg="white", anchor="w")
        self.status.pack(fill=tk.X, padx=10, pady=5)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#2b2b2b')
        style.configure('TNotebook.Tab', background='#3c3c3c', foreground='white', padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', '#4a9eff')])
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='white')

    def on_tab_changed(self, event):
        self.refresh_authors_list()
        self.refresh_videos_list()
        self.refresh_author_combo()
        if hasattr(self, 'skits_listbox'):
            self.refresh_skits_list()

    def create_analyze_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="動画分析")
        top_frame = ttk.Frame(tab)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(top_frame, text="YouTube URL:").pack(side=tk.LEFT)
        self.url_entry = tk.Entry(top_frame, width=50, font=("Arial", 11))
        self.url_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="貼り付け", command=self.paste_url, bg="#666666", fg="white").pack(side=tk.LEFT)
        ttk.Label(top_frame, text="作者:").pack(side=tk.LEFT, padx=(20, 5))
        self.author_combo = ttk.Combobox(top_frame, width=20)
        self.author_combo.pack(side=tk.LEFT)
        self.refresh_author_combo()
        tk.Button(top_frame, text="新規作者", command=self.add_new_author, bg="#4a9eff", fg="white").pack(side=tk.LEFT, padx=5)
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btn_frame, text="字幕取得", command=self.fetch_transcript, bg="#4a9eff", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="分析", command=self.analyze_video, bg="#4a9eff", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="保存", command=self.save_analysis, bg="#4a9eff", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        ttk.Label(tab, text="字幕:").pack(anchor="w", padx=10)
        self.transcript_text = scrolledtext.ScrolledText(tab, width=110, height=10, font=("Arial", 10), bg="#1e1e1e", fg="white")
        self.transcript_text.pack(padx=10, pady=5)
        ttk.Label(tab, text="分析結果:").pack(anchor="w", padx=10)
        self.analysis_text = scrolledtext.ScrolledText(tab, width=110, height=15, font=("Arial", 10), bg="#1e1e1e", fg="white")
        self.analysis_text.pack(padx=10, pady=5)
        self.current_video_id = None

    def refresh_author_combo(self):
        authors = self.db.get_authors()
        self.author_combo['values'] = [a['name'] for a in authors]
        if authors and not self.author_combo.get():
            self.author_combo.current(0)

    def add_new_author(self):
        name = simpledialog.askstring("新規作者", "作者名を入力:")
        if name:
            self.db.add_author(name)
            self.refresh_author_combo()
            self.author_combo.set(name)
            self.refresh_authors_list()
            self.set_status(f"作者「{name}」を追加しました")

    def paste_url(self):
        try:
            clipboard = self.root.clipboard_get()
            if clipboard:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, clipboard.strip())
                self.set_status("URLを貼り付けました")
        except tk.TclError:
            self.set_status("クリップボードにテキストがありません")

    def fetch_transcript(self):
        url = self.url_entry.get().strip()
        if not url:
            self.set_status("URLを入力してください")
            return
        self.set_status("字幕取得中...")
        self.root.update()
        self.current_video_id = self.yt.get_video_id(url)
        result = self.yt.fetch_transcript(self.current_video_id)
        if result['success']:
            self.transcript_text.delete("1.0", tk.END)
            self.transcript_text.insert(tk.END, result['transcript'])
            self.set_status(f"字幕取得完了（{result['count']}件）")
        else:
            self.set_status(f"エラー: {result['error']}")

    def analyze_video(self):
        transcript = self.transcript_text.get("1.0", tk.END).strip()
        if not transcript:
            self.set_status("先に字幕を取得してください")
            return
        self.set_status("Geminiで分析中...")
        self.root.update()
        result = self.gemini.analyze_video(transcript)
        if result['success']:
            self.analysis_text.delete("1.0", tk.END)
            self.analysis_text.insert(tk.END, result['analysis'])
            self.set_status("分析完了")
        else:
            self.set_status(f"分析エラー: {result['error']}")

    def save_analysis(self):
        transcript = self.transcript_text.get("1.0", tk.END).strip()
        analysis = self.analysis_text.get("1.0", tk.END).strip()
        if not transcript or not analysis:
            self.set_status("字幕と分析結果が必要です")
            return
        author_name = self.author_combo.get()
        if not author_name:
            self.set_status("作者を選択してください")
            return
        author_id = self.db.add_author(author_name)
        url = self.url_entry.get().strip()
        video_db_id = self.db.add_video(self.current_video_id, f"Video {self.current_video_id}", url, author_id)
        self.db.add_transcript(video_db_id, transcript)
        self.db.add_analysis(video_db_id, analysis)
        self.set_status(f"保存完了: {self.current_video_id}")
        self.refresh_videos_list()
        self.refresh_authors_list()

    def create_authors_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="作者管理")
        left_frame = ttk.Frame(tab)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        ttk.Label(left_frame, text="作者一覧:").pack(anchor="w")
        self.authors_listbox = tk.Listbox(left_frame, width=25, height=12, bg="#1e1e1e", fg="white", font=("Arial", 11))
        self.authors_listbox.pack(pady=5)
        self.authors_listbox.bind('<<ListboxSelect>>', self.on_author_select)
        tk.Button(left_frame, text="作者パターン分析", command=self.analyze_author_patterns, bg="#4a9eff", fg="white", width=20).pack(pady=5)
        ttk.Separator(left_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(left_frame, text="コント生成:").pack(anchor="w")
        ttk.Label(left_frame, text="テーマ（任意）:").pack(anchor="w", pady=(5, 0))
        self.skit_theme_entry = tk.Entry(left_frame, width=25, font=("Arial", 11))
        self.skit_theme_entry.pack(pady=5)
        self.skit_theme_entry.insert(0, "例: コンビニ、面接、電話")
        self.skit_theme_entry.bind('<FocusIn>', lambda e: self.skit_theme_entry.delete(0, tk.END) if self.skit_theme_entry.get().startswith("例:") else None)
        tk.Button(left_frame, text="ショートコント生成", command=self.generate_skit, bg="#ff9f4a", fg="white", width=20, height=2).pack(pady=10)
        ttk.Separator(left_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(left_frame, text="VOICEVOX割り当て:").pack(anchor="w")
        char_names = list(self.VOICEVOX_CHARACTERS.keys())
        char_frame = ttk.Frame(left_frame)
        char_frame.pack(fill=tk.X, pady=5)
        ttk.Label(char_frame, text="A:").pack(side=tk.LEFT)
        self.char_a_combo = ttk.Combobox(char_frame, values=char_names, width=12)
        self.char_a_combo.pack(side=tk.LEFT, padx=2)
        self.char_a_combo.current(0)
        ttk.Label(char_frame, text="B:").pack(side=tk.LEFT, padx=(5, 0))
        self.char_b_combo = ttk.Combobox(char_frame, values=char_names, width=12)
        self.char_b_combo.pack(side=tk.LEFT, padx=2)
        self.char_b_combo.current(1)
        tk.Button(left_frame, text="口調変換", command=self.convert_to_character, bg="#4aff9f", fg="black", width=20).pack(pady=5)
        tk.Button(left_frame, text="台本コピー", command=self.copy_script, bg="#9f4aff", fg="white", width=20).pack(pady=5)
        tk.Button(left_frame, text="トーク保存", command=self.save_skit, bg="#4a9fff", fg="white", width=20).pack(pady=5)
        tk.Button(left_frame, text="音声生成", command=self.generate_audio, bg="#ff4a9f", fg="white", width=20).pack(pady=5)
        tk.Button(left_frame, text="再生プレイヤー", command=self.open_player, bg="#ff9f4a", fg="white", width=20).pack(pady=5)
        ttk.Separator(left_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(left_frame, text="保存済みトーク:").pack(anchor="w")
        self.skits_listbox = tk.Listbox(left_frame, width=25, height=6, bg="#1e1e1e", fg="white", font=("Arial", 10))
        self.skits_listbox.pack(pady=5)
        self.skits_listbox.bind('<<ListboxSelect>>', self.on_skit_select)
        tk.Button(left_frame, text="トーク削除", command=self.delete_skit, bg="#ff4a4a", fg="white", width=20).pack(pady=5)
        right_frame = ttk.Frame(tab)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        top_right = ttk.Frame(right_frame)
        top_right.pack(fill=tk.X)
        videos_frame = ttk.Frame(top_right)
        videos_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(videos_frame, text="この作者の動画:").pack(anchor="w")
        self.author_videos_listbox = tk.Listbox(videos_frame, width=40, height=4, bg="#1e1e1e", fg="white", font=("Arial", 10))
        self.author_videos_listbox.pack(pady=5, fill=tk.X)
        pattern_frame = ttk.Frame(top_right)
        pattern_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        ttk.Label(pattern_frame, text="作者の共通パターン:").pack(anchor="w")
        self.author_pattern_text = scrolledtext.ScrolledText(pattern_frame, width=50, height=4, font=("Arial", 10), bg="#1e1e1e", fg="white")
        self.author_pattern_text.pack(pady=5, fill=tk.X)
        ttk.Label(right_frame, text="生成されたショートコント:").pack(anchor="w", pady=(10, 0))
        self.generated_skit_text = scrolledtext.ScrolledText(right_frame, width=100, height=25, font=("Arial", 11), bg="#1e1e1e", fg="#ffdd88")
        self.generated_skit_text.pack(pady=5, fill=tk.BOTH, expand=True)
        self.refresh_authors_list()
        self.refresh_skits_list()

    def refresh_authors_list(self):
        self.authors_listbox.delete(0, tk.END)
        for author in self.db.get_authors():
            self.authors_listbox.insert(tk.END, author['name'])

    def on_author_select(self, event):
        selection = self.authors_listbox.curselection()
        if not selection:
            return
        author_name = self.authors_listbox.get(selection[0])
        authors = self.db.get_authors()
        author = next((a for a in authors if a['name'] == author_name), None)
        if author:
            self.author_videos_listbox.delete(0, tk.END)
            for video in self.db.get_videos_by_author(author['id']):
                self.author_videos_listbox.insert(tk.END, f"{video['video_id']}")
            pattern = self.db.get_author_pattern(author['id'])
            self.author_pattern_text.delete("1.0", tk.END)
            if pattern:
                self.author_pattern_text.insert(tk.END, pattern['analysis_summary'])

    def analyze_author_patterns(self):
        selection = self.authors_listbox.curselection()
        if not selection:
            self.set_status("作者を選択してください")
            return
        author_name = self.authors_listbox.get(selection[0])
        authors = self.db.get_authors()
        author = next((a for a in authors if a['name'] == author_name), None)
        if not author:
            return
        analyses = self.db.get_analyses_by_author(author['id'])
        if len(analyses) < 2:
            self.set_status("パターン分析には2つ以上の動画が必要です")
            return
        self.set_status("作者パターンを分析中...")
        self.root.update()
        analyses_text = "\n\n---\n\n".join([f"### {a['youtube_id']}\n\n{a['raw_analysis']}" for a in analyses])
        result = self.gemini.analyze_author_patterns(analyses_text)
        if result['success']:
            self.db.save_author_pattern(author['id'], "", result['analysis'])
            self.author_pattern_text.delete("1.0", tk.END)
            self.author_pattern_text.insert(tk.END, result['analysis'])
            self.set_status("作者パターン分析完了")
        else:
            self.set_status(f"エラー: {result['error']}")

    def generate_skit(self):
        selection = self.authors_listbox.curselection()
        if not selection:
            self.set_status("作者を選択してください")
            return
        author_name = self.authors_listbox.get(selection[0])
        authors = self.db.get_authors()
        author = next((a for a in authors if a['name'] == author_name), None)
        if not author:
            return
        transcripts = self.db.get_transcripts_by_author(author['id'])
        if not transcripts:
            self.set_status("この作者の字幕データがありません")
            return
        analyses = self.db.get_analyses_by_author(author['id'])
        pattern = self.db.get_author_pattern(author['id'])
        pattern_text = pattern['analysis_summary'] if pattern else ""
        transcripts_text = "\n\n---\n\n".join([f"【{t['youtube_id']}】\n{t['content']}" for t in transcripts])
        analyses_text = "\n\n---\n\n".join([f"【{a['youtube_id']}】\n{a['raw_analysis']}" for a in analyses]) if analyses else ""
        theme = self.skit_theme_entry.get().strip()
        if theme.startswith("例:"):
            theme = ""
        self.set_status(f"「{author_name}」風のショートコントを生成中...")
        self.root.update()
        result = self.gemini.generate_short_skit(author_name, pattern_text, transcripts_text, analyses_text, theme)
        if result['success']:
            self.generated_skit_text.delete("1.0", tk.END)
            self.generated_skit_text.insert(tk.END, result['skit'])
            self.set_status(f"「{author_name}」風ショートコント生成完了")
        else:
            self.set_status(f"生成エラー: {result['error']}")

    def copy_script(self):
        skit = self.generated_skit_text.get("1.0", tk.END).strip()
        if not skit:
            self.set_status("先にコントを生成してください")
            return
        char_a = self.char_a_combo.get()
        char_b = self.char_b_combo.get()
        lines = []
        for line in skit.split('\n'):
            line = line.strip()
            if line.startswith('A:'):
                lines.append(f'{char_a}「{line[2:].strip()}」')
            elif line.startswith('B:'):
                lines.append(f'{char_b}「{line[2:].strip()}」')
            elif line.startswith(f'{char_a}:'):
                lines.append(f'{char_a}「{line[len(char_a)+1:].strip()}」')
            elif line.startswith(f'{char_b}:'):
                lines.append(f'{char_b}「{line[len(char_b)+1:].strip()}」')
            elif line:
                lines.append(line)
        result = '\n'.join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(result)
        self.set_status(f"台本をコピーしました（{char_a} / {char_b}）")

    def save_skit(self):
        skit = self.generated_skit_text.get("1.0", tk.END).strip()
        if not skit:
            self.set_status("先にコントを生成してください")
            return

        # 作者を取得
        selection = self.authors_listbox.curselection()
        if not selection:
            self.set_status("作者を選択してください")
            return

        author_name = self.authors_listbox.get(selection[0])
        authors = self.db.get_authors()
        author = next((a for a in authors if a['name'] == author_name), None)
        if not author:
            return

        # タイトルを入力
        title = simpledialog.askstring("トーク保存", "タイトルを入力してください:")
        if not title:
            return

        theme = self.skit_theme_entry.get().strip()
        if theme.startswith("例:"):
            theme = ""

        char_a = self.char_a_combo.get()
        char_b = self.char_b_combo.get()

        self.db.save_skit(author['id'], title, skit, theme, char_a, char_b)
        self.refresh_skits_list()
        self.set_status(f"トーク「{title}」を保存しました")

    def refresh_skits_list(self):
        self.skits_listbox.delete(0, tk.END)
        for skit in self.db.get_all_skits():
            display = f"{skit['title']} ({skit['author_name'] or '不明'})"
            self.skits_listbox.insert(tk.END, display)
        # IDを保持
        self._skit_ids = [skit['id'] for skit in self.db.get_all_skits()]

    def on_skit_select(self, event):
        selection = self.skits_listbox.curselection()
        if not selection:
            return

        if not hasattr(self, '_skit_ids') or selection[0] >= len(self._skit_ids):
            return

        skit_id = self._skit_ids[selection[0]]
        skit = self.db.get_skit(skit_id)
        if skit:
            self.generated_skit_text.delete("1.0", tk.END)
            self.generated_skit_text.insert(tk.END, skit['content'])
            if skit['char_a']:
                self.char_a_combo.set(skit['char_a'])
            if skit['char_b']:
                self.char_b_combo.set(skit['char_b'])
            self.set_status(f"トーク「{skit['title']}」を読み込みました")

    def delete_skit(self):
        selection = self.skits_listbox.curselection()
        if not selection:
            self.set_status("削除するトークを選択してください")
            return

        if not hasattr(self, '_skit_ids') or selection[0] >= len(self._skit_ids):
            return

        skit_id = self._skit_ids[selection[0]]
        skit = self.db.get_skit(skit_id)
        if skit and messagebox.askyesno("確認", f"トーク「{skit['title']}」を削除しますか？"):
            self.db.delete_skit(skit_id)
            self.refresh_skits_list()
            self.set_status("トークを削除しました")

    def convert_to_character(self):
        skit = self.generated_skit_text.get("1.0", tk.END).strip()
        if not skit:
            self.set_status("先にコントを生成してください")
            return
        char_a_name = self.char_a_combo.get()
        char_b_name = self.char_b_combo.get()
        char_a_info = {
            'name': char_a_name,
            'tone': self.VOICEVOX_CHARACTERS[char_a_name]['tone'],
            'example': self.VOICEVOX_CHARACTERS[char_a_name]['example']
        }
        char_b_info = {
            'name': char_b_name,
            'tone': self.VOICEVOX_CHARACTERS[char_b_name]['tone'],
            'example': self.VOICEVOX_CHARACTERS[char_b_name]['example']
        }
        self.set_status(f"口調変換中（{char_a_name} / {char_b_name}）...")
        self.root.update()
        result = self.gemini.convert_to_character(skit, char_a_info, char_b_info)
        if result['success']:
            self.generated_skit_text.delete("1.0", tk.END)
            self.generated_skit_text.insert(tk.END, result['skit'])
            self.set_status(f"口調変換完了（{char_a_name} / {char_b_name}）")
        else:
            self.set_status(f"変換エラー: {result['error']}")

    def generate_audio(self):
        skit = self.generated_skit_text.get("1.0", tk.END).strip()
        if not skit:
            self.set_status("先にコントを生成してください")
            return

        if not self.voicevox.is_available():
            self.set_status("VOICEVOXが起動していません（localhost:50021）")
            messagebox.showerror("エラー", "VOICEVOXが起動していません。\nVOICEVOXを起動してから再度お試しください。")
            return

        # 固定の出力フォルダ（アプリと同じ場所のaudio_outputフォルダ）
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "audio_output")

        self.set_status("音声生成中...")
        self.root.update()

        # A/Bを選択されたキャラクターにマッピング
        char_mapping = {
            "A": self.char_a_combo.get(),
            "B": self.char_b_combo.get(),
        }

        result = self.voicevox.generate_skit_audio(skit, output_dir, char_mapping)
        if result['success']:
            file_count = len(result['files'])
            self.set_status(f"音声生成完了（{file_count}ファイル → {output_dir}）")
            messagebox.showinfo("完了", f"{file_count}個の音声ファイルを生成しました。\n\n保存先: {output_dir}")
        else:
            self.set_status(f"音声生成エラー: {result['error']}")
            messagebox.showerror("エラー", result['error'])

    def open_player(self):
        """再生プレイヤーを開く"""
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        audio_dir = os.path.join(script_dir, "audio_output")

        # 音声フォルダが存在するか確認
        if not os.path.exists(audio_dir) or not os.listdir(audio_dir):
            messagebox.showwarning("警告", "音声ファイルがありません。\n先に音声生成を行ってください。")
            return

        # プレイヤーを開く（skit_info.jsonから字幕を読み込む）
        player = SkitPlayer(parent=self.root, audio_dir=audio_dir)

        self.set_status("再生プレイヤーを開きました")

    def create_videos_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="動画一覧")
        top_frame = ttk.Frame(tab)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        columns = ('video_id', 'author', 'created_at')
        self.videos_tree = ttk.Treeview(top_frame, columns=columns, show='headings', height=10)
        self.videos_tree.heading('video_id', text='動画ID')
        self.videos_tree.heading('author', text='作者')
        self.videos_tree.heading('created_at', text='追加日時')
        self.videos_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.videos_tree.bind('<<TreeviewSelect>>', self.on_video_select)
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="削除", command=self.delete_video, bg="#ff4a4a", fg="white", width=10).pack(pady=5)
        detail_frame = ttk.Frame(tab)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        left_detail = ttk.Frame(detail_frame)
        left_detail.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(left_detail, text="字幕（セリフ）:").pack(anchor="w")
        self.video_transcript_text = scrolledtext.ScrolledText(left_detail, width=55, height=12, font=("Arial", 10), bg="#1e1e1e", fg="#88ff88")
        self.video_transcript_text.pack(fill=tk.BOTH, expand=True)
        right_detail = ttk.Frame(detail_frame)
        right_detail.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        ttk.Label(right_detail, text="分析結果:").pack(anchor="w")
        self.video_detail_text = scrolledtext.ScrolledText(right_detail, width=55, height=12, font=("Arial", 10), bg="#1e1e1e", fg="white")
        self.video_detail_text.pack(fill=tk.BOTH, expand=True)
        self.refresh_videos_list()

    def refresh_videos_list(self):
        for item in self.videos_tree.get_children():
            self.videos_tree.delete(item)
        for video in self.db.get_all_videos():
            self.videos_tree.insert('', tk.END, values=(video['video_id'], video['author_name'] or '不明', video['created_at']), iid=video['id'])

    def on_video_select(self, event):
        selection = self.videos_tree.selection()
        if not selection:
            return
        video_db_id = int(selection[0])
        transcript = self.db.get_transcript(video_db_id)
        self.video_transcript_text.delete("1.0", tk.END)
        if transcript:
            self.video_transcript_text.insert(tk.END, transcript)
        analysis = self.db.get_analysis(video_db_id)
        self.video_detail_text.delete("1.0", tk.END)
        if analysis:
            self.video_detail_text.insert(tk.END, analysis['raw_analysis'])

    def delete_video(self):
        selection = self.videos_tree.selection()
        if not selection:
            self.set_status("削除する動画を選択してください")
            return
        video_db_id = int(selection[0])
        if messagebox.askyesno("確認", "この動画を削除しますか？\n（字幕・分析結果も削除されます）"):
            self.db.delete_video(video_db_id)
            self.video_transcript_text.delete("1.0", tk.END)
            self.video_detail_text.delete("1.0", tk.END)
            self.refresh_videos_list()
            self.set_status("動画を削除しました")

    def create_patterns_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="全体解析")
        ttk.Label(tab, text="全作者の共通パターン分析").pack(pady=10)
        tk.Button(tab, text="全体解析を実行", command=self.run_global_analysis, bg="#4a9eff", fg="white", width=20).pack(pady=10)
        self.global_analysis_text = scrolledtext.ScrolledText(tab, width=110, height=30, font=("Arial", 10), bg="#1e1e1e", fg="white")
        self.global_analysis_text.pack(padx=10, pady=10)

    def run_global_analysis(self):
        authors = self.db.get_authors()
        if len(authors) < 2:
            self.set_status("全体解析には2人以上の作者が必要です")
            return
        self.set_status("全体解析中...")
        self.root.update()
        patterns_text = ""
        for author in authors:
            pattern = self.db.get_author_pattern(author['id'])
            if pattern:
                patterns_text += f"### {author['name']}\n\n{pattern['analysis_summary']}\n\n---\n\n"
        if not patterns_text:
            self.set_status("先に各作者のパターン分析を行ってください")
            return
        try:
            prompt = f"以下は複数のコメディ作者のパターン分析結果です。全体を通して見られる面白いコメディの共通法則を抽出してください。\n\n{patterns_text}"
            result = self.gemini._generate(prompt)
            self.global_analysis_text.delete("1.0", tk.END)
            self.global_analysis_text.insert(tk.END, result)
            self.set_status("全体解析完了")
        except Exception as e:
            self.set_status(f"エラー: {e}")

    def set_status(self, message):
        self.status.config(text=message)

    def run(self):
        self.root.mainloop()
        self.db.close()

if __name__ == "__main__":
    ComedyAnalyzer().run()
