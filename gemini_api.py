import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

ANALYSIS_PROMPT = '''
以下はYouTube動画の字幕（コメディ/コント）です。
このコンテンツが「なぜ面白いのか」をロジカルに分析してください。

## 分析項目
1. 擦り続けている概念/言葉
2. ボケのパターン
3. ツッコミのパターン
4. 構造（導入→展開→オチ）
5. このコンテンツの公式（○○×○○→○○）

## 字幕テキスト
{transcript}
'''

AUTHOR_PATTERN_PROMPT = '''
以下は同じ作者による複数のコメディ動画の分析結果です。
共通パターンを抽出してください。

## 分析項目
1. この作者の特徴的なボケのパターン
2. この作者の特徴的なツッコミのパターン
3. この作者がよく使う構造
4. この作者の公式
5. この作者のスタイルを再現するポイント

## 各動画の分析結果
{analyses}
'''

GENERATE_SKIT_PROMPT = '''
あなたは「{author_name}」のゴーストライターです。
セリフサンプルを完全に模倣して新しいコントを書いてください。

## 絶対厳守ルール

### 1. セリフサンプルの構造を完全コピー
- ボケとツッコミの役割をサンプルと同じにする
- ツッコミのスタイル（オウム返し、冷静な指摘、等）をサンプルと同じにする
- 両方がボケているサンプルでない限り、片方は常識人

### 2. 短く
- 5〜8往復程度

### 3. トーンを合わせる
- セリフサンプルで「！」「？」が少なければ使わない
- 淡々としていれば淡々と

## テーマ
{theme}

## ★これを完全に模倣せよ★
{transcripts}

## 参考
{analyses}

{pattern}

## 出力
タイトル: 〇〇

A:
B:
...
'''

class GeminiAPI:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)

    def analyze_video(self, transcript):
        try:
            prompt = ANALYSIS_PROMPT.format(transcript=transcript)
            response = self.model.generate_content(prompt)
            return {'success': True, 'analysis': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def analyze_author_patterns(self, analyses_text):
        try:
            prompt = AUTHOR_PATTERN_PROMPT.format(analyses=analyses_text)
            response = self.model.generate_content(prompt)
            return {'success': True, 'analysis': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_short_skit(self, author_name, pattern, transcripts, analyses, theme="自由"):
        try:
            prompt = GENERATE_SKIT_PROMPT.format(
                author_name=author_name,
                pattern=pattern if pattern else "（パターン分析なし）",
                transcripts=transcripts,
                analyses=analyses if analyses else "（分析結果なし）",
                theme=theme if theme else "自由"
            )
            response = self.model.generate_content(prompt)
            return {'success': True, 'skit': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
