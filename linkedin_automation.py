#!/usr/bin/env python3
"""
LinkedIn Automation with Browser-Use
===================================

This script connects to your existing Chrome browser session for LinkedIn automation,
enabling task execution while maintaining your authentic session.

Features:
- Connects to existing Chrome profile
- Maintains LinkedIn authentication
- Provides interactive task menu
- Supports custom automation tasks

Prerequisites:
- Chrome browser installed
- OpenAI API key configured
- LinkedIn account access

Author: Starnus Development Team
License: MIT
"""

import asyncio
import os
import sys
import subprocess
import time
import socket
from pathlib import Path
from typing import Optional

# Add browser-use to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from browser_use import Agent
from browser_use.browser import BrowserSession
from browser_use.llm import ChatGoogle

class LinkedInAutomation:
    """Main class for LinkedIn automation using your existing Chrome profile"""
    
    def __init__(self):
        self.browser_session: Optional[BrowserSession] = None
        self.debug_port = 9222
        self.chrome_path = self._get_chrome_path()
        self.linkedin_automation_dir = os.path.expanduser("~/linkedin-automation")  # Cross-platform user directory
        
    def _get_chrome_path(self) -> str:
        """Get Chrome executable path based on operating system"""
        import platform
        system = platform.system()
        if system == "Windows":
            return "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        elif system == "Darwin":  # macOS
            return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        else:  # Linux
            return "google-chrome"
        
    def _find_available_port(self, start_port: int = 9222) -> int:
        """Find an available port starting from start_port"""
        for port in range(start_port, start_port + 10):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        return start_port  # Fallback to original port
        
    def _close_all_chrome(self) -> bool:
        """Close all Chrome processes"""
        try:
            result = subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], 
                                  capture_output=True, check=False)
            if result.returncode == 0:
                print("✅ Closed all Chrome processes")
                time.sleep(3)  # Wait longer for processes to fully close
                return True
            else:
                print("⚠️  No Chrome processes to close")
                return True
        except Exception as e:
            print(f"❌ Failed to close Chrome: {e}")
            return False
    
    def _start_chrome_with_debugging(self) -> bool:
        """Start Chrome with debugging enabled using LinkedIn automation directory"""
        # Find available port
        self.debug_port = self._find_available_port(9222)
        print(f"🔧 Using debug port: {self.debug_port}")
        
        # Enhanced Chrome arguments for better debugging support
        cmd = [
            self.chrome_path,
            f'--remote-debugging-port={self.debug_port}',
            f'--user-data-dir={self.linkedin_automation_dir}',
            '--no-first-run',
            '--no-default-browser-check', 
            '--disable-default-apps',
            '--disable-popup-blocking',
            '--disable-translate',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-device-discovery-notifications'
        ]
        
        try:
            print(f"🚀 Starting Chrome with LinkedIn automation directory...")
            print(f"Directory: {self.linkedin_automation_dir}")
            print(f"Debug port: {self.debug_port}")
            print(f"Command: {' '.join(cmd)}")
            
            # Start Chrome process
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            print(f"🔧 Chrome process started with PID: {process.pid}")
            
            # Wait longer for Chrome to start and debugging port to become available
            print("⏳ Waiting for Chrome to start and debugging port to become available...")
            
            # Check if Chrome process is still running
            time.sleep(2)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"❌ Chrome process exited unexpectedly!")
                print(f"Exit code: {process.returncode}")
                if stderr:
                    print(f"Error: {stderr.decode()}")
                return False
            
            # Wait up to 15 seconds for debugging port to become available
            for i in range(15):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(1)
                        result = s.connect_ex(('127.0.0.1', self.debug_port))
                        if result == 0:
                            print(f"✅ Chrome debugging port {self.debug_port} is now available!")
                            time.sleep(2)  # Give Chrome a bit more time to fully initialize
                            return True
                except Exception:
                    pass
                
                print(f"⏳ Waiting for port {self.debug_port}... ({i+1}/15)")
                time.sleep(1)
            
            print(f"❌ Chrome debugging port {self.debug_port} did not become available after 15 seconds")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start Chrome: {e}")
            return False
    
    def _check_debug_connection(self) -> bool:
        """Check if Chrome debugging port is accessible"""
        try:
            import requests
            
            # Try multiple times with different timeouts
            for attempt in range(3):
                try:
                    print(f"🔍 Testing connection to http://localhost:{self.debug_port}/json/version (attempt {attempt + 1}/3)")
                    response = requests.get(f'http://localhost:{self.debug_port}/json/version', timeout=10)
                    if response.status_code == 200:
                        version_info = response.json()
                        print(f"✅ Chrome debugging connected!")
                        print(f"Browser: {version_info.get('Browser', 'Unknown')}")
                        print(f"Protocol Version: {version_info.get('Protocol-Version', 'Unknown')}")
                        return True
                    else:
                        print(f"⚠️  HTTP {response.status_code} response from debugging port")
                except requests.exceptions.ConnectionError as e:
                    print(f"⚠️  Connection attempt {attempt + 1} failed: {e}")
                    if attempt < 2:  # Don't sleep on the last attempt
                        time.sleep(2)
                except Exception as e:
                    print(f"⚠️  Unexpected error on attempt {attempt + 1}: {e}")
                    if attempt < 2:
                        time.sleep(2)
            
            print("❌ Chrome debugging port not accessible after 3 attempts")
            return False
            
        except Exception as e:
            print(f"❌ Cannot connect to Chrome debugging: {e}")
            return False
    
    async def connect_to_chrome(self) -> bool:
        """Connect browser-use to existing Chrome session"""
        try:
            print("🔗 Connecting browser-use to Chrome...")
            
            # Import BrowserProfile
            from browser_use.browser import BrowserProfile
            
            # Create a minimal browser profile for connecting to existing Chrome
            browser_profile = BrowserProfile(
                user_data_dir=self.linkedin_automation_dir,
                keep_alive=True,  # Don't close the browser when we're done
                headless=False
            )
            
            # Create browser session that connects via CDP
            self.browser_session = BrowserSession(
                cdp_url=f'http://localhost:{self.debug_port}',
                browser_profile=browser_profile
            )
            
            # Start the session (connect to Chrome)
            await self.browser_session.start()
            
            # Test the connection
            page = await self.browser_session.get_current_page()
            print(f"📍 Connected! Current page: {page.url}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect browser-use to Chrome: {e}")
            print("💡 This could be due to:")
            print("   - Chrome not starting with debugging enabled")
            print("   - Port conflicts")
            print("   - Chrome profile locked by another process")
            return False
    
    async def navigate_to_linkedin(self) -> bool:
        """Navigate to LinkedIn and verify login status"""
        try:
            if not self.browser_session:
                print("❌ No browser session available")
                return False
            
            page = await self.browser_session.get_current_page()
            
            print("🔗 Navigating to LinkedIn...")
            await page.goto('https://www.linkedin.com/feed/')
            await asyncio.sleep(3)
            
            current_url = page.url
            page_content = await page.content()
            
            # Check if we're logged in
            if 'feed' in current_url or 'feed' in page_content.lower():
                print("🎉 Successfully connected to LinkedIn!")
                print("✅ You are logged into LinkedIn")
                return True
            elif 'login' in current_url or 'challenge' in current_url:
                print("⚠️  You need to log into LinkedIn manually")
                print("Please log in through the browser window and try again")
                return False
            else:
                print("⚠️  LinkedIn page loaded but login status unclear")
                print("Please check the browser window")
                return False
                
        except Exception as e:
            print(f"❌ Error navigating to LinkedIn: {e}")
            return False
    
    async def run_linkedin_task(self, task: str) -> bool:
        """Run a specific LinkedIn automation task"""
        try:
            if not self.browser_session:
                print("❌ No browser session available")
                return False
            
            # Check if we have an API key
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                print("❌ GOOGLE_API_KEY not found in environment variables")
                print("Please set your Google API key to use AI automation")
                return False
            
            print(f"🤖 Running LinkedIn task: {task}")
            
            # Create LLM
            llm = ChatGoogle(model='gemini-2.5-pro', api_key=api_key)
            
            # Create Agent with your existing browser session
            agent = Agent(
                task=task,
                llm=llm,
                browser_session=self.browser_session,
            )
            
            # Run the task
            await agent.run()
            
            print("✅ LinkedIn task completed!")
            return True
            
        except Exception as e:
            print(f"❌ Error running LinkedIn task: {e}")
            return False
    
    async def close(self):
        """Close the browser session (but keep Chrome running)"""
        if self.browser_session:
            try:
                await self.browser_session.close()
                print("✅ Browser session closed (Chrome remains open)")
            except Exception as e:
                print(f"⚠️  Error closing session: {e}")

