Linux:
 only-cli:
     nuitka --standalone --static-libpython=yes --output-dir=dist/linux --onefile ssh_client.py
 gui-cli:
     nuitka --standalone --static-libpython=yes --output-dir=dist/linux-gui --onefile ssh_client_gui.py
Windows:
 only-cli:
     nuitka --standalone --static-libpython=yes --output-dir=dist/windows --onefile ssh_client.py
 gui-cli:
     nuitka --standalone --static-libpython=yes --output-dir=dist/windows-gui --onefile ssh_client_gui.py
