# app/controllers/video_maker.py

import subprocess
import sys
import os
from datetime import datetime
import tempfile
import re
from PIL import Image, ImageDraw, ImageFont
import textwrap

class VideoMaker:
    def __init__(self, script_file, scene_name="MainScene", quality="l", preview=True):
        self.script_file = script_file
        self.scene_name = scene_name
        self.quality = quality
        self.preview = preview
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

    def render_video(self):
        # First try the standard Manim approach
        video_path = self._try_manim_render()
        if video_path and os.path.exists(video_path):
            return video_path
            
        # If Manim fails, fall back to automatic video generation
        print("Manim rendering failed. Generating automatic video instead.")
        return self._generate_auto_video()
        
    def _try_manim_render(self):
        """Try to render with Manim first"""
        try:
            # First, analyze and fix the script file for common errors
            self._preprocess_script_file()
            
            # Check if manim is installed
            process = subprocess.run(["manim", "--version"], 
                                    check=False, 
                                    capture_output=True, 
                                    text=True)
            
            if process.returncode != 0:
                print("Manim check failed. Using automatic video generation.")
                return None
                
            command = ["manim", "render"]
            
            if self.preview:
                command.append("-p")
            
            # Map quality names
            quality_map = {"low": "l", "medium": "m", "high": "h"}
            q = self.quality.lower()
            quality_flag = quality_map.get(q, q)
            command.extend(["-q", quality_flag])
            
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
            
    def _preprocess_script_file(self):
        """Analyze and fix common errors in the Manim script before rendering"""
        try:
            if not os.path.exists(self.script_file):
                print(f"Script file {self.script_file} does not exist.")
                return
                
            with open(self.script_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for and fix common errors
            fixes_applied = False
            
            # Fix 1: Incorrect random point generation using np.array with random.uniform
            if re.search(r'random\.uniform\(np\.array\(\[', content):
                print("Fixing incorrect random point generation...")
                content = re.sub(
                    r'random\.uniform\(np\.array\(\[([-\d.]+),\s*([-\d.]+)(?:,\s*\d+)?\]\)(?:,\s*np\.array\(\[([-\d.]+),\s*([-\d.]+)(?:,\s*\d+)?\]\))?\)',
                    r'np.random.uniform(\1, \2)',
                    content
                )
                fixes_applied = True
                
            # Fix 2: Add missing numpy import
            if 'np.' in content and 'import numpy as np' not in content:
                print("Adding missing numpy import...")
                content = content.replace('from manim import *', 'from manim import *\nimport numpy as np')
                fixes_applied = True
                
            # Fix 3: Add missing random import if needed
            if 'random.' in content and 'import random' not in content:
                print("Adding missing random import...")
                content = content.replace('from manim import *', 'from manim import *\nimport random')
                fixes_applied = True
                
            # Fix 4: Add random seed for reproducibility
            if 'np.random' in content and 'np.random.seed' not in content:
                print("Adding random seed for reproducibility...")
                pattern = r'(class\s+LSTMScene.*?\n\s+def\s+construct.*?\n\s+)'
                replacement = r'\1        np.random.seed(42)  # For reproducibility\n        '
                content = re.sub(pattern, replacement, content)
                fixes_applied = True
                
            # Check for linear regression specific issues
            if 'linear regression' in content.lower() or 'best fit' in content.lower():
                print("Detected linear regression content, applying specific fixes...")
                content, lr_fixes = self._fix_linear_regression_script(content)
                fixes_applied = fixes_applied or lr_fixes
                
            # Write back the modified content if fixes were applied
            if fixes_applied:
                print("Applied fixes to the Manim script.")
                with open(self.script_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
        except Exception as e:
            print(f"Error preprocessing Manim script: {e}")
            # Continue with the rendering process even if preprocessing fails
            
    def _fix_linear_regression_script(self, content):
        """Apply specific fixes for linear regression scripts"""
        fixes_applied = False
        
        # Fix common pattern with random point generation in linear regression
        if 'random' in content and 'point' in content:
            # Check for problematic random point generation
            if re.search(r'point\s*=.*?random\.uniform', content) or re.search(r'x\s*=.*?random\.uniform', content):
                print("Fixing linear regression point generation...")
                
                # Create a replacement block with proper data generation
                replacement = """
        # Generate random data points properly
        np.random.seed(42)  # For reproducibility
        x_values = np.random.uniform(-2, 2, 10)
        # Create y values with some linear relationship plus noise
        y_values = 0.5 * x_values + 0.5 + np.random.normal(0, 0.3, 10)
        
        # Convert to 3D points and create dots
        points = [np.array([x, y, 0]) for x, y in zip(x_values, y_values)]
        dots = [Dot(point=point, radius=0.05) for point in points]
        
        # Show the points
        self.play(*[Create(dot) for dot in dots])
        self.wait(1)
"""
                
                # Find where the point generation starts
                point_gen_pattern = r'(\s+# (?:Create|Generate|Place|Draw) (?:data )?points.*?\n\s+)(?:data_points|points) = \[\]'
                if re.search(point_gen_pattern, content):
                    # Replace the entire points generation and animation section
                    content_parts = re.split(point_gen_pattern, content, 1)
                    if len(content_parts) > 2:
                        # Remove the next part that creates the points
                        next_section = re.split(r'\s+self\.wait\([\d\.]+\)\s*\n', content_parts[2], 1)
                        if len(next_section) > 1:
                            # Only keep the content after the point creation section
                            content = content_parts[0] + content_parts[1] + replacement + next_section[1]
                            fixes_applied = True
                
        # Fix best fit line calculation to use polyfit
        if 'best fit' in content.lower() or 'regression' in content.lower():
            if not 'polyfit' in content and ('Line' in content or 'line' in content):
                print("Adding proper best fit line calculation...")
                
                line_creation_pattern = r'(\s+# (?:Create|Generate|Draw) (?:best fit|hypothesis) line.*?\n\s+)(?:best_fit_line|hypothesis_line) = Line\('
                
                if re.search(line_creation_pattern, content):
                    line_calc = """
        # Calculate best fit line using numpy polyfit
        coefficients = np.polyfit(x_values, y_values, 1)
        slope = coefficients[0]
        intercept = coefficients[1]
        
        # Create best fit line with calculated values
        best_fit_line = Line(
            start=np.array([-3, slope * -3 + intercept, 0]), 
            end=np.array([3, slope * 3 + intercept, 0]), 
            color=YELLOW
        )
"""
                    content_parts = re.split(line_creation_pattern, content, 1)
                    if len(content_parts) > 2:
                        # Find where this section ends
                        next_section = re.split(r'\s+self\.play\(Create\((?:best_fit_line|hypothesis_line)\)\)\s*', content_parts[2], 1)
                        
                        if len(next_section) > 1:
                            # Replace with the proper calculation
                            content = content_parts[0] + content_parts[1] + line_calc + "        self.play(Create(best_fit_line))" + next_section[1]
                            fixes_applied = True
                
                # Add equation text if not present
                if not 'equation' in content.lower() and fixes_applied:
                    equation_addition = """
        # Show the equation of the line
        equation_text = Text(f"y = {slope:.2f}x + {intercept:.2f}", font_size=24).next_to(best_fit_line, DOWN)
        self.play(Write(equation_text))
        self.wait(1)
"""
                    # Find a good place to insert it - after the best fit line is created
                    wait_pattern = r'(\s+self\.play\(Create\(best_fit_line\)\)\s*\n\s+self\.wait\([\d\.]+\))'
                    content = re.sub(wait_pattern, r'\1' + equation_addition, content)
        
        return content, fixes_applied

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
            output_video = os.path.join(os.getcwd(), 'media', 'videos', 'auto_generated.mp4')
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
        
    def _create_slide_image(self, text, output_path, is_title=False):
        """Create a single slide as an image"""
        width, height = 1280, 720
        
        # Create image with gradient background
        image = Image.new('RGB', (width, height), color=(25, 25, 40))
        draw = ImageDraw.Draw(image)
        
        try:
            # Try to load a nice font, fall back to default if not available
            try:
                if is_title:
                    font = ImageFont.truetype("arial.ttf", 60)
                    small_font = ImageFont.truetype("arial.ttf", 30)
                else:
                    font = ImageFont.truetype("arial.ttf", 40)
                    small_font = ImageFont.truetype("arial.ttf", 24)
            except:
                if is_title:
                    font = ImageFont.load_default()
                    small_font = ImageFont.load_default()
                else:
                    font = ImageFont.load_default()
                    small_font = ImageFont.load_default()
            
            # Add gradient
            for y in range(height):
                r = int(25 + (y/height) * 30)
                g = int(25 + (y/height) * 30)
                b = int(40 + (y/height) * 40)
                for x in range(width):
                    draw.point((x, y), fill=(r, g, b))
            
            # Draw decorative elements
            if is_title:
                # Title slide design
                draw.rectangle([100, 100, width-100, height-100], 
                              outline=(100, 150, 255), width=5)
                
                # Add title text
                draw.text((width//2, height//2-50), text, 
                         font=font, fill=(255, 255, 255), anchor="mm")
                
                # Add subtitle
                draw.text((width//2, height//2+50), 
                         "Mathematical Visualization", 
                         font=small_font, fill=(200, 200, 255), anchor="mm")
                         
                # Add timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d")
                draw.text((width//2, height-150), 
                         timestamp, 
                         font=small_font, fill=(180, 180, 220), anchor="mm")
            else:
                # Regular slide design with wrapped text
                margin = 100
                wrapper = textwrap.TextWrapper(width=60)
                wrapped_text = wrapper.fill(text)
                lines = wrapped_text.split('\n')
                
                y_position = height//2 - (len(lines) * 30)//2
                for line in lines:
                    draw.text((width//2, y_position), line, 
                             font=font, fill=(255, 255, 255), anchor="mm")
                    y_position += 50
            
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
            
    def _create_video_from_images(self, image_files, output_path, slide_duration=3.0):
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
            
    def _create_simple_fallback_video(self):
        """Create a very simple fallback video as last resort"""
        fallback_dir = os.path.join(os.getcwd(), "backend", "media", "fallback")
        os.makedirs(fallback_dir, exist_ok=True)
        
        fallback_path = os.path.join(fallback_dir, "simple_fallback.mp4")
        
        try:
            # Basic text content
            text = "Mathematical Visualization\n\nThis video shows concepts in mathematics and their applications."
            
            # Write text to file
            text_path = os.path.join(fallback_dir, "text.txt")
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
