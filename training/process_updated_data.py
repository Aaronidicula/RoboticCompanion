import pandas as pd
from datetime import datetime  # Explicit import to avoid conflict
import json
from sklearn.model_selection import train_test_split

# Load the updated CSV file
file_path = "training_data_20250627_132921.csv"
data = pd.read_csv(file_path).to_dict(orient='records')
print(f"Loaded {len(data)} conversations from {file_path}.")

# Simple validation
empty_users = [i for i, d in enumerate(data) if pd.isna(d['user']) or not d['user'].strip()]
empty_assistants = [i for i, d in enumerate(data) if pd.isna(d['assistant']) or not d['assistant'].strip()]
if empty_users or empty_assistants:
    print(f"Warning: Empty 'user' at indices {empty_users} or 'assistant' at {empty_assistants}")
else:
    print("Validation: No empty entries found.")
print(f"very_long_responses: {sum(1 for d in data if len(str(d['assistant'])) > 500)}")  # Example threshold

# Save a new version with a timestamp
new_file_name = f"training_data_updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
pd.DataFrame(data).to_csv(new_file_name, index=False)
print(f"Data saved to {new_file_name}.")

# Convert to JSON for Kaggle compatibility
json_data = [{"user": item["user"], "assistant": item["assistant"]} for item in data]
json_file_name = f"training_data_updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(json_file_name, 'w') as json_file:
    json.dump(json_data, json_file, indent=4)
print(f"JSON data saved to {json_file_name}.")

# Split into train and test sets
train_data, test_data = train_test_split(data, test_size=0.2, random_state=42)
pd.DataFrame(train_data).to_csv("training_data_train_20250627_1747.csv", index=False)
pd.DataFrame(test_data).to_csv("training_data_test_20250627_1747.csv", index=False)
print("Train and test sets saved with 80% train and 20% test.")
