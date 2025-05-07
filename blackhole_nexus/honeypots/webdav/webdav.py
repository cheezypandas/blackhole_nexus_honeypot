from flask import Flask, request, jsonify
import json
from datetime import datetime
import os
import logging
from logging.handlers import RotatingFileHandler
from logging.handlers import RotatingFileHandler

# Initialise Flask
app = Flask("BlackholeNexusApp")

# after app = Flask(...)
LOG_DIR = os.path.join(PROJECT_ROOT, "logging")
JSON_LOG = os.path.join(LOG_DIR, "upload_log.json")
os.makedirs(LOG_DIR, exist_ok=True)

handler = RotatingFileHandler(JSON_LOG, maxBytes=1_000_000, backupCount=3)
handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

@app.route('/upload', methods=['PUT'])
def upload():
    # build your log entry
    log_entry = {
      "timestamp": datetime.utcnow().isoformat() + "Z",
      "source_ip": request.remote_addr,
      "action": "file_upload",
      "filename": request.files.get('file').filename if request.files.get('file') else None,
      "user_agent": request.headers.get("User-Agent","")
    }

    # 1) log it immediately
    app.logger.info(json.dumps(log_entry))

    # 2) now handle the file  
    uploaded = request.files.get('file')
    if not uploaded:
        return jsonify({"status":"error","message":"No file"}),400

    out_path = os.path.join(os.path.dirname(__file__),'uploads', uploaded.filename)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    uploaded.save(out_path)

    return jsonify({"status":"success"}),200


# Base paths
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))  # Two levels up
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
LOG_DIR = os.path.join(PROJECT_ROOT, 'logging')
LOG_FILE_PATH = os.path.join(LOG_DIR, 'blackhole_nexus.log')
JSON_LOG_FILE = os.path.join(LOG_DIR, 'upload_log.json')

# Hardcoded log directory path (adjust if needed)
LOG_FOLDER = '/mnt/d/GitHub Projects/blackhole_nexus/logging'
LOG_FILE = os.path.join(LOG_FOLDER, 'blackhole_nexus.log')

# Ensure logging directory exists
os.makedirs(LOG_FOLDER, exist_ok=True)

# Set up logger for file and console output
logger = logging.getLogger('BlackholeNexus')
logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
logger.addHandler(console_handler)

# Confirm setup
logger.info("=== Blackhole Nexus Logger Initialised ===")
logger.info(f"Logs will be saved to: {LOG_FILE}")

# Ensure all directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Setup rotating log handler for the log file
file_handler_rotating = RotatingFileHandler(LOG_FILE_PATH, maxBytes=1_000_000, backupCount=5)
file_handler_rotating.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Console handler for printing to terminal
console_handler_rotating = logging.StreamHandler()
console_handler_rotating.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))

# Add both handlers to the logger
logger.addHandler(file_handler_rotating)
logger.addHandler(console_handler_rotating)

logger.info("=== Blackhole Nexus WebDAV Honeypot Initialised ===")

@app.route('/upload', methods=['GET', 'PUT'])
def handle_upload():
    logger.info(f"Request: {request.remote_addr} {request.method} {request.path} - UA: {request.headers.get('User-Agent', '')}")
    
    if request.method == 'PUT':
        uploaded_file = request.files.get('file')
        if not uploaded_file:
            logger.warning("Upload attempt with no file.")
            return jsonify({"status": "error", "message": "No file uploaded!"}), 400

        original_filename = uploaded_file.filename
        timestamp = datetime.utcnow().isoformat()
        logger.info(f"Received file: {original_filename} at {timestamp}")

        # JSON log entry
        log_entry = {
            "timestamp": timestamp,
            "source_ip": request.remote_addr,
            "action": "file_upload",
            "filename": original_filename,
            "user_agent": request.headers.get("User-Agent", ""),
            "method": request.method
        }

        try:
            if os.path.exists(JSON_LOG_FILE):
                with open(JSON_LOG_FILE, 'r+', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
                    data.append(log_entry)
                    f.seek(0)
                    json.dump(data, f, indent=4)
            else:
                with open(JSON_LOG_FILE, 'w', encoding='utf-8') as f:
                    json.dump([log_entry], f, indent=4)
            logger.info(f"Log entry successfully written to {JSON_LOG_FILE}")
        except Exception as e:
            logger.error(f"Failed to write JSON log: {e}")
            return jsonify({"status": "error", "message": f"Logging failed: {str(e)}"}), 500

        unique_filename = f"{timestamp}_{original_filename}".replace(":", "_")
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        try:
            uploaded_file.save(file_path)
            logger.info(f"File saved to {file_path}")
            return jsonify({"status": "success", "message": f"File {original_filename} uploaded successfully!"}), 200
        except Exception as e:
            logger.error(f"File saving failed: {e}")
            return jsonify({"status": "error", "message": f"File saving failed: {str(e)}"}), 500

    # Handle GET requests
    logger.info("GET request served fake data response")
    return "Fake Excel Data", 200

if __name__ == '__main__':
    # Run the Flask app with reloader disabled
    logger.info("Launching Flask app on 0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
