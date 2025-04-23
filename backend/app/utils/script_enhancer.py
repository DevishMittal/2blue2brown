# app/utils/script_enhancer.py

import os
import re
import sys
from datetime import datetime
from app.controllers.synchronized_voiceover import SynchronizedVoiceover

def enhance_manim_script(script_path, scene_name="LSTMScene"):
    """
    Add narration comments to a Manim script to enable synchronized voiceovers
    
    Parameters:
    - script_path: Path to Manim script
    - scene_name: Name of scene class to enhance
    
    Returns:
    - Path to enhanced script
    """
    if not os.path.exists(script_path):
        print(f"Error: Script file not found: {script_path}")
        return None
        
    print(f"Enhancing Manim script: {script_path}")
    
    sync_voiceover = SynchronizedVoiceover(
        script_file=script_path,
        scene_name=scene_name
    )
    
    enhanced_script_path = sync_voiceover.generate_script_with_comments()
    
    if enhanced_script_path:
        print(f"Enhanced script created: {enhanced_script_path}")
        print("Use this script for better synchronized narration with your animations")
        return enhanced_script_path
    else:
        print("Failed to enhance script")
        return None

def create_animation_with_narration(script_path, scene_name="LSTMScene", quality="h"):
    """
    Create a Manim animation with synchronized narration
    
    Parameters:
    - script_path: Path to Manim script with narration comments
    - scene_name: Name of scene class to render
    - quality: Manim quality setting (l, m, h)
    
    Returns:
    - Path to video with synchronized narration
    """
    from app.controllers.video_maker import VideoMaker
    
    if not os.path.exists(script_path):
        print(f"Error: Script file not found: {script_path}")
        return None
        
    print(f"Creating animation with synchronized narration from: {script_path}")
    
    # First check if script has narration comments
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check for animation blocks with comments
    animation_pattern = r'#\s*(.*?)\s*\n\s*self\.play\('
    has_narration_comments = bool(re.search(animation_pattern, content, re.DOTALL))
    
    if not has_narration_comments:
        print("No narration comments found. Enhancing script first...")
        enhanced_script = enhance_manim_script(script_path, scene_name)
        if enhanced_script:
            script_path = enhanced_script
        
    # Create video with synchronized voiceover
    print("Rendering animation with synchronized narration...")
    video_maker = VideoMaker(
        script_file=script_path,
        scene_name=scene_name,
        quality=quality,
        preview=False
    )
    
    video_path = video_maker.render_video(add_voiceover=True)
    
    if video_path and os.path.exists(video_path):
        print(f"Animation with synchronized narration created: {video_path}")
        return video_path
    else:
        print("Failed to create animation with narration")
        return None
        
if __name__ == "__main__":
    # When run as script, enhance the provided Manim script
    if len(sys.argv) < 2:
        print("Usage: python -m app.utils.script_enhancer <manim_script_path> [scene_name]")
        sys.exit(1)
        
    script_path = sys.argv[1]
    scene_name = sys.argv[2] if len(sys.argv) > 2 else "LSTMScene"
    
    enhance_manim_script(script_path, scene_name)