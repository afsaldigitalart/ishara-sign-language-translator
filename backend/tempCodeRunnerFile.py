"""This is a temp file generate by the module for processing the code."""

import os
import cv2
import mediapipe as mp
import pandas as pd
import json
from datetime import datetime
import os
import cv2
import mediapipe as mp
import pandas as pd
import json
from datetime import datetime

class HandLandmarkCapture:
    def __init__(self, output_file=r"csv\train_landmarks.csv", class_file=r"D:\sign-language\hand-detection-main\model training\class_names.json"):
        """Initialize the hand landmark capture tool."""
        # Add A, B, C to the classes
        self.default_classes = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C"]
        
        # Load available classes or create new with default
        try:
            with open(class_file, 'r') as f:
                self.classes = json.load(f)
                
            # Check if A, B, C are already in the classes, if not add them
            for letter in ["A", "B", "C"]:
                if letter not in self.classes:
                    self.classes.append(letter)
                    
            # Save updated classes back to file
            with open(class_file, 'w') as f:
                json.dump(self.classes, f)
                
            print(f"Loaded and updated {len(self.classes)} classes: {self.classes}")
        except FileNotFoundError:
            # Use default classes with A, B, C
            self.classes = self.default_classes
            print(f"Class file not found. Using default classes: {self.classes}")
            
            # Save the class list to the JSON file
            with open(class_file, 'w') as f:
                json.dump(self.classes, f)
            print(f"Saved classes to {class_file}")
        
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Drawing specifications
        self.landmark_drawing_spec = self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
        self.connection_drawing_spec = self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
        
        # Output file
        self.output_file = output_file
        self.landmarks_collected = 0
        self.current_class = None
        
        # Create DataFrame columns
        self.columns = ['image_path', 'label']
        for i in range(21):  # 21 landmarks per hand
            self.columns.extend([f'x{i}', f'y{i}', f'z{i}'])
        
        # Check if file exists, load if it does
        if os.path.isfile(self.output_file):
            try:
                self.df = pd.read_csv(self.output_file)
                self.landmarks_collected = len(self.df)
                print(f"Loaded existing dataset with {self.landmarks_collected} samples")
            except Exception as e:
                print(f"Error loading existing file: {e}")
                self.df = pd.DataFrame(columns=self.columns)
        else:
            self.df = pd.DataFrame(columns=self.columns)
            print(f"Created new dataset file: {self.output_file}")

        # Create a class to index mapping for easy selection
        self.class_to_index = {cls: idx for idx, cls in enumerate(self.classes)}
        print("Class mapping:", self.class_to_index)
    
    def save_landmarks(self, landmarks, label, image_path):
        """Save hand landmarks to the dataframe."""
        # Create a new row
        row = [image_path, label]
        
        # Add all landmarks
        for landmark in landmarks:
            row.extend([landmark.x, landmark.y, landmark.z])
        
        # Check if we have the right number of items
        expected_columns = len(self.columns)
        actual_items = len(row)
        
        # If not enough landmarks, pad with zeros
        if actual_items < expected_columns:
            row.extend([0.0] * (expected_columns - actual_items))
        # If too many landmarks, truncate
        elif actual_items > expected_columns:
            row = row[:expected_columns]

        # Append to DataFrame
        new_row = pd.DataFrame([row], columns=self.columns)
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        self.landmarks_collected += 1
        
        # Save to CSV periodically
        if self.landmarks_collected % 10 == 0:
            self.df.to_csv(self.output_file, index=False)
            print(f"Saved {self.landmarks_collected} samples to {self.output_file}")
    
    def capture_landmarks(self):
        """Main loop for capturing landmarks."""
        # Start webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return
        
        # Tracking variables
        self.current_class = None
        is_recording = False
        frames_captured = 0
        sample_counter = 0
        last_key = None
        
        print("\nHand Landmark Capture Tool")
        print("-------------------------")
        print("Press 1-9 to select a numeric sign class")
        print("Press 'a', 'b', or 'c' to select letter classes")
        print("Press SPACE to start/stop recording")
        print("Press 's' to save the dataset")
        print("Press 'q' to quit")
        
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Failed to capture frame.")
                continue
            
            # Flip the image for a selfie-view
            image = cv2.flip(image, 1)
            
            # Process the image
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.hands.process(image_rgb)
            
            # Create a clean copy for display
            display_image = image.copy()
            
            # Draw hand landmarks
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        display_image, 
                        hand_landmarks, 
                        self.mp_hands.HAND_CONNECTIONS,
                        self.landmark_drawing_spec,
                        self.connection_drawing_spec
                    )
                    
                    # If recording, save landmarks
                    if is_recording and self.current_class is not None:
                        # Only save every 3 frames to avoid too similar samples
                        if frames_captured % 3 == 0:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            image_name = f"sample_{self.current_class}_{timestamp}_{sample_counter}.jpg"
                            
                            # Save landmarks
                            self.save_landmarks(
                                hand_landmarks.landmark, 
                                self.current_class, 
                                image_name
                            )
                            sample_counter += 1
            
            # Display class selection
            class_text = f"Current class: {self.current_class}" if self.current_class else "No class selected"
            cv2.putText(
                display_image, 
                class_text, 
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                (255, 255, 0), 
                2
            )
            
            # Display recording status
            status_text = f"RECORDING (samples: {sample_counter})" if is_recording else "NOT RECORDING"
            status_color = (0, 0, 255) if is_recording else (255, 0, 0)
            cv2.putText(
                display_image, 
                status_text, 
                (10, 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                status_color, 
                2
            )
            
            # Display total samples
            cv2.putText(
                display_image, 
                f"Total dataset: {self.landmarks_collected} samples", 
                (10, 110), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (0, 255, 255), 
                2
            )
            
            # Show last key pressed (for debugging)
            if last_key is not None:
                cv2.putText(
                    display_image,
                    f"Last key: {last_key}",
                    (10, 140),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1
                )
            
            # Show available classes
            y_pos = 170
            cv2.putText(
                display_image,
                "Available Classes:",
                (10, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 200, 200),
                1
            )
            
            # Display numeric classes
            for i in range(min(9, len(self.classes))):
                y_pos += 25
                cv2.putText(
                    display_image,
                    f"{i+1}: {self.classes[i]}",
                    (20, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (200, 200, 200),
                    1
                )
            
            # Display letter classes
            letters = ["A", "B", "C"]
            for letter in letters:
                if letter in self.classes:
                    y_pos += 25
                    cv2.putText(
                        display_image,
                        f"{letter.lower()}: {letter}",
                        (20, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (200, 200, 200),
                        1
                    )
            
            # Show the image
            cv2.imshow('Hand Landmark Capture', display_image)
            
            # Handle key presses
            key = cv2.waitKey(5) & 0xFF
            last_key = key  # Store for debugging
            
            # Number keys 1-9 select class
            if 49 <= key <= 57:  # ASCII values for 1-9
                class_idx = key - 49  # Convert to 0-8
                if class_idx < len(self.classes):
                    self.current_class = self.classes[class_idx]
                    print(f"Selected class: {self.current_class}")
            
            # Letter keys a, b, c
            elif key == ord('a') and "A" in self.classes:
                self.current_class = "A"
                print(f"Selected class: {self.current_class}")
            elif key == ord('b') and "B" in self.classes:
                self.current_class = "B"
                print(f"Selected class: {self.current_class}")
            elif key == ord('c') and "C" in self.classes:
                self.current_class = "C"
                print(f"Selected class: {self.current_class}")
            
            # Space toggles recording
            elif key == 32:  # Space
                if self.current_class is None:
                    print("Please select a class before recording")
                else:
                    is_recording = not is_recording
                    status = "Started" if is_recording else "Stopped"
                    print(f"{status} recording for class: {self.current_class}")
                    
                    # Reset sample counter when starting new recording
                    if is_recording:
                        sample_counter = 0
            
            # 's' saves the dataset
            elif key == ord('s'):
                self.df.to_csv(self.output_file, index=False)
                print(f"Saved {self.landmarks_collected} samples to {self.output_file}")
            
            # 'q' quits
            elif key == 27:
                break
            
            # Increment frame counter if recording
            if is_recording:
                frames_captured += 1
        
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        
        # Save the final dataset    capturer.capture_landmarks()
        self.df.to_csv(self.output_file, index=False)
        print(f"Capture complete. Saved {self.landmarks_collected} samples to {self.output_file}")

if __name__ == "__main__":
    # Create data directory if needed
    os.makedirs("data/train", exist_ok=True)
    
    # Create capture tool and run it
    capturer = HandLandmarkCapture()
class HandLandmarkCapture:
    def __init__(self, output_file=r"model training\csv\train_landmarks.csv", class_file=r"model training\class_names.json"):
        """Initialize the hand landmark capture tool."""
        # Add A, B, C to the classes
        self.default_classes = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C"]
        
        # Load available classes or create new with default
        try:
            with open(class_file, 'r') as f:
                self.classes = json.load(f)
                
            # Check if A, B, C are already in the classes, if not add them
            for letter in ["A", "B", "C"]:
                if letter not in self.classes:
                    self.classes.append(letter)
                    
            # Save updated classes back to file
            with open(class_file, 'w') as f:
                json.dump(self.classes, f)
                
            print(f"Loaded and updated {len(self.classes)} classes: {self.classes}")
        except FileNotFoundError:
            # Use default classes with A, B, C
            self.classes = self.default_classes
            print(f"Class file not found. Using default classes: {self.classes}")
            
            # Save the class list to the JSON file
            with open(class_file, 'w') as f:
                json.dump(self.classes, f)
            print(f"Saved classes to {class_file}")
        
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Drawing specificationsk
        self.landmark_drawing_spec = self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
        self.connection_drawing_spec = self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
        
        # Output file
        self.output_file = output_file
        self.landmarks_collected = 0
        self.current_class = None
        
        # Create DataFrame columns
        self.columns = ['image_path', 'label']
        for i in range(21):  # 21 landmarks per hand
            self.columns.extend([f'x{i}', f'y{i}', f'z{i}'])
        
        # Check if file exists, load if it does
        if os.path.isfile(self.output_file):
            try:
                self.df = pd.read_csv(self.output_file)
                self.landmarks_collected = len(self.df)
                print(f"Loaded existing dataset with {self.landmarks_collected} samples")
            except Exception as e:
                print(f"Error loading existing file: {e}")
                self.df = pd.DataFrame(columns=self.columns)
        else:
            self.df = pd.DataFrame(columns=self.columns)
            print(f"Created new dataset file: {self.output_file}")

        # Create a class to index mapping for easy selection
        self.class_to_index = {cls: idx for idx, cls in enumerate(self.classes)}
        print("Class mapping:", self.class_to_index)
    
    def save_landmarks(self, landmarks, label, image_path):
        """Save hand landmarks to the dataframe."""
        # Create a new row
        row = [image_path, label]
        
        # Add all landmarks
        for landmark in landmarks:
            row.extend([landmark.x, landmark.y, landmark.z])
        
        # Check if we have the right number of items
        expected_columns = len(self.columns)
        actual_items = len(row)
        
        # If not enough landmarks, pad with zeros
        if actual_items < expected_columns:
            row.extend([0.0] * (expected_columns - actual_items))
        # If too many landmarks, truncate
        elif actual_items > expected_columns:
            row = row[:expected_columns]

        # Append to DataFrame
        new_row = pd.DataFrame([row], columns=self.columns)
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        self.landmarks_collected += 1
        
        # Save to CSV periodically
        if self.landmarks_collected % 10 == 0:
            self.df.to_csv(self.output_file, index=False)
            print(f"Saved {self.landmarks_collected} samples to {self.output_file}")
    
    def capture_landmarks(self):
        """Main loop for capturing landmarks."""
        # Start webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return
        
        # Tracking variables
        self.current_class = None
        is_recording = False
        frames_captured = 0
        sample_counter = 0
        last_key = None
        
        print("\nHand Landmark Capture Tool")
        print("-------------------------")
        print("Press 1-9 to select a numeric sign class")
        print("Press 'a', 'b', or 'c' to select letter classes")
        print("Press SPACE to start/stop recording")
        print("Press 's' to save the dataset")
        print("Press 'q' to quit")
        
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Failed to capture frame.")
                continue
            
            # Flip the image for a selfie-view
            image = cv2.flip(image, 1)
            
            # Process the image
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.hands.process(image_rgb)
            
            # Create a clean copy for display
            display_image = image.copy()
            
            # Draw hand landmarks
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        display_image, 
                        hand_landmarks, 
                        self.mp_hands.HAND_CONNECTIONS,
                        self.landmark_drawing_spec,
                        self.connection_drawing_spec
                    )
                    
                    # If recording, save landmarks
                    if is_recording and self.current_class is not None:
                        # Only save every 3 frames to avoid too similar samples
                        if frames_captured % 3 == 0:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            image_name = f"sample_{self.current_class}_{timestamp}_{sample_counter}.jpg"
                            
                            # Save landmarks
                            self.save_landmarks(
                                hand_landmarks.landmark, 
                                self.current_class, 
                                image_name
                            )
                            sample_counter += 1
            
            # Display class selection
            class_text = f"Current class: {self.current_class}" if self.current_class else "No class selected"
            cv2.putText(
                display_image, 
                class_text, 
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                (255, 255, 0), 
                2
            )
            
            # Display recording status
            status_text = f"RECORDING (samples: {sample_counter})" if is_recording else "NOT RECORDING"
            status_color = (0, 0, 255) if is_recording else (255, 0, 0)
            cv2.putText(
                display_image, 
                status_text, 
                (10, 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                status_color, 
                2
            )
            
            # Display total samples
            cv2.putText(
                display_image, 
                f"Total dataset: {self.landmarks_collected} samples", 
                (10, 110), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (0, 255, 255), 
                2
            )
            
            # Show last key pressed (for debugging)
            if last_key is not None:
                cv2.putText(
                    display_image,
                    f"Last key: {last_key}",
                    (10, 140),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1
                )
            
            # Show available classes
            y_pos = 170
            cv2.putText(
                display_image,
                "Available Classes:",
                (10, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 200, 200),
                1
            )
            
            # Display numeric classes
            for i in range(min(9, len(self.classes))):
                y_pos += 25
                cv2.putText(
                    display_image,
                    f"{i+1}: {self.classes[i]}",
                    (20, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (200, 200, 200),
                    1
                )
            
            # Display letter classes
            letters = ["A", "B", "C"]
            for letter in letters:
                if letter in self.classes:
                    y_pos += 25
                    cv2.putText(
                        display_image,
                        f"{letter.lower()}: {letter}",
                        (20, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (200, 200, 200),
                        1
                    )
            
            # Show the image
            cv2.imshow('Hand Landmark Capture', display_image)
            
            # Handle key presses
            key = cv2.waitKey(5) & 0xFF
            last_key = key  # Store for debugging
            
            # Number keys 1-9 select class
            if 49 <= key <= 57:  # ASCII values for 1-9
                class_idx = key - 49  # Convert to 0-8
                if class_idx < len(self.classes):
                    self.current_class = self.classes[class_idx]
                    print(f"Selected class: {self.current_class}")
            
            # Letter keys a, b, c
            elif key == ord('a') and "A" in self.classes:
                self.current_class = "A"
                print(f"Selected class: {self.current_class}")
            elif key == ord('b') and "B" in self.classes:
                self.current_class = "B"
                print(f"Selected class: {self.current_class}")
            elif key == ord('c') and "C" in self.classes:
                self.current_class = "C"
                print(f"Selected class: {self.current_class}")
            
            # Space toggles recording
            elif key == 32:  # Space
                if self.current_class is None:
                    print("Please select a class before recording")
                else:
                    is_recording = not is_recording
                    status = "Started" if is_recording else "Stopped"
                    print(f"{status} recording for class: {self.current_class}")
                    
                    # Reset sample counter when starting new recording
                    if is_recording:
                        sample_counter = 0
            
            # 's' saves the dataset
            elif key == ord('s'):
                self.df.to_csv(self.output_file, index=False)
                print(f"Saved {self.landmarks_collected} samples to {self.output_file}")
            
            # 'q' quits
            elif key == 27:
                break
            
            # Increment frame counter if recording
            if is_recording:
                frames_captured += 1
        
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        
        # Save the final dataset
        self.df.to_csv(self.output_file, index=False)
        print(f"Capture complete. Saved {self.landmarks_collected} samples to {self.output_file}")

if __name__ == "__main__":
    # Create data directory if needed
    os.makedirs("data/train", exist_ok=True)
    
    # Create capture tool and run it
    capturer = HandLandmarkCapture()
    capturer.capture_landmarks()