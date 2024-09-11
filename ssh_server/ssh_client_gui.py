import requests
import json
import os
import time
import paramiko
from scp import SCPClient
import socket
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import argparse

# Constants
HOSTNAME = socket.gethostname()
SESSION_FILE = 'session_id'
API_BASE_URL = None
POLL_INTERVAL = 5  # seconds
REMOTE_PATH = '/home/user2402/data'  # Remote Directory
REMOTE_HOSTNAME = "139.59.17.95"
REMOTE_PORT = 22
REMOTE_PASSWORD = "dbNdBfw8HO2k7a1s"
REMOTE_USERNAME = "user2402"
CONFIG_PATH = os.path.join(Path.home(), '.ssh_client_config.json')


# Create a JSON file with default data
def create_json_file():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'w') as json_file:
            json.dump({'API_BASE_URL': f'http://{REMOTE_HOSTNAME}:8080'}, json_file, indent=4)
        print(f"JSON file created with default data at {CONFIG_PATH}")


def get_config():
    with open(CONFIG_PATH, 'r') as json_file:
        data = json.load(json_file)
        return data


# Save session_id to file
def save_session_id(session_id):
    with open(SESSION_FILE, 'w') as file:
        file.write(session_id)


# Read session_id from file
def read_session_id():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as file:
            return file.read().strip()
    return None


# Delete session file
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
            return session_id
        raise Exception(f"Failed to initiate connection: {response.json()}")
    else:
        raise Exception(f"Failed to initiate connection: {response.content}")


# Poll session approval
def poll_session_approval(session_id, progress_callback=None):
    while True:
        response = requests.get(f'{API_BASE_URL}/connections/status/{session_id}/approved')
        if response.status_code == 200:
            if progress_callback:
                progress_callback(f"Session {session_id} approved.")
            return True
        elif response.status_code == 409:
            if progress_callback:
                progress_callback(f"Session {session_id} expired.")
            return False
        if progress_callback:
            progress_callback(f"Waiting for session {session_id} to be approved...")
        time.sleep(POLL_INTERVAL)


# Mark session as uploaded
def mark_as_session_id_uploaded(session_id):
    response = requests.put(f'{API_BASE_URL}/connections/upload/{session_id}/completed')
    if response.status_code == 200:
        return True
    return False


# SCP file transfer with progress
def scp_upload_file_with_progress(hostname, port, username, password, local_file_path, remote_file_path, progress_callback=None):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname, port=port, username=username, password=password)

    def progress(filename, size, sent):
        if progress_callback:
            progress_callback(sent, size)

    with SCPClient(ssh_client.get_transport(), progress=progress) as scp:
        scp.put(local_file_path, remote_file_path)

    ssh_client.close()

    
