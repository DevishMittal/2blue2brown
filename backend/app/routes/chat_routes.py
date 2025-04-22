from datetime import datetime
from flask import Blueprint, jsonify, request, send_file
from app.services.supabase import post_message, get_chat_histories, create_new_session
from app.controllers import Chunky, build_graph
import os
import time
import base64
from .blawb import SupabaseStorage

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/create_new_session", methods=["POST"])
def route_send_message():
    result = create_new_session()
    # Handle different result formats
    if isinstance(result, list) and result:
        return jsonify(result[0]), 200
    elif isinstance(result, dict):
        return jsonify(result), 200
    else:
        return jsonify({"error": "Failed to create session"}), 500

@chat_bp.route("/get_chat_histories", methods=["GET"])
def route_chat_histories():
    chat_session_id = request.args.get("chat_session_id")
    if not chat_session_id:
        return jsonify({"error": "Missing chat_session_id parameter"}), 400

    try:
        result = get_chat_histories(chat_session_id)
        # Check if result is an error dictionary or an empty list
        if isinstance(result, dict) and "error" in result:
            return jsonify({"error": result["error"]}), 500
        return jsonify(result), 200
    except Exception as e:
        print(f"Error retrieving chat histories: {e}")
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/get_chat", methods=["GET"])
def get_chat():
    chat_session_id = request.args.get("chat_session_id")
    if not chat_session_id:
        return jsonify({"error": "Missing chat_session_id parameter"}), 400

    try:
        chat_history = get_chat_histories(chat_session_id)
        ai_messages = [msg for msg in chat_history if msg.get("role") == "ai"]
        if not ai_messages:
            return jsonify({"error": "No generated result found for this session"}), 404

        latest_ai_message = ai_messages[-1]
        result = {
            "chat_response": latest_ai_message.get("message"),
            "video": latest_ai_message.get("video_url")
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@chat_bp.route("/chat", methods=["POST"])
def handle_chat():
    from app.controllers import build_graph
    from app.controllers.combiner import CombinedCodeGenerator
    from app.controllers.video_maker import VideoMaker
    import traceback
    
    user_input = request.form.get("user_input")
    session_id = request.form.get("session_id")
    
    # Create a new session if we don't have one
    if not session_id or session_id == "NULL":
        new_session = create_new_session()
        if isinstance(new_session, list) and new_session:
            session_id = new_session[0].get("id")
        elif isinstance(new_session, dict):
            if "error" in new_session:
                print(f"Session creation error: {new_session}")
                # Continue anyway, we'll create a session when posting the message
            else:
                session_id = new_session.get("id")
    
    print("session_id:", session_id)
    print("user_input:", user_input)

    # Initialize these variables
    image_summary = None
    image_url = None
    video_url = None

    if "image" in request.files:
        image_file = request.files["image"]
        if image_file.filename != "":
            try:
                chunky = Chunky()
                file_bytes = image_file.read()
                encoded_image = base64.b64encode(file_bytes).decode('utf-8')
                image_summary = chunky.advanced_image_handling(user_input, encoded_image)
                user_input += f"\n\nThe user also uploaded an image with these contents:\n\n{image_summary}"
                
                # Save the image to a temporary location
                temp_dir = "/tmp"
                temp_path = os.path.join(temp_dir, image_file.filename)
                with open(temp_path, "wb") as temp_file:
                    temp_file.write(file_bytes)
                    
                # Upload the image to Supabase
                storage = SupabaseStorage()
                try:
                    image_url = storage.upload_file(temp_path)
                except Exception as e:
                    print("Error uploading image:", e)
                    # Store locally as fallback if upload fails
                    local_images_dir = os.path.join(os.getcwd(), "backend", "local_db", "images")
                    os.makedirs(local_images_dir, exist_ok=True)
                    local_image_path = os.path.join(local_images_dir, f"{int(time.time())}_{image_file.filename}")
                    with open(local_image_path, "wb") as f:
                        f.write(file_bytes)
                    image_url = f"local://{local_image_path}"
            except Exception as e:
                print(f"Error processing image: {e}")
                traceback.print_exc()

    graph = build_graph()
    state = {
        "user_input": user_input,
        "session_id": session_id,
    }

    try:
        result = graph.invoke(state)
    except Exception as e:
        print("Error invoking graph:", e)
        traceback.print_exc()
        return jsonify({"error": "AI processing failed. Please try again."}), 500

    ai_message = result.get("chat_response")
    chat_session_id = session_id
    
    # Check for code chunks
    code_chunks = result.get("code_chunks", [])
    manim_code = "\n".join(code_chunks) if code_chunks else None
    
    # Initialize video_url as None
    video_url = None
    
    # Only attempt video rendering if we have code chunks
    if manim_code and code_chunks:
        try:
            print("Attempting to generate and render Manim video...")
            
            # Sanitize AI message to remove problematic characters
            ai_message_sanitized = ai_message.replace('\u25cf', '*')  # Replace bullet points with asterisks
            ai_message_sanitized = ''.join(c for c in ai_message_sanitized if ord(c) < 128 or c.isspace())  # Keep ASCII chars only
            ai_message_comment = f"# {ai_message_sanitized.replace('\n', '\n# ')}"
            
            manim_code = ai_message_comment + "\n\n" + manim_code
            
            combiner = CombinedCodeGenerator(code_chunks)
            combined_file = combiner.save_to_file(folder="generated_manim", filename='manim.py')
            
            # Add AI response as comments to the generated file
            with open(combined_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            with open(combined_file, 'w', encoding='utf-8') as f:
                f.write(f"{ai_message_comment}\n\n{file_content}")
            
            print(f"Combined Manim script saved to: {combined_file}")
            
            # Use simpler scene name without timestamp
            scene_name = "LSTMScene"
            
            video_maker = VideoMaker(
                script_file=combined_file,
                scene_name=scene_name,
                quality='l',
                preview=False
            )

            # Get the video file path from render_video()
            video_file = video_maker.render_video()
            print(f"Video file path: {video_file}")

            if video_file and os.path.exists(video_file):
                storage = SupabaseStorage()
                try:
                    print("Uploading video... named: ", video_file)
                    video_url = storage.upload_file(video_file, file_name=f"video_{int(time.time())}.mp4")
                    print(f"Video uploaded successfully. URL: {video_url}")
                except Exception as e:
                    print("Error uploading video: ", e)
                    traceback.print_exc()
                    # Store video locally as fallback
                    local_videos_dir = os.path.join(os.getcwd(), "backend", "local_db", "videos")
                    os.makedirs(local_videos_dir, exist_ok=True)
                    local_video_path = os.path.join(local_videos_dir, f"video_{int(time.time())}.mp4")
                    import shutil
                    shutil.copy(video_file, local_video_path)
                    video_url = f"local://{local_video_path}"
                    print(f"Video saved locally at: {local_video_path}")
            else:
                print("No video file was created or found")
        except Exception as e:
            print(f"Error in video generation/rendering process: {str(e)}")
            traceback.print_exc()

    # Save the user message
    user_post_status = post_message("user", user_input, chat_session_id, image_url=image_url)
    if isinstance(user_post_status, dict) and "error" in user_post_status:
        print(f"Error saving user message: {user_post_status}")
    elif isinstance(user_post_status, dict) and "success" in user_post_status:
        print("User message saved successfully")
        # If chat_session_id was null before, extract it from the response
        if not chat_session_id and "data" in user_post_status:
            chat_session_id = user_post_status["data"].get("chat_session_id")

    # Save the AI response
    ai_post_status = post_message(
        "ai",
        ai_message,
        chat_session_id,
        manim_code=manim_code,
        image_summary=image_summary,
        video_url=video_url
    )
    if isinstance(ai_post_status, dict) and "error" in ai_post_status:
        print(f"Error saving AI message: {ai_post_status}")
    elif isinstance(ai_post_status, dict) and "success" in ai_post_status:
        print("AI message saved successfully")

    # Return the response to the frontend
    response_data = {
        "message": ai_message,
        "video_url": video_url
    }
    
    # Add session_id to response if available
    if chat_session_id:
        response_data["session_id"] = chat_session_id
        
    return jsonify(response_data), 200

@chat_bp.route("/serve_local_file", methods=["GET"])
def serve_local_file():
    file_path = request.args.get("path")
    if not file_path:
        return jsonify({"error": "Missing file path parameter"}), 400
    
    try:
        # Security check to prevent directory traversal
        if ".." in file_path or file_path.startswith("/"):
            return jsonify({"error": "Invalid file path"}), 403
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
            
        # Return the file
        return send_file(file_path)
    except Exception as e:
        print(f"Error serving local file: {e}")
        return jsonify({"error": str(e)}), 500
