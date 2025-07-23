# Browser-Use LinkedIn Automation

<div align="center">
  <img src="./static/browser-use.png" alt="Browser-Use LinkedIn Automation" width="180" style="display:inline-block;vertical-align:middle;"/>
  <span style="display:inline-block;width:32px;"></span>
  <img src="./static/starnus-logo.png" alt="Starnus Technology B.V." width="180" style="display:inline-block;vertical-align:middle;"/>
  
  <h2>🚀 AI-Powered LinkedIn Automation by Starnus</h2>
  
  [![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Starnus](https://img.shields.io/badge/Made%20by-Starnus-blue)](https://github.com/Starnus)
  [![Browser-Use](https://img.shields.io/badge/Based%20on-Browser--Use-orange)](https://github.com/browser-use/browser-use)
  
  **Professional LinkedIn automation tool that connects to your existing Chrome session for authentic, detection-resistant automation.**
</div>

## ⚠️ **IMPORTANT LEGAL DISCLAIMER**

**READ [DISCLAIMER.md](DISCLAIMER.md) BEFORE USING THIS SOFTWARE**

You are solely responsible for ensuring your use complies with LinkedIn's Terms of Service. By using this software, you agree to indemnify and hold harmless Starnus Technology B.V. and contributors from any liability arising from your use.

## 🌟 Features

- **🔐 Authentic Session**: Uses your existing Chrome profile with LinkedIn login
- **🤖 AI-Powered**: Leverages advanced language models for intelligent automation
- **📊 Excel Integration**: Processes LinkedIn profiles from Excel files
- **🔍 Mutual Connections**: Automatically extracts mutual connection data
- **🛡️ Detection Resistant**: Maintains natural browsing patterns
- **🔧 Cross-Platform**: Works on Windows, macOS, and Linux

## 🏢 About Starnus

This project is developed and maintained by **Starnus Technology B.V.**, showcasing our expertise in:
- AI-powered automation solutions
- Browser automation and web scraping
- Professional networking tools
- Enterprise-grade software development

Visit us at: [github.com/Starnus](https://github.com/Starnus)

## 🚀 First-Time Setup Guide

### Prerequisites Check

Before starting, ensure you have:
- **Python 3.11+** - [Download from python.org](https://python.org/downloads/)
- **Google Chrome** - [Download here](https://www.google.com/chrome/)
- **Google AI API Key** - [Get one from Google AI Studio](https://aistudio.google.com/apikey)
- **LinkedIn Account** - You must be logged into LinkedIn

### Step-by-Step Installation

#### 1. **Clone & Navigate**
```bash
git clone https://github.com/Starnus/browser-use-linkedin.git
cd browser-use-linkedin
```

#### 2. **Python Environment Setup** (Recommended)
```bash
# Create virtual environment
python -m venv linkedin-automation
# Activate it
source linkedin-automation/bin/activate  # Linux/Mac
# OR
linkedin-automation\Scripts\activate     # Windows
```

#### 3. **Install Dependencies**
```bash
# Install Python packages
pip install -r requirements.txt

# Install browser (this may take 2-3 minutes)
playwright install chromium --with-deps --no-shell
```

#### 4. **Environment Configuration**
Create a `.env` file in the project root:
```bash
# Windows
echo GOOGLE_API_KEY=your_actual_api_key_here > .env

# Linux/Mac  
echo "GOOGLE_API_KEY=your_actual_api_key_here" > .env
```

**⚠️ Important**: Replace `your_actual_api_key_here` with your real Google AI API key!

#### 5. **Prepare Your Data**
Create an Excel file (.xlsx) with LinkedIn URLs:

| profile_url | name |
|-------------|------|
| https://www.linkedin.com/in/johndoe/ | John Doe |
| https://www.linkedin.com/in/janesmith/ | Jane Smith |

**Save as**: `linkedin_profiles.xlsx`

#### 6. **LinkedIn Session Setup**
1. Open Chrome manually
2. Log into LinkedIn
3. Keep this browser window open
4. **Important**: Make sure you're fully logged in before running the automation

### 🏃‍♂️ First Run

#### Option 1: Interactive Automation
```bash
python linkedin_automation.py
```
This opens an interactive menu where you can test the connection and run custom tasks.

#### Option 2: Batch Process Excel File
```bash
cd linkedin_mutual_connections
python main.py linkedin_profiles.xlsx
```
This processes your Excel file automatically and updates it with mutual connections.

### ✅ Verify Setup
After first installation, test with:
```bash
python -c "import browser_use; print('✅ Installation successful!')"
```

## 📋 Detailed Setup Guide

### 1. LinkedIn Profile URLs
Your Excel file should contain LinkedIn profile URLs in this format:
```
https://www.linkedin.com/in/username/
https://www.linkedin.com/in/another-user/
```

### 2. Chrome Configuration
The tool will automatically:
- Close existing Chrome instances
- Launch Chrome with debugging enabled
- Connect to your existing profile
- Maintain your LinkedIn session

### 3. Automation Process
1. **Authentication Check**: Verifies LinkedIn login status
2. **Profile Processing**: Iterates through Excel profiles
3. **Data Extraction**: Collects mutual connections
4. **Results Storage**: Updates Excel with findings

## 🔧 Configuration

### Environment Variables
```bash
GOOGLE_API_KEY=your_api_key_here        # Required: Google AI API access
CHROME_DEBUGGING_PORT=9222              # Optional: Chrome debug port
LOG_LEVEL=INFO                          # Optional: Logging level
```

### Config File
Customize settings in `linkedin_mutual_connections/modules/config.py`:
```python
MUTUAL_CONNECTIONS_TO_EXTRACT = 10      # Max connections per profile
PAGE_LOAD_TIMEOUT = 120000              # Page load timeout (ms)
RETRY_ATTEMPTS = 3                      # Failed request retries
```

## 📊 Output Format

The tool updates your Excel file with:
- **mutual_connections**: List of mutual connection names
- **status**: Processing status (done/processing/error)
- **timestamp**: Last update time

## 🛡️ Security & Privacy

- **No Password Storage**: Uses existing browser session
- **Local Processing**: All data stays on your machine
- **Encrypted Communication**: HTTPS-only connections
- **Rate Limiting**: Respects LinkedIn's systems

## 🔍 Troubleshooting

### First-Time Setup Issues

**❌ "Python not found" error**
```bash
# Check Python installation
python --version
# If not found, download from python.org
```

**❌ "pip not found" error**
```bash
# Try python -m pip instead
python -m pip install -r requirements.txt
```

**❌ "playwright install failed"**
```bash
# Run with elevated permissions
sudo playwright install chromium --with-deps  # Linux/Mac
# Or run PowerShell as Administrator (Windows)
```

**❌ "Module 'browser_use' not found"**
```bash
# Ensure you're in the right directory
ls  # Should see browser_use/ folder
# Activate virtual environment if using one
source linkedin-automation/bin/activate
```

### Runtime Issues

**❌ Chrome won't start**
```bash
# Close all Chrome instances first
taskkill /f /im chrome.exe          # Windows
pkill -f Chrome                     # macOS/Linux

# Check if port 9222 is available
netstat -an | grep 9222
```

**❌ "LinkedIn not logged in" error**
1. Open Chrome manually **first**
2. Navigate to linkedin.com and log in completely
3. **Keep this window open** while running the script
4. Make sure you can see your LinkedIn feed

**❌ "Google API error"**
```bash
# Verify your API key
echo $GOOGLE_API_KEY  # Linux/Mac
echo %GOOGLE_API_KEY% # Windows

# Test API key
python -c "import google.generativeai as genai; print('API key format looks correct')"
```

**❌ Excel file errors**
- Ensure file is .xlsx format (not .xls or .csv)
- Check LinkedIn URLs are complete (include https://)
- Verify file isn't open in Excel while running

### Performance Issues

**🐌 Slow processing**
- Reduce `MUTUAL_CONNECTIONS_TO_EXTRACT` to 5
- Check your internet connection
- Use a paid Google AI plan for faster API responses

### Getting Help

1. **First**: Check this troubleshooting section
2. **Search**: [GitHub Issues](https://github.com/Starnus/browser-use-linkedin/issues)
3. **Report**: Create a new issue with:
   - Your OS (Windows/Mac/Linux)
   - Python version (`python --version`)
   - Error message (full text)
   - Steps that led to the error
4. **Enterprise Support**: contact@starnus.com

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License & Attribution

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

### Acknowledgments

This project builds upon the excellent [browser-use](https://github.com/browser-use/browser-use) library:
- Original work © 2024 Gregor Zunic
- LinkedIn extensions © 2025 Starnus Technology B.V.

See [NOTICE](NOTICE) for complete attribution details.

## ⚠️ Responsible Use

This tool is designed for:
- ✅ Professional networking research
- ✅ Educational purposes
- ✅ Legitimate business development

**Do not use for:**
- ❌ Spam or unsolicited messaging
- ❌ Data harvesting violations
- ❌ LinkedIn Terms of Service violations

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/Starnus/browser-use-linkedin/issues)
- **Security**: [SECURITY.md](SECURITY.md)
- **Business Inquiries**: support@starnustech.com

---

<div align="center">
  <p><strong>Made with ❤️ by <a href="https://github.com/Starnus">Starnus</a></strong></p>
  <p>Building the future of intelligent automation</p>
</div>
