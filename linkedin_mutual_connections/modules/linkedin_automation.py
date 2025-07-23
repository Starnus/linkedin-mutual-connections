"""
LinkedIn Automation Module for Mutual Connections Extraction.

Handles browser automation for extracting mutual connections from LinkedIn profiles
using the browser-use library with OpenAI integration.
"""

import asyncio
import logging
import subprocess
import time
import socket
from pathlib import Path
from typing import Optional, Dict, Any

from browser_use import Agent
from browser_use.browser import BrowserSession, BrowserProfile
from browser_use.llm import ChatGoogle  # you can also choose ChatOpenAI, then also change the model name

from .config import config, DONE_STATUS, ERROR_STATUS, RETRY_DELAY

logger = logging.getLogger(__name__)


class LinkedInAutomation:
    """Handles LinkedIn automation for mutual connections extraction."""
    
    def __init__(self):
        """Initialize the LinkedIn automation system."""
        self.browser_session: Optional[BrowserSession] = None
        self.llm: Optional[ChatGoogle] = None
        self.chrome_process: Optional[subprocess.Popen] = None
        
        logger.info("LinkedIn automation initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize the browser session and LLM.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing LinkedIn automation...")
            
            # Setup LLM
            self._setup_llm()
            
            # Start Chrome with debugging
            if not await self._start_chrome_with_debugging():
                return False
            
            # Connect browser-use to Chrome
            if not await self._connect_browser_session():
                return False
            
            # Navigate to LinkedIn to verify connection
            if not await self._verify_linkedin_access():
                return False
            
            logger.info("LinkedIn automation initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LinkedIn automation: {e}")
            return False
    
    def _setup_llm(self) -> None:
        """Setup the OpenAI LLM for automation."""
        try:
            self.llm = ChatGoogle(
                model='gemini-2.5-pro',
                api_key=config.google_api_key
            )
            logger.info("LLM initialized successfully with gpt-4o")

        except Exception as e:
            logger.error(f"Failed to setup LLM: {e}")
            raise
    
    async def _start_chrome_with_debugging(self) -> bool:
        """
        Start Chrome with debugging enabled.
        
        Returns:
            True if Chrome started successfully, False otherwise
        """
        try:
            logger.info("Starting Chrome with debugging...")
            
            # Close existing Chrome processes
            self._close_existing_chrome()
            
            # Start Chrome with debugging
            chrome_command = config.get_chrome_command()
            logger.debug(f"Chrome command: {' '.join(chrome_command)}")
            
            self.chrome_process = subprocess.Popen(
                chrome_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if subprocess.sys.platform == 'win32' else 0
            )
            
            logger.info(f"Chrome started with PID: {self.chrome_process.pid}")
            
            # Wait for debugging port to become available
            if not await self._wait_for_debug_port():
                logger.error("Chrome debugging port never became available")
                return False
            
            logger.info("Chrome debugging port is ready")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Chrome: {e}")
            return False
    
    def _close_existing_chrome(self) -> None:
        """Close all existing Chrome processes."""
        try:
            if subprocess.sys.platform == 'win32':
                result = subprocess.run(
                    ['taskkill', '/f', '/im', 'chrome.exe'],
                    capture_output=True,
                    check=False
                )
                if result.returncode == 0:
                    logger.info("Closed existing Chrome processes")
                    time.sleep(3)  # Wait for cleanup
            else:
                # Linux/macOS
                subprocess.run(['pkill', '-f', 'chrome'], check=False)
                time.sleep(2)
                
        except Exception as e:
            logger.warning(f"Error closing Chrome processes: {e}")
    
    async def _wait_for_debug_port(self, timeout: int = 30) -> bool:
        """
        Wait for Chrome debugging port to become available.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if port becomes available, False otherwise
        """
        for attempt in range(timeout):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('127.0.0.1', config.chrome_debugging_port))
                    if result == 0:
                        return True
            except Exception:
                pass
            
            if attempt == 0:
                logger.info("Waiting for Chrome debugging port...")
            
            await asyncio.sleep(1)
        
        return False
    
    async def _connect_browser_session(self) -> bool:
        """
        Connect browser-use to the Chrome debugging session.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("Connecting browser-use to Chrome...")
            
            # Create browser profile for connecting to existing Chrome
            browser_profile = BrowserProfile(
                user_data_dir=config.chrome_user_data_dir,
                keep_alive=True,
                headless=False
            )
            
            # Create browser session
            self.browser_session = BrowserSession(
                cdp_url=f'http://localhost:{config.chrome_debugging_port}',
                browser_profile=browser_profile
            )
            
            # Start the session
            await self.browser_session.start()
            
            # Test the connection
            page = await self.browser_session.get_current_page()
            logger.info(f"Browser-use connected successfully. Current page: {page.url}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect browser-use: {e}")
            return False
    
    async def _verify_linkedin_access(self) -> bool:
        """
        Verify that we can access LinkedIn.
        
        Returns:
            True if LinkedIn is accessible, False otherwise
        """
        try:
            logger.info("Verifying LinkedIn access...")
            
            page = await self.browser_session.get_current_page()
            await page.goto('https://www.linkedin.com/feed/')
            await asyncio.sleep(3)
            
            current_url = page.url
            
            if 'feed' in current_url or 'linkedin.com' in current_url:
                logger.info("LinkedIn access verified")
                return True
            elif 'login' in current_url or 'challenge' in current_url:
                logger.warning("LinkedIn login required. Please log in manually and restart.")
                return False
            else:
                logger.warning("LinkedIn access unclear. Proceeding with caution.")
                return True
                
        except Exception as e:
            logger.error(f"Failed to verify LinkedIn access: {e}")
            return False
    
    async def extract_mutual_connections(self, linkedin_url: str) -> Dict[str, Any]:
        """
        Extract mutual connections from a LinkedIn profile.
        
        Args:
            linkedin_url: The LinkedIn profile URL to process
            
        Returns:
            Dictionary with extraction results:
            {
                'success': bool,
                'mutual_connections': str,
                'status': str,
                'error': str (if any)
            }
        """
        logger.info(f"Extracting mutual connections from: {linkedin_url}")
        
        result = {
            'success': False,
            'mutual_connections': '',
            'status': ERROR_STATUS,
            'error': ''
        }
        
        try:
            # Validate inputs
            if not self.browser_session or not self.llm:
                raise ValueError("Browser session or LLM not initialized")
            
            # Create automation prompt
            prompt = config.get_automation_prompt(linkedin_url)
            logger.debug(f"Automation prompt: {prompt}")
            
            # Create and run agent
            agent = Agent(
                task=prompt,
                llm=self.llm,
                browser_session=self.browser_session
            )
            
            # Run the automation with timeout and capture the result
            history = await asyncio.wait_for(
                agent.run(),
                timeout=config.page_timeout / 1000
            )
            
            # Debug: Log the full history structure
            logger.debug(f"Agent completed. History length: {len(history.history)}")
            logger.debug(f"Agent is_done: {history.is_done()}")
            logger.debug(f"Agent is_successful: {history.is_successful()}")
            
            # Extract the actual result from the agent history
            final_result = history.final_result()
            logger.debug(f"Final result from history.final_result(): {final_result}")
            
            # Also check the last action result manually
            if history.history and history.history[-1].result:
                last_results = history.history[-1].result
                logger.debug(f"Last action results count: {len(last_results)}")
                for i, action_result in enumerate(last_results):
                    logger.debug(f"Result {i}: extracted_content='{action_result.extracted_content}', is_done={action_result.is_done}, error='{action_result.error}'")
            
            # Try multiple ways to get the result
            extracted_names = None
            
            # Method 1: Use final_result()
            if final_result:
                extracted_names = str(final_result).strip()
                logger.info(f"Got result via final_result(): {extracted_names}")
            
            # Method 2: Check the last done action
            elif history.history:
                for history_item in reversed(history.history):
                    if history_item.result:
                        for action_result in reversed(history_item.result):
                            if action_result.is_done and action_result.extracted_content:
                                extracted_names = str(action_result.extracted_content).strip()
                                logger.info(f"Got result via done action: {extracted_names}")
                                break
                    if extracted_names:
                        break
            
            # Method 3: Check all extracted content
            if not extracted_names:
                all_extracted = history.extracted_content()
                if all_extracted:
                    # Take the last meaningful extraction
                    extracted_names = str(all_extracted[-1]).strip()
                    logger.info(f"Got result via extracted_content: {extracted_names}")
            
            if extracted_names:
                # Validate the result
                if extracted_names and extracted_names.lower() not in ['none', 'null', '']:
                    if 'no mutual connections found' in extracted_names.lower():
                        result['mutual_connections'] = "No mutual connections found"
                    elif 'error:' in extracted_names.lower():
                        result['mutual_connections'] = extracted_names
                    else:
                        # Successfully extracted names
                        result['mutual_connections'] = extracted_names
                    
                    result['status'] = DONE_STATUS
                    result['success'] = True
                    logger.info(f"Successfully extracted mutual connections for: {linkedin_url}")
                else:
                    result['mutual_connections'] = "Empty result returned from automation"
                    result['status'] = DONE_STATUS
                    result['success'] = True
                    logger.warning(f"Empty result returned for: {linkedin_url}")
            else:
                # Check if the task was successful even without a final result
                if history.is_successful():
                    result['mutual_connections'] = "Task completed but no result extracted"
                    result['status'] = DONE_STATUS
                    result['success'] = True
                    logger.warning(f"Task completed but no result for: {linkedin_url}")
                else:
                    # Fallback: try to check the page content for mutual connections
                    page = await self.browser_session.get_current_page()
                    page_content = await page.content()
                    
                    if "mutual connection" in page_content.lower():
                        result['mutual_connections'] = "Mutual connections found but extraction failed"
                        result['status'] = DONE_STATUS
                        result['success'] = True
                        logger.warning(f"Found mutual connections but couldn't extract names for: {linkedin_url}")
                    else:
                        result['mutual_connections'] = "No mutual connections found"
                        result['status'] = DONE_STATUS
                        result['success'] = True
                        logger.info(f"No mutual connections found for: {linkedin_url}")
            
        except asyncio.TimeoutError:
            error_msg = f"Timeout while processing {linkedin_url}"
            logger.error(error_msg)
            result['error'] = error_msg
            result['mutual_connections'] = "Timeout"
            
        except Exception as e:
            error_msg = f"Error extracting mutual connections: {e}"
            logger.error(error_msg)
            result['error'] = error_msg
            result['mutual_connections'] = f"Error: {str(e)}"
        
        return result
    
    async def process_with_retry(self, linkedin_url: str, max_retries: int = None) -> Dict[str, Any]:
        """
        Process a LinkedIn URL with retry logic.
        
        Args:
            linkedin_url: The LinkedIn profile URL to process
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with extraction results
        """
        max_retries = max_retries or config.retry_attempts
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt} for: {linkedin_url}")
                await asyncio.sleep(RETRY_DELAY)
            
            result = await self.extract_mutual_connections(linkedin_url)
            
            if result['success']:
                return result
            
            logger.warning(f"Attempt {attempt + 1} failed for {linkedin_url}: {result.get('error', 'Unknown error')}")
        
        logger.error(f"All {max_retries + 1} attempts failed for: {linkedin_url}")
        return result
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            logger.info("Cleaning up LinkedIn automation...")
            
            if self.browser_session:
                await self.browser_session.close()
                logger.info("Browser session closed")
            
            # Note: We don't close Chrome here to allow manual inspection
            # The user can close it manually if needed
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def complete_shutdown(self) -> None:
        """Complete shutdown including terminating Chrome process."""
        try:
            logger.info("Performing complete shutdown...")
            
            # Close browser session first
            if self.browser_session:
                await self.browser_session.close()
                logger.info("Browser session closed")
            
            # Wait a moment for session to close
            await asyncio.sleep(2)
            
            # Force terminate Chrome process
            if self.chrome_process and self.chrome_process.poll() is None:
                logger.info(f"Terminating Chrome process (PID: {self.chrome_process.pid})")
                try:
                    self.chrome_process.terminate()
                    # Wait for graceful termination
                    await asyncio.sleep(3)
                    
                    # Force kill if still running
                    if self.chrome_process.poll() is None:
                        self.chrome_process.kill()
                        logger.info("Chrome process force killed")
                    else:
                        logger.info("Chrome process terminated gracefully")
                except Exception as e:
                    logger.warning(f"Error terminating Chrome process: {e}")
            
            # Additional cleanup: kill any remaining Chrome processes
            try:
                if subprocess.sys.platform == 'win32':
                    subprocess.run(
                        ['taskkill', '/f', '/im', 'chrome.exe'],
                        capture_output=True,
                        check=False
                    )
                    logger.info("Killed any remaining Chrome processes")
            except Exception as e:
                logger.warning(f"Error killing remaining Chrome processes: {e}")
            
            # Reset instance variables
            self.browser_session = None
            self.chrome_process = None
            
            logger.info("Complete shutdown finished")
            
        except Exception as e:
            logger.error(f"Error during complete shutdown: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the automation system.
        
        Returns:
            Dictionary with status information
        """
        return {
            'browser_session_active': self.browser_session is not None,
            'llm_initialized': self.llm is not None,
            'chrome_process_running': self.chrome_process and self.chrome_process.poll() is None,
            'chrome_pid': self.chrome_process.pid if self.chrome_process else None
        } 