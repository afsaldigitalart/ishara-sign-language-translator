import os
import cv2
import mediapipe as mp
import pandas as pdclear
import numpy as np
from tqdm import tqdm

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.5)

# Define paths
base_folder = r"model training\training_data"
train_folder = os.path.join(base_folder, "train")
test_folder = os.path.join(base_folder, "test")
train_csv = r"model training\csv\train_landmarks.csv"

def process_images(folder_path, output_csv):
    """Process all images in a folder and save landmarks to CSV."""
    all_data = []
    
    # Get all sign classes (assuming they're subfolders)
    sign_classes = [d for d in os.listdir(folder_path) 
                    if os.path.isdir(os.path.join(folder_path, d))]
    
    for sign_class in sign_classes:
        class_folder = os.path.join(folder_path, sign_class)
        print(f"Processing class: {sign_class}")
        
        for filename in tqdm(os.listdir(class_folder)):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                # Read image
                image_path = os.path.join(class_folder, filename)
                image = cv2.imread(image_path)
                
                # Convert to RGB (MediaPipe requires RGB input)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Process image with MediaPipe
                results = hands.process(image_rgb)
                
                # If hands are detected
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Create a list for this observation
                        row = [image_path, sign_class]
                        
                        # Extract all landmarks (x, y, z for each of the 21 landmarks)
                        for oi, landmark in enumerate(hand_landmarks.landmark):
                            row.extend([landmark.x, landmark.y, landmark.z])
                        
                        # Add to our dataset
                        all_data.append(row)
                else:
                    print(f"No hands detected in {image_path}")
    
    # Create column names
    columns = ['image_path', 'label']
    for i in range(21):  # 21 landmarks per hand
        columns.extend([f'x{i}', f'y{i}', f'z{i}'])
    
    # Create DataFrame and save to CSV
    landmarks_df = pdclear.DataFrame(all_data, columns=columns)
    landmarks_df.to_csv(output_csv, index=False)
    
    print(f"Saved {len(landmarks_df)} hand landmark entries to {output_csv}")
    return landmarks_df

# Process train and test folders
print("Processing training images...")
train_df = process_images(train_folder, train_csv)

print(f"\nCompleted extraction of hand landmarks.")
print(f"Training data: {len(train_df)} entries")