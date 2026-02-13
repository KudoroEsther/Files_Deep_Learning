# Data Validation Report
**AI Tools Dataset - Quality Check**

**By:** AI Engineering Intern  
**Date:** February 13, 2026  
**Dataset:** AI_Tools.csv (54,910 records)

---

## What I Did

I ran a complete data validation pipeline on our AI tools dataset. Here's what I found and fixed:

**Quick Stats:**
- Started with: 54,910 records
- Final clean records: 54,821
- Records removed: 89 (88 old years + 1 bad URL)
- Text columns cleaned: 9
- **Big issue found:** 19.1% of descriptions are just "See website" 😬

**The Pipeline:**
1. Check for duplicates
2. Handle missing required fields
3. Validate URLs
4. Fix launch years (2015-2026)
5. Validate ratings/reviews
6. Standardize text formatting
7. Flag bad descriptions

---

## 1. Duplicate Detection

**Good news:** No duplicates found! 🎉

I checked for duplicates using Tool Name + Company + Website, and the dataset is already clean on this front.

**Result:** All 54,910 records are unique.

---

## 2. Missing Data Check

**What I checked:**
Three fields MUST be filled in:
- Tool Name (can't have a tool without a name!)
- Category (need this for organizing)
- Website (users need to access the tool)

**What I found:**
1,420 records had missing values in some fields.

**What I did:**
Instead of deleting them, I **flagged** them with a `has_missing` column. This way we can decide later what to do with them, but they're still in the dataset.

**Why flag instead of delete?**
Some of these records might just be missing optional fields (like Company or Launch Year). Better to keep them and let users filter as needed.

---

## 3. URL Validation

**What I checked:**
Made sure all Website URLs actually look like URLs.

**Results:**
- Valid URLs: 54,909 ✓
- Invalid URLs: 1 (removed)

**Validation rules:**
- Must start with `http://` or `https://` (I auto-added it if missing)
- Has to be a real domain format
- No placeholder text like "N/A" or "coming soon"

**What I did:**
Removed that 1 record with a malformed URL. The dataset is super clean on this front!

---

## 4. Launch Year Check

**Valid range:** 2015 - 2026

**Why these limits?**
- We're focusing on modern AI tools (2015+)
- Can't launch in the future (it's 2026 now)

**What I found:**
- Valid years: 54,821 ✓
- Too old (before 2015): 88 (removed)

**My approach:**
Used `remove` strategy - deleted records with years before 2015 since we want a modern tools dataset.

**Note:** I initially had missing Launch Year values, but that was because my min_year was set too high (2020). After fixing it to 2015, most records became valid. Then I converted the Launch Year column to Int64 type for better data handling.

---

## 5. Ratings & Reviews Check

**What I validated:**

1. **average_rating** - Should be 0 to 5
2. **review_count** - Should be non-negative whole numbers

**Results:**
- Invalid ratings: 0 
- Invalid review counts: 0 

**Great news!** All numeric data is already clean. No out-of-range ratings, no negative review counts, no weird decimal issues.

The dataset has solid data quality on the numeric fields!

---

## 6. Text Cleanup

**What I fixed:**
- Extra spaces between words
- Leading/trailing whitespace
- Weird encoding issues
- Inconsistent casing

**Processed:** 9 text columns across all 54,909 records

**Casing rules I applied:**

| Column | Case |
|--------|------|
| Tool Name, Category, Company | Title Case |
| Description, Primary Function | Sentence case |

**Examples:**
- `"  kaedim  "` → `"Kaedim"`
- `"GET3D   by NVIDIA"` → `"Get3D By Nvidia"`

**Why this matters:**
Makes the data look professional and consistent. Also helps with search/matching later.

**Result:** Everything's nice and uniform now. No more weird spacing or encoding issues!

---

## 7. Description Quality Issue

**Okay, so here's the main problem I found...**

I checked if descriptions were actually useful or just placeholder text.

**My criteria:**
- At least 10 characters long
- At least 3 words
- Not just "See website" or "N/A" or other meaningless stuff

**What I found:**

**10,466 out of 54,821 records (19.1%) are flagged!**

**Breakdown:**
- 10,465 have "See website" or similar placeholders
- 1 has too few words

**This is a quality issue.** Almost 1 in 5 records doesn't have a real description - they just say "See website."

**What I did:**
I added a `desc_flag` column to mark these records, but **I didn't delete them**. 

**Why not delete?**
- These records still have valid Tool Names, Categories, Websites, etc.
- Deleting 19% of the dataset seemed too aggressive
- Better to flag them so we know what needs work

**The flag values:**
- `NULL` = Good description
- `"meaningless"` = Has placeholder text  
- `"few_words"` = Less than 3 words
- `"too_short"` = Less than 10 chars

**My recommendation:**
We should prioritize getting real descriptions for the flagged records. Maybe scrape them from the websites or contact tool creators?

---

## Summary

**What got done:**
No duplicates found - dataset is clean!  
1,420 records flagged for missing values (not removed)  
1 invalid URL removed  
88 records with old launch years (<2015) removed  
All ratings and review counts are valid  
9 text columns standardized  
Launch Year converted to Int64 type
10,466 descriptions flagged (19.1% - but not removed)

**Final numbers:**
- Started: 54,910 records
- Removed: 89 records (88 old years + 1 bad URL)
- Final clean dataset: 54,821 records
- Retention rate: 99.8%

**The dataset is now clean and ready to use!**

**Main takeaway:**
The description quality issue affects 19.1% of records. I flagged these but kept them in the dataset since they have other useful info.

**Next steps I'd recommend:**

1. **Short-term:** Use `desc_flag IS NULL` to filter for high-quality descriptions when needed
2. **Medium-term:** Scrape descriptions from the actual websites for flagged records
3. **Long-term:** Set up validation rules for new data so this doesn't happen again

**How to use this cleaned data:**
```python
# Get only high-quality descriptions
good_descriptions = df[df['desc_flag'].isna()]

# Get all valid tools (regardless of description quality)
all_valid = df  # Everything is clean now (54,821 records)

# Find tools that need description work
needs_work = df[df['desc_flag'].notna()]  # 10,466 records
```

**Data saved as:** `Cleaned_AI_Tools_final.csv`


---

**Validation classes used:**
1. `DuplicateHandler` - No duplicates found
2. `MissingDataHandler` - Flagged 1,420 records
3. `URLValidator` - Removed 1 invalid URL
4. `YearValidator` - Removed 88 old records (min_year=2015)
5. `NumericValidator` - All clean, no issues
6. `TextStandardizer` - Cleaned 9 columns
7. `DescriptionValidator` - Flagged 10,466 records
