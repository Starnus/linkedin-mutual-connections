"""
Excel Handler Module for LinkedIn Mutual Connections Automation.

Handles all Excel file operations including:
- Reading and writing Excel files
- Detecting LinkedIn URL columns
- Managing mutual connections and status columns
- Data validation and processing
"""

import pandas as pd
import logging
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from urllib.parse import urlparse

from .config import (
    MUTUAL_CONNECTIONS_COLUMN, 
    STATUS_COLUMN, 
    DONE_STATUS,
    PROCESSING_STATUS,
    ERROR_STATUS
)

logger = logging.getLogger(__name__)


class ExcelHandler:
    """Handles all Excel file operations for LinkedIn automation."""
    
    def __init__(self, file_path: str):
        """
        Initialize Excel handler with file path.
        
        Args:
            file_path: Path to the Excel file
            
        Raises:
            FileNotFoundError: If the Excel file doesn't exist
            ValueError: If the file is not a valid Excel file
        """
        self.file_path = Path(file_path)
        self.df: Optional[pd.DataFrame] = None
        self.linkedin_url_column: Optional[str] = None
        self.mutual_connections_column: Optional[str] = None
        self.status_column: Optional[str] = None
        
        self._validate_file()
        logger.info(f"Excel handler initialized for: {self.file_path}")
    
    def _validate_file(self) -> None:
        """Validate that the file exists and is a valid Excel file."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")
        
        if not self.file_path.suffix.lower() in ['.xlsx', '.xls']:
            raise ValueError(f"File must be an Excel file (.xlsx or .xls): {self.file_path}")
    
    def load_data(self) -> pd.DataFrame:
        """
        Load data from Excel file.
        
        Returns:
            DataFrame containing the Excel data
            
        Raises:
            Exception: If unable to read the Excel file
        """
        try:
            logger.info("Loading Excel data...")
            self.df = pd.read_excel(self.file_path)
            logger.info(f"Successfully loaded {len(self.df)} rows and {len(self.df.columns)} columns")
            
            # Log column names for debugging
            logger.debug(f"Columns found: {list(self.df.columns)}")
            
            return self.df
            
        except Exception as e:
            logger.error(f"Failed to load Excel file: {e}")
            raise
    
    def detect_linkedin_url_column(self) -> Optional[str]:
        """
        Detect which column contains LinkedIn URLs.
        
        Returns:
            Column name containing LinkedIn URLs, or None if not found
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        logger.info("Detecting LinkedIn URL column...")
        
        for column in self.df.columns:
            # Check if column contains LinkedIn URLs
            sample_values = self.df[column].dropna().head(10)
            linkedin_url_count = 0
            
            for value in sample_values:
                if self._is_linkedin_url(str(value)):
                    linkedin_url_count += 1
            
            # If majority of non-null values are LinkedIn URLs
            if linkedin_url_count >= len(sample_values) * 0.7:
                self.linkedin_url_column = column
                logger.info(f"LinkedIn URL column detected: '{column}'")
                return column
        
        logger.warning("No LinkedIn URL column detected")
        return None
    
    def _is_linkedin_url(self, url: str) -> bool:
        """
        Check if a string is a valid LinkedIn URL.
        
        Args:
            url: URL string to check
            
        Returns:
            True if it's a LinkedIn URL, False otherwise
        """
        try:
            # Basic URL pattern check
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed = urlparse(url)
            
            # Check if it's a LinkedIn domain
            linkedin_domains = ['linkedin.com', 'www.linkedin.com']
            if parsed.netloc.lower() not in linkedin_domains:
                return False
            
            # Check if it's a profile URL
            path_patterns = [
                r'/in/[\w\-]+/?$',  # Standard profile URLs
                r'/pub/[\w\-]+/\w+/\w+/\w+/?$'  # Public profile URLs
            ]
            
            for pattern in path_patterns:
                if re.search(pattern, parsed.path):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def check_existing_columns(self) -> Tuple[bool, bool]:
        """
        Check if mutual connections and status columns already exist.
        
        Returns:
            Tuple of (has_mutual_connections_column, has_status_column)
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        has_mutual_connections = MUTUAL_CONNECTIONS_COLUMN in self.df.columns
        has_status = STATUS_COLUMN in self.df.columns
        
        if has_mutual_connections:
            self.mutual_connections_column = MUTUAL_CONNECTIONS_COLUMN
            logger.info(f"Found existing mutual connections column: '{MUTUAL_CONNECTIONS_COLUMN}'")
        
        if has_status:
            self.status_column = STATUS_COLUMN
            logger.info(f"Found existing status column: '{STATUS_COLUMN}'")
        
        return has_mutual_connections, has_status
    
    def add_missing_columns(self) -> None:
        """Add mutual connections and status columns if they don't exist."""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        if self.linkedin_url_column is None:
            raise ValueError("LinkedIn URL column not detected. Cannot add columns.")
        
        # Find the position after the LinkedIn URL column
        linkedin_col_index = self.df.columns.get_loc(self.linkedin_url_column)
        
        # Add mutual connections column if it doesn't exist
        if MUTUAL_CONNECTIONS_COLUMN not in self.df.columns:
            self.df.insert(linkedin_col_index + 1, MUTUAL_CONNECTIONS_COLUMN, "")
            self.mutual_connections_column = MUTUAL_CONNECTIONS_COLUMN
            logger.info(f"Added mutual connections column: '{MUTUAL_CONNECTIONS_COLUMN}'")
        
        # Add status column if it doesn't exist
        if STATUS_COLUMN not in self.df.columns:
            status_insert_index = linkedin_col_index + 2 if MUTUAL_CONNECTIONS_COLUMN not in self.df.columns else linkedin_col_index + 2
            self.df.insert(status_insert_index, STATUS_COLUMN, "")
            self.status_column = STATUS_COLUMN
            logger.info(f"Added status column: '{STATUS_COLUMN}'")
    
    def find_resume_point(self) -> int:
        """
        Find the first row that doesn't have 'done' status.
        
        Returns:
            Row index to start processing from (0-based)
        """
        if self.df is None or self.status_column is None:
            return 0
        
        # Find first row where status is not 'done'
        for index, row in self.df.iterrows():
            status = str(row[self.status_column]).strip().lower()
            if status != DONE_STATUS.lower():
                logger.info(f"Resuming from row {index + 1} (0-based index: {index})")
                return index
        
        # All rows are done
        logger.info("All rows are marked as done")
        return len(self.df)
    
    def get_linkedin_urls_to_process(self, start_index: int = 0) -> List[Tuple[int, str]]:
        """
        Get LinkedIn URLs that need to be processed.
        
        Args:
            start_index: Index to start from
            
        Returns:
            List of (row_index, linkedin_url) tuples
        """
        if self.df is None or self.linkedin_url_column is None:
            return []
        
        urls_to_process = []
        
        for index in range(start_index, len(self.df)):
            row = self.df.iloc[index]
            
            # Get LinkedIn URL
            linkedin_url = str(row[self.linkedin_url_column]).strip()
            
            # Skip empty URLs
            if not linkedin_url or linkedin_url.lower() in ['nan', 'none', '']:
                continue
            
            # Check if already processed (if status column exists)
            if self.status_column:
                status = str(row[self.status_column]).strip().lower()
                if status == DONE_STATUS.lower():
                    continue
            
            # Validate LinkedIn URL
            if self._is_linkedin_url(linkedin_url):
                urls_to_process.append((index, linkedin_url))
            else:
                logger.warning(f"Invalid LinkedIn URL at row {index + 1}: {linkedin_url}")
        
        logger.info(f"Found {len(urls_to_process)} URLs to process")
        return urls_to_process
    
    def update_row(self, row_index: int, mutual_connections: str, status: str) -> None:
        """
        Update a row with mutual connections data and status.
        
        Args:
            row_index: Row index to update
            mutual_connections: Mutual connections data
            status: Status to set
        """
        if self.df is None:
            raise ValueError("Data not loaded.")
        
        if self.mutual_connections_column:
            self.df.at[row_index, self.mutual_connections_column] = mutual_connections
        
        if self.status_column:
            self.df.at[row_index, self.status_column] = status
        
        logger.debug(f"Updated row {row_index + 1}: mutual_connections='{mutual_connections}', status='{status}'")
    
    def set_processing_status(self, row_index: int) -> None:
        """Set a row's status to 'processing'."""
        if self.status_column:
            self.df.at[row_index, self.status_column] = PROCESSING_STATUS
            logger.debug(f"Set row {row_index + 1} status to 'processing'")
    
    def save_data(self, backup: bool = True) -> None:
        """
        Save the DataFrame back to the Excel file.
        
        Args:
            backup: Whether to create a backup of the original file
        """
        if self.df is None:
            raise ValueError("No data to save.")
        
        try:
            # Create backup if requested
            if backup:
                backup_path = self.file_path.with_suffix(f'.backup{self.file_path.suffix}')
                if backup_path.exists():
                    # Add timestamp to backup if one already exists
                    import datetime
                    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_path = self.file_path.with_suffix(f'.backup_{timestamp}{self.file_path.suffix}')
                
                import shutil
                shutil.copy2(self.file_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Save the updated data
            self.df.to_excel(self.file_path, index=False)
            logger.info(f"Data saved successfully to: {self.file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            raise
    
    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the data for logging/debugging.
        
        Returns:
            Dictionary with data summary
        """
        if self.df is None:
            return {"error": "Data not loaded"}
        
        total_rows = len(self.df)
        
        summary = {
            "total_rows": total_rows,
            "total_columns": len(self.df.columns),
            "linkedin_url_column": self.linkedin_url_column,
            "mutual_connections_column": self.mutual_connections_column,
            "status_column": self.status_column
        }
        
        if self.status_column:
            status_counts = self.df[self.status_column].value_counts().to_dict()
            summary["status_distribution"] = status_counts
            summary["rows_completed"] = status_counts.get(DONE_STATUS, 0)
            summary["rows_remaining"] = total_rows - status_counts.get(DONE_STATUS, 0)
        
        return summary 