"""
Build PDTS as a single-file Windows executable.
Run:  python build_exe.py
Output:  dist/PDTS.exe
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def build():
    args = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--clean',
        '--onefile',
        '--windowed',                         # No console window
        '--name', 'PDTS',
        '--add-data', f'templates{os.pathsep}templates',   # Bundle templates
        '--hidden-import', 'flask',
        '--hidden-import', 'flask_cors',
        '--hidden-import', 'webview',
        '--hidden-import', 'clr_loader',
        '--collect-all', 'webview',
        'launch_pdts.py',
    ]
    print("Running PyInstaller...")
    print(" ".join(args))
    subprocess.check_call(args, cwd=HERE)
    print("\n✓ Build complete.")
    print(f"✓ Executable: {os.path.join(HERE, 'dist', 'PDTS.exe')}")


if __name__ == '__main__':
    build()