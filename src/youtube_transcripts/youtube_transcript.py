import time

import pandas as pd
from googleapiclient.discovery import build
from tqdm.auto import tqdm
from youtube_transcript_api import (
    YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
)
# Only require if YouTube block requests
# from youtube_transcript_api.proxies import WebshareProxyConfig

from config.config import settings
from src.utils.logger import get_logger

logger = get_logger("youtube_transcript")

class YouTubeTranscriptCollector:
    def __init__(self):
        self.youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)
        self.channels = settings.channels
        self.max_videos_per_channel = settings.max_videos_per_channel
        self.language = settings.language
    
    def _resolve_channel_id(self, channel_input: str) -> dict:
        """
        Resolve a YouTube channel handle or ID to its channel ID and title.

        This function takes either a full channel ID (starting with 'UC') or a 
        channel handle (starting with '@') and returns a dictionary containing 
        the channel ID and the channel's title.

        Args:
            channel_input (str): The YouTube channel identifier, either a channel 
                ID (24 characters, starting with 'UC') or a handle (starting with '@').
        
        Returns:
            dict: A dictionary with keys:
                - 'channel_id' (str): The YouTube channel's unique ID.
                - 'channel_title' (str): The title of the channel.
        """
        if channel_input.startswith("UC") and len(channel_input) == 24:
            resp = self.youtube.channels().list(part="snippet", id=channel_input).execute()
        else:
            handle = channel_input.lstrip("@")
            resp = self.youtube.channels().list(part="snippet", forHandle=handle).execute()

        if not resp.get("items"):
            raise ValueError(f"Channel not found: {channel_input}")

        item = resp["items"][0]
        return {"channel_id": item["id"], "channel_title": item["snippet"]["title"]}
    
    def _get_uploads_playlist_id(self, channel_id: str) -> str:
        """
        Retrieve the uploads playlist ID for a given YouTube channel.

        Every YouTube channel has a special "uploads" playlist that contains all 
        videos uploaded by that channel. This function fetches the playlist ID 
        corresponding to that uploads playlist.

        Args:
            channel_id (str): The unique ID of the YouTube channel (starts with 'UC').

        Returns:
            str: The playlist ID of the channel's uploads playlist.
        """
        resp = self.youtube.channels().list(part="contentDetails", id=channel_id).execute()
        return resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    def _get_videos_from_playlist(self, playlist_id: str, max_videos=None) -> list:
        """
        Fetch video details from a YouTube playlist.

        This function retrieves all videos from the specified playlist, returning 
        their video IDs, titles, and publication dates. It handles pagination 
        automatically and can optionally limit the number of videos returned.

        Args:
            playlist_id (str): The ID of the YouTube playlist to fetch videos from.
            max_videos (int, optional): The maximum number of videos to retrieve. 
                If None, all videos in the playlist are returned.
        
        Returns:
            list of dict: A list of dictionaries, each containing:
                - 'video_id' (str): The unique ID of the video.
                - 'title' (str): The title of the video.
                - 'published_at' (str): The ISO 8601 timestamp of when the video 
                was published.
        """
        videos = []
        next_page_token = None

        while True:
            resp = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            ).execute()

            for item in resp["items"]:
                snippet = item["snippet"]
                videos.append({
                    "video_id":     snippet["resourceId"]["videoId"],
                    "title":        snippet["title"],
                    "published_at": snippet["publishedAt"],
                })

            next_page_token = resp.get("nextPageToken")
            if not next_page_token:
                break
            if max_videos and len(videos) >= max_videos:
                break

        return videos[:max_videos] if max_videos else videos
    
    def _get_transcript(self, video_id: str) -> str | None:
        """
        Fetch the transcript text for a YouTube video.

        This function retrieves the transcript for the specified video in the 
        requested language. It first tries to fetch a manually created transcript, 
        and if unavailable, falls back to an automatically generated transcript. 
        If no transcript is available or an error occurs, it returns None.

        Args:
            video_id (str): The unique ID of the YouTube video.
            language (str, optional): Defaults to 'en'.
        
        Returns:
            str or None: The full transcript text as a single string, or None if 
            the transcript is unavailable.
        """
        try:
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.list(video_id)

            try:
                transcript = transcript_list.find_transcript([self.language])
            except NoTranscriptFound:
                transcript = transcript_list.find_generated_transcript([self.language])

            segments = transcript.fetch()
            return " ".join(seg.text for seg in segments)

        except (NoTranscriptFound, TranscriptsDisabled):
            return None
        except Exception as e:
            logger.warning("Error fetching transcript for %s: %s", video_id, e)
            return None
    
    def collect(self) -> pd.DataFrame:
        """
        Collect transcripts for all configured YouTube channels.

        Iterates over each channel in `self.channels`, resolves the channel ID,
        fetches videos from the uploads playlist up to `self.max_videos_per_channel`,
        and retrieves the transcript for each video in `self.language`.

        Returns:
            pd.DataFrame: A DataFrame where each row represents a video, with columns:
                - 'channel' (str): The channel's display title.
                - 'channel_id' (str): The channel's unique YouTube ID.
                - 'video_id' (str): The video's unique YouTube ID.
                - 'title' (str): The video title.
                - 'published_at' (str): ISO 8601 timestamp of when the video was published.
                - 'url' (str): Full YouTube URL for the video.
                - 'transcript' (str or None): The transcript text, or None if unavailable.
                - 'transcript_available' (bool): Whether a transcript was successfully retrieved.
        """
        all_records = []

        for channel_input in self.channels:
            logger.info("Processing channel: %s", channel_input)

            try:
                channel_info  = self._resolve_channel_id(channel_input)
                channel_id    = channel_info["channel_id"]
                channel_title = channel_info["channel_title"]
                logger.info("Resolved channel: %s (%s)", channel_title, channel_id)

                playlist_id = self._get_uploads_playlist_id(channel_id)
                videos      = self._get_videos_from_playlist(playlist_id, max_videos=self.max_videos_per_channel)
                logger.info("Found %d videos for channel: %s", len(videos), channel_title)

            except Exception as e:
                logger.error("Could not fetch channel %s: %s", channel_input, e)
                continue

            for video in tqdm(videos, desc=f"Transcripts [{channel_title}]"):
                transcript = self._get_transcript(video["video_id"])
                all_records.append({
                    "channel":              channel_title,
                    "channel_id":           channel_id,
                    "video_id":             video["video_id"],
                    "title":                video["title"],
                    "published_at":         video["published_at"],
                    "url":                  f"https://www.youtube.com/watch?v={video['video_id']}",
                    "transcript":           transcript,
                    "transcript_available": transcript is not None,
                })
                time.sleep(2)

        df = pd.DataFrame(all_records)
        logger.info(
            "Done. %d videos total. Transcripts available: %d / %d",
            len(df), df["transcript_available"].sum(), len(df)
        )
        return df
