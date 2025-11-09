# Feature Branch Workflow Guide

## Current Setup

You're currently in: `~/Desktop/careerlens/backend`

## Quick Start: Working on Feature Branch

### 1. Navigate to Project Root

From anywhere in the project, go to the root:

```bash
cd ~/Desktop/careerlens
```

### 2. Check Current Branch

```bash
git branch
```

You'll see:
- `* main` (if on main branch)
- `* feature/testing` (if on feature branch)

### 3. Switch to Feature Branch

```bash
git checkout feature/testing
```

### 4. Verify You're on Feature Branch

```bash
git branch
# Should show: * feature/testing
```

## Working on Features

### From Backend Directory

Even if you're in `backend/`, you can work on the feature branch:

```bash
# From backend directory
cd ~/Desktop/careerlens
git checkout feature/testing

# Now go back to backend
cd backend

# Make your changes
# ... edit files ...

# When ready to commit, go back to root
cd ~/Desktop/careerlens
git add .
git commit -m "Feature: your feature description"
git push origin feature/testing
```

### Recommended Workflow

**Option 1: Work from Project Root (Recommended)**

```bash
# Always start from project root
cd ~/Desktop/careerlens

# Switch to feature branch
git checkout feature/testing

# Now you can work in any directory
cd backend
# ... make changes ...
cd ../frontend
# ... make changes ...

# When done, commit from root
cd ~/Desktop/careerlens
git add .
git commit -m "Feature: your feature description"
git push origin feature/testing
```

**Option 2: Work from Any Directory**

```bash
# From backend directory
cd ~/Desktop/careerlens/backend

# Switch branch (from root)
cd .. && git checkout feature/testing && cd backend

# Make changes
# ... edit files ...

# Commit (from root)
cd .. && git add . && git commit -m "Feature: your feature" && git push origin feature/testing
```

## Common Workflows

### 1. Start New Feature

```bash
cd ~/Desktop/careerlens

# Make sure you're on main and up to date
git checkout main
git pull origin main  # If repository exists on GitHub

# Create new feature branch
git checkout -b feature/your-feature-name

# Now work on your feature
cd backend
# ... make changes ...
```

### 2. Make Changes on Feature Branch

```bash
# From any directory
cd ~/Desktop/careerlens

# Switch to feature branch
git checkout feature/testing

# Work on your changes
cd backend
# ... edit files in backend/ ...
cd ../frontend
# ... edit files in frontend/ ...

# Commit changes
cd ~/Desktop/careerlens
git add .
git commit -m "Feature: Add new API endpoint"
git push origin feature/testing
```

### 3. Test Your Feature

```bash
# From backend directory
cd ~/Desktop/careerlens/backend

# Start backend server
make dev
# or
uvicorn app.main:app --reload

# In another terminal, start frontend
cd ~/Desktop/careerlens/frontend
npm run dev

# Test your feature
# ... test in browser ...
```

### 4. Merge Feature to Main

```bash
cd ~/Desktop/careerlens

# Switch to main
git checkout main

# Pull latest changes (if working with team)
git pull origin main

# Merge feature branch
git merge feature/testing

# Push to main
git push origin main
```

### 5. Continue Working on Feature

```bash
cd ~/Desktop/careerlens

# Switch back to feature branch
git checkout feature/testing

# Make more changes
cd backend
# ... edit files ...

# Commit and push
cd ~/Desktop/careerlens
git add .
git commit -m "Feature: Update API endpoint"
git push origin feature/testing
```

## Useful Commands

### Check Current Branch (from any directory)

```bash
cd ~/Desktop/careerlens && git branch
```

### See What Files Changed

```bash
cd ~/Desktop/careerlens
git status
```

### See Changes in Files

```bash
cd ~/Desktop/careerlens
git diff
```

### View Commit History

```bash
cd ~/Desktop/careerlens
git log --oneline
```

### Discard Changes (if you make a mistake)

```bash
cd ~/Desktop/careerlens
git checkout -- .
# or for specific file
git checkout -- backend/app/routes/analyze.py
```

## Best Practices

1. **Always commit from project root**: `cd ~/Desktop/careerlens` before `git add` and `git commit`

2. **Use descriptive commit messages**:
   ```bash
   git commit -m "Feature: Add job search filter"
   git commit -m "Fix: Resolve CORS error in analyze endpoint"
   git commit -m "Update: Improve error handling in job search"
   ```

3. **Test before committing**:
   - Make sure backend runs: `cd backend && make dev`
   - Make sure frontend runs: `cd frontend && npm run dev`
   - Test your feature in browser

4. **Commit often**: Don't wait until everything is done
   ```bash
   git add .
   git commit -m "Feature: Add job filter UI"
   git push origin feature/testing
   ```

5. **Keep feature branch updated**:
   ```bash
   cd ~/Desktop/careerlens
   git checkout main
   git pull origin main
   git checkout feature/testing
   git merge main  # Merge latest main into feature
   ```

## Quick Reference

```bash
# Navigate to project root
cd ~/Desktop/careerlens

# Switch to feature branch
git checkout feature/testing

# Make changes (from any directory)
cd backend
# ... edit files ...

# Commit (always from root)
cd ~/Desktop/careerlens
git add .
git commit -m "Feature: your description"
git push origin feature/testing
```

## Current Status

- **Main branch**: Production-ready code
- **Feature branch**: `feature/testing` - For testing new features
- **Your location**: `~/Desktop/careerlens/backend`

## Next Steps

1. Switch to feature branch:
   ```bash
   cd ~/Desktop/careerlens
   git checkout feature/testing
   ```

2. Make your changes in `backend/` or `frontend/`

3. Commit and push:
   ```bash
   cd ~/Desktop/careerlens
   git add .
   git commit -m "Feature: your feature description"
   git push origin feature/testing
   ```

4. Test your feature before merging to main!

