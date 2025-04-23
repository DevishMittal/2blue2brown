# app/controllers/synchronized_voiceover.py

import os
import re
import json
import tempfile
import subprocess
from datetime import datetime
from gtts import gTTS
import numpy as np
from pydub import AudioSegment

class SynchronizedVoiceover:
    """
    Class to generate and synchronize voice narrations for animations
    with precise timing matched to the Manim animations.
    """
    
    def __init__(self, script_file=None, scene_name="LSTMScene", lang='en', tld='us'):
        """
        Initialize SynchronizedVoiceover with a Manim script file
        
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
        
    def parse_script(self):
        """Parse Manim script file to extract animation timing and narration text"""
        if not self.script_file or not os.path.exists(self.script_file):
            print("Script file not found")
            return False
            
        try:
            with open(self.script_file, 'r', encoding='utf-8') as f:
                self.script_content = f.read()
                
            # Find scene class definition
            scene_pattern = rf'class\s+{self.scene_name}\s*\(Scene\)\s*:(.*?)(?:class\s+\w+|\Z)'
            scene_match = re.search(scene_pattern, self.script_content, re.DOTALL)
            
            if not scene_match:
                print(f"Could not find scene class {self.scene_name}")
                return False
                
            scene_code = scene_match.group(1)
            
            # Extract animation blocks and associated comments
            segments = self._extract_animation_segments(scene_code)
            
            if segments:
                self.narration_segments = segments
                return True
                
            return False
            
        except Exception as e:
            print(f"Error parsing script: {e}")
            return False
            
    def _extract_animation_segments(self, scene_code):
        """Extract animation segments with timing and potential narration text"""
        segments = []
        
        # Look for animation blocks and associated comments
        animation_pattern = r'(?:#\s*(.*?)\s*\n)?\s*self\.play\((.*?)\)(?:[\s\n]*self\.wait\(([0-9.]+)\))?'
        wait_pattern = r'(?:#\s*(.*?)\s*\n)?\s*self\.wait\(([0-9.]+)\)'
        
        # Extract animation blocks
        for match in re.finditer(animation_pattern, scene_code, re.DOTALL):
            comment = match.group(1)
            animation = match.group(2)
            wait_time = float(match.group(3) or 1.0)  # Default to 1.0 if not specified
            
            # If there's a comment, use it as narration text
            if comment:
                narration = comment.strip()
            else:
                # Try to extract meaningful description from the animation
                narration = self._generate_narration_from_animation(animation)
                
            segments.append({
                'narration': narration,
                'duration': wait_time,
                'animation': animation
            })
            
        # Extract stand-alone wait blocks
        for match in re.finditer(wait_pattern, scene_code, re.DOTALL):
            comment = match.group(1)
            wait_time = float(match.group(2) or 1.0)
            
            if comment:
                segments.append({
                    'narration': comment.strip(),
                    'duration': wait_time,
                    'animation': 'wait'
                })
                
        return segments
        
    def _generate_narration_from_animation(self, animation_code):
        """Generate narration text from animation code if no comment is available"""
        # Try to extract meaningful text from the animation code
        text_match = re.search(r'Text\([\'"]([^\'"]+)[\'"]', animation_code)
        if text_match:
            return text_match.group(1)
            
        # Check for common animation types and generate descriptions
        if 'Create' in animation_code:
            obj_match = re.search(r'Create\((\w+)', animation_code)
            if obj_match:
                return f"Creating {obj_match.group(1)}"
                
        if 'Write' in animation_code:
            obj_match = re.search(r'Write\((\w+)', animation_code)
            if obj_match:
                return f"Writing {obj_match.group(1)}"
                
        if 'FadeIn' in animation_code:
            obj_match = re.search(r'FadeIn\((\w+)', animation_code)
            if obj_match:
                return f"Fading in {obj_match.group(1)}"
                
        # Default to a generic description
        return "Continuing with the animation"
    
    def generate_synchronized_voiceover(self):
        """Generate synchronized voice segments for each narration part"""
        if not self.narration_segments:
            print("No narration segments found")
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
            output_path = os.path.join(video_dir, f"{name}_with_sync_audio{ext}")
        
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

    def generate_script_with_comments(self):
        """
        Generate an enhanced Manim script with proper narration comments
        that will be used for synchronization
        
        Returns:
        - Path to the enhanced script file
        """
        if not self.script_file or not os.path.exists(self.script_file):
            print("Script file not found")
            return None
            
        try:
            with open(self.script_file, 'r', encoding='utf-8') as f:
                script_content = f.read()
                
            # Get explanations from any available comment blocks at the top
            explanations = self._extract_explanation_from_comments(script_content)
            
            # Find scene class definition
            scene_pattern = rf'class\s+{self.scene_name}\s*\(Scene\)\s*:(.*?)(?:class\s+\w+|\Z)'
            scene_match = re.search(scene_pattern, script_content, re.DOTALL)
            
            if not scene_match:
                return self.script_file
                
            scene_code = scene_match.group(1)
            
            # Find key animation points where we should add narration comments
            enhanced_scene_code = self._add_narration_comments(scene_code, explanations)
            
            # Replace the original scene code with the enhanced one
            enhanced_script = script_content.replace(scene_code, enhanced_scene_code)
            
            # Save to a new file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_script_path = os.path.join(os.path.dirname(self.script_file), 
                                             f"enhanced_{timestamp}_manim.py")
            
            with open(output_script_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_script)
                
            return output_script_path
                
        except Exception as e:
            print(f"Error enhancing script with narration comments: {e}")
            return self.script_file
            
    def _extract_explanation_from_comments(self, script_content):
        """Extract explanations from the comment blocks at the top of the script"""
        # Look for top comment block
        top_comment_match = re.match(r'^#\s*(.*?)(?=\n\s*(?:#|\n|from|import))', script_content, re.DOTALL)
        
        explanations = {}
        if top_comment_match:
            comment_text = top_comment_match.group(1).strip()
            
            # Split into sentences or paragraphs
            sentences = re.split(r'(?<=[.!?])\s+', comment_text)
            
            # Store useful explanations
            for i, sentence in enumerate(sentences):
                if len(sentence) > 20:  # Only keep meaningful sentences
                    explanations[i] = sentence
                    
        return explanations
        
    def _add_narration_comments(self, scene_code, explanations):
        """Add narration comments to key animation points in the scene code"""
        enhanced_code = scene_code
        
        # Find all animation play() and wait() calls without existing comments
        animation_pattern = r'(\s+)(?<!#.*)self\.play\((.*?)\)'
        wait_pattern = r'(\s+)(?<!#.*)self\.wait\(([0-9.]+)\)'
        
        # Track which explanations have been used
        used_explanations = set()
        
        # Add comments to animations
        animation_matches = list(re.finditer(animation_pattern, enhanced_code, re.DOTALL))
        for i, match in enumerate(animation_matches):
            indent = match.group(1)
            animation = match.group(2)
            
            # Try to find a good explanation
            narration = None
            
            # First try to infer from the animation itself
            narration = self._generate_narration_from_animation(animation)
            
            # If no narration yet, try to use an explanation from the comment block
            if not narration and explanations and i < len(explanations):
                # Find an unused explanation
                for idx in sorted(explanations.keys()):
                    if idx not in used_explanations:
                        narration = explanations[idx]
                        used_explanations.add(idx)
                        break
            
            if narration:
                # Add the comment before the animation
                comment_line = f"{indent}# {narration}\n"
                enhanced_code = enhanced_code.replace(match.group(0), comment_line + match.group(0), 1)
        
        # Also add comments to wait calls that might need narration
        wait_matches = list(re.finditer(wait_pattern, enhanced_code, re.DOTALL))
        for match in wait_matches:
            indent = match.group(1)
            wait_time = float(match.group(2))
            
            # Only add narration if wait time is significant
            if wait_time >= 2.0:
                narration = None
                
                # Try to use remaining explanations
                if explanations:
                    for idx in sorted(explanations.keys()):
                        if idx not in used_explanations:
                            narration = explanations[idx]
                            used_explanations.add(idx)
                            break
                            
                # If no explanation found, create a generic one
                if not narration:
                    narration = "Taking a moment to observe the animation"
                    
                # Add the comment before the wait
                comment_line = f"{indent}# {narration}\n"
                enhanced_code = enhanced_code.replace(match.group(0), comment_line + match.group(0), 1)
                
        return enhanced_code