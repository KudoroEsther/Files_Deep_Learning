"""
Example Usage of Data Cleaning Pipeline
Demonstrates different cleaning scenarios
"""

from data_cleaning_pipeline import DataCleaningPipeline

# ============================================
# SCENARIO 1: Basic Cleaning
# ============================================
def basic_cleaning_example():
    """
    Basic cleaning: remove duplicates, handle missing values, 
    standardize text, and save.
    """
    print("=== SCENARIO 1: Basic Cleaning ===\n")
    
    pipeline = DataCleaningPipeline('your_data.csv')
    pipeline.load_data()
    pipeline.display_info()
    
    # Remove duplicates
    pipeline.remove_duplicates()
    
    # Handle missing values automatically
    pipeline.handle_missing_values(strategy='auto')
    
    # Standardize text columns
    pipeline.standardize_text(lowercase=True, strip=True)
    
    # Save cleaned data
    pipeline.save_cleaned_data('cleaned_basic.csv')
    pipeline.generate_report()


# ============================================
# SCENARIO 2: Advanced Cleaning with Outliers
# ============================================
def advanced_cleaning_example():
    """
    Advanced cleaning including outlier removal and type conversion.
    """
    print("\n=== SCENARIO 2: Advanced Cleaning ===\n")
    
    pipeline = DataCleaningPipeline('your_data.csv')
    pipeline.load_data()
    
    # Remove duplicates based on specific columns
    pipeline.remove_duplicates(subset=['id', 'email'])
    
    # Handle missing values with different strategies
    pipeline.handle_missing_values(
        strategy='fill',
        fill_value=0,
        columns=['age', 'salary']
    )
    
    # Remove outliers from numeric columns
    pipeline.remove_outliers(
        columns=['price', 'quantity'],
        method='iqr',
        threshold=1.5
    )
    
    # Convert data types
    pipeline.convert_data_types({
        'order_date': 'datetime',
        'price': 'float',
        'quantity': 'int'
    })
    
    # Rename columns
    pipeline.rename_columns(snake_case=True)
    
    # Reset index
    pipeline.reset_index()
    
    # Save
    pipeline.save_cleaned_data('cleaned_advanced.csv')
    pipeline.generate_report()


# ============================================
# SCENARIO 3: Custom Column-Specific Cleaning
# ============================================
def custom_cleaning_example():
    """
    Custom cleaning with specific column operations.
    """
    print("\n=== SCENARIO 3: Custom Cleaning ===\n")
    
    pipeline = DataCleaningPipeline('your_data.csv')
    pipeline.load_data()
    
    # Remove duplicates
    pipeline.remove_duplicates(keep='last')
    
    # Drop rows with missing values in critical columns
    pipeline.handle_missing_values(
        strategy='drop',
        columns=['customer_id', 'order_id']
    )
    
    # Fill missing values in other columns
    pipeline.handle_missing_values(
        strategy='auto',
        columns=['city', 'state', 'country']
    )
    
    # Standardize specific text columns
    pipeline.standardize_text(
        columns=['email', 'username'],
        lowercase=True,
        strip=True,
        remove_special=False
    )
    
    # Remove unwanted columns
    pipeline.remove_columns(['temp_column', 'debug_info'])
    
    # Save
    pipeline.save_cleaned_data('cleaned_custom.csv')
    pipeline.generate_report()


# ============================================
# SCENARIO 4: Minimal Cleaning (Just Remove Duplicates)
# ============================================
def minimal_cleaning_example():
    """
    Minimal cleaning - just remove duplicates.
    """
    print("\n=== SCENARIO 4: Minimal Cleaning ===\n")
    
    pipeline = DataCleaningPipeline('your_data.csv')
    pipeline.load_data()
    pipeline.remove_duplicates()
    pipeline.save_cleaned_data('cleaned_minimal.csv')
    pipeline.generate_report()


# ============================================
# Run Examples
# ============================================
if __name__ == "__main__":
    print("Choose a scenario to run:")
    print("1. Basic Cleaning")
    print("2. Advanced Cleaning with Outliers")
    print("3. Custom Column-Specific Cleaning")
    print("4. Minimal Cleaning")
    
    # Uncomment the scenario you want to run:
    # basic_cleaning_example()
    # advanced_cleaning_example()
    # custom_cleaning_example()
    # minimal_cleaning_example()
    
    print("\nUncomment the scenario you want to run in the script!")
