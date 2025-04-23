# app/controllers/video_maker.py

import subprocess
import sys
import os
from datetime import datetime
import tempfile
import re
from PIL import Image, ImageDraw, ImageFont
import textwrap
from app.controllers.voiceover_maker import VoiceOverMaker

class VideoMaker:
    def __init__(self, script_file, scene_name="MainScene", quality="l", preview=True, session_id=None):
        self.script_file = script_file
        self.scene_name = scene_name
        self.quality = quality
        self.preview = preview
        self.session_id = session_id
        # Store AI response for fallback mechanism
        self.ai_response = self._extract_ai_response()

    def _extract_ai_response(self):
        """Extract the AI explanation from the generated Manim script comments"""
        try:
            with open(self.script_file, 'r') as f:
                content = f.read()
                
            # Look for any comments that might contain the explanation
            comments = re.findall(r'#\s*(.*)', content)
            if comments:
                return " ".join(comments)
                
            # If no comments, get the class and function descriptions
            descriptions = re.findall(r'class\s+(\w+).*?def\s+construct\s*\(\s*self\s*\):\s*(.*?)def', 
                                     content, re.DOTALL)
            if descriptions:
                return " ".join([d[0] + ": " + d[1] for d in descriptions])
                
            # If still nothing, just return a basic description
            return "Mathematical visualization of concepts."
            
        except Exception as e:
            print(f"Error extracting AI response: {e}")
            return "Advanced mathematical concepts visualization."

    def render_video(self, add_voiceover=True):
        # First try the standard Manim approach
        video_path = self._try_manim_render()
        if video_path and os.path.exists(video_path):
            if add_voiceover:
                video_path = self._add_voiceover_to_video(video_path)
            return video_path
            
        # If Manim fails, fall back to automatic video generation
        print("Manim rendering failed. Generating automatic video instead.")
        video_path = self._generate_auto_video()
        if add_voiceover and video_path:
            video_path = self._add_voiceover_to_video(video_path)
        return video_path
    
    def _add_voiceover_to_video(self, video_path):
        """Add voiceover to the video using VoiceOverMaker"""
        try:
            # Create voiceover maker instance
            voiceover_maker = VoiceOverMaker()
            
            # Extract text from script
            voiceover_maker.set_text_from_script(self.script_file)
            
            # If no text extracted from script, use AI response
            if not voiceover_maker.text or len(voiceover_maker.text) < 10:
                voiceover_maker.set_text(self.ai_response)
            
            # Generate voiceover audio
            voiceover_maker.generate_voiceover()
            
            # Combine with video
            if voiceover_maker.output_path and os.path.exists(voiceover_maker.output_path):
                # Generate output filename with session_id for uniqueness
                if self.session_id:
                    output_dir = os.path.dirname(video_path)
                    timestamp = int(datetime.now().timestamp())
                    basename = f"video_{self.session_id}_{timestamp}_with_audio.mp4"
                    output_path = os.path.join(output_dir, basename)
                else:
                    output_path = None
                    
                return voiceover_maker.combine_with_video(video_path, output_path)
                
            return video_path
            
        except Exception as e:
            print(f"Error adding voiceover: {e}")
            return video_path
        
    def _try_manim_render(self):
        """Try to render with Manim first"""
        try:
            # Check if manim is installed
            process = subprocess.run(["manim", "--version"], 
                                   check=False, 
                                   capture_output=True, 
                                   text=True,
                                   encoding='utf-8',
                                   errors='replace')
            
            if process.returncode != 0:
                print("Manim check failed. Using automatic video generation.")
                return None
                
            # Improved command with higher resolution
            command = ["manim", "render"]
            
            if self.preview:
                command.append("-p")
            
            # Higher quality for better visibility
            command.extend(["-q", "h"])  # Use higher quality
            
            # Use a larger resolution
            command.extend(["--resolution", "1920,1080"])
            
            # Add flags to avoid LaTeX issues
            command.append("--disable_caching")
            
            # Append script file and scene name
            command.append(self.script_file)
            command.append(self.scene_name)
            
            print(f"Executing command: {' '.join(command)}")
            
            # Execute the command
            process = subprocess.run(command, 
                                   check=False, 
                                   capture_output=True, 
                                   text=True,
                                   encoding='utf-8',
                                   errors='replace',
                                   timeout=120)  # 2-minute timeout
            
            if process.returncode != 0:
                print(f"Manim error: {process.stderr}")
                return None
                
            # Try to find the output video
            media_dir = os.path.join(os.getcwd(), 'media', 'videos')
            for root, dirs, files in os.walk(media_dir):
                for file in files:
                    if file.endswith('.mp4') and self.scene_name in file:
                        return os.path.join(root, file)
                        
            # Look in standard locations
            standard_path = os.path.join(media_dir, 'manim', '480p15', f"{self.scene_name}.mp4")
            if os.path.exists(standard_path):
                return standard_path
                
            # Find any mp4 file
            for root, dirs, files in os.walk(media_dir):
                for file in files:
                    if file.endswith('.mp4'):
                        return os.path.join(root, file)
                        
            return None
            
        except Exception as e:
            print(f"Error in Manim rendering: {e}")
            return None
            
    def _generate_auto_video(self):
        """Generate a video automatically from AI response without requiring Manim"""
        try:
            # Create temporary directory for our assets
            temp_dir = tempfile.mkdtemp()
            
            # Get concept explanation from AI response
            explanation = self.ai_response
            if not explanation or len(explanation) < 10:
                explanation = "Visualization of mathematical concepts and equations."
                
            # Split explanation into slides
            slides = self._create_slides_from_text(explanation)
            
            # Generate images for each slide
            image_files = []
            for i, slide_text in enumerate(slides):
                image_path = os.path.join(temp_dir, f"slide_{i:03d}.png")
                self._create_slide_image(slide_text, image_path, i==0)
                image_files.append(image_path)
                
            # Create video with ffmpeg
            # Use session_id for unique filename
            timestamp = int(datetime.now().timestamp())
            
            if self.session_id:
                basename = f"video_{self.session_id}_{timestamp}.mp4"
            else:
                basename = f"video_{timestamp}.mp4"
                
            output_video = os.path.join(os.getcwd(), 'media', 'videos', basename)
            os.makedirs(os.path.dirname(output_video), exist_ok=True)
            
            # Calculate duration based on text length
            total_duration = max(10, min(30, len(explanation) / 50))  # Between 10-30 seconds
            slide_duration = total_duration / len(slides)
            
            # Create video using ffmpeg
            self._create_video_from_images(image_files, output_video, slide_duration)
            
            return output_video
            
        except Exception as e:
            print(f"Error in automatic video generation: {e}")
            fallback_path = self._create_simple_fallback_video()
            return fallback_path
            
    def _create_slides_from_text(self, text):
        """Split text into slides of reasonable size"""
        # Clean text
        text = text.replace('\n', ' ').strip()
        words = text.split()
        
        # Determine how many slides based on text length
        words_per_slide = min(50, max(20, len(words) // 5))  # Between 20-50 words per slide
        
        slides = []
        for i in range(0, len(words), words_per_slide):
            slide = " ".join(words[i:i+words_per_slide])
            slides.append(slide)
            
        # Ensure we have at least 3 slides
        while len(slides) < 3:
            slides.append("Mathematical concepts and visualizations.")
            
        # Add title slide at beginning
        slides.insert(0, "Mathematical Visualization")
        
        return slides
        
    def _create_simple_fallback_video(self):
        """Create a very simple fallback video as last resort"""
        fallback_dir = os.path.join(os.getcwd(), "media", "fallback")
        os.makedirs(fallback_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = int(datetime.now().timestamp())
        if self.session_id:
            basename = f"fallback_{self.session_id}_{timestamp}.mp4"
        else:
            basename = f"fallback_{timestamp}.mp4"
            
        fallback_path = os.path.join(fallback_dir, basename)
        
        try:
            # Basic text content
            text = "Mathematical Visualization\n\nThis video shows concepts in mathematics and their applications."
            
            # Write text to file
            text_path = os.path.join(fallback_dir, f"text_{timestamp}.txt")
            with open(text_path, "w") as f:
                f.write(text)
                
            # Try ffmpeg command for simplest possible video
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", 
                "-i", "color=c=blue:s=1280x720:d=10",
                "-vf", f"drawtext=fontfile=/Windows/Fonts/arial.ttf:textfile={text_path}:fontcolor=white:fontsize=30:x=(w-text_w)/2:y=(h-text_h)/2",
                fallback_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=False, capture_output=True)
            
            if os.path.exists(fallback_path):
                return fallback_path
                
            # If that fails, try even simpler version
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", 
                "-i", "color=c=blue:s=640x480:d=5",
                fallback_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=False, capture_output=True)
            
            if os.path.exists(fallback_path):
                return fallback_path
                
        except Exception as e:
            print(f"Error creating fallback video: {e}")
            
        return None

    def _create_slide_image(self, text, output_path, is_title=False):
        """Create a single slide as an image with improved layout"""
        width, height = 1920, 1080  # Increased resolution
        
        # Create image with gradient background
        image = Image.new('RGB', (width, height), color=(25, 25, 40))
        draw = ImageDraw.Draw(image)
        
        try:
            # Try to load a nice font, fall back to default if not available
            try:
                if is_title:
                    font = ImageFont.truetype("arial.ttf", 80)  # Larger font
                    small_font = ImageFont.truetype("arial.ttf", 40)
                else:
                    font = ImageFont.truetype("arial.ttf", 60)  # Larger font
                    small_font = ImageFont.truetype("arial.ttf", 36)
            except:
                # Fallback fonts
                if is_title:
                    font = ImageFont.load_default()
                    small_font = ImageFont.load_default()
                else:
                    font = ImageFont.load_default()
                    small_font = ImageFont.load_default()
            
            # Add gradient background
            for y in range(height):
                r = int(25 + (y/height) * 30)
                g = int(25 + (y/height) * 30)
                b = int(40 + (y/height) * 40)
                for x in range(width):
                    draw.point((x, y), fill=(r, g, b))
            
            if is_title:
                # Title slide design with more space
                draw.rectangle([150, 150, width-150, height-150], 
                              outline=(100, 150, 255), width=8)
                
                # Add title text
                draw.text((width//2, height//2-100), text, 
                         font=font, fill=(255, 255, 255), anchor="mm")
                
                # Add subtitle with more space
                draw.text((width//2, height//2+100), 
                         "Mathematical Visualization", 
                         font=small_font, fill=(200, 200, 255), anchor="mm")
                         
                # Add timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d")
                draw.text((width//2, height-200), 
                         timestamp, 
                         font=small_font, fill=(180, 180, 220), anchor="mm")
            else:
                # Regular slide design with wrapped text and better spacing
                margin = 200  # Increased margin
                wrapper = textwrap.TextWrapper(width=40)  # Fewer words per line
                wrapped_text = wrapper.fill(text)
                lines = wrapped_text.split('\n')
                
                # Calculate position with more spacing between lines
                line_height = 70  # Increased line height
                y_position = height//2 - (len(lines) * line_height)//2
                
                for line in lines:
                    draw.text((width//2, y_position), line, 
                             font=font, fill=(255, 255, 255), anchor="mm")
                    y_position += line_height
            
            # Save the image
            image.save(output_path)
            return True
            
        except Exception as e:
            print(f"Error creating slide image: {e}")
            # Create very simple backup image
            draw.rectangle([0, 0, width, height], fill=(0, 0, 50))
            draw.text((width//2, height//2), text[:100], fill=(255, 255, 255))
            image.save(output_path)
            return False
            
    def _create_video_from_images(self, image_files, output_path, slide_duration=5.0):
        """Create video from images using ffmpeg"""
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create temporary text file listing images
            list_file = os.path.join(os.path.dirname(image_files[0]), "files.txt")
            with open(list_file, 'w') as f:
                for img in image_files:
                    f.write(f"file '{os.path.basename(img)}'\n")
                    f.write(f"duration {slide_duration}\n")
                # Add last image again to handle last duration
                f.write(f"file '{os.path.basename(image_files[-1])}'\n")
            
            # Run ffmpeg to create video
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-vsync", "vfr",
                "-pix_fmt", "yuv420p",
                "-c:v", "libx264",
                "-crf", "18",  # Higher quality (lower is better, 18-23 is good)
                "-preset", "slow",  # Better compression
                output_path
            ]
            
            process = subprocess.run(cmd, 
                                    check=False, 
                                    capture_output=True, 
                                    cwd=os.path.dirname(image_files[0]))
            
            if process.returncode != 0:
                print(f"FFmpeg error: {process.stderr.decode('utf-8')}")
                return self._create_simple_fallback_video()
                
            return output_path
            
        except Exception as e:
            print(f"Error creating video from images: {e}")
            return self._create_simple_fallback_video()
