import os
import tempfile
from gtts import gTTS
import subprocess
import re
from datetime import datetime

class VoiceOverMaker:
    """
    Class to generate voice narrations for videos using Google Text-to-Speech (gTTS)
    """
    
    def __init__(self, text=None, lang='en', tld='us', slow=False):
        """
        Initialize VoiceOverMaker with text to convert to speech
        
        Parameters:
        - text: Text to convert to speech
        - lang: Language for TTS (default: 'en' for English)
        - tld: Top Level Domain for accent (default: 'us' for American English)
        - slow: Whether to speak slowly (default: False)
        """
        self.text = text
        self.lang = lang
        self.tld = tld
        self.slow = slow
        self.output_path = None
        
    def set_text(self, text):
        """Set the text to be converted to speech"""
        self.text = text
        
    def set_text_from_script(self, script_file):
        """Extract narration text from a Manim script file comments"""
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for any comments that might contain the explanation
            comments = re.findall(r'#\s*(.*)', content)
            if comments:
                cleaned_comments = []
                for comment in comments:
                    # Skip common code comments like imports or basic explanations
                    if not (comment.startswith('import') or 
                           'filepath:' in comment or 
                           'class ' in comment or 
                           'def ' in comment or
                           comment.strip() == ''):
                        cleaned_comments.append(comment)
                
                if cleaned_comments:
                    # Convert to proper sentences and paragraphs
                    text = ' '.join(cleaned_comments)
                    # Remove repeated whitespace
                    text = re.sub(r'\s+', ' ', text)
                    self.text = text
                    return True
                
            # If no useful comments, look for content in scene descriptions
            scene_desc = re.search(r'scene_description = "(.*?)"', content)
            if scene_desc:
                self.text = scene_desc.group(1)
                return True
                
            # If still no content, use subtitle texts
            subtitles = re.findall(r'subtitle\s*=\s*Text\("([^"]+)"', content)
            if subtitles:
                self.text = " ".join(subtitles)
                return True
                
            # Final fallback
            self.text = "Mathematical visualization of important concepts and their relationships."
            return False
                
        except Exception as e:
            print(f"Error extracting text from script: {e}")
            self.text = "Mathematical visualization demonstration."
            return False
            
    def generate_voiceover(self):
        """Generate the voiceover audio file"""
        if not self.text:
            print("No text provided for voiceover generation")
            return None
            
        try:
            # Create temp dir if needed
            temp_dir = os.path.join(os.getcwd(), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_path = os.path.join(temp_dir, f"voiceover_{timestamp}.mp3")
            
            # Create gTTS object
            tts = gTTS(text=self.text, lang=self.lang, tld=self.tld, slow=self.slow)
            
            # Save to file
            tts.save(self.output_path)
            print(f"Voiceover saved to {self.output_path}")
            
            return self.output_path
            
        except Exception as e:
            print(f"Error generating voiceover: {e}")
            return None
    
    def combine_with_video(self, video_path, output_path=None):
        """
        Combine the voiceover audio with a video file
        
        Parameters:
        - video_path: Path to the input video file
        - output_path: Path for the output video with audio (optional)
        
        Returns:
        - Path to the output video file with audio
        """
        if not self.output_path:
            self.generate_voiceover()
            
        if not self.output_path or not os.path.exists(self.output_path):
            print("Voiceover generation failed")
            return video_path
            
        if not output_path:
            # Generate output path if not provided
            video_dir = os.path.dirname(video_path)
            video_name = os.path.basename(video_path)
            name, ext = os.path.splitext(video_name)
            output_path = os.path.join(video_dir, f"{name}_with_audio{ext}")
        
        try:
            # Use ffmpeg to combine video with audio
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,     # Input video
                "-i", self.output_path,  # Input audio
                "-c:v", "copy",       # Copy video stream without re-encoding
                "-c:a", "aac",        # Convert audio to AAC format
                "-shortest",          # End when the shortest input ends
                output_path
            ]
            
            process = subprocess.run(cmd, check=False, capture_output=True)
            
            if process.returncode != 0:
                print(f"FFmpeg error: {process.stderr.decode('utf-8')}")
                return video_path
                
            return output_path
            
        except Exception as e:
            print(f"Error combining video and audio: {e}")
            return video_path
