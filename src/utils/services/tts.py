from typing import List
from pathlib import Path
import os
from elevenlabs import generate, save, set_api_key, Voice
from ..config.settings import settings
from ..models.podcast import PodcastSegment

class TTSService:
    def __init__(self):
        set_api_key(settings.ELEVENLABS_API_KEY)
        
        # Define voice personalities for each speaker
        self.voices = {
            "Clara": Voice(
                voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
                settings={"stability": 0.71, "similarity_boost": 0.5, "style": 0.0, "use_speaker_boost": True}
            ),
            "Ben": Voice(
                voice_id="ErXwobaYiN019PkySvjV",   # Antoni
                settings={"stability": 0.71, "similarity_boost": 0.5, "style": 0.0, "use_speaker_boost": True}
            ),
            "Alice": Voice(
                voice_id="EXAVITQu4vr4xnSDxMaL",  # Bella
                settings={"stability": 0.71, "similarity_boost": 0.5, "style": 0.0, "use_speaker_boost": True}
            )
        }
    
    def generate_audio(self, segments: List[PodcastSegment], output_dir: str = "audio_outputs") -> List[str]:
        """Generate audio files for each segment and return their paths"""
        os.makedirs(output_dir, exist_ok=True)
        audio_files = []
        
        for i, segment in enumerate(segments):
            voice = self.voices.get(segment.speaker, self.voices["Clara"])
            
            # Generate audio for the segment
            audio = generate(
                text=segment.content,
                voice=voice,
                model="eleven_multilingual_v2"
            )
            
            # Save the audio file
            filename = f"{output_dir}/segment_{i+1}_{segment.speaker.lower()}.mp3"
            save(audio, filename)
            audio_files.append(filename)
        
        return audio_files
    
    def combine_audio_files(self, audio_files: List[str], output_file: str):
        """Combine all audio segments into a single podcast file"""
        try:
            from pydub import AudioSegment
            
            combined = AudioSegment.empty()
            for file in audio_files:
                segment = AudioSegment.from_mp3(file)
                combined += segment
            
            # Add a short pause between segments
            pause = AudioSegment.silent(duration=1000)  # 1 second
            final_audio = AudioSegment.empty()
            
            for i, segment in enumerate(combined):
                final_audio += segment
                if i < len(combined) - 1:  # Don't add pause after last segment
                    final_audio += pause
            
            final_audio.export(output_file, format="mp3")
            return output_file
            
        except ImportError:
            print("Please install pydub: poetry add pydub")
            raise 