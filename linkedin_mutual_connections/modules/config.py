"""
Configuration module for LinkedIn Mutual Connections Automation.

Contains all configuration constants, settings, and environment variables
used throughout the application.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any

# Load environment variables from parent directory (.env file in browser-use folder)
from dotenv import load_dotenv
parent_dir = Path(__file__).parent.parent.parent  # Go up to browser-use folder
env_path = parent_dir / '.env'
load_dotenv(env_path)

# Application Constants
APP_NAME = "LinkedIn Mutual Connections Automation"
VERSION = "1.0.0"

# LinkedIn Automation Settings
MUTUAL_CONNECTIONS_TO_EXTRACT = 10
CHROME_DEBUGGING_PORT = 9222
CHROME_USER_DATA_DIR = os.path.expanduser("~/linkedin-automation")  # Cross-platform user directory

# Excel Column Names
MUTUAL_CONNECTIONS_COLUMN = "mutual_connections"
STATUS_COLUMN = "status"
DONE_STATUS = "done"
PROCESSING_STATUS = "processing"
ERROR_STATUS = "error"

# Browser Automation Settings
PAGE_LOAD_TIMEOUT = 120000  # milliseconds (increased from 30 to 120 seconds)
ELEMENT_WAIT_TIMEOUT = 10000  # milliseconds
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # seconds

# Logging Configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Chrome Launch Command Template
def get_chrome_path():
    """Get Chrome executable path based on operating system"""
    import platform
    system = platform.system()
    if system == "Windows":
        return "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    elif system == "Darwin":  # macOS
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    else:  # Linux
        return "google-chrome"

CHROME_LAUNCH_COMMAND = [
    get_chrome_path(),
    f"--remote-debugging-port={CHROME_DEBUGGING_PORT}",
    f"--user-data-dir={CHROME_USER_DATA_DIR}",
    "--no-first-run",
    "--no-default-browser-check"
]

# LinkedIn Automation Prompt Template - SIMPLIFIED AND FOCUSED
LINKEDIN_AUTOMATION_PROMPT = """
Navigate to {linkedin_url} and extract mutual connections.

MANDATORY FIRST STEP - ALWAYS START HERE:
1. MUST navigate to this EXACT URL: {linkedin_url}
   (Do not stay on any previous page - go to this specific URL!)

THEN FOLLOW THESE STEPS:
2. On the profile page, look for text like "John Doe, Jane Smith, and X other mutual connections"
3. If you don't see mutual connections, return "No mutual connections found"
4. If you see mutual connections, click on that section (goes to connections page)
5. YOU WILL NOW BE ON A PAGE WITH URL CONTAINING "search/results/people" - THIS IS CORRECT!
6. This "search/results" page IS the mutual connections page - DO NOT GO BACK TO PROFILE!
7. Extract the FULL NAMES of the first {count} people you see on this connections page
8. Return ONLY the names as plain text: "Name1 | Name2 | Name3 | Name4 | Name5 | ..."

EXAMPLE ANSWER: "John Smith, Jane Doe, Mike Johnson, Sarah Wilson, Tom Brown"

CRITICAL UNDERSTANDING:
- After clicking mutual connections, you will be on linkedin.com/search/results/people/?face...
- THIS IS THE CORRECT DESTINATION - stay here and extract names!
- Do NOT think this is wrong and go back to the profile page!
- The "search/results" URL is LinkedIn's normal behavior for connections pages!

CRITICAL RULES:
- ALWAYS start by going to the specific URL: {linkedin_url}
- Do NOT create any files or attachments
- Do NOT write to files
- Return ONLY plain text with names
- Do NOT search on Google
- Do NOT click "Contact info"
- If fewer than {count} names exist, just return what you see
- If NO mutual connections exist, return "No mutual connections found"
- Once on the connections page (search/results URL), STAY THERE and extract names!

REMEMBER: Each task is independent - always start fresh at the given URL!
"""

class Config:
    """Configuration class for managing application settings."""
    
    def __init__(self):
        """Initialize configuration with environment variables and defaults."""
        self._load_environment_variables()
        self._validate_configuration()
    
    def _load_environment_variables(self) -> None:
        """Load configuration from environment variables."""
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        
        # Allow override of default settings via environment
        self.chrome_debugging_port = int(os.getenv('CHROME_DEBUG_PORT', CHROME_DEBUGGING_PORT))
        self.chrome_user_data_dir = os.getenv('CHROME_USER_DATA_DIR', CHROME_USER_DATA_DIR)
        self.mutual_connections_count = int(os.getenv('MUTUAL_CONNECTIONS_COUNT', MUTUAL_CONNECTIONS_TO_EXTRACT))
        self.retry_attempts = int(os.getenv('RETRY_ATTEMPTS', RETRY_ATTEMPTS))
        self.page_timeout = int(os.getenv('PAGE_TIMEOUT', PAGE_LOAD_TIMEOUT))
    
    def _validate_configuration(self) -> None:
        """Validate that all required configuration is present."""
        if not self.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )
    
    def get_chrome_command(self) -> list:
        """Get the Chrome launch command with current settings."""
        return [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            f"--remote-debugging-port={self.chrome_debugging_port}",
            f"--user-data-dir={self.chrome_user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check"
        ]
    
    def get_automation_prompt(self, linkedin_url: str) -> str:
        """Get the LinkedIn automation prompt for a specific URL."""
        return LINKEDIN_AUTOMATION_PROMPT.format(
            linkedin_url=linkedin_url,
            count=self.mutual_connections_count
        )
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration dictionary."""
        return {
            'level': LOG_LEVEL,
            'format': LOG_FORMAT,
            'datefmt': LOG_DATE_FORMAT
        }

# Global configuration instance
config = Config() 