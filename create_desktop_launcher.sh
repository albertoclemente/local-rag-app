#!/bin/bash

# Create AppleScript Application to launch RAG App

APP_NAME="RAG App Launcher"
DESKTOP_PATH="$HOME/Desktop"
APP_PATH="$DESKTOP_PATH/$APP_NAME.app"
SCRIPT_PATH="/Users/alberto/projects/RAG_APP/start_rag_app.sh"

# Create the app bundle structure
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# Create the executable launcher
cat > "$APP_PATH/Contents/MacOS/$APP_NAME" << 'LAUNCHER'
#!/bin/bash
osascript -e 'tell application "Terminal"
    do script "cd /Users/alberto/projects/RAG_APP && ./start_rag_app.sh"
    activate
end tell'
LAUNCHER

# Make it executable
chmod +x "$APP_PATH/Contents/MacOS/$APP_NAME"

# Create Info.plist
cat > "$APP_PATH/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>RAG App Launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.local.ragapp</string>
    <key>CFBundleName</key>
    <string>RAG App Launcher</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# Create a simple icon (using emoji as placeholder)
cat > "$APP_PATH/Contents/Resources/AppIcon.icns" << 'ICON'
🚀
ICON

echo "✅ Created desktop launcher at: $APP_PATH"
echo "📍 You can now double-click 'RAG App Launcher' on your Desktop to start the app"
