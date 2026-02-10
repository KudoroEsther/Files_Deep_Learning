"""
Data Cleaning Pipeline for CSV Files
A modular pipeline for cleaning and preprocessing CSV data
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataCleaningPipeline:
    """
    A comprehensive data cleaning pipeline for CSV files.
    """
    
    def __init__(self, filepath):
        """
        Initialize the pipeline with a CSV file.
        
        Args:
            filepath (str): Path to the CSV file
        """
        self.filepath = filepath
        self.df = None
        self.original_shape = None
        self.cleaning_report = {}
        
    def load_data(self, **kwargs):
        """
        Load CSV data into a pandas DataFrame.
        
        Args:
            **kwargs: Additional arguments to pass to pd.read_csv()
        """
        logger.info(f"Loading data from {self.filepath}")
        try:
            self.df = pd.read_csv(self.filepath, **kwargs)
            self.original_shape = self.df.shape
            logger.info(f"Data loaded successfully. Shape: {self.df.shape}")
            self.cleaning_report['original_rows'] = self.df.shape[0]
            self.cleaning_report['original_columns'] = self.df.shape[1]
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
            
    def display_info(self):
        """Display basic information about the dataset."""
        if self.df is None:
            logger.warning("No data loaded yet.")
            return
            
        logger.info("\n=== Dataset Information ===")
        logger.info(f"Shape: {self.df.shape}")
        logger.info(f"Columns: {list(self.df.columns)}")
        logger.info(f"\nData Types:\n{self.df.dtypes}")
        logger.info(f"\nMissing Values:\n{self.df.isnull().sum()}")
        logger.info(f"\nDuplicate Rows: {self.df.duplicated().sum()}")
        
    def remove_duplicates(self, subset=None, keep='first'):
        """
        Remove duplicate rows.
        
        Args:
            subset (list): Column names to consider for duplicates
            keep (str): Which duplicates to keep ('first', 'last', or False)
        """
        if self.df is None:
            logger.warning("No data loaded yet.")
            return
            
        initial_rows = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep=keep)
        rows_removed = initial_rows - len(self.df)
        
        logger.info(f"Removed {rows_removed} duplicate rows")
        self.cleaning_report['duplicates_removed'] = rows_removed
        
    def handle_missing_values(self, strategy='auto', fill_value=None, columns=None):
        """
        Handle missing values with various strategies.
        
        Args:
            strategy (str): 'drop', 'fill', 'auto', 'ffill', 'bfill'
            fill_value: Value to use for filling (if strategy is 'fill')
            columns (list): Specific columns to apply strategy to
        """
        if self.df is None:
            logger.warning("No data loaded yet.")
            return
            
        missing_before = self.df.isnull().sum().sum()
        
        if columns is None:
            columns = self.df.columns
            
        if strategy == 'drop':
            self.df = self.df.dropna(subset=columns)
            logger.info(f"Dropped rows with missing values")
            
        elif strategy == 'fill':
            self.df[columns] = self.df[columns].fillna(fill_value)
            logger.info(f"Filled missing values with {fill_value}")
            
        elif strategy == 'ffill':
            self.df[columns] = self.df[columns].fillna(method='ffill')
            logger.info(f"Forward filled missing values")
            
        elif strategy == 'bfill':
            self.df[columns] = self.df[columns].fillna(method='bfill')
            logger.info(f"Backward filled missing values")
            
        elif strategy == 'auto':
            for col in columns:
                if self.df[col].dtype in ['int64', 'float64']:
                    # Fill numeric columns with median
                    self.df[col].fillna(self.df[col].median(), inplace=True)
                else:
                    # Fill categorical columns with mode
                    mode_value = self.df[col].mode()
                    if len(mode_value) > 0:
                        self.df[col].fillna(mode_value[0], inplace=True)
            logger.info(f"Auto-filled missing values (median for numeric, mode for categorical)")
        
        missing_after = self.df.isnull().sum().sum()
        self.cleaning_report['missing_values_handled'] = missing_before - missing_after
        
    def remove_outliers(self, columns=None, method='iqr', threshold=1.5):
        """
        Remove outliers from numeric columns.
        
        Args:
            columns (list): Columns to check for outliers
            method (str): 'iqr' or 'zscore'
            threshold (float): IQR multiplier or z-score threshold
        """
        if self.df is None:
            logger.warning("No data loaded yet.")
            return
            
        initial_rows = len(self.df)
        
        if columns is None:
            columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
            
        for col in columns:
            if method == 'iqr':
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                self.df = self.df[(self.df[col] >= lower_bound) & (self.df[col] <= upper_bound)]
                
            elif method == 'zscore':
                z_scores = np.abs((self.df[col] - self.df[col].mean()) / self.df[col].std())
                self.df = self.df[z_scores < threshold]
        
        rows_removed = initial_rows - len(self.df)
        logger.info(f"Removed {rows_removed} outlier rows using {method} method")
        self.cleaning_report['outliers_removed'] = rows_removed
        
    def standardize_text(self, columns=None, lowercase=True, strip=True, remove_special=False):
        """
        Standardize text columns.
        
        Args:
            columns (list): Text columns to standardize
            lowercase (bool): Convert to lowercase
            strip (bool): Remove leading/trailing whitespace
            remove_special (bool): Remove special characters
        """
        if self.df is None:
            logger.warning("No data loaded yet.")
            return
            
        if columns is None:
            columns = self.df.select_dtypes(include=['object']).columns.tolist()
            
        for col in columns:
            if strip:
                self.df[col] = self.df[col].astype(str).str.strip()
            if lowercase:
                self.df[col] = self.df[col].astype(str).str.lower()
            if remove_special:
                self.df[col] = self.df[col].astype(str).str.replace(r'[^a-zA-Z0-9\s]', '', regex=True)
                
        logger.info(f"Standardized text columns: {columns}")
        self.cleaning_report['text_columns_standardized'] = len(columns)
        
    def convert_data_types(self, type_dict):
        """
        Convert column data types.
        
        Args:
            type_dict (dict): Dictionary mapping column names to data types
                             Example: {'age': 'int', 'price': 'float', 'date': 'datetime'}
        """
        if self.df is None:
            logger.warning("No data loaded yet.")
            return
            
        for col, dtype in type_dict.items():
            try:
                if dtype == 'datetime':
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                else:
                    self.df[col] = self.df[col].astype(dtype)
                logger.info(f"Converted {col} to {dtype}")
            except Exception as e:
                logger.error(f"Error converting {col} to {dtype}: {e}")
                
        self.cleaning_report['columns_type_converted'] = len(type_dict)
        
    def rename_columns(self, rename_dict=None, snake_case=False):
        """
        Rename columns.
        
        Args:
            rename_dict (dict): Dictionary mapping old names to new names
            snake_case (bool): Convert all column names to snake_case
        """
        if self.df is None:
            logger.warning("No data loaded yet.")
            return
            
        if rename_dict:
            self.df.rename(columns=rename_dict, inplace=True)
            logger.info(f"Renamed columns: {rename_dict}")
            
        if snake_case:
            new_columns = {}
            for col in self.df.columns:
                # Convert to snake_case
                snake = re.sub(r'(?<!^)(?=[A-Z])', '_', col).lower()
                snake = re.sub(r'[^a-z0-9_]', '_', snake)
                snake = re.sub(r'_+', '_', snake).strip('_')
                new_columns[col] = snake
            self.df.rename(columns=new_columns, inplace=True)
            logger.info(f"Converted column names to snake_case")
            
    def remove_columns(self, columns):
        """
        Remove specified columns.
        
        Args:
            columns (list): List of column names to remove
        """
        if self.df is None:
            logger.warning("No data loaded yet.")
            return
            
        existing_cols = [col for col in columns if col in self.df.columns]
        self.df = self.df.drop(columns=existing_cols)
        logger.info(f"Removed columns: {existing_cols}")
        self.cleaning_report['columns_removed'] = len(existing_cols)
        
    def reset_index(self):
        """Reset the DataFrame index."""
        if self.df is None:
            logger.warning("No data loaded yet.")
            return
            
        self.df.reset_index(drop=True, inplace=True)
        logger.info("Reset index")
        
    def save_cleaned_data(self, output_path, index=False, **kwargs):
        """
        Save cleaned data to CSV.
        
        Args:
            output_path (str): Path for output CSV file
            index (bool): Whether to write row indices
            **kwargs: Additional arguments to pass to to_csv()
        """
        if self.df is None:
            logger.warning("No data loaded yet.")
            return
            
        try:
            self.df.to_csv(output_path, index=index, **kwargs)
            logger.info(f"Cleaned data saved to {output_path}")
            logger.info(f"Final shape: {self.df.shape}")
            self.cleaning_report['final_rows'] = self.df.shape[0]
            self.cleaning_report['final_columns'] = self.df.shape[1]
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            raise
            
    def generate_report(self):
        """Generate and display cleaning report."""
        logger.info("\n=== Data Cleaning Report ===")
        for key, value in self.cleaning_report.items():
            logger.info(f"{key}: {value}")
        
        if 'original_rows' in self.cleaning_report and 'final_rows' in self.cleaning_report:
            rows_change = self.cleaning_report['original_rows'] - self.cleaning_report['final_rows']
            pct_change = (rows_change / self.cleaning_report['original_rows']) * 100
            logger.info(f"\nTotal rows removed: {rows_change} ({pct_change:.2f}%)")
            
        return self.cleaning_report


# Example usage
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = DataCleaningPipeline('your_data.csv')
    
    # Load data
    pipeline.load_data()
    
    # Display initial info
    pipeline.display_info()
    
    # Clean the data
    pipeline.remove_duplicates()
    pipeline.handle_missing_values(strategy='auto')
    pipeline.standardize_text(lowercase=True, strip=True)
    pipeline.remove_outliers(method='iqr', threshold=1.5)
    
    # Optional: Convert data types
    # pipeline.convert_data_types({'date_column': 'datetime', 'price': 'float'})
    
    # Optional: Rename columns to snake_case
    # pipeline.rename_columns(snake_case=True)
    
    # Reset index
    pipeline.reset_index()
    
    # Save cleaned data
    pipeline.save_cleaned_data('cleaned_data.csv')
    
    # Generate report
    pipeline.generate_report()
