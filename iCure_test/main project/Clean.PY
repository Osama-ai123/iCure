import pandas as pd

df = pd.read_excel(r"C:\Users\osama\OneDrive\Desktop\grad proj\dataset\AHD Arabic Healthcare Dataset\AHD Arabic Healthcare Dataset\AHD_english.xlsx")

'''print("Columns:", df.columns.tolist())
print("Total size:", df.shape)
print("\nData sample:")
print(df.head(3))
print("\nNull values:")
print(df.isnull().sum())
print("\nTop 10 categories:")
print(df['Category'].value_counts().head(10))
print("\nBottom 10 categories:")
print(df['Category'].value_counts().tail(10))'''

'''
print("All categories with counts:")
print(df['Category'].value_counts().to_string())

category_mapping = {
    'Skin diseases': 'skin diseases',
    'Dental health': 'Dentistry',
    'Psychological illnesses': 'Psychiatric illness',
    'Mental health': 'Psychiatric illness',
    'Children\'s diseases': 'Pediatric',
}
df['Category'] = df['Category'].replace(category_mapping)

non_medical = ['Medical News', 'organic chemistry', 'Ecology']
df = df[~df['Category'].isin(non_medical)]

category_counts = df['Category'].value_counts()
valid_categories = category_counts[category_counts >= 150].index
df = df[df['Category'].isin(valid_categories)]

print(df['Category'].value_counts().to_string())'''




# Step 1: Drop nulls
df = df.dropna()

# Step 2: Merge categories
category_mapping = {
    'Skin diseases': 'skin diseases',
    'General medicine': 'General Medicine',
    'Nose, Ear and Throat': 'Nose, ear and throat',
    'Medical News': None,
    'organic chemistry': None,
    'Ecology': None,
    'feed': 'Nutrition',
    'Esoteric diseases': 'Internal Medicine',
    'Herbalists': 'Alternative medicine',
    'Oral diseases': 'Dental',
    'Teeth health': 'Dental',
    'dentist': 'Dental',
    'Dental diseases': 'Dental',
    'Jaw and dental surgery': 'Dental',
    'Psychological health': 'Psychiatry',
    'Psychiatric illness': 'Psychiatry',
    'psychology': 'Psychiatry',
    'Mental health': 'Psychiatry',
    'Psychological illnesses': 'Psychiatry',
    'Sexual diseases': 'Sexual health',
    'Child health': 'Pediatric',
    "Children's diseases": 'Pediatric',
}

df['Category'] = df['Category'].map(lambda x: category_mapping.get(x, x))
df = df[df['Category'].notna()]

# Step 3: Remove categories under 150
category_counts = df['Category'].value_counts()
valid_categories = category_counts[category_counts >= 150].index
df = df[df['Category'].isin(valid_categories)]

# Step 4: Remove short text
df = df[df['Question'].str.split().str.len() >= 5]
df = df[df['Answer'].str.split().str.len() >= 10]

# Step 5: Reset index
df = df.reset_index(drop=True)

# Results
print("Final size:", df.shape)
print("Categories count:", df['Category'].nunique())
print("\nFinal categories:")
print(df['Category'].value_counts().to_string())

# Save
df.to_csv("C:/Users/osama/OneDrive/Desktop/flask/iCure_test/STEP1/cleaned_dataset.csv", index=False)
print("\nDone — saved to clean_data.csv")