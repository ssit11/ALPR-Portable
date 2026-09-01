name: Build iOS IPA

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build-ios:
    runs-on: macos-latest

    steps:
    - name: Checkout Code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install Dependencies & Briefcase
      run: |
        python -m pip install --upgrade pip
        pip install briefcase toga

    - name: Select Xcode Version
      run: |
        sudo xcode-select -switch /Applications/Xcode.app
        xcodebuild -version

    - name: Create iOS Xcode Project
      run: briefcase create iOS --no-input

    - name: Compile Native Release iOS Binary for Real iPhone
      run: |
        # Build the Xcode project directly for physical ARM64 iPhones without signing requirements
        xcodebuild -project build/my_app/ios/xcode/ALPR-Portable.xcodeproj \
                   -scheme "ALPR-Portable" \
                   -configuration Release \
                   -sdk iphoneos \
                   CODE_SIGNING_ALLOWED=NO \
                   CODE_SIGNING_REQUIRED=NO \
                   CODE_SIGN_IDENTITY="" \
                   build

    - name: Package Unsigned IPA
      run: |
        set -x
        
        # Locate the compiled ARM64 .app bundle output by xcodebuild
        APP_PATH=$(find build/my_app/ios/xcode/build ~/Library/Developer/Xcode/DerivedData -name "*.app" -path "*Release-iphoneos*" 2>/dev/null | head -n 1)
        
        if [ -z "$APP_PATH" ]; then
          # Fallback lookup for any physical device .app output
          APP_PATH=$(find . ~/Library/Developer/Xcode/DerivedData -name "*.app" 2>/dev/null | grep -v "iphonesimulator" | head -n 1)
        fi

        if [ -z "$APP_PATH" ]; then
          echo "Error: Could not find compiled .app file!"
          exit 1
        fi

        echo "Found compiled iPhone app at: $APP_PATH"

        mkdir -p Payload
        cp -R "$APP_PATH" Payload/
        zip -r ALPR-Portable-unsigned.ipa Payload/

    - name: Upload IPA Artifact
      uses: actions/upload-artifact@v4
      with:
        name: ALPR-Portable-Unsigned-IPA
        path: ALPR-Portable-unsigned.ipa