# Tkinter GUI for file selection, requester info, and upload with progress
def tkinter_mode():
    # Create the main window
    root = tk.Tk()
    root.title("File Upload")
    root.geometry("1024x768")

    # Label and entry for requester info
    tk.Label(root, text="Requester Info").pack(pady=5)
    requester_entry = tk.Entry(root, width=40)
    requester_entry.insert(0, os.getlogin())
    requester_entry.pack(pady=5)

    # File selection button
    file_path_var = tk.StringVar()

    def select_file():
        file_path = filedialog.askopenfilename(title="Select file to upload")
        if file_path:
            file_path_var.set(file_path)
        else:
            messagebox.showwarning("No File", "You must select a file to upload.")

    tk.Button(root, text="Select File", command=select_file).pack(pady=10)
    tk.Label(root, textvariable=file_path_var).pack(pady=5)

    # Label for displaying polling and progress information
    progress_label = tk.Label(root, text="")
    progress_label.pack(pady=5)

    # Progress bar
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(pady=10)

    # Function to handle the submission and start the process
    def submit():
        requester = requester_entry.get()
        file_path = file_path_var.get()

        if not requester or not file_path:
            messagebox.showwarning("Incomplete Info", "Requester info and file path are required.")
            return

        session_id = read_session_id()
        if session_id:
            if messagebox.askyesno("Session Found", "Continue with existing session?"):
                status = poll_session_approval(session_id, root.title)
            else:
                delete_session_file()
                session_id = initiate_connection_request(f'{requester}:{HOSTNAME}')
                status = poll_session_approval(session_id, root.title)
        else:
            session_id = initiate_connection_request(f'{requester}:{HOSTNAME}')
            status = poll_session_approval(session_id, root.title)

        # Upload the file
        if status:
            def update_progress(sent, size):
                progress_percentage = (sent / size) * 100
                progress_bar['value'] = progress_percentage
                progress_label.config(text=f"{progress_percentage:.2f}% transferred")
                root.update_idletasks()  # Force the GUI to update

            try:
                scp_upload_file_with_progress(
                    hostname=REMOTE_HOSTNAME,
                    port=REMOTE_PORT,
                    username=REMOTE_USERNAME,
                    password=REMOTE_PASSWORD,
                    local_file_path=file_path,
                    remote_file_path=REMOTE_PATH,
                    progress_callback=update_progress
                )
                progress_label.config(text="File upload completed successfully.")
                mark_as_session_id_uploaded(session_id)
                delete_session_file()
            except Exception as e:
                messagebox.showerror("Upload Failed", f"Error during file upload: {e}")

        else:
            progress_label.config(text="Session approval failed or expired. Click Reset")

    # Submit button to start the upload
    tk.Button(root, text="Submit", command=submit).pack(pady=10)

    # Reset button to clear session and restart
    def reset_session():
        delete_session_file()
        file_path_var.set("")
        requester_entry.delete(0, tk.END)
        requester_entry.insert(0, os.getlogin())
        progress_label.config(text="")
        progress_bar['value'] = 0
        
        messagebox.showinfo("Reset", "Session reset successfully.")

    tk.Button(root, text="Reset", command=reset_session).pack(pady=5)
    root.title("File Upload")
    root.mainloop()


# Command-line mode using argparse
def cli_mode(requester, path):
    session_id = read_session_id()
    if session_id:
        print(f"Found existing session ID: {session_id}")
        choice = input("Upload for session is not complete. Continue with old session (y/n)? ")
        if choice.lower() != 'y':
            delete_session_file()
            session_id = initiate_connection_request(f'{requester}:{HOSTNAME}')
        status = poll_session_approval(session_id, print)
    else:
        session_id = initiate_connection_request(f'{requester}:{HOSTNAME}')
        status = poll_session_approval(session_id, print)

    if status:
        print(f"Uploading file {path}")
        def update_progress(sent, size):
            progress_percentage = (sent / size) * 100
            print(f"{progress_percentage:.2f}% transferred", end='\r')

        try:
            scp_upload_file_with_progress(
                hostname=REMOTE_HOSTNAME,
                port=REMOTE_PORT,
                username=REMOTE_USERNAME,
                password=REMOTE_PASSWORD,
                local_file_path=path,
                remote_file_path=REMOTE_PATH,
                progress_callback=update_progress
            )
            print("\nFile upload completed successfully.")
            mark_as_session_id_uploaded(session_id)
            delete_session_file()
        except Exception as e:
            print(f"Error during file upload: {e}")


# Main function to determine mode (CLI or GUI)
def main():
    create_json_file()
    config = get_config()
    global API_BASE_URL
    API_BASE_URL = config['API_BASE_URL']

    parser = argparse.ArgumentParser(description="File upload to remote server via SCP")
    parser.add_argument('--path', help='Path to the local file to upload')
    parser.add_argument('--requester', help='Requester information', default=os.getlogin())
    args = parser.parse_args()

    if args.path:
        cli_mode(requester=args.requester, path=args.path)
    else:
        tkinter_mode()


if __name__ == '__main__':
    main()
