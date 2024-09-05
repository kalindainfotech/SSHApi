#!/usr/bin/python3
from bottle import Bottle, request, response, run
import paramiko
from scp import SCPClient
import sqlite3
import os
import uuid

app = Bottle()

remote_path = '/home/user2402/data' #Remote Directory
REMOTE_HOSTNAME = "139.59.17.95"
REMOTE_PASSWORD = "dbNdBfw8HO2k7a1s"
REMOTE_USERNAME = "user2402"
# Database setup
def init_db():
    conn = sqlite3.connect('ssh_sessions.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        hostname TEXT,
                        username TEXT,
                        password TEXT,
                        requester TEXT,
                        status INTEGER DEFAULT -1,
                        file_path TEXT)''')
    conn.commit()
    conn.close()

init_db()

def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        response.headers['Access-Control-Allow-Origin'] = '*'  # Allow all origins, adjust as needed
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        # If this is an OPTIONS request, skip the route handler
        if request.method == 'OPTIONS':
            return {}
        return fn(*args, **kwargs)
    return _enable_cors

@app.route('/connections/requests', method=['GET', 'OPTIONS'])
@enable_cors
def get_connections():
    try:
        conn = sqlite3.connect('ssh_sessions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT session_id, hostname, requester, status FROM sessions WHERE status = -1')
        new_connections = cursor.fetchall()
        conn.close()

        return {"connections": [{"session_id": row[0], "hostname": row[1], "requester": row[2], "status":row[3]} for row in new_connections]}
    except Exception as e:
        return {"error": str(e)}


# Route to initiate an SSH connection request
@app.route('/connections/initiate', method=['POST', 'OPTIONS'])
@enable_cors
def initiate_ssh():
    try:
        print(dict(request.json),'ssssssssssssssssssss')
        session_id = str(uuid.uuid4())
        hostname = request.forms.get('hostname', REMOTE_HOSTNAME)
        username = request.forms.get('username', REMOTE_USERNAME)
        password = request.forms.get('password', REMOTE_PASSWORD)
        requester = request.json.get('requester')

        print(requester)

        conn = sqlite3.connect('ssh_sessions.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO sessions (session_id, hostname, username, password, requester)
                          VALUES (?, ?, ?, ?, ?)''', 
                          (session_id, hostname, username, password, requester))
        conn.commit()
        conn.close()

        return {"status": "SSH connection request initiated.", "session_id": session_id}
    except Exception as e:
        return {"error": str(e)}

# Route to approve or reject the SSH connection
@app.route('/connections/action', method=['PUT', 'OPTIONS'])
@enable_cors
def handle_connection():
    try:
        print(dict(request.json))
        session_id = request.json.get('session_id')
        action = request.json.get('action')

        conn = sqlite3.connect('ssh_sessions.db')
        cursor = conn.cursor()

        if action == 'approve':
            cursor.execute('UPDATE sessions SET status = 1 WHERE session_id = ?', (session_id,))
            conn.commit()
            return {"status": "SSH connection approved."}
        elif action == 'reject':
            #cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            cursor.execute('UPDATE sessions SET status = 0 WHERE session_id = ?', (session_id,))
            conn.commit()
            return {"status": "SSH connection rejected and session deleted."}
        else:
            return {"error": "Invalid action. Use 'approve' or 'reject'."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

# Route to upload a file
@app.route('/connections/upload', method=['POST', 'OPTIONS'])
@enable_cors
def upload_file():
    file_path = None
    try:
        session_id = request.forms.get('session_id')

        conn = sqlite3.connect('ssh_sessions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT hostname, username, password, file_path, status FROM sessions WHERE session_id = ? AND status = 1', (session_id,))
        session_data = cursor.fetchone()

        if not session_data:
            return {"error": "Approved session not found."}

        hostname, username, password, file_path, status = session_data

        if status != 1:
            return {"error": "SSH connection not approved or session does not exist."}

        upload = request.files.get('upload')
        if not upload:
            return {"error": "No file uploaded."}

        file_path = f"./{session_id}_{upload.filename}"
        upload.save(file_path)

        if not os.path.exists(file_path):
            return {"error": f"File {file_path} does not exist."}

        if not os.path.exists(file_path):
            return {"error": f"File {file_path} does not exist."}

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname, username=username, password=password)

        with SCPClient(ssh_client.get_transport()) as scp:
            scp.put(file_path, "{}/{}".format(remote_path, os.path.basename(file_path)) )

        cursor.execute('UPDATE sessions SET status = 2,file_path=? WHERE session_id = ?', (file_path,session_id))
        conn.commit()

        return {"status": "File uploaded successfully."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
        if file_path:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as ex:
                print('[Error while removing file {} ->{}]'.format(file_path,ex))

if __name__ == '__main__':
    run(app, host='0.0.0.0', port=8080)
