from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import numpy as np
from PIL import Image
import cv2
import firebase_admin
from firebase_admin import credentials, storage
from io import BytesIO
import requests
from datetime import timedelta
import tempfile
from gradio_client import Client, handle_file
import re

# Initialize Firebase
try:
    cred = credentials.Certificate("iti110-project-firebase-adminsdk-fbsvc-91f399e4ca.json")  
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'iti110-project.firebasestorage.app' 
    })
    print("Firebase Admin SDK initialized successfully!")
except FileNotFoundError:
    print("Error: Firebase credentials file not found.")
except ValueError as e:
    print(f"Error initializing Firebase: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Endpoint to handle image upload and inspection
@app.route('/upload/image', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file.seek(0)

    # Upload file to Firebase Storage
    bucket = storage.bucket()
    blob = bucket.blob(f"uploads/{file.filename}")
    if not blob.exists():
        blob.upload_from_file(file)
        
    # Generate a signed URL for the uploaded file
    file_url = blob.generate_signed_url(expiration=timedelta(hours=1), method='GET')
    print(file_url)

    # Call AI model in HF for prediction
    client = Client("DennyW/WeldPrediction")
    result = client.predict(
		image=handle_file(file_url),
        is_frame="No",
		api_name="/predict_image"
    )
    print(result)

    # Define a regex pattern to extract the result and confidence
    pattern = r"Result: (\w+), Confidence: ([\d.]+)"

    # Use re.search to find the matches
    match = re.search(pattern, result)

    if match:
        status = match.group(1)  # Extract status
        details = match.group(2)  # Extract confidence

    result = {"status": status, "details": details}
    
    return jsonify(result), 200

# Endpoint to handle video upload and inspection
@app.route('/upload/video', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    filename = secure_filename(file.filename)
    #file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    #file.save(file_path)
    file.seek(0)

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
            
        bucket = storage.bucket()
        original_blob = bucket.blob(f"uploads/{file.filename}")
        if not original_blob.exists():
            #blob.upload_from_file(file)
            original_blob.upload_from_filename(temp_file_path)

        # Generate signed URL of the video
        original_video_url = original_blob.generate_signed_url(expiration=timedelta(hours=1), method='GET')

        file.seek(0)
        
        
        cap = cv2.VideoCapture(temp_file_path)
        
        acceptable_frames = 0
        rejectable_frames = 0
        frame_predictions = []
        frame_index = 0
        frame_count = 0
        frame_skip_interval = 10
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / frame_skip_interval)

        # Video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        # Create a temporary file for the output video
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_output_file:
            temp_output_path = temp_output_file.name

        # Output video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_output_path, fourcc, fps, (frame_width, frame_height))

        # Process video frames one at a time
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Downsample by only processing specific frame
            frame_count += 1
            if frame_count % frame_skip_interval != 0:
                continue

            _, frame_buffer = cv2.imencode('.jpg', frame)
            ori_frame_blob = bucket.blob(f"preprocessed_frames/frame_{frame_index}.jpg")
            ori_frame_blob.upload_from_string(frame_buffer.tobytes(), content_type='image/jpeg')
            ori_frame_url = ori_frame_blob.generate_signed_url(expiration=timedelta(hours=1), method='GET')

            client = Client("DennyW/WeldPrediction")
            result = client.predict(
                image=handle_file(ori_frame_url),
                is_frame="Yes",
                api_name="/predict_image"
            )
            print(result)
            # Define a regex pattern to extract the result and confidence
            pattern = r"Result: (\w+), Confidence: ([\d.]+)"

            # Use re.search to find the matches
            match = re.search(pattern, result)

            if match:
                status = match.group(1)  # Extract status
                confidence = float(match.group(2))  # Extract confidence
            
            # Interpret the prediction for the frame
            if status == "Accepted":
                acceptable_frames += 1
            else:
                rejectable_frames += 1

            # Add the processed frame result to list
            frame_predictions.append({
                "index": frame_index,
                "status": status,
                "confidence": float(confidence)  # Convert confidence to float
            })
            frame_index += 1

            # Overlay results
            text_color = (0, 0, 255)  # Red color (BGR format)
            if status == "Rejected":
                text_color = (0, 0, 255) # Red color (BGR format)

            else:
                text_color = (0, 255, 0) # Green color (BGR format)

            cv2.putText(frame, f"Class: {status}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)
            
            cv2.putText(frame, f"Confidence: {confidence:.2f}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Write to output video
            out.write(frame)

            # Save the processed frame to Firebase Storage
            _, frame_buffer = cv2.imencode('.jpg', frame)
            frame_blob = bucket.blob(f"processed_frames/frame_{frame_index}.jpg")
            frame_blob.upload_from_string(frame_buffer.tobytes(), content_type='image/jpeg')
            frame_url = frame_blob.generate_signed_url(expiration=timedelta(hours=1), method='GET')

            # Add the frame URL to the predictions list
            frame_predictions[-1]["frame_url"] = frame_url

        cap.release()
        out.release()
     
        # Upload the processed video to Firebase Storage
        output_video_blob = bucket.blob(f"processed_videos/{file.filename}")
        #output_video_blob.upload_from_string(output_video_buffer.getvalue(), content_type='video/mp4')
        output_video_blob.upload_from_filename(temp_output_path, content_type='video/mp4')
        processed_video_url = output_video_blob.generate_signed_url(expiration=timedelta(hours=1), method='GET')

        # Calculate percentages
        acceptable_percentage = (acceptable_frames / total_frames) * 100
        rejectable_percentage = (rejectable_frames / total_frames) * 100

        return jsonify({
            "total_frames": total_frames,
            "acceptable_frames": acceptable_frames,
            "rejectable_frames": rejectable_frames,
            "acceptable_percentage": acceptable_percentage,
            "rejectable_percentage": rejectable_percentage,
            "frame_predictions": frame_predictions,
            "video_url": original_video_url,
            "processed_video_url": processed_video_url
        }), 200
    finally:
        # Clean up the temporary files
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)


# Endpoint to handle additional training data upload
@app.route('/train', methods=['POST'])
def train_model():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Save the file (for demonstration purposes)
    # Upload file to Firebase Storage
    bucket = storage.bucket()
    blob = bucket.blob(f"training/{file.filename}")
    if not blob.exists():
        blob.upload_from_file(file)

    return jsonify({"message": "Training data uploaded successfully"}), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    bucket = storage.bucket()
    blob = bucket.blob(f"processed_frames/{filename}")

    if not blob.exists():
        return "File not found", 404

    # Generate a signed URL with a short expiration time
    file_url = blob.generate_signed_url(expiration=timedelta(minutes=20), method='GET')

    return redirect(file_url)


if __name__ == '__main__':
    # Create uploads and training_data directories if they don't exist
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('training_data', exist_ok=True)
    app.run(debug=True)