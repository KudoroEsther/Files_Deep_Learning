from data_validation_pipeline import(
    load_data,
    DuplicateHandler,
    MissingDataHandler,
    URLValidator,
    save_cleaned_data
)

# Loading data
# path = r"C:\Users\owner\Desktop\Files_Deep_Learning\NeuraGuide\AI_Tools.csv"
# path = r"C:\Users\ncc333\Desktop\Deep_Learning\NeuraGuide\AI_Tools.csv"

path = r"C:\Users\ncc333\Desktop\Deep_Learning\Cleaned_AI_Tools.csv"
df = load_data(path)
df = df.copy()

# Identifying and removing duplicate tools
handler = DuplicateHandler(df)
cleaned_df, removed_records = handler.remove_duplicates()

missing_handler = MissingDataHandler(cleaned_df)
print(missing_handler.get_missing_summary())
cleaned_df, removed_records = missing_handler.remove_incomplete()

validator = URLValidator(df)
print(f"Invalid URLs: {len(validator.get_invalid_urls())}")
cleaned_df, invalid_urls = validator.clean_urls()

# Optional: Check reachability (slower), had to stop it because it took over 11mins and it wasn't done
# reachable_df = validator.check_reachability()
# print(reachable_df)

# saved_to_csv = save_cleaned_data(data=cleaned_df, filename="Cleaned_AI_Tools.csv")