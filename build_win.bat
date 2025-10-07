@echo off

@REM build exe
uv run pyinstaller build_win.spec -y


@REM copy files
xcopy /i /y "src\ffmpeg.exe" ".\dist\Video Downloader\"
xcopy /i /y "src\logo.ico" ".\dist\Video Downloader\"
