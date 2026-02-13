print("Importing libraries...")
import csv
import os
import pandas as pd
import numpy as np
import random

import re
from urllib.parse import urlparse

import logging

random.seed(42)

print("Libraries imported!")


pd.options.display.float_format = "{:.2f}".format

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



def load_data(path:str):
    """Loads the dataset"""
    data = pd.read_csv(path)
    return data


    

# Detect duplicate entries using Tool Name, Company, and Website. Decide which record to keep and remove the rest using deterministic logic.

class DuplicateHandler:
    def __init__(self, df):
        self.df = df
        self.duplicate_keys = ['Tool Name', 'Company', 'Website']
        logger.info(f"DuplicateHandler initialized with {len(self.df)} records")
        logger.info(f"Duplicate detection keys: {', '.join(self.duplicate_keys)}")
        
    def find_duplicates(self):
        """Identify duplicate groups"""
        duplicates = self.df[self.df.duplicated(subset=self.duplicate_keys, keep=False)]
        logger.info(f"Found {len(duplicates)} duplicate records in {duplicates.groupby(self.duplicate_keys, dropna=False).ngroups} groups")
        return duplicates
    
    def rank_records(self, group):
        """Score records: higher is better"""
        scores = pd.DataFrame(index=group.index)
        scores['completeness'] = group.notna().sum(axis=1)
        scores['reviews'] = group['review_count'].fillna(0)
        scores['rating'] = group['average_rating'].fillna(0)
        scores['recency'] = group['Launch Year'].fillna(0)
        scores['position'] = -np.arange(len(group))  # negative for ascending
        return scores.sum(axis=1).idxmax()
    
    def remove_duplicates(self):
        """Keep best record per duplicate group"""
        dupes = self.find_duplicates()
        if dupes.empty:
            logger.info("No duplicates found")
            return self.df, pd.DataFrame()
        
        keep_indices = dupes.groupby(self.duplicate_keys, dropna=False).apply(self.rank_records)
        removed = self.df[self.df.index.isin(dupes.index) & ~self.df.index.isin(keep_indices)]
        cleaned = self.df[~self.df.index.isin(dupes.index) | self.df.index.isin(keep_indices)]
        
        logger.info(f"Removed {len(removed)} duplicate records")
        logger.info(f"Retained {len(cleaned)} unique records")
        return cleaned.reset_index(drop=True), removed


class MissingDataHandler:
    def __init__(self, df):
        self.df = df.copy()
        
    def find_missing(self):
        """Find rows with missing required fields"""
        mask = self.df.isna().any(axis=1)
        return self.df[mask]
    
    def get_summary(self):
        """Get missing data summary"""
        summary = pd.DataFrame({
            'missing_count': self.df.isna().sum(),
            'missing_percentage': (self.df.isna().sum() / len(self.df) * 100).round(2)
        })
        return summary[summary['missing_count'] > 0].sort_values('missing_count', ascending=False)
    
    def flag_records(self):
        """Add flag column for rows with missing data"""
        flagged = self.df.copy()
        flagged['has_missing'] = self.df.isna().any(axis=1)
        logger.info(f"Flagged {flagged['has_missing'].sum()} records with missing values")
        return flagged
    
    # def remove_records(self):
    #     """Remove rows with missing required fields"""
    #     missing = self.find_missing()
    #     cleaned = self.df[~self.df.index.isin(missing.index)]
    #     logger.info(f"Removed {len(missing)} rows with missing values")
    #     return cleaned.reset_index(drop=True), missing
    
    def handle_missing_records(self, drop=False):
        """Handle missing records: fill with median/mode or drop"""
        if drop:
            missing = self.find_missing()
            cleaned = self.df[~self.df.index.isin(missing.index)]
            logger.info(f"Removed {len(missing)} rows with missing values")
            return cleaned.reset_index(drop=True), missing
        
        cleaned = self.df.copy()
        for col in cleaned.columns:
            if cleaned[col].isna().any():
                if pd.api.types.is_numeric_dtype(cleaned[col]):
                    fill_value = cleaned[col].median()
                    if pd.isna(fill_value):  # If all values are NaN, use 0
                        fill_value = 0
                else:
                    mode_vals = cleaned[col].mode()
                    fill_value = mode_vals[0] if len(mode_vals) > 0 else "Unknown"
                cleaned[col] = cleaned[col].fillna(fill_value)
        
        logger.info(f"Filled missing values")
        return cleaned
    

