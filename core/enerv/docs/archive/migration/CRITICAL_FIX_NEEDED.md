# CRITICAL FIX NEEDED: Index Corruption
## IndexAggregator.rebuild() Generates Invalid Entries

**Priority:** P0 (BLOCKING)  
**Severity:** HIGH - System unusable until fixed  
**Impact:** Newly migrated folders don't appear in index

---

## The Problem

When `facet index --force` is run, the `index.jsonl` file contains corrupted entries:

```json
{"File-Date": "2024-05-16"}
{"File-Date": "2024-05-16"}
{"File-Date": "2024-05-16"}
```

These entries:
- Should NOT exist in the index
- Block valid entries from being found
- Break the entire indexing system

---

## How to Reproduce

```bash
# Create a folder with metadata
facet migrate-folder "C:\telo\new-folder" --title "New Folder"

# Try to index it
facet index --force

# Check if it worked
facet current-info "C:\telo\new-folder"
# Result: indexed: false (SHOULD BE: indexed: true)
```

---

## Root Cause (Hypothesis)

The `IndexAggregator.rebuild()` method in `core/index.py` is writing entries to `index.jsonl` that shouldn't be there.

**Likely culprits:**
1. The aggregator is reading non-facet files and trying to index them
2. A fallback or default value (`{"File-Date": "..."}`) is being written
3. The JSONL writing logic has a bug that creates extra entries
4. The timestamp being used is `2024-05-16` which is stale

---

## Files to Check

1. **`tools/core/index.py`** — Main aggregation logic
   - Look for `rebuild()` method
   - Check what writes to `index.jsonl`
   - Look for any hardcoded fallbacks or defaults

2. **`tools/core/meta.py`** — Meta file handling
   - Check if it generates any default entries
   - Look for timestamp handling

3. **`tools/core/journal.py`** — Operations logging
   - Check if journal entries are bleeding into index

---

## What to Look For

```python
# BAD: Appending File-Date entries
with open(index_file, 'a') as f:
    f.write('{"File-Date": "2024-05-16"}\n')  # ❌ Don't do this

# GOOD: Only append valid facet entries
for meta_entry in all_meta_files:
    f.write(json.dumps(meta_entry) + '\n')  # ✅ Correct
```

---

## Testing the Fix

After fixing `IndexAggregator.rebuild()`:

```bash
# 1. Delete the corrupted index
rm "C:\telo\.facets\index.jsonl"

# 2. Rebuild it
facet index --force

# 3. Verify it's clean (should have ~13 valid entries, no File-Date entries)
grep -c "File-Date" "C:\telo\.facets\index.jsonl"
# Expected: 0 matches

# 4. Verify migration works
facet migrate-folder "C:\telo\card-benefits-hub" --title "Card Benefits Hub"
facet current-info "C:\telo\card-benefits-hub"
# Expected: indexed: true (not false)
```

---

## Quick Fix Strategy

1. **Isolate the bug** by tracing through `IndexAggregator.rebuild()`
2. **Add logging** to see what entries are being written
3. **Validate entries** before writing to index.jsonl:
   ```python
   # Check each entry has required fields
   required_fields = {'path', 'identifier', 'title', 'type'}
   for entry in entries:
       assert all(field in entry for field in required_fields)
   ```
4. **Rebuild index** after fix and test migration again

---

## Estimated Effort

- **Debugging:** 1-2 hours (to find where `File-Date` is coming from)
- **Fix:** 30 min - 1 hour (once root cause identified)
- **Testing:** 30 min

**Total: 2-3.5 hours**

---

## Why This Matters

This is the **only thing blocking successful deployment** of the improvements. Once fixed:
- ✅ Users can migrate folders with `facet migrate-folder`
- ✅ Root auto-detection works
- ✅ All commands work without `--root`
- ✅ System is production-ready

**Do not deploy until this is fixed.**
