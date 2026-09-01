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

    - name: Build iOS App
      run: briefcase build iOS --no-input

    - name: Package Unsigned IPA
      run: |
        set -x
        
        # Dynamically search for the .app bundle across build directories and DerivedData
        APP_PATH=$(find build/ ~/Library/Developer/Xcode/DerivedData -name "*.app" 2>/dev/null | head -n 1)

        if [ -z "$APP_PATH" ]; then
          echo "Error: Could not find compiled .app file!"
          exit 1
        fi

        echo "Found compiled app at: $APP_PATH"

        mkdir -p Payload
        cp -R "$APP_PATH" Payload/
        zip -r ALPR-Portable-unsigned.ipa Payload/

    - name: Upload IPA Artifact
      uses: actions/upload-artifact@v4
      with:
        name: ALPR-Portable-Unsigned-IPA
        path: ALPR-Portable-unsigned.ipa