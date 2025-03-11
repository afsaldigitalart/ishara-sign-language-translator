# app.py - FastAPI WebSocket Server
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import cv2
import mediapipe as mp
import numpy as np
import joblib
import base64
import json
import uvicorn
from io import BytesIO
from PIL import Image

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.3
)

# Load the model, scaler, and labels
try:
    model = joblib.load(r'model/sign_language_model.pkl')
    scaler = joblib.load(r'model/sign_language_scaler.pkl')
    labels = joblib.load(r'model/sign_labels.pkl')
    print(f"Loaded model with {len(labels)} signs: {labels}")
    num_expected_features = scaler.n_features_in_
    print(f"Model expects {num_expected_features} features.")
except FileNotFoundError as e:
    print(f"Error loading model files: {e}")
    exit(1)

# For smoothing predictions
prediction_history = []
history_length = 5

def smooth_prediction(new_pred, history=prediction_history, max_length=history_length):
    """Use a simple majority vote from recent predictions."""
    history.append(new_pred)
    if len(history) > max_length:
        history.pop(0)
    
    # Count occurrences of each prediction
    from collections import Counter
    counter = Counter(history)
    
    # Return the most common prediction
    return counter.most_common(1)[0][0]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established")
    
    try:
        while True:
            # Receive the JSON message from the client
            data = await websocket.receive_text()
            json_data = json.loads(data)
            
            # Get base64 encoded image
            base64_image = json_data.get("frame")
            
            if not base64_image:
                continue
                
            # Decode base64 to image
            image_bytes = base64.b64decode(base64_image)
            image = Image.open(BytesIO(image_bytes))
            
            # Convert PIL Image to numpy array for OpenCV
            image_np = np.array(image)
            
            # Convert from RGB to BGR (if needed)
            if len(image_np.shape) == 3 and image_np.shape[2] == 3:
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
            
            # Process with MediaPipe
            image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
            results = hands.process(image_rgb)
            
            prediction = ""
            confidence = 0.0
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Extract landmarks for prediction
                    landmarks = []
                    for landmark in hand_landmarks.landmark:
                        landmarks.extend([landmark.x, landmark.y, landmark.z])
                    
                    # Ensure we have the expected number of features
                    if len(landmarks) != num_expected_features:
                        if len(landmarks) > num_expected_features:
                            landmarks = landmarks[:num_expected_features]
                        else:
                            landmarks.extend([0] * (num_expected_features - len(landmarks)))
                    
                    # Scale the landmarks and reshape for prediction
                    landmarks_scaled = scaler.transform(np.array(landmarks).reshape(1, -1))
                    
                    # Predict the sign
                    raw_prediction = model.predict(landmarks_scaled)[0]
                    confidence = float(np.max(model.predict_proba(landmarks_scaled)))
                    
                    # Smooth prediction for stability
                    prediction = smooth_prediction(raw_prediction)
                    
                    # Only return a prediction if confidence is high enough
                    if confidence < 0.3:
                        prediction = ""
                    
                    # For now, we only process the first detected hand
                    break
            
            # Send the prediction back to the client
            await websocket.send_json({
                "prediction": prediction,
                "confidence": confidence
            })
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        print("WebSocket connection closed")

@app.get("/")
def read_root():
    return {"message": "Sign Language Translation API - Connect via WebSocket"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)