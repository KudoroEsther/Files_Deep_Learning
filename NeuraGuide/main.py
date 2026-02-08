from data_validation_pipeline import(
    load_data
)

path = r"C:\Users\owner\Desktop\Files_Deep_Learning\NeuraGuide\AI_Tools.csv"
df = load_data(path)
df = df.copy()

