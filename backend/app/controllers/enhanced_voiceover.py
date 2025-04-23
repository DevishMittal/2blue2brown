# app/controllers/enhanced_voiceover.py

import os
import re
import json
import tempfile
import subprocess
from datetime import datetime
from gtts import gTTS
import numpy as np
from pydub import AudioSegment
from app.langgraph_nodes.voiceover_script_agent import VoiceoverScriptAgent

class EnhancedVoiceover:
    """
    Enhanced voiceover generator that creates educational narration for animations
    using a specialized script agent rather than generating literal descriptions.
    """
    
    def __init__(self, script_file=None, scene_name="LSTMScene", lang='en', tld='us'):
        """
        Initialize EnhancedVoiceover with a Manim script file
        
        Parameters:
        - script_file: Path to the Manim script file
        - scene_name: Name of the scene class to parse
        - lang: Language for TTS (default: 'en' for English)
        - tld: Top Level Domain for accent (default: 'us' for American English)
        """
        self.script_file = script_file
        self.scene_name = scene_name
        self.lang = lang
        self.tld = tld
        self.script_content = None
        self.narration_segments = []
        self.output_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(self.output_dir, exist_ok=True)
        self.script_agent = VoiceoverScriptAgent()
        
    def generate_educational_script(self, educational_level="general"):
        """Generate an educational voiceover script using the VoiceoverScriptAgent"""
        if not self.script_file or not os.path.exists(self.script_file):
            print("Script file not found")
            return False
        
        try:
            # Read the script content
            with open(self.script_file, 'r', encoding='utf-8') as f:
                self.script_content = f.read()
                
            # Generate a script using the VoiceoverScriptAgent
            voiceover_script = self.script_agent.generate_script(
                manim_code=self.script_content,
                educational_level=educational_level
            )
            
            # Convert the script to narration segments
            self.narration_segments = []
            for segment in voiceover_script.get("animation_scripts", []):
                self.narration_segments.append({
                    "narration": segment["script"],
                    "duration": segment["wait_time"],
                    "animation_index": segment["animation_index"]
                })
                
            return len(self.narration_segments) > 0
            
        except Exception as e:
            print(f"Error generating educational script: {e}")
            return False
    
    def generate_synchronized_voiceover(self):
        """Generate synchronized voice segments for each narration part"""
        if not self.narration_segments:
            if not self.generate_educational_script():
                print("Failed to generate narration segments")
                return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_segments = []
        audio_files = []
        
        for i, segment in enumerate(self.narration_segments):
            if not segment['narration']:
                continue
                
            # Generate audio for this segment
            audio_file = os.path.join(self.output_dir, f"segment_{timestamp}_{i}.mp3")
            try:
                tts = gTTS(text=segment['narration'], lang=self.lang, tld=self.tld, slow=False)
                tts.save(audio_file)
                audio_files.append(audio_file)
                
                # Load with pydub to adjust timing
                audio = AudioSegment.from_mp3(audio_file)
                
                # Calculate target duration based on animation wait time
                target_duration_ms = segment['duration'] * 1000
                current_duration_ms = len(audio)
                
                # If audio is longer than animation, speed it up slightly
                if current_duration_ms > target_duration_ms:
                    # Speed up by at most 20%
                    speed_factor = min(current_duration_ms / target_duration_ms, 1.2)
                    audio = self._adjust_audio_speed(audio, speed_factor)
                    
                audio_segments.append(audio)
                
            except Exception as e:
                print(f"Error generating audio for segment {i}: {e}")
                
        if not audio_segments:
            return None
            
        # Combine all segments into one audio file
        combined_audio = audio_segments[0]
        for segment in audio_segments[1:]:
            combined_audio = combined_audio + segment
            
        combined_file = os.path.join(self.output_dir, f"combined_voiceover_{timestamp}.mp3")
        combined_audio.export(combined_file, format="mp3")
        
        # Cleanup individual segments
        for file in audio_files:
            try:
                os.remove(file)
            except:
                pass
                
        return combined_file
        
    def _adjust_audio_speed(self, audio, speed_factor):
        """Adjust audio speed without changing pitch"""
        if speed_factor == 1.0:
            return audio
            
        # For small adjustments, this simple approach works reasonably well
        return audio.speedup(playback_speed=speed_factor)
        
    def add_voiceover_to_video(self, video_file, output_path=None):
        """
        Add the synchronized voiceover to the video
        
        Parameters:
        - video_file: Path to the input video file
        - output_path: Path for the output video with audio (optional)
        
        Returns:
        - Path to the output video file with synchronized audio
        """
        if not os.path.exists(video_file):
            print("Video file not found")
            return None
            
        # Generate voiceover
        audio_file = self.generate_synchronized_voiceover()
        if not audio_file or not os.path.exists(audio_file):
            print("Failed to generate voiceover")
            return video_file
            
        if not output_path:
            # Generate output path if not provided
            video_dir = os.path.dirname(video_file)
            video_name = os.path.basename(video_file)
            name, ext = os.path.splitext(video_name)
            output_path = os.path.join(video_dir, f"{name}_with_enhanced_audio{ext}")
        
        try:
            # Use ffmpeg to combine video with audio
            cmd = [
                "ffmpeg", "-y",
                "-i", video_file,     # Input video
                "-i", audio_file,     # Input audio
                "-c:v", "copy",       # Copy video stream without re-encoding
                "-c:a", "aac",        # Convert audio to AAC format
                "-shortest",          # End when the shortest input ends
                output_path
            ]
            
            process = subprocess.run(cmd, check=False, capture_output=True)
            
            if process.returncode != 0:
                print(f"FFmpeg error: {process.stderr.decode('utf-8')}")
                return video_file
                
            return output_path
            
        except Exception as e:
            print(f"Error adding voiceover to video: {e}")
            return video_file