Linux:
 only-cli:
     nuitka --standalone --static-libpython=yes --output-dir=dist/linux --onefile ssh_client.py
 gui-cli:
     nuitka --standalone --static-libpython=yes --output-dir=dist/linux-gui --enable-plugin=tk-inter --onefile ssh_client_gui.py
Windows:
 only-cli:
     nuitka --standalone --mingw64 --output-dir=dist/windows --onefile ssh_client.py
 gui-cli:
     nuitka --standalone --mingw64 --output-dir=dist/windows-gui --enable-plugin=tk-inter --onefile ssh_client_gui.py