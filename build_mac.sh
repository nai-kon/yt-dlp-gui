#! /bin/zsh
set -euo pipefail

# build exe
uv run pyinstaller build_mac.spec -y

# remove temp folder
rm -rf 'dist/Video Downloader/'
