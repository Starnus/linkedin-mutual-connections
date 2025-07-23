"""
Main Orchestrator for LinkedIn Mutual Connections Automation.

This module coordinates the entire automation process:
1. Load and analyze Excel file
2. Initialize LinkedIn automation
3. Process LinkedIn profiles
4. Extract mutual connections
5. Update Excel file with results
"""

import asyncio
import logging
import sys
import argparse
from pathlib import Path
from typing import Optional

from modules.config import config, APP_NAME, VERSION
from modules.excel_handler import ExcelHandler
from modules.linkedin_automation import LinkedInAutomation


def setup_logging() -> None:
    """Setup professional logging configuration."""
    logging_config = config.get_logging_config()
    
    # Create formatter
    formatter = logging.Formatter(
        logging_config['format'],
        datefmt=logging_config['datefmt']
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging_config['level'])
    
    # Setup file handler
    log_file = Path("linkedin_automation.log")
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # File gets more detailed logs
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)
    
    print(f"Logging configured. Log file: {log_file.absolute()}")


class LinkedInMutualConnectionsProcessor:
    """Main processor for LinkedIn mutual connections automation."""
    
    def __init__(self, excel_file_path: str):
        """
        Initialize the processor.
        
        Args:
            excel_file_path: Path to the Excel file to process
        """
        self.excel_file_path = excel_file_path
        self.excel_handler: Optional[ExcelHandler] = None
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Processor initialized for: {excel_file_path}")
    
    async def run(self) -> bool:
        """
        Run the complete automation process.
        
        Returns:
            True if process completed successfully, False otherwise
        """
        try:
            self.logger.info(f"Starting {APP_NAME} v{VERSION}")
            
            # Step 1: Initialize Excel handler
            if not await self._initialize_excel_handler():
                return False
            
            # Step 2: Process LinkedIn profiles (each with fresh automation)
            if not await self._process_linkedin_profiles():
                return False
            
            # Step 3: Save results
            if not await self._save_results():
                return False
            
            self.logger.info("Automation process completed successfully!")
            return True
            
        except KeyboardInterrupt:
            self.logger.info("Process interrupted by user")
            return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error in main process: {e}", exc_info=True)
            return False
            
        finally:
            await self._cleanup()
    
    async def _initialize_excel_handler(self) -> bool:
        """Initialize and setup the Excel handler."""
        try:
            self.logger.info("Step 1: Initializing Excel handler...")
            
            # Create Excel handler
            self.excel_handler = ExcelHandler(self.excel_file_path)
            
            # Load data
            self.excel_handler.load_data()
            
            # Detect LinkedIn URL column
            linkedin_column = self.excel_handler.detect_linkedin_url_column()
            if not linkedin_column:
                self.logger.error("No LinkedIn URL column found in Excel file")
                return False
            
            # Check for existing columns
            has_mutual_conn, has_status = self.excel_handler.check_existing_columns()
            
            # Add missing columns if needed
            if not has_mutual_conn or not has_status:
                self.logger.info("Adding missing columns to Excel file...")
                self.excel_handler.add_missing_columns()
            
            # Log data summary
            summary = self.excel_handler.get_data_summary()
            self.logger.info(f"Excel data summary: {summary}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Excel handler: {e}")
            return False
    
    async def _process_linkedin_profiles(self) -> bool:
        """Process all LinkedIn profiles in the Excel file."""
        try:
            self.logger.info("Step 2: Processing LinkedIn profiles...")
            
            # Find resume point
            start_index = self.excel_handler.find_resume_point()
            
            # Get URLs to process
            urls_to_process = self.excel_handler.get_linkedin_urls_to_process(start_index)
            
            if not urls_to_process:
                self.logger.info("No LinkedIn URLs to process")
                return True
            
            self.logger.info(f"Processing {len(urls_to_process)} LinkedIn profiles...")
            
            # Process each URL with complete isolation
            for i, (row_index, linkedin_url) in enumerate(urls_to_process):
                self.logger.info(f"Processing {i+1}/{len(urls_to_process)}: Row {row_index + 1}")
                
                # Create fresh automation instance for this URL
                linkedin_automation = None
                
                try:
                    # Set processing status
                    self.excel_handler.set_processing_status(row_index)
                    
                    # Save intermediate progress
                    if i % 5 == 0:  # Save every 5 processed items
                        self.excel_handler.save_data()
                    
                    # Create fresh LinkedIn automation instance
                    self.logger.info(f"Creating fresh automation instance for URL: {linkedin_url}")
                    linkedin_automation = LinkedInAutomation()
                    
                    # Initialize the automation (starts Chrome, connects browser-use)
                    if not await linkedin_automation.initialize():
                        raise Exception("Failed to initialize LinkedIn automation")
                    
                    # Process the LinkedIn profile with the fresh instance
                    result = await linkedin_automation.process_with_retry(linkedin_url)
                    
                    # Update Excel with results
                    self.excel_handler.update_row(
                        row_index,
                        result['mutual_connections'],
                        result['status']
                    )
                    
                    if result['success']:
                        self.logger.info(f"✅ Successfully processed row {row_index + 1}")
                    else:
                        self.logger.warning(f"⚠️ Failed to process row {row_index + 1}: {result.get('error', 'Unknown error')}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing row {row_index + 1}: {e}")
                    
                    # Update with error status
                    self.excel_handler.update_row(
                        row_index,
                        f"Error: {str(e)}",
                        "error"
                    )
                
                finally:
                    # CRITICAL: Complete shutdown for each URL
                    if linkedin_automation:
                        try:
                            self.logger.info("Performing complete shutdown before next URL...")
                            await linkedin_automation.complete_shutdown()
                            self.logger.info("Shutdown complete - ready for next URL")
                        except Exception as e:
                            self.logger.error(f"Error during shutdown: {e}")
                    
                    # Brief pause between URLs
                    if i < len(urls_to_process) - 1:  # Don't wait after the last URL
                        self.logger.info("Waiting 3 seconds before next URL...")
                        await asyncio.sleep(3)
            
            self.logger.info("Finished processing all LinkedIn profiles")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in profile processing: {e}")
            return False
    
    async def _save_results(self) -> bool:
        """Save the final results to Excel."""
        try:
            self.logger.info("Step 3: Saving results...")
            
            self.excel_handler.save_data(backup=True)
            
            # Log final summary
            final_summary = self.excel_handler.get_data_summary()
            self.logger.info(f"Final data summary: {final_summary}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
            return False
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.logger.info("Cleaning up resources...")
            
            # Note: No need to cleanup linkedin_automation here since each URL 
            # creates and completely shuts down its own instance
            
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


async def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} v{VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py linkedin_profiles.xlsx
  python main.py "C:\\path\\to\\your\\file.xlsx"
        """
    )
    
    parser.add_argument(
        'excel_file',
        help='Path to the Excel file containing LinkedIn URLs'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'{APP_NAME} v{VERSION}'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Validate Excel file
    excel_path = Path(args.excel_file)
    if not excel_path.exists():
        print(f"Error: Excel file not found: {excel_path}")
        sys.exit(1)
    
    # Create and run processor
    processor = LinkedInMutualConnectionsProcessor(str(excel_path))
    success = await processor.run()
    
    if success:
        print("\n🎉 Automation completed successfully!")
        print(f"📊 Results saved to: {excel_path}")
        print("📋 Check the log file for detailed information.")
    else:
        print("\n❌ Automation failed. Check the log file for details.")
        sys.exit(1)


if __name__ == "__main__":
    # Set up event loop policy for Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main()) 