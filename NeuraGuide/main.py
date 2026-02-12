import numpy as np
import pandas as pd

from data_validation_pipeline import(
    load_data,
    DuplicateHandler,
    MissingDataHandler,
    URLValidator,
    YearValidator,
    NumericValidator,
    TextStandardizer,
    DescriptionValidator,
    save_cleaned_data
)

# Loading data
# path = r"C:\Users\owner\Desktop\Files_Deep_Learning\NeuraGuide\AI_Tools.csv"
# path = r"C:\Users\ncc333\Desktop\Deep_Learning\NeuraGuide\AI_Tools.csv"

# path = r"C:\Users\ncc333\Desktop\Deep_Learning\Cleaned_AI_Tools.csv"

path = r"C:\Users\owner\Desktop\Files_Deep_Learning\Cleaned_AI_Tools5.csv"
df = load_data(path)
df = df.copy()

mask = df["Launch Year"] == "Unknown"
df.loc[mask, "Launch Year"] = np.random.randint(2020, 2025, size=mask.sum())

df["average_rating"] = np.where(df["average_rating"] == 0.0, 
                             np.round(1 + 4 * np.random.beta(a=5, b=1.5, size=len(df)), 2), 
                             df["average_rating"]) 

mask = df["Company"] == "Unknown"
df.loc[mask, "Company"] = df.loc[mask, "Tool Name"]

# Identifying and removing duplicate tools
handler = DuplicateHandler(df)
cleaned_df, removed_records = handler.remove_duplicates()

missing_handler = MissingDataHandler(cleaned_df)
print(missing_handler.get_summary())
flagged_df = missing_handler.flag_records()
# # or
cleaned_df= missing_handler.handle_missing_records()



validator = URLValidator(df)
print(f"Invalid URLs: {len(validator.get_invalid_urls())}")
cleaned_df, invalid_urls = validator.clean_urls()

# Optional: Check reachability (slower), had to stop it because it took over 11mins and it wasn't done
# reachable_df = validator.check_reachability()
# print(reachable_df)

validator = YearValidator(cleaned_df)
summary = validator.get_summary()
cleaned_df, invalid_records = validator.clean_years(strategy='nullify')
# 
# # Or attempt corrections first
# corrected_df, corrections_log = validator.correct_years()

validator = NumericValidator(cleaned_df, rating_min=0, rating_max=5)
print(validator.get_summary())
flagged_df = validator.flag_records()
# # or
cleaned_df, invalid = validator.clean_records(strategy='nullify')

# 
standardizer = TextStandardizer(cleaned_df)
cleaned_df = standardizer.standardize_all()
# See what changed
changes = standardizer.get_changes_summary(cleaned_df)


validator = DescriptionValidator(cleaned_df, min_length=10, min_words=3)
summary = validator.get_summary()
flagged_df = validator.flag_descriptions()

save_cleaned_data(cleaned_df, filename="Cleaned_AI_Tools5.csv")