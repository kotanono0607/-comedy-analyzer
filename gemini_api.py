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
以下のセリフサンプルを熟読し、この作者の「声」で新しいコントを書いてください。

## 絶対厳守ルール

### 1. 句読点・記号のルール
- セリフサンプルで「！」「？」「！？」が使われていない場合、絶対に使わない
- セリフサンプルの句読点の打ち方を完全にコピーする
- 淡々としたトーンの場合、淡々と書く

### 2. ツッコミの温度感
- セリフサンプルのツッコミが冷静なら、冷静に書く
- 「なんでだよ！」のような熱いツッコミがサンプルにないなら使わない
- 元の温度感を絶対に上げない

### 3. 言い回しの模倣
- セリフサンプルにある語尾をそのまま使う
- セリフサンプルにある表現・フレーズを積極的に流用する
- 新しい言い回しを発明しない

## テーマ
{theme}

## ★最重要★ このセリフを完全に模倣せよ
以下がこの作者の実際のセリフです。句読点、語尾、温度感をすべてコピーしてください。

{transcripts}

## 参考情報（補助）
{analyses}

{pattern}

## 出力
タイトル: 〇〇

【台本】
A: セリフ
B: セリフ
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
