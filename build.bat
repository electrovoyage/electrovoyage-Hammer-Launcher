@echo off
py -m PyInstaller --upx-dir F:/upx --icon icon.ico --optimize 1 --noconsole -y --add-data resources/logo.png;resources --workpath temp --distpath HammerLauncher --clean --onefile launcher.py