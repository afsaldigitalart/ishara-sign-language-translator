"""Run this script to check the accuracy of the model and print a classification report.
It shows the prection and the confidence level of the prediction. Uses Open CV to capture the video feed and MediaPipe to detect the hand landmarks.
"""

import cv2
import mediapipe as mp
import numpy as np
import joblib
import time

print("Loading model files...")
# Load the trained model, scaler, and labels 
try:
    model = joblib.load(r'model\sign_language_model.pkl')
    scaler = joblib.load(r'model\sign_language_scaler.pkl')
    labels = joblib.load(r'model\sign_labels.pkl')
    print(f"Loaded model with {len(labels)} signs: {labels}")
except FileNotFoundError as e:
    print(f"Error loading model files: {e}")
    print("Make sure you've run the training script first.")
    exit(1)

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.3
)

# Landmark drawing specifications for better visibility
landmark_drawing_spec = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
connection_drawing_spec = mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)

# Start webcam
print("Initializing webcam...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit(1)

# For FPS calculation
prev_frame_time = 0
new_frame_time = 0

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

print("Starting real-time detection. Press 'q' to quit.")

# Get the number of features expected by the model
num_expected_features = scaler.n_features_in_
print(f"Model expects {num_expected_features} features.")

while cap.isOpened():
    success, image = cap.read()
    if not success:
        print("Ignoring empty camera frame.")
        continue
    
    # Calculate FPS
    new_frame_time = time.time()
    fps = 1/(new_frame_time-prev_frame_time) if prev_frame_time > 0 else 0
    prev_frame_time = new_frame_time
    
    # Flip the image horizontally for a more intuitive selfie-view
    image = cv2.flip(image, 1)
    
    # Convert the image to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Process the image
    results = hands.process(image_rgb)
    
    # Create a clean copy for display
    display_image = image.copy()
    
    # Draw hand landmarks and predict
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw landmarks
            mp_drawing.draw_landmarks(
                display_image, 
                hand_landmarks, 
                mp_hands.HAND_CONNECTIONS,
                landmark_drawing_spec,
                connection_drawing_spec
            )
            
            # Extract landmarks for prediction
            landmarks = []
            for landmark in hand_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
            
            # Ensure we have the expected number of features
            if len(landmarks) != num_expected_features:
                # If model expects more or fewer features, handle this
                if len(landmarks) > num_expected_features:
                    landmarks = landmarks[:num_expected_features]
                else:
                    # Pad with zeros if needed (not ideal but prevents crashes)
                    landmarks.extend([0] * (num_expected_features - len(landmarks)))
                    
            # Scale the landmarks and reshape for prediction
            landmarks_scaled = scaler.transform(np.array(landmarks).reshape(1, -1))
            
            # Predict the sign
            raw_prediction = model.predict(landmarks_scaled)[0]
            prediction_prob = np.max(model.predict_proba(landmarks_scaled))
            
            # Smooth prediction for stability
            prediction = smooth_prediction(raw_prediction)
            
            # Display the prediction if confidence is high enough
            if prediction_prob > 0.6:
                # Display with green text for high confidence
                cv2.putText(
                    display_image, 
                    f"Sign: {prediction} ({prediction_prob:.2f})", 
                    (10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1, 
                    (0, 255, 0), 
                    2
                )
            else:
                # Display with yellow text for low confidence
                cv2.putText(
                    display_image, 
                    f"Sign: {prediction} (Low confidence: {prediction_prob:.2f})", 
                    (10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1, 
                    (0, 255, 255), 
                    2
                )
    else:
        # Display message when no hands detected
        cv2.putText(
            display_image, 
            "No hands detected", 
            (10, 50), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (0, 0, 255), 
            2
        )
    
    # Display FPS
    cv2.putText(
        display_image, 
        f"FPS: {int(fps)}", 
        (10, 30), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        1, 
        (255, 0, 0), 
        2
    )
    
    # Display the image
    cv2.imshow('Sign Language Detection', display_image)
    
    # Break the loop when 'q' is pressed
    if cv2.waitKey(5) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()