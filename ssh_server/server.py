#!/usr/bin/python3
from bottle import Bottle, request, response, run, abort, static_file, redirect
import paramiko
from scp import SCPClient
import sqlite3
import os
import uuid

app = Bottle()

DB_PATH = 'ssh_sessions.db'
remote_path = '/home/user2402/data' #Remote Directory
REMOTE_HOSTNAME = "139.59.17.95"
REMOTE_PASSWORD = "dbNdBfw8HO2k7a1s"
REMOTE_USERNAME = "user2402"
WEB_PATH = os.path.join( os.path.dirname(os.path.dirname(os.path.realpath(__file__)) ), "ssh_admin", "build")
WEB_STATIC_PATH = os.path.join( os.path.dirname(os.path.dirname(os.path.realpath(__file__)) ), "ssh_admin", "build", "static")
# Database setup
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        hostname TEXT,
                        username TEXT,
                        password TEXT,
                        requester TEXT NOT NULL,
                        status INTEGER DEFAULT -1,
                        file_path TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        comment TEXT)''')
    
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL,
                        access_token TEXT,
                        login_session_id TEXT
                    )
                    ''')
    
    conn.commit()
    conn.close()

def create_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO users (username, password, access_token, login_session_id)
                          VALUES (?, ?, ?, ?)''', 
                          (username, password, str(uuid.uuid4()), None ))
    conn.commit()
    conn.close()


def create_default_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    if count == 0:
        create_user('admin', 'admin123')
        create_user('deva', 'deva123')

init_db()
create_default_users()


def check_auth(func):
    def wrapper(*args, **kwargs):
        login_session_id = request.get_cookie('login_session_id')
        if not login_session_id:
            auth_header = request.get_header('Authorization')
            if not auth_header:
                return abort(401, "Unauthorized: No session cookie found")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        session = None
        if login_session_id:
            cursor.execute("SELECT user_id, username FROM users WHERE login_session_id = ?", (login_session_id,))
            session = cursor.fetchone()
        if not session:
            auth_header = request.get_header('Authorization')
            cursor.execute("SELECT user_id, username FROM users WHERE access_token = ?", (auth_header,))
            session = cursor.fetchone()

        conn.close()

        if session:
            user_id, username = session
            response.set_cookie('user_id', str(user_id))
            response.set_cookie('username', username)
            return func(*args, **kwargs)
        else:
            return abort(401, "Unauthorized: Invalid session")
    
    return wrapper


def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        response.headers['Access-Control-Allow-Origin'] = '*'  # Allow all origins, adjust as needed
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token, Authorization'

        # If this is an OPTIONS request, skip the route handler
        if request.method == 'OPTIONS':
            return {}
        return fn(*args, **kwargs)
    return _enable_cors


@app.route('/login', method=['POST','OPTIONS'])
@enable_cors
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()

    if user:
        login_session_id = str(uuid.uuid4())  
        cursor.execute('UPDATE users SET login_session_id = ? WHERE user_id = ?', (login_session_id, user[0]) )
        conn.commit()
        conn.close()
        
        response.set_cookie('login_session_id', login_session_id)
        response.set_cookie('user_id', str(user[0]))

        return {"status": 200,"user_id":str(user[0]),"login_session_id":login_session_id}
    else:
        return abort(401, "Unauthorized: Invalid session")

@app.route('/logout', method=['DELETE','OPTIONS'])
@enable_cors
@check_auth
def logout():
    user_id = int(request.get_cookie('user_id', 0))
    login_session_id = request.get_cookie('login_session_id')

    if login_session_id:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET login_session_id = ? WHERE user_id = ?', (None, user_id) )
        conn.commit()
        conn.close()

        response.delete_cookie('login_session_id')
        response.delete_cookie('user_id')
        response.delete_cookie('username')
        return {"status": "Logged out successfully"}
    else:
        return {"status": "No session found"}


@app.route('/users', method=['GET', 'OPTIONS'])
@enable_cors
# @check_auth
def get_users():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, access_token, login_session_id FROM users')
        users = cursor.fetchall()

        return {"users": [{"user_id": row[0], "username": row[1], "access_token": row[2], "login_session_id": row[3]} for row in users]}
    except Exception as e:
        return {"error": str(e), "users": []}

@app.route('/connections/requests', method=['GET', 'OPTIONS'])
@enable_cors
# @check_auth
def get_connections():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        status = request.query.status if request.query.status else -1
        hostname = request.query.hostname if request.query.hostname else None
        requester = request.query.requester if request.query.requester else None

        query = 'SELECT session_id, hostname, requester, status, comment, created_at FROM sessions WHERE status = ?'
        params = [status]

        if hostname:
            query += ' AND hostname = ?'
            params.append(hostname)
        
        if requester:
            query += ' AND requester = ?'
            params.append(requester)

        cursor.execute(query, params)
        new_connections = cursor.fetchall()
        conn.close()

        return {"connections": [{"session_id": row[0], "hostname": row[1], "requester": row[2], "status":row[3], 'comment': row[4], "created_at": row[5]} for row in new_connections]}
    except Exception as e:
        return {"error": str(e), "connections": []}


# Route to initiate an SSH connection request
@app.route('/connections/initiate', method=['POST', 'OPTIONS'])
@enable_cors
def initiate_ssh():
    try:
        print(dict(request.json))
        session_id = str(uuid.uuid4())
        hostname = request.json.get('hostname', REMOTE_HOSTNAME)
        username = request.forms.get('username', REMOTE_USERNAME)
        password = request.forms.get('password', REMOTE_PASSWORD)
        requester = request.json.get('requester')

        conn = sqlite3.connect(DB_PATH)
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
# @check_auth
def handle_connection():
    try:
        print(dict(request.json))
        session_id = request.json.get('session_id')
        action = request.json.get('action')
        user_name = request.get_cookie('username')


        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if action == 'approve':
            cursor.execute('UPDATE sessions SET status = 1, comment = ? WHERE session_id = ?', (f'{user_name}: Approved the connection', session_id,))
            conn.commit()
            return {"status": "SSH connection approved."}
        elif action == 'reject':
            #cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            cursor.execute('UPDATE sessions SET status = 0, comment = ? WHERE session_id = ?', (f'{user_name}: Rejected the connection', session_id,))
            conn.commit()
            return {"status": "SSH connection rejected and session deleted."}
        else:
            return {"error": "Invalid action. Use 'approve' or 'reject'."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

# Route to check the session_id status
@app.route('/connections/status', method=['POST', 'OPTIONS'])
@enable_cors
def status_check():
    try:
        session_id = request.json.get('session_id')
        print(session_id)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        query = 'SELECT session_id, hostname, requester, status, comment FROM sessions WHERE session_id = ?'
        params = [session_id]
        cursor.execute(query, params)
        new_connections = cursor.fetchall()
        conn.close()

        return {"connections": [{"session_id": row[0], "hostname": row[1], "requester": row[2], "status":row[3], 'comment': row[4]} for row in new_connections]}
    except Exception as e:
        return {"error": str(e), "connections": []}       
        

@app.route('/connections/status/<session_id>/approved', method=['GET', 'OPTIONS'])
@enable_cors
def is_approved(session_id):
    print(session_id)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = 'SELECT session_id, hostname, requester, status, comment FROM sessions WHERE session_id = ?'
    params = [session_id]
    cursor.execute(query, params)
    session_data = cursor.fetchone()
    conn.close()
    if session_data[3] == -1:
        return abort(406, f'Session_id<{session_id}> not approved')
    
    if session_data[3] in [0, 2]:
        return abort(409, f'Session_id<{session_id}> Already used')

    return {"connections": {"session_id": session_data[0], "hostname": session_data[1], "requester": session_data[2], "status":session_data[3], 'comment': session_data[4]} }



# Route to upload a file
@app.route('/connections/upload', method=['POST', 'OPTIONS'])
@enable_cors
def upload_file():
    file_path = None
    try:
        session_id = request.forms.get('session_id')
        print(session_id)
        conn = sqlite3.connect(DB_PATH)
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
        conn.close()

        return {"status": "File uploaded successfully."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            conn.close()
        if file_path:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as ex:
                print('[Error while removing file {} ->{}]'.format(file_path,ex))

@app.route('/connections/upload/<session_id>/completed', method=['PUT'])
def mark_session_id_as_completed(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE sessions SET status = 2 WHERE session_id = ?', (session_id,))
    conn.commit()
    conn.close()

@app.route('/static/<path:path>')
def serve_file(path):
    return static_file(path, root=WEB_STATIC_PATH)

@app.route('/manifest.json')
def serve_file():
    path = "manifest.json"
    return static_file(path, root=WEB_PATH)

@app.route('/logo:re:.+')
def serve_file(path):
    print(path)
    return static_file(path, root=WEB_PATH)

@app.route('/web/<path:path>')
def serve_file(path):
    return static_file(path, root=WEB_PATH)

@app.route('/')
def redirect_to_web():
    return redirect('/web/index.html')

if __name__ == '__main__':
    run(app, host='0.0.0.0', port=8080)
