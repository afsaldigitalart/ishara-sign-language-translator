import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# Load the landmarks CSV file
data_file = r"csv\train_landmarks.csv"  # Update this to your CSV file path
print("Loading data from", data_file)

# Load with low_memory=False to handle mixed types
df = pd.read_csv(data_file, low_memory=False)

# Print column names to debug
print("Columns in dataset:", df.columns.tolist())

# Find the label column and the feature columns
# Assuming first column is path/filename and second is label
# Then all remaining columns are features (x0, y0, z0, etc.)
path_col = df.columns[0]  # First column (likely image_path or filename)
label_col = df.columns[1]  # Second column (likely label)

print(f"Path column: {path_col}")
print(f"Label column: {label_col}")
print(f"Total number of columns: {len(df.columns)}")

# Extract features and target
X = df.drop([path_col, label_col], axis=1)
y = df[label_col]

# Print basic info about the dataset
print(f"\nDataset info:")
print(f"Number of samples: {len(df)}")
print(f"Number of features: {X.shape[1]}")
print(f"Number of classes: {len(y.unique())}")
print(f"Classes: {y.unique().tolist()}")

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"\nTraining with {len(X_train)} samples, testing with {len(X_test)} samples")

# Scale the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train a Random Forest classifier
print("\nTraining model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)

# Evaluate the model
y_pred = model.predict(X_test_scaled)
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Get unique labels
unique_labels = sorted(y.unique())


# Save the model, scaler, and labels
joblib.dump(model, r'model\sign_language_model.pkl')
joblib.dump(scaler, r'model\sign_language_scaler.pkl')
joblib.dump(unique_labels, r'model\sign_labels.pkl.pkl')
print("\nModel, scaler, and label list saved to disk")

print("\nTraining complete.")