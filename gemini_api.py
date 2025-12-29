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
以下は「{author_name}」というコメディ作者の実際のセリフサンプルです。
このセリフの「言い回し」「口調」「ニュアンス」「間の取り方」を徹底的に模倣して、
オリジナルのショートコント台本を生成してください。

## 最重要：セリフのニュアンス再現
- 実際のセリフサンプルの言葉選び、語尾、リズムを完全にコピーする
- この作者特有の「クセ」や「言い回し」をそのまま使う
- ツッコミの温度感（強め/弱め/冷静/激しい）を再現する
- ボケの飛躍度合いを同じレベルに保つ

## 生成ルール
1. セリフサンプルにある表現をベースに新しいネタを作る
2. 1〜2分程度で演じられる長さ
3. 台本形式で出力

## テーマ
{theme}

## 実際のセリフサンプル（これを模倣する）
{transcripts}

## 参考：パターン分析（補助情報）
{pattern}

## 出力形式
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

    def generate_short_skit(self, author_name, pattern, transcripts, theme="自由"):
        try:
            prompt = GENERATE_SKIT_PROMPT.format(
                author_name=author_name,
                pattern=pattern if pattern else "（パターン分析なし）",
                transcripts=transcripts,
                theme=theme if theme else "自由"
            )
            response = self.model.generate_content(prompt)
            return {'success': True, 'skit': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
