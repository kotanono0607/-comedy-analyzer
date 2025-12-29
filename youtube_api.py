import re
from youtube_transcript_api import YouTubeTranscriptApi

class YouTubeAPI:
    def __init__(self):
        self.api = YouTubeTranscriptApi()

    def get_video_id(self, url):
        patterns = [r'v=([^&]+)', r'youtu\.be/([^?]+)', r'shorts/([^?]+)']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return url

    def fetch_transcript(self, video_id):
        try:
            transcript_list = self.api.fetch(video_id, languages=['ja'])
            transcript_text = '\n'.join([entry.text for entry in transcript_list])
            return {'success': True, 'transcript': transcript_text, 'count': len(transcript_list)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