class URLValidator:
    def __init__(self, df, url_column='Website'):
        self.df = df.copy()
        self.url_column = url_column
        logger.info(f"URLValidator initialized for column: {url_column}")
        logger.info(f"Total records to validate: {len(self.df)}")
        
    def is_valid_url(self, url):
        """Check if URL is properly formatted"""
        if pd.isna(url) or not isinstance(url, str):
            return False
        
        # Basic pattern check
        url = url.strip()
        if not re.match(r'^https?://', url, re.IGNORECASE):
            url = 'http://' + url
        
        try:
            import validators
            return validators.url(url) is True
        except ImportError:
            # Fallback to regex if validators not installed
            pattern = re.compile(
                r'^https?://'
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
                r'localhost|'
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                r'(?::\d+)?'
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            return bool(pattern.match(url))
    
    def validate_urls(self):
        """Validate all URLs and return results"""
        results = self.df.copy()
        results['url_valid'] = results[self.url_column].apply(self.is_valid_url)
        results['url_missing'] = results[self.url_column].isna()

        valid_count = results['url_valid'].sum()
        missing_count = results['url_missing'].sum()
        invalid_count = (~results['url_valid'] & ~results['url_missing']).sum()

        logger.info(f"URL validation complete:")
        logger.info(f"  - Valid URLs: {valid_count}")
        logger.info(f"  - Missing URLs: {missing_count}")
        logger.info(f"  - Invalid URLs: {invalid_count}")
        return results
    
    def get_invalid_urls(self):
        """Get records with invalid URLs"""
        validated = self.validate_urls()
        return validated[~validated['url_valid'] & ~validated['url_missing']]
    
    def check_reachability(self, timeout=5, max_workers=10):
        """Check if URLs are reachable (optional)"""
        import requests
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def check_url(url):
            if pd.isna(url):
                return None
            try:
                url = url.strip()
                if not re.match(r'^https?://', url, re.IGNORECASE):
                    url = 'http://' + url
                response = requests.head(url, timeout=timeout, allow_redirects=True)
                return response.status_code < 400
            except: 
                return False
        
        urls = self.df[self.url_column].dropna().unique()
        reachability = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_url, url): url for url in urls}
            for future in as_completed(futures):
                url = futures[future]
                reachability[url] = future.result()
        
        results = self.df.copy()
        results['url_reachable'] = results[self.url_column].map(reachability)
        return results
    
    def clean_urls(self):
        """Remove records with invalid URLs"""
        validated = self.validate_urls()
        cleaned = validated[validated['url_valid'] | validated['url_missing']]
        invalid = validated[~validated['url_valid'] & ~validated['url_missing']]

        logger.info(f"Removed {len(invalid)} records with invalid URLs")
        logger.info(f"Retained {len(cleaned)} records with valid or missing URLs")

        return cleaned.drop(columns=['url_valid', 'url_missing']).reset_index(drop=True), invalid




