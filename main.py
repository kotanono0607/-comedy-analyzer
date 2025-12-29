import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from database import Database
from youtube_api import YouTubeAPI
from gemini_api import GeminiAPI

class ComedyAnalyzer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("コメディ分析ツール")
        self.root.geometry("1000x750")
        self.root.configure(bg="#2b2b2b")
        self.db = Database()
        self.yt = YouTubeAPI()
        self.gemini = GeminiAPI()
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
        self.authors_listbox = tk.Listbox(left_frame, width=30, height=20, bg="#1e1e1e", fg="white")
        self.authors_listbox.pack(pady=5)
        self.authors_listbox.bind('<<ListboxSelect>>', self.on_author_select)
        tk.Button(left_frame, text="作者パターン分析", command=self.analyze_author_patterns, bg="#4a9eff", fg="white").pack(pady=5)
        ttk.Separator(left_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(left_frame, text="コント生成:").pack(anchor="w")
        ttk.Label(left_frame, text="テーマ（任意）:").pack(anchor="w", pady=(5, 0))
        self.skit_theme_entry = tk.Entry(left_frame, width=28, font=("Arial", 10))
        self.skit_theme_entry.pack(pady=5)
        self.skit_theme_entry.insert(0, "例: コンビニ、面接、電話")
        self.skit_theme_entry.bind('<FocusIn>', lambda e: self.skit_theme_entry.delete(0, tk.END) if self.skit_theme_entry.get().startswith("例:") else None)
        tk.Button(left_frame, text="ショートコント生成", command=self.generate_skit, bg="#ff9f4a", fg="white").pack(pady=5)
        right_frame = ttk.Frame(tab)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        ttk.Label(right_frame, text="この作者の動画:").pack(anchor="w")
        self.author_videos_listbox = tk.Listbox(right_frame, width=50, height=6, bg="#1e1e1e", fg="white")
        self.author_videos_listbox.pack(pady=5, fill=tk.X)
        ttk.Label(right_frame, text="作者の共通パターン:").pack(anchor="w")
        self.author_pattern_text = scrolledtext.ScrolledText(right_frame, width=70, height=8, font=("Arial", 10), bg="#1e1e1e", fg="white")
        self.author_pattern_text.pack(pady=5)
        ttk.Label(right_frame, text="生成されたショートコント:").pack(anchor="w")
        self.generated_skit_text = scrolledtext.ScrolledText(right_frame, width=70, height=12, font=("Arial", 10), bg="#1e1e1e", fg="#ffdd88")
        self.generated_skit_text.pack(pady=5)
        self.refresh_authors_list()

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
        pattern = self.db.get_author_pattern(author['id'])
        pattern_text = pattern['analysis_summary'] if pattern else ""
        transcripts_text = "\n\n---\n\n".join([f"【{t['youtube_id']}】\n{t['content']}" for t in transcripts])
        theme = self.skit_theme_entry.get().strip()
        if theme.startswith("例:"):
            theme = ""
        self.set_status(f"「{author_name}」風のショートコントを生成中...")
        self.root.update()
        result = self.gemini.generate_short_skit(author_name, pattern_text, transcripts_text, theme)
        if result['success']:
            self.generated_skit_text.delete("1.0", tk.END)
            self.generated_skit_text.insert(tk.END, result['skit'])
            self.set_status(f"「{author_name}」風ショートコント生成完了")
        else:
            self.set_status(f"生成エラー: {result['error']}")

    def create_videos_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="動画一覧")
        columns = ('video_id', 'author', 'created_at')
        self.videos_tree = ttk.Treeview(tab, columns=columns, show='headings', height=20)
        self.videos_tree.heading('video_id', text='動画ID')
        self.videos_tree.heading('author', text='作者')
        self.videos_tree.heading('created_at', text='追加日時')
        self.videos_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.videos_tree.bind('<<TreeviewSelect>>', self.on_video_select)
        detail_frame = ttk.Frame(tab)
        detail_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(detail_frame, text="分析結果:").pack(anchor="w")
        self.video_detail_text = scrolledtext.ScrolledText(detail_frame, width=110, height=10, font=("Arial", 10), bg="#1e1e1e", fg="white")
        self.video_detail_text.pack()
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
        analysis = self.db.get_analysis(video_db_id)
        self.video_detail_text.delete("1.0", tk.END)
        if analysis:
            self.video_detail_text.insert(tk.END, analysis['raw_analysis'])

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
            response = self.gemini.model.generate_content(f"以下は複数のコメディ作者のパターン分析結果です。全体を通して見られる面白いコメディの共通法則を抽出してください。\n\n{patterns_text}")
            self.global_analysis_text.delete("1.0", tk.END)
            self.global_analysis_text.insert(tk.END, response.text)
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
