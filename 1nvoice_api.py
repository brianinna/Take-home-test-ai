import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Verify if environment variables are successfully loaded
api_key = os.getenv("TEXT_MODEL_API_KEY")
base_url = os.getenv("TEXT_MODEL_API_URL")

# Now environment variables can be accessed via os.environ or os.getenv

# --- 1. Configuration ---
# Your FastAPI server address and endpoint
API_URL = "http://127.0.0.1:8000/api/v1/extract"

# Path to PDF files to upload
FILES_TO_UPLOAD = [
                   # "./Sample Invoices/invoice1.pdf",
                   # "./Sample Invoices/invoice2.pdf",
                   # "./Sample Invoices/invoice3.pdf",
                   "./Sample Invoices/invoice6.pdf",
                   # "./Sample Invoices/invoice5.pdf"
]

# --- 2. Check if files exist ---
print(f"Checking if files exist: {', '.join(FILES_TO_UPLOAD)}")
for filename in FILES_TO_UPLOAD:
    if not os.path.exists(filename):
        print(f"Warning: File {filename} does not exist, please ensure the path is correct and the file exists")
        exit(1)

# Prepare list of files to send
# Format for multipart/form-data is: [('files', ('filename1', file_object1, 'application/pdf')), ('files', ...)]
files_to_send = []
file_objects = []

try:
    # --- 3. Prepare and send request ---
    # Open all files in binary read mode ('rb')
    for filename in FILES_TO_UPLOAD:
        file_obj = open(filename, 'rb')
        file_objects.append(file_obj)
        # The key name "files" needs to correspond to your FastAPI function parameter `files: List[UploadFile]`
        files_to_send.append(('files', (filename, file_obj, 'application/pdf')))

    print(f"\nSending POST request to {API_URL}...")
    # Use requests.post to send files
    response = requests.post(API_URL, files=files_to_send)

    # --- 4. Print results ---
    print("\n✅ Request completed. Server response below:")
    print("-----------------------------------")
    print(f"HTTP 状态码: {response.status_code}")

    # Try to format the response as readable JSON
    try:
        # Use json.dumps to beautify output, especially when handling Chinese characters
        pretty_json = json.dumps(response.json(), indent=2, ensure_ascii=False)
        print(f"Response content (JSON):\n{pretty_json}")
    except requests.exceptions.JSONDecodeError:
        # If the response is not in JSON format, print the text directly
        print(f"Response content (non-JSON):\n{response.text}")
    print("-----------------------------------")

except requests.exceptions.RequestException as e:
    print(f"\n❌ Request failed: {e}")
    print("👉 Please check if your FastAPI service is running normally at http://127.0.0.1:8000.")

finally:
    # --- 5. Cleanup ---
    # Ensure all opened files are closed
    for f in file_objects:
        f.close()

    # No need to delete files as we are using existing files
    print("\nTest completed, no file cleanup needed.")