class YearValidator:
    def __init__(self, df, year_column='Launch Year', min_year=2015, max_year=2026):
        self.df = df.copy()
        self.year_column = year_column
        self.min_year = min_year
        self.max_year = max_year or pd.Timestamp.now().year
        logger.info(f"YearValidator initialized")
        
    def is_valid_year(self, year):
        """Check if year is numeric and within range"""
        if pd.isna(year):
            return None  # Missing, not invalid
        try:
            year_int = int(float(year))
            return self.min_year <= year_int <= self.max_year
        except (ValueError, TypeError):
            return False
    
    def validate_years(self):
        """Validate all years and categorize issues"""
        results = self.df.copy()
        results['year_missing'] = results[self.year_column].isna()
        results['year_valid'] = results[self.year_column].apply(self.is_valid_year)
        
        # Categorize invalid reasons
        def categorize_invalid(row):
            if row['year_missing']:
                return 'missing'
            if row['year_valid']:
                return 'valid'
            try:
                year_int = int(float(row[self.year_column]))
                if year_int > self.max_year:
                    return 'future'
                if year_int < self.min_year:
                    return 'too_old'
            except:
                return 'non_numeric'
            return 'invalid'
        
        results['year_issue'] = results.apply(categorize_invalid, axis=1)
        logger.info(f"Year validation complete: {len(results)} records processed")
        return results
    
    def get_invalid_years(self):
        """Get records with invalid years"""
        validated = self.validate_years()
        return validated[validated['year_issue'].isin(['future', 'too_old', 'non_numeric'])]
    
    def get_summary(self):
        """Summary of year validation issues"""
        validated = self.validate_years()
        summary = validated['year_issue'].value_counts()
        logger.info(f"Year validation summary:\n{summary}")
        return summary
    
    def clean_years(self, strategy='remove'):
        """
        Clean invalid years
        strategy: 'remove' (delete rows) or 'nullify' (set to NaN)
        """
        validated = self.validate_years()
        
        if strategy == 'remove':
            cleaned = validated[validated['year_issue'].isin(['valid', 'missing'])]
            invalid = validated[~validated['year_issue'].isin(['valid', 'missing'])]
        elif strategy == 'nullify':
            cleaned = validated.copy()
            mask = ~cleaned['year_issue'].isin(['valid', 'missing'])
            cleaned.loc[mask, self.year_column] = np.nan
            invalid = validated[mask]
        else:
            raise ValueError("strategy must be 'remove' or 'nullify'")
        
        # Drop helper columns
        cols_to_drop = ['year_missing', 'year_valid', 'year_issue']
        cleaned = cleaned.drop(columns=cols_to_drop)
        logger.info(f"Cleaning complete: {len(cleaned)} records remaining")
        return cleaned.reset_index(drop=True), invalid
    
    def correct_years(self):
        """Attempt to correct obvious errors"""
        corrected = self.df.copy()
        corrections = []
        
        for idx, row in corrected.iterrows():
            year = row[self.year_column]
            if pd.isna(year):
                continue
                
            try:
                year_int = int(float(year))
                original = year_int
                
                # Common errors: 2-digit years
                if 0 <= year_int <= 99:
                    year_int = 2000 + year_int if year_int <= self.max_year % 100 else 1900 + year_int
                
                # Future years: might be typo (e.g., 2025 instead of 2015)
                if year_int > self.max_year:
                    continue  # Can't reliably correct
                
                if year_int != original and self.min_year <= year_int <= self.max_year:
                    corrected.at[idx, self.year_column] = year_int
                    corrections.append({
                        'index': idx,
                        'original': original,
                        'corrected': year_int,
                        'tool': row.get('Tool Name', 'Unknown')
                    })
            except:
                continue
        logger.info(f"Corrected {len(corrections)} year values")
        return corrected, pd.DataFrame(corrections)


class NumericValidator:
    def __init__(self, df, rating_col='average_rating', review_col='review_count', 
                 rating_min=0, rating_max=5):
        self.df = df.copy()
        self.rating_col = rating_col
        self.review_col = review_col
        self.rating_min = rating_min
        self.rating_max = rating_max
        
    def validate_ratings(self):
        """Check if ratings are within valid bounds"""
        ratings = self.df[self.rating_col].copy()
        mask = (ratings < self.rating_min) | (ratings > self.rating_max)
        return self.df[mask & ratings.notna()]
    
    def validate_reviews(self):
        """Check if review counts are non-negative integers"""
        reviews = self.df[self.review_col].copy()
        
        # Check for negative or non-integer values
        mask_negative = reviews < 0
        mask_non_integer = reviews != reviews.astype(int)
        mask = (mask_negative | mask_non_integer) & reviews.notna()
        
        return self.df[mask]
    
    def get_summary(self):
        """Get validation summary"""
        invalid_ratings = len(self.validate_ratings())
        invalid_reviews = len(self.validate_reviews())
        
        summary = {
            'invalid_ratings': invalid_ratings,
            'invalid_reviews': invalid_reviews,
            'total_rows': len(self.df)
        }
        
        logger.info(f"Invalid ratings: {invalid_ratings}")
        logger.info(f"Invalid review counts: {invalid_reviews}")
        
        return summary
    
    def flag_records(self):
        """Add flag columns for invalid values"""
        flagged = self.df.copy()
        
        ratings = flagged[self.rating_col]
        reviews = flagged[self.review_col]
        
        flagged['invalid_rating'] = ((ratings < self.rating_min) | (ratings > self.rating_max)) & ratings.notna()
        flagged['invalid_review'] = ((reviews < 0) | (reviews != reviews.astype(int))) & reviews.notna()
        
        return flagged
    
    def clean_records(self, strategy='remove'):
        """
        Clean invalid records
        strategy: 'remove' (delete rows) or 'nullify' (set to NaN)
        """
        invalid_ratings = self.validate_ratings()
        invalid_reviews = self.validate_reviews()
        invalid_indices = invalid_ratings.index.union(invalid_reviews.index)
        
        if strategy == 'remove':
            cleaned = self.df[~self.df.index.isin(invalid_indices)]
            invalid = self.df[self.df.index.isin(invalid_indices)]
        elif strategy == 'nullify':
            cleaned = self.df.copy()
            
            ratings = cleaned[self.rating_col]
            mask_rating = ((ratings < self.rating_min) | (ratings > self.rating_max)) & ratings.notna()
            cleaned.loc[mask_rating, self.rating_col] = np.nan
            
            reviews = cleaned[self.review_col]
            mask_review = ((reviews < 0) | (reviews != reviews.astype(int))) & reviews.notna()
            cleaned.loc[mask_review, self.review_col] = np.nan
            
            invalid = self.df[self.df.index.isin(invalid_indices)]
        else:
            raise ValueError("strategy must be 'remove' or 'nullify'")
        
        logger.info(f"Cleaned {len(invalid)} records with invalid numeric values")
        return cleaned.reset_index(drop=True), invalid


