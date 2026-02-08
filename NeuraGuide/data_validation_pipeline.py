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

class DuplicateHandler:
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
