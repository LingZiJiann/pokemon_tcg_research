from src.youtube_transcripts.youtube_transcript import YouTubeTranscriptCollector

def main():
    collector = YouTubeTranscriptCollector()
    df = collector.collect()
    print(df)

if __name__ == "__main__":
    main()