class TextStandardizer:
    def __init__(self, df, text_columns=None):
        self.df = df.copy()
        self.text_columns = text_columns or self.df.select_dtypes(include=['object']).columns.tolist()
        
    def clean_text(self, text):
        """Standardize single text value"""
        if pd.isna(text) or not isinstance(text, str):
            return text
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Normalize unicode characters
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        return text
    
    
    def standardize_all(self, case_rules=None):
        """
        Standardize all text columns
        case_rules: dict mapping column names to case types
        """
        standardized = self.df.copy()
        
        # Default case rules
        if case_rules is None:
            case_rules = {
                'Tool Name': 'title',
                'Category': 'title',
                'Company': 'title',
                'Primary Function': 'sentence',
                'Description': 'sentence',
                'Pricing Model': 'title',
                'Target Users': 'title'
            }
        
        # Clean whitespace and encoding for all text columns
        for col in self.text_columns:
            if col in standardized.columns:
                standardized[col] = standardized[col].apply(self.clean_text)
        
        # Apply case rules
        for col, case_type in case_rules.items():
            if col in standardized.columns:
                if case_type == 'title':
                    standardized[col] = standardized[col].str.title()
                elif case_type == 'lower':
                    standardized[col] = standardized[col].str.lower()
                elif case_type == 'upper':
                    standardized[col] = standardized[col].str.upper()
                elif case_type == 'sentence':
                    standardized[col] = standardized[col].apply(
                        lambda x: x.capitalize() if isinstance(x, str) else x
                    )
        
        logger.info(f"Standardized {len(self.text_columns)} text columns")
        return standardized
    
    def get_changes_summary(self, standardized_df):
        """Compare original vs standardized data"""
        changes = []
        
        for col in self.text_columns:
            if col in self.df.columns:
                mask = self.df[col] != standardized_df[col]
                changed_count = mask.sum()
                if changed_count > 0:
                    changes.append({
                        'column': col,
                        'changes': changed_count,
                    })
        
        return pd.DataFrame(changes)


class DescriptionValidator:
    def __init__(self, df, description_col='Description', min_length=10, min_words=3):
        self.df = df.copy()
        self.description_col = description_col
        self.min_length = min_length
        self.min_words = min_words
        self.meaningless = ['n/a', 'na', 'none', 'null', 'tbd', 'tba', 'coming soon',
                           'no description', 'not available', 'see website', 'lorem ipsum']
        
    def get_flag_reason(self, text):
        """Check description and return reason if invalid"""
        if pd.isna(text):
            return 'missing'
        
        text_str = str(text).strip()
        text_lower = text_str.lower()
        reasons = []
        
        if len(text_str) < self.min_length:
            reasons.append('too_short')
        if len(text_str.split()) < self.min_words:
            reasons.append('few_words')
        if any(pattern in text_lower for pattern in self.meaningless):
            reasons.append('meaningless')
        
        return ', '.join(reasons) if reasons else None
    
    def flag_descriptions(self):
        """Add flag column for invalid descriptions"""
        flagged = self.df.copy()
        flagged['desc_flag'] = flagged[self.description_col].apply(self.get_flag_reason)
        
        invalid_count = flagged['desc_flag'].notna().sum()
        logger.info(f"Flagged {invalid_count} invalid descriptions")
        
        return flagged
    
    def get_summary(self):
        """Get summary of flagged descriptions"""
        flagged = self.flag_descriptions()
        total_flagged = flagged['desc_flag'].notna().sum()
        
        reasons = flagged['desc_flag'].dropna().str.split(', ').explode().value_counts()
        
        logger.info(f"Total flagged: {total_flagged}")
        logger.info(f"\n{reasons}")
        
        return reasons




def save_cleaned_data(data: pd.DataFrame, filename: str, index: bool = False):
    try: 
        data.to_csv(filename, index = False)
        logger.info(
            "Cleaned data saved successfully")
    except IOError as e:
        logger.error(
            f"Failed to save cleaned data to {filename}",
            exc_info=True
        )

