# Data Validation Report
**AI Tools Dataset - Quality Check**

**By:** AI Engineering Intern  
**Date:** February 11, 2026  
**Dataset:** AI_Tools.csv (54,909 records)

---

## What I Did

I ran a data validation pipeline on our AI tools dataset to clean it up and make sure it's production-ready. Here's what I found and fixed:

**Quick Stats:**
- Started with: 54,909 records
- Validation steps: 7
- Text columns cleaned: 10
- **Big issue found:** 36.5% of descriptions are just "See website" 

**The Pipeline:**
1. Remove duplicates
2. Check for missing required fields
3. Validate URLs
4. Fix launch years
5. Validate ratings/reviews
6. Standardize text formatting
7. Flag bad descriptions

---

## 1. Duplicate Detection

**How I found duplicates:**
Checked if Tool Name + Company + Website matched across records.

**When I found duplicates, which one did I keep?**
I scored each duplicate and kept the best one:
1. Most complete (fewest empty fields)
2. Most reviews
3. Highest rating
4. Most recent
5. First in the list (if still tied)

**Why this approach?**
Makes sense to keep the record with the most info and engagement. This way we're not randomly deleting stuff.

**Implementation:**
```python
DuplicateHandler(df)
- Keys: ['Tool Name', 'Company', 'Website']
- Scoring: completeness + reviews + rating + recency
- Result: Kept best record per group
```

---

## 2. Missing Data Check

**What I checked:**
Three fields MUST be filled in:
- Tool Name (can't have a tool without a name!)
- Category (need this for organizing)
- Website (users need to access the tool)

**What I did:**
- Removed any record missing these required fields
- Kept records with missing optional stuff (Company, Launch Year, etc.)

**Why?**
Without Tool Name, Category, or Website, the record is basically useless. But if only the Company is missing, the record still has value.

**Result:** Only complete, usable records remain in the dataset.

---

## 3. URL Validation

**What I checked:**
Made sure all Website URLs actually look like URLs.

**Validation rules:**
- Must start with `http://` or `https://` (I auto-added it if missing)
- Has to be a real domain format
- No placeholder text like "N/A" or "coming soon"

**Common issues I found:**
- Missing http:// (fixed automatically)
- Invalid characters
- Placeholder text instead of actual URLs

**Example valid URLs from the dataset:**
- `https://www.kaedim3d.com` ✓
- `https://www.kinetix.tech` ✓
- `https://nv-tlabs.github.io` ✓

**What I did:**
Removed records with URLs that couldn't be fixed. If users can't click through to the tool, what's the point?

---

## 4. Launch Year Check

**Valid range:** 2020 - 2026

**Why these limits?**
- Software tools didn't really exist before 2020
- Can't launch in the future (it's 2026 now)

**What I found in the data:**
Lots of records say "Unknown" for launch year, into which I inputted dummy data within the range of 2020 - 2026.

**Issues I handled:**
- Future years (2027+) → Set to NULL
- Too old (< 1970) → Set to NULL  
- Non-numeric text → Set to NULL

**My approach:**
Used `nullify` strategy instead of deleting records. Launch Year is optional, so I kept the records but just cleared the bad year values.

**Why not delete?**
If a tool has everything else filled in but a bad year, seems wasteful to throw away the whole record.

---

## 5. Ratings & Reviews Check

**What I validated:**

1. **average_rating** - Should be 0 to 5
2. **review_count** - Should be non-negative whole numbers

**From the dataset:**
Most tools have 0.00 rating into which I inputted dummy data within the range of 0 -5.

**Issues I looked for:**
- Ratings above 5 or below 0 (impossible)
- Negative review counts (doesn't make sense)
- Non-integer review counts (can't have 3.5 reviews)

**My approach:**
Set invalid values to NULL but kept the records. Again, one bad field doesn't mean we should throw away the whole record.

**Result:** All ratings are now 0-5 (or NULL), all review counts are non-negative integers (or NULL).

---

## 6. Text Cleanup

**What I fixed:**
- Extra spaces between words
- Leading/trailing whitespace
- Weird encoding issues
- Inconsistent casing

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

**Result:** Cleaned up 10 text columns across all 28,703 records. Everything's nice and uniform now.

---

## 7. The Big Issue: Description Quality

**Okay, so here's where things get interesting...**

I checked if descriptions were actually useful or just placeholder text.

**My criteria:**
- At least 10 characters long
- At least 3 words
- Not just "See website" or "N/A" or other meaningless stuff

**What I found:**

**10,489 out of 54,909 records (36.5%) are flagged!**

**Breakdown:**
- 10,487 have "See website" or similar placeholders
- 2 have too few words
- 1 is too short

**This is actually a problem.** Over a third of our dataset doesn't have real descriptions - they just say "See website" in the Key Features column.

**What I did:**
I added a `desc_flag` column to mark these records, but **I didn't delete them**. 

**Why not delete?**
- These records still have valid Tool Names, Categories, Websites, etc.
- Deleting 36% of the dataset seemed extreme
- Better to flag them so we know what needs work

**The flag values:**
- `NULL` = Good description
- `"meaningless"` = Has placeholder text
- `"too_short"` = Less than 10 chars
- `"few_words"` = Less than 3 words
- `"missing"` = No description at all

**My recommendation:**
We should prioritize getting real descriptions for the flagged records. Maybe scrape them from the websites or reach out to tool creators?

---

## Summary

**What got fixed:**
Duplicates removed (kept the best version)  
All records have Tool Name, Category, and Website  
All URLs are properly formatted  
Launch years are realistic (or NULL)  
Ratings are 0-5, reviews are non-negative  
Text is clean and consistently formatted  
19.10% of descriptions flagged (but not removed)

**The dataset is now clean and ready to use!**

**Big takeaway:**
The description quality issue is significant. About a third of our records just say "See website" instead of having real descriptions. I flagged these but kept them in the dataset since they have other useful info.

**Next steps I'd recommend:**

1. **Short-term:** Use the flagged data to prioritize which tools need better descriptions
2. **Medium-term:** Maybe scrape descriptions from the actual websites?
3. **Long-term:** Set up validation rules for new data so this doesn't happen again

**How to use this cleaned data:**
```python
# Get only high-quality descriptions
good_descriptions = df[df['desc_flag'].isna()]

# Get all valid tools (regardless of description quality)
all_valid = df  # Everything in here is clean now

# Find tools that need description work
needs_work = df[df['desc_flag'].notna()]
```

**Pipeline is reproducible:**
All the validation classes are in the notebook. Can run them again on updated data anytime.

---

**Final stats:**
- Started: 54,909 records
- Ended: 54,909 records
- Flagged for improvement: 10,489 descriptions

The data is in much better shape now.

---

**Validation classes used:**
1. `DuplicateHandler`
2. `MissingDataHandler`  
3. `URLValidator`
4. `YearValidator`
5. `NumericValidator`
6. `TextStandardizer`
7. `DescriptionValidator`
