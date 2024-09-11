import requests
import json
import os
import time
import argparse
import paramiko
from scp import SCPClient
import socket

# Constants
HOSTNAME = socket.gethostname()
SESSION_FILE = 'session_id'
API_BASE_URL = None
POLL_INTERVAL = 5  # seconds
REMOTE_PATH = '/home/user2402/data' #Remote Directory
REMOTE_HOSTNAME = "139.59.17.95"
REMOTE_PORT = 22
REMOTE_PASSWORD = "dbNdBfw8HO2k7a1s"
REMOTE_USERNAME = "user2402"
CONFIG_PATH = os.path.join( os.path.dirname(os.path.realpath(__file__)) , 'config.json')


def create_json_file():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'w') as json_file:
            json.dump({'API_BASE_URL': f'http://{REMOTE_HOSTNAME}:8080'}, json_file, indent=4)
        print(f"JSON file created with default data at {CONFIG_PATH}")

def get_config():
    with open(CONFIG_PATH, 'r') as json_file:
        data = json.load(json_file)
        return data
    
# Function to save session_id to file
def save_session_id(session_id):
    with open(SESSION_FILE, 'w') as file:
        file.write(session_id)

# Function to read session_id from file
def read_session_id():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as file:
            return file.read().strip()
    return None

# Function to delete the session file
def delete_session_file():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# Initiate new connection request
def initiate_connection_request(requester):
    response = requests.post(f'{API_BASE_URL}/connections/initiate', json={"requester": requester})
    if response.status_code == 200:
        session_id = response.json().get('session_id')
        if session_id:
            save_session_id(session_id)
            print(f"New session initiated. Session ID: {session_id}")
            return session_id
        raise Exception(f"Failed to initiate connection: {response.json()}")
    else:
        raise Exception(f"Failed to initiate connection: {response.content}")

# Poll session approval
def poll_session_approval(session_id):
    while True:
        response = requests.get(f'{API_BASE_URL}/connections/status/{session_id}/approved')
        if response.status_code == 200:
            print(f"Session {session_id} approved.")
            return True
        elif response.status_code == 409:
            print(f"Session {session_id} expired.")
            return False
        print(f"Waiting for session {session_id} to be approved...")
        time.sleep(POLL_INTERVAL)


def mark_as_session_id_uploaded(session_id):
    response = requests.put(f'{API_BASE_URL}/connections/upload/{session_id}/completed')
    if response.status_code == 200:
        return True
    return False

# SCP file transfer with progress
def scp_upload_file(hostname, port, username, password, local_file_path, remote_file_path):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname, port=port, username=username, password=password)

    def progress(filename, size, sent):
        progress_percentage = (sent / size) * 100
        print(f"{filename}: {progress_percentage:.2f}% transferred")

    with SCPClient(ssh_client.get_transport(), progress=progress) as scp:
        scp.put(local_file_path, remote_file_path)

    ssh_client.close()

# Main function
def main():
    parser = argparse.ArgumentParser(description='Upload a file to a remote server using SCP')
    parser.add_argument('--path', help='Path to the local file to be uploaded')
    parser.add_argument('--requester', help='Requester information', default=os.getlogin())
    args = parser.parse_args()

    session_id = read_session_id()
    if session_id:
        print(f"Found existing session ID: {session_id}")
        choice = input("Upload for session is not complete. Continue with old session (y/n)? ")
        if choice.lower() != 'y':
            delete_session_file()
            session_id = initiate_connection_request(f'{args.requester}:{HOSTNAME}')
        status = poll_session_approval(session_id)
    else:
        session_id = initiate_connection_request(f'{args.requester}:{HOSTNAME}')
        status = poll_session_approval(session_id)

    try:
        if status:
            print(f"Uploading file {args.path}")
            scp_upload_file(
                hostname=REMOTE_HOSTNAME,
                port=REMOTE_PORT,
                username=REMOTE_USERNAME,
                password=REMOTE_PASSWORD,
                local_file_path=args.path,
                remote_file_path=REMOTE_PATH
            )
            print("File upload completed successfully.")
            mark_as_session_id_uploaded(session_id)
        delete_session_file()  # Delete session file after successful upload
        
    except Exception as e:
        print(f"Error during file upload: {e}")

if __name__ == '__main__':
    create_json_file()
    config = get_config()
    API_BASE_URL = config['API_BASE_URL']
    main()
