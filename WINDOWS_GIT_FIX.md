# 🔧 Fix Git Configuration on Windows (VS Code)

## Quick Fix for "Port Number" Error

### Method 1: Direct Push (What Worked!)

```powershell
# Push local master to remote branch
git push -u origin master:claude/aiml-portfolio-ideas-0153dmNBEmwKJzAmeZzoQjf4 --force
```

✅ This successfully pushed your changes!

---

## Alternative Methods

### Method 2: Create Local Branch

```powershell
# Create the correct branch locally
git checkout -b claude/aiml-portfolio-ideas-0153dmNBEmwKJzAmeZzoQjf4

# Push it
git push -u origin claude/aiml-portfolio-ideas-0153dmNBEmwKJzAmeZzoQjf4
```

### Method 3: Fix Remote URL

```powershell
# Remove broken remote
git remote remove origin

# Add correct remote
git remote add origin https://github.com/aryantuntune/Zesty.git

# Push
git push -u origin claude/aiml-portfolio-ideas-0153dmNBEmwKJzAmeZzoQjf4
```

---

## Common Git Commands for Windows

### Check Status
```powershell
git status
git branch
git remote -v
```

### View Commits
```powershell
git log --oneline -10
```

### Sync with Remote
```powershell
# Pull latest changes
git pull origin claude/aiml-portfolio-ideas-0153dmNBEmwKJzAmeZzoQjf4

# Push your changes
git push origin claude/aiml-portfolio-ideas-0153dmNBEmwKJzAmeZzoQjf4
```

---

## VS Code Git Interface

If command line isn't working, use VS Code's built-in Git:

1. **View Changes:**
   - Click Source Control icon (left sidebar)
   - See all modified files

2. **Stage & Commit:**
   - Click `+` next to files to stage
   - Type commit message
   - Click ✓ checkmark

3. **Push:**
   - Click `...` (more actions)
   - Select "Push to..."
   - Choose branch

---

## Troubleshooting

### "Port Number Was Not a Decimal Number"
- Remote URL had literal "PORT" instead of number
- Solution: Use GitHub URL instead of local proxy

### "src refspec does not match any"
- You're on different branch than you're trying to push
- Solution: Use `master:claude/...` syntax

### "Nothing to Commit"
- Changes already committed
- Just need to push to remote

---

## What We Learned

Your Windows setup had committed changes to `master` branch locally. The solution was to push that local `master` to the remote `claude/aiml-portfolio-ideas-0153dmNBEmwKJzAmeZzoQjf4` branch using:

```powershell
git push -u origin master:claude/aiml-portfolio-ideas-0153dmNBEmwKJzAmeZzoQjf4 --force
```

This syntax means: "Take my local `master` and push it to remote `claude/aiml-portfolio-ideas-0153dmNBEmwKJzAmeZzoQjf4`"

✅ **Success!** Your changes are now in the remote repository.
