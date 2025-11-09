#!/bin/bash
# Run this AFTER creating the repository on GitHub.com

echo "🚀 Pushing CareerLens code to GitHub..."

# Push feature branch
echo "📤 Pushing feature/testing branch..."
git push -u origin feature/testing

# Also push main branch
echo "📤 Pushing main branch..."
git checkout main
git merge feature/testing
git push -u origin main

echo ""
echo "✅ Done! Your repository is now at:"
echo "   https://github.com/sumanshah7/careerlens"
echo ""
echo "📋 Branches pushed:"
echo "   - feature/testing"
echo "   - main"