async def main():
    """Main execution function"""
    print("🔗 LinkedIn Automation with Browser-Use")
    print("=" * 50)
    
    automation = LinkedInAutomation()
    
    try:
        # Step 1: Prepare Chrome
        print("\n1️⃣  Preparing Chrome browser...")
        if not automation._close_all_chrome():
            print("❌ Failed to close existing Chrome processes")
            return
        
        if not automation._start_chrome_with_debugging():
            print("❌ Failed to start Chrome with debugging")
            print("\n💡 Troubleshooting tips:")
            print("   - Make sure Chrome is fully closed before running")
            print("   - Check if another application is using the debug port")
            print("   - Try restarting your computer if Chrome processes are stuck")
            return
        
        # Step 2: Check connection
        print("\n2️⃣  Checking Chrome debugging connection...")
        if not automation._check_debug_connection():
            print("❌ Chrome debugging not accessible")
            print("\n💡 Troubleshooting tips:")
            print("   - Chrome may have started but debugging port is not working")
            print("   - Try manually starting Chrome with:")
            print(f"     \"{automation.chrome_path}\" --remote-debugging-port={automation.debug_port} --user-data-dir=\"{automation.linkedin_automation_dir}\" --no-first-run --no-default-browser-check")
            return
        
        # Step 3: Connect browser-use
        print("\n3️⃣  Connecting browser-use to Chrome...")
        if not await automation.connect_to_chrome():
            print("❌ Failed to connect browser-use")
            return
        
        # Step 4: Navigate to LinkedIn
        print("\n4️⃣  Connecting to LinkedIn...")
        if not await automation.navigate_to_linkedin():
            print("❌ LinkedIn connection failed")
            print("💡 Please log into LinkedIn manually in the browser window")
            return
        
        print("\n🎉 LinkedIn automation setup complete!")
        print("🤖 You can now run automation tasks")
        
        # Interactive mode
        while True:
            print("\n" + "=" * 50)
            print("LinkedIn Automation Menu:")
            print("1. Run custom task")
            print("2. View my LinkedIn feed")
            print("3. Check my messages")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == '1':
                task = input("Enter your LinkedIn task: ").strip()
                if task:
                    await automation.run_linkedin_task(task)
                else:
                    print("❌ No task entered")
            
            elif choice == '2':
                task = "Look at my LinkedIn feed and tell me about the most recent posts"
                await automation.run_linkedin_task(task)
            
            elif choice == '3':
                task = "Check my LinkedIn messages and tell me if there are any unread messages"
                await automation.run_linkedin_task(task)
            
            elif choice == '4':
                print("👋 Exiting LinkedIn automation...")
                break
            
            else:
                print("❌ Invalid choice. Please select 1-4.")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await automation.close()
        print("✅ Done!")

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    # Check if Chrome exists
    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    if not Path(chrome_path).exists():
        print(f"❌ Chrome not found at: {chrome_path}")
        print("Please install Google Chrome or update the path in the script")
        sys.exit(1)
    
    # Run the automation
    asyncio.run(main()) 