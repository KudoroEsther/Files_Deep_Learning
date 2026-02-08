import csv
import os
import pandas as pd
import numpy as np
import pydantic

import re
from urllib.parse import urlparse



def load_data(path:str):
    """Loads the dataset"""
    data = pd.read_csv(path)
    return data

def save_cleaned_data(df: pd.DataFrame, filename: str, index: bool = False):
    try: 
        df.to_csv(filename, index = False)
    except IOError as e:
        print(f"Error saving file: {e}")
    

class DuplicateHandler:
    """Identifies and removes duplicate tools. Detects duplicate entries using specific columns. Decides which record to keep and remove the rest using deterministic logic."""
    def __init__(self, df):
        self.df = df
        self.duplicate_keys = ['Tool Name', 'Company', 'Website']
        
    def find_duplicates(self):
        """Identify duplicate groups"""
        return self.df[self.df.duplicated(subset=self.duplicate_keys, keep=False)]
    
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
            print("There are no duplicates")
            return self.df, pd.DataFrame()
        
        keep_indices = dupes.groupby(self.duplicate_keys, dropna=False).apply(self.rank_records)
        removed = self.df[self.df.index.isin(dupes.index) & ~self.df.index.isin(keep_indices)]
        cleaned = self.df[~self.df.index.isin(dupes.index) | self.df.index.isin(keep_indices)]
        
        return cleaned.reset_index(drop=True), removed

class MissingDataHandler:
    """
    Detects missing critical fields and removes records based on defined rules.
    """
    def __init__(self, df, essential_fields=None, flag_fields=None):
        self.df = df.copy()
        self.essential_fields = essential_fields or ['Tool Name', 'Category', 'Website']
        self.flag_fields = flag_fields or ['Description', 'Primary Function', 'Company']
        
    def find_missing_essential(self):
        """Find rows with missing essential fields"""
        mask = self.df[self.essential_fields].isna().any(axis=1)
        return self.df[mask]
    
    def find_missing_flagged(self):
        """Find rows with missing flagged fields (warning only)"""
        mask = self.df[self.flag_fields].isna().any(axis=1)
        return self.df[mask]
    
    def get_missing_summary(self):
        """Summary of missing data by column"""
        summary = pd.DataFrame({
            'missing_count': self.df.isna().sum(),
            'missing_pct': (self.df.isna().sum() / len(self.df) * 100).round(2)
        })
        return summary[summary['missing_count'] > 0].sort_values('missing_count', ascending=False)
    
    def remove_incomplete(self):
        """Remove rows missing essential fields"""
        incomplete = self.find_missing_essential()
        cleaned = self.df[~self.df.index.isin(incomplete.index)]
        return cleaned.reset_index(drop=True), incomplete
    
    def flag_incomplete(self):
        """Add flag column for incomplete records"""
        df_flagged = self.df.copy()
        df_flagged['missing_essential'] = self.df[self.essential_fields].isna().any(axis=1)
        df_flagged['missing_flagged'] = self.df[self.flag_fields].isna().any(axis=1)
        return df_flagged
    

class URLValidator:
    def __init__(self, df, url_column='Website'):
        self.df = df.copy()
        self.url_column = url_column
        
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
        return cleaned.drop(columns=['url_valid', 'url_missing']).reset_index(drop=True), invalid


