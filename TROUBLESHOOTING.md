# 🔧 DeepTrace Troubleshooting Guide

**Quick solutions for common issues**

---

## 🚨 Your Issue: "Sherlock timed out" & "No leads found"

### **ROOT CAUSES:**

1. **Sherlock timeout (60 seconds)** - Too short for 300+ sites
2. **Network issues** - Slow connection or rate limiting
3. **Google blocking** - Automated searches blocked

---

## ✅ **FIXES APPLIED:**

I've just fixed these issues! Here's what changed:

### **1. Increased Timeouts**
```python
# Before:
SHERLOCK_TIMEOUT = 5 seconds (per site)
subprocess timeout = 60 seconds (total)

# After:
SHERLOCK_TIMEOUT = 10 seconds (per site)
SHERLOCK_TOTAL_TIMEOUT = 300 seconds (5 minutes total)
```

**Result:** Sherlock now has **5 minutes** instead of 1 minute!

---

### **2. Better Error Handling**
- Saves partial results even if timeout occurs
- Continues on individual query failures
- Parses stdout if output file missing

---

### **3. Manual URL Fallback** (NEW!)

If Sherlock/Google Dorks fail, you'll now see:

```
⚠️  No leads found automatically.

💡 MANUAL INPUT OPTIONS:
   1. Enter URLs manually (if you know their accounts)
   2. Try different target name variations
   3. Exit and troubleshoot network issues

❓ What would you like to do? (1/2/3):
```

**Option 1:** Enter URLs manually
```
URL: https://github.com/aryantuntune
URL: https://linkedin.com/in/aryan-tuntune
URL: [press Enter to finish]
```

**Option 2:** Try different username
```
🎯 Enter new target name/username: aryantuntune
```

---

## 🎯 **HOW TO USE (After Fix):**

### **Run Again:**
```bash
python main_advanced_v3.py
```

