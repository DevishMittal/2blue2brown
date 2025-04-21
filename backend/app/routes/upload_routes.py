from flask import jsonify, request, Blueprint, send_from_directory
import os

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("/upload_image", methods=["POST"])
def route_upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No file part named 'image' in request"}), 400

    image_file = request.files["image"]

    if image_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    file_bytes = image_file.read()

    print("File received:")
    print(f"Filename: {image_file.filename}")
    print(f"Content type: {image_file.content_type}")
    print(f"Size: {len(file_bytes)} bytes")

    return jsonify({"message": "File uploaded successfully", "filename": image_file.filename}), 200

@upload_bp.route("/upload_file", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    # Process the file upload
    return jsonify({"message": "File uploaded successfully"}), 200

@upload_bp.route("/media/<filename>", methods=["GET"])
def serve_media(filename):
    """Serve media files from local storage"""
    local_storage_path = os.path.join(os.getcwd(), "local_storage")
    return send_from_directory(local_storage_path, filename)
