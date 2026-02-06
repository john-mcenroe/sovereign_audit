#!/bin/bash
# Script to fix Homebrew permissions and install ffmpeg

echo "Fixing Homebrew permissions..."
sudo chown -R johnmcenroe /opt/homebrew /Users/johnmcenroe/Library/Logs/Homebrew

echo ""
echo "Installing ffmpeg..."
brew install ffmpeg

echo ""
echo "Done! You can now run: python3 edit_video.py"