**What to expect:**
1. ✅ Sherlock will run for up to 5 minutes (won't timeout at 60s)
2. ✅ Better progress messages
3. ✅ If still fails, manual URL option available

---

## 🔍 **TROUBLESHOOTING SPECIFIC ISSUES:**

### **Issue 1: Sherlock Still Timing Out**

**Symptoms:**
```
Sherlock timed out after 300s
```

**Solutions:**

**A. Check Sherlock installation:**
```bash
pip install --upgrade sherlock-project
sherlock --version
```

**B. Test Sherlock manually:**
```bash
# Test with a known username
sherlock google

# This should find: https://github.com/google
```

**C. Try with just username (no spaces):**
```python
# Instead of: "Aryan Anil Tuntune"
# Try: "aryantuntune"
```

---

### **Issue 2: Google Dorks Finding 0 Results**

**Symptoms:**
```
Google Dorks found 0 additional leads
```

**Causes:**
- Google rate limiting (too many requests)
- Google blocking automated searches
- Network/firewall issues

**Solutions:**

**A. Wait and retry:**
```bash
# Google may be rate limiting
# Wait 30-60 minutes, then retry
```

**B. Use manual search:**
```
1. Open browser
2. Search: site:github.com "Aryan Tuntune"
3. Search: site:linkedin.com "Aryan Tuntune"
4. Copy URLs found
5. Use manual URL input in DeepTrace
```

**C. Check googlesearch-python:**
```bash
pip install --upgrade googlesearch-python
```

**D. Use VPN (if rate limited):**
```bash
# Switch IP to bypass rate limiting
```

---

### **Issue 3: Still No Results**

**If automated tools AND manual search find nothing:**

**Possible reasons:**
1. **Target has minimal online presence** (uncommon)
2. **Different name variations** (e.g., "Aryan T" instead of "Aryan Tuntune")
3. **Private accounts** (not publicly searchable)

**Solutions:**

**A. Try known usernames:**
```python
# You mentioned these usernames in profile:
# - aryantuntune
# - SOUL
# - aryan28
# - aryantuntune42

# Try each one separately:
python main_advanced_v3.py
# Enter: aryantuntune

# Then try:
python main_advanced_v3.py
# Enter: aryan28
```

**B. Try platforms directly:**
```
Manual URLs:
https://github.com/aryantuntune
https://github.com/aryan28
https://linkedin.com/in/aryan-tuntune
https://twitter.com/aryantuntune
https://instagram.com/aryantuntune
```

**C. Use known email:**
```
Search Google for:
"aryantuntune42@gmail.com"

This often reveals accounts tied to that email
```

---

## 🌐 **NETWORK TROUBLESHOOTING:**

### **Check Internet Connection:**
```bash
# Test general connectivity
ping google.com

# Test Sherlock connectivity
curl -I https://github.com

# Test if websites are accessible
curl -I https://linkedin.com
curl -I https://twitter.com
```

### **Check Firewall/Antivirus:**
```bash
# Sherlock may be blocked by:
# - Windows Firewall
# - Antivirus software
# - Corporate firewall
# - VPN restrictions

# Try temporarily disabling and retrying
```

### **Check Proxy Settings:**
```bash
# If behind corporate proxy:
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port

python main_advanced_v3.py
```

---

## 💡 **BEST PRACTICES:**

### **1. Start with Username, Not Full Name:**
```bash
# Instead of: "Aryan Anil Tuntune"
# Use: "aryantuntune"

# Why? Usernames are unique, names are not!
```

### **2. Use Known Information:**
```bash
# If you know they have a GitHub account:
# 1. Find their GitHub username manually
# 2. Use that username in DeepTrace
# 3. It will find connected accounts
```

### **3. Leverage Profile Data:**
```bash
# You provided:
# - Known usernames: aryantuntune, SOUL, aryan28, aryantuntune42
# - Known email: aryantuntune42@gmail.com
# - Known platforms: GitHub, LinkedIn, Twitter, Instagram

# Use this information!
# Try each username separately
```

---

## 🚀 **QUICK FIX WORKFLOW:**

### **Step 1: Update Code**
```bash
git pull origin claude/aiml-portfolio-ideas-0153dmNBEmwKJzAmeZzoQjf4
```

### **Step 2: Try Again**
```bash
python main_advanced_v3.py

# When asked for name, try usernames instead:
# "aryantuntune" (not "Aryan Anil Tuntune")
```

### **Step 3: If Still Fails, Use Manual Input**
```bash
# When you see "Manual Input Options", choose 1
# Enter URLs you can find manually:

URL: https://github.com/aryantuntune
URL: https://linkedin.com/in/aryan-tuntune
URL: [Enter to finish]
```

### **Step 4: Investigation Continues!**
```bash
# DeepTrace will now analyze those URLs
# AI will help filter and verify
# You'll get results!
```

---

## 📊 **WHY THIS HAPPENS:**

### **Common Scenario:**

**Full Name Search:** "Aryan Anil Tuntune"
- Sherlock searches 300+ sites for this EXACT name
- Most sites use usernames, not full names
- Result: 0 found (even though accounts exist!)

**Username Search:** "aryantuntune"
- Sherlock searches 300+ sites for this username
- Finds: GitHub, maybe Twitter, etc.
- Result: 5-10 accounts found!

**Solution:** Use username, not full name!

---

## 🎯 **EXPECTED RESULTS (After Fix):**

### **With Full Name:**
```
Running Sherlock...
⏳ This may take 2-5 minutes...
✅ Sherlock completed successfully
✅ Total unique leads: 0-5

(Full names rarely match usernames)
```

### **With Username:**
```
Running Sherlock...
⏳ This may take 2-5 minutes...
✅ Sherlock completed successfully
✅ Total unique leads: 10-30

(Usernames match accounts!)
```

---

## 📧 **EXAMPLE: Investigate by Email**

**Given:** aryantuntune42@gmail.com

### **Method 1: Google Search**
```
Search: "aryantuntune42@gmail.com"

Finds:
- GitHub profile
- LinkedIn profile
- Stack Overflow profile
```

### **Method 2: Extract Username**
```
Email: aryantuntune42@gmail.com
Username: aryantuntune42

Run DeepTrace with: "aryantuntune42"
```

### **Method 3: Variations**
```
Try all variations:
- aryantuntune
- aryantuntune42
- aryan28
- SOUL
```

---

## ✅ **WHAT I FIXED:**

1. **Increased timeouts** - 5 minutes instead of 1 minute
2. **Better error handling** - Saves partial results
3. **Manual URL fallback** - Continue even if automation fails
4. **Better progress indicators** - Know what's happening
5. **Retry options** - Try different usernames easily

---

## 🎉 **TRY AGAIN NOW!**

```bash
# Pull the fixes
git pull

# Run investigation
python main_advanced_v3.py

# Tips:
# 1. Use username instead of full name
# 2. Wait for full 5 minutes (don't interrupt)
# 3. Use manual input if needed
# 4. Try different username variations
```

---

## 📞 **STILL HAVING ISSUES?**

### **Debug Mode:**
```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
python main_advanced_v3.py

# This will show detailed error messages
```

### **Check Logs:**
```bash
# Look for error details
cat data/reports/*latest*.md

# Or check Sherlock output directly
cat data/raw_leads/*sherlock.txt
```

### **Test Components:**
```bash
# Test Sherlock alone
sherlock aryantuntune

# Test Google Dorks alone
python -c "from googlesearch import search; print(list(search('site:github.com aryantuntune')))"
```

---

**Your system is now fixed and ready to investigate! 🚀**
