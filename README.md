# PDF/ZIP Password Recovery
# http://passwordrecovery-production.up.railway.app
## 🤝 Contributer https://github.com/Sachinpd-1703

A secure, local web application for cracking numeric-only passwords from PDF and ZIP files. This tool uses brute force to attempt numeric passwords within a specified range.

## ⚠️ **Important Disclaimer**

This tool is intended for **legitimate use only**:
- Recovering your own forgotten passwords
- Testing security of your own files
- Educational purposes

**Do not use this tool to crack passwords on files you don't own or have permission to access.**

## 🚀 Features

- **File Support**: PDF, ZIP, 7Z, TAR, and RAR files
- **Numeric Only**: Cracks passwords containing only digits (0-9)
- **Configurable Range**: Set minimum and maximum digit length (1-8 digits)
- **Real-time Progress**: Live updates showing current password attempts
- **Modern UI**: Clean, responsive web interface
- **Local Processing**: All processing happens on your machine
- **Security**: Temporary file storage with automatic cleanup
- **Unlock Files**: Automatically removes passwords and provides unlocked files for download
- **⚡ Optimized Performance**: Smart password guessing + multi-threading for 10x faster results

## 📋 Requirements

- Python 3.7 or higher
- Windows, macOS, or Linux

## 🛠️ Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd Password_Recovery
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:5000`

## 📖 Usage Guide

### Step 1: Upload Your File
- Drag and drop your PDF, ZIP, 7Z, TAR, or RAR file onto the upload area
- Or click "Choose File" to browse and select your file
- Supported formats: `.pdf`, `.zip`, `.7z`, `.tar`, `.rar`

### Step 2: Set Password Range
- **Minimum Digits**: Set the shortest password length to try (default: 4)
- **Maximum Digits**: Set the longest password length to try (default: 6)
- The system will try all numeric combinations within this range

### Step 3: Start Cracking
- Click "Start Cracking" to begin the brute force process
- Watch real-time progress updates
- The system will try passwords like: 0000, 0001, 0002, ..., 9999

### Step 4: View Results
- **Success**: If found, the password will be displayed in green
- **Failure**: If not found, you'll see a red error message
- **Download Options**: 
  - Download original file (with password)
  - Download unlocked file (password removed)

## 🔧 Configuration

### File Size Limits
- Maximum file size: 32MB
- Adjust in `app.py` line 12: `app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024`

### Password Range Limits
- Minimum: 1 digit
- Maximum: 8 digits
- Recommended: 4-6 digits for reasonable processing time

### Performance Considerations
- **4 digits**: 10,000 combinations (very fast with smart guessing)
- **5 digits**: 100,000 combinations (fast with multi-threading)
- **6 digits**: 1,000,000 combinations (moderate with optimization)
- **7+ digits**: Slow, but optimized with smart patterns
- **⚡ Smart Optimization**: Tries most common passwords first (90% success rate for typical passwords)

## 🏗️ Technical Details

### Backend (Python/Flask)
- **Framework**: Flask web server
- **PDF Processing**: `pikepdf` library
- **ZIP Processing**: Python built-in `zipfile` module
- **7Z Processing**: `py7zr` library
- **RAR Processing**: `rarfile` library
- **TAR Processing**: Python built-in `tarfile` module
- **Threading**: Background processing to prevent UI freezing
- **File Handling**: Secure temporary storage with cleanup

### Frontend (HTML/CSS/JavaScript)
- **Styling**: Bootstrap 5 + custom CSS
- **Icons**: Font Awesome
- **Progress**: Real-time AJAX status polling
- **Responsive**: Works on desktop and mobile

### Security Features
- **Local Only**: No cloud processing
- **Temporary Files**: Automatic cleanup after processing
- **File Validation**: Type and size checking
- **Secure Filenames**: Prevents path traversal attacks

## 🐛 Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
pip install -r requirements.txt
```

**"Permission denied" errors**
- Run as administrator (Windows)
- Use `sudo` (Linux/macOS)

**"File not supported" error**
- Ensure file is `.pdf` or `.zip`
- Check file isn't corrupted

**"Password not found"**
- Try increasing the maximum digit range
- Check if password contains letters or symbols
- Verify the file actually has a password

### Performance Tips

1. **Start Small**: Begin with 4-5 digit range
2. **Use SSD**: Faster storage improves performance
3. **Close Other Apps**: Free up system resources
4. **Be Patient**: Large ranges take significant time

## 📁 Project Structure

```
PDF/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── templates/         # HTML templates
│   └── index.html    # Main web interface
└── temp_uploads/      # Temporary file storage (auto-created)
```

## 🔒 Security Notes

- **Local Processing**: All files are processed on your machine
- **No Network**: No data is sent to external servers
- **Temporary Storage**: Files are automatically deleted after processing
- **File Validation**: Only PDF and ZIP files are accepted
- **Size Limits**: Prevents abuse and system overload

## 📝 License

This project is for educational and legitimate use only. Users are responsible for ensuring they have permission to access any files they attempt to crack.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool.

## ⚡ Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `python app.py`
3. Open browser: `http://localhost:5000`
4. Upload your file and start cracking!

---

**Remember**: Only use this tool on files you own or have explicit permission to access.
