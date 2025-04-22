# main.py

import os
import sys
import time

# Ensure the 'app' folder is in the Python path.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import node functions for the pipeline.
from app.langgraph_nodes.context import load_context
from app.langgraph_nodes.decision import should_generate_video
from app.langgraph_nodes.director import run_director_and_summarizer
from app.langgraph_nodes.clip_agents import generate_clips
from app.langgraph_nodes.chat_response import chat_response

# Import supporting controllers.
from app.controllers.combiner import CombinedCodeGenerator
from app.controllers.video_maker import VideoMaker

def execute_pipeline(state):
    # Run load_context node.
    state.update(load_context(state))
    # Run decision node to determine if a video is needed.
    state.update(should_generate_video(state))
    
    if state.get("make_video"):
        # Run director to get scene plan and summary.
        state.update(run_director_and_summarizer(state))
        # Generate code chunks for each scene.
        state.update(generate_clips(state))
    else:
        # Otherwise, simply get a chat response.
        state.update(chat_response(state))
    
    return state

def main():
    user_prompt = input("Enter a concept you'd like explained: ")
    
    # Initial pipeline state.
    state = { 
        "user_input": user_prompt,
        "session_id": None,
        "content_structure": {
            "introduction": True,
            "core_concepts": True,
            "visual_examples": True,
            "real_world_applications": True,
            "summary": True
    }
}
    
    # Execute the pipeline.
    final_state = execute_pipeline(state)
    
    # Check if video code chunks were generated.
    code_chunks = final_state.get("code_chunks", [])
    
    if code_chunks:
        # Combine the code chunks into one Manim script.
        combiner = CombinedCodeGenerator(code_chunks)
        combined_file = combiner.save_to_file(folder="generated_manim", filename="manim.py")
        print(f"Combined Manim script saved to: {combined_file}")
        
        # Generate a session_id if one doesn't exist
        session_id = final_state.get("session_id") or int(time.time())
        
        # Render the video using VideoMaker with voiceover
        video_maker = VideoMaker(
            script_file=combined_file,
            scene_name="LSTMScene",
            quality="l",             # Use 'l' (low) quality flag.
            preview=False,
            session_id=session_id
        )
        
        # Get the script text for voiceover
        script_text = final_state.get("chat_response", "")
        
        # Extract AI response if no chat response available
        if not script_text:
            script_text = video_maker.ai_response
        
        # Render video with automatic voiceover integration
        video_file = video_maker.render_video(add_voiceover=True)
        
        print(f"Video file path: {video_file}")
    else:
        # If no video was generated, just output the chat response.
        print("No video generated. The chat response is:\n")
        print(final_state.get("chat_response", "No response available."))

if __name__ == "__main__":
    main()
