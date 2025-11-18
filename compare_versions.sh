#!/bin/bash

# Compare Versions Script
# Shows what changed in the merged version

echo "🔍 Merged Version Analysis"
echo "======================================"
echo ""

# Files that were modified
FILES=(
    "main_advanced_v3.py"
    "src/account_selector.py"
    "src/dragnet.py"
    "src/local_ai.py"
    "src/target_profiler.py"
    "src/config.py"
)

# New files added
NEW_FILES=(
    "src/account_utils.py"
    "test_sherlock.py"
)

echo "📁 Modified Files:"
echo ""

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
        echo "   Last modified: $(stat -c %y "$file" 2>/dev/null | cut -d'.' -f1)"
        echo "   Lines: $(wc -l < "$file")"
        echo ""
    else
        echo "❌ $file - NOT FOUND"
        echo ""
    fi
done

echo "📁 New Files Added:"
echo ""

for file in "${NEW_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
        echo "   Lines: $(wc -l < "$file")"
        echo "   Purpose: $(head -2 "$file" | tail -1 | sed 's/^[#\"]*//;s/\"*$//')"
        echo ""
    else
        echo "❌ $file - NOT FOUND"
        echo ""
    fi
done

echo "📊 Merged Features:"
echo ""
echo "✅ Timeout Fixes (src/config.py):"
echo "   - SHERLOCK_TIMEOUT: 10s per site"
echo "   - SHERLOCK_TOTAL_TIMEOUT: 300s (5 minutes)"
echo ""

echo "✅ Manual URL Fallback (main_advanced_v3.py):"
echo "   - Interactive menu when no results found"
echo "   - Options: Manual URLs, Retry, Exit"
echo ""

echo "✅ Safe Account Handling (src/account_utils.py):"
echo "   - filter_none_accounts()"
echo "   - safe_get()"
echo "   - is_valid_account()"
echo "   - process_accounts_safely()"
echo ""

echo "✅ Testing (test_sherlock.py):"
echo "   - Quick Sherlock integration test"
echo ""

echo "✅ Error Handling (src/dragnet.py):"
echo "   - Partial results on timeout"
echo "   - Stdout parsing fallback"
echo "   - add_manual_urls() method"
echo ""

echo "🎯 Combined Result:"
echo "   Full-featured DeepTrace with robust error handling,"
echo "   safe account processing, and comprehensive testing!"
echo ""
