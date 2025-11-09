#!/bin/bash

# Script to create GitHub repository and push CareerLens code
# Make sure you're authenticated with GitHub CLI first: gh auth login

echo "🚀 Pushing CareerLens to GitHub..."

# Check if authenticated
if ! gh auth status &>/dev/null; then
    echo "❌ Not authenticated with GitHub CLI"
    echo "📝 Please run: gh auth login"
    echo "   Then run this script again"
    exit 1
fi

# Check if repository already exists
if gh repo view sumanshah7/careerlens &>/dev/null; then
    echo "✅ Repository already exists, pushing code..."
    git push -u origin feature/testing
    echo "✅ Code pushed to feature/testing branch"
else
    echo "📦 Creating repository on GitHub..."
    gh repo create careerlens --public --description "AI-powered career development platform with resume analysis, job matching, and personalized learning plans" --source=. --remote=origin --push
    echo "✅ Repository created and code pushed!"
fi

echo ""
echo "🌐 Your repository is now at: https://github.com/sumanshah7/careerlens"
echo "📋 Current branch: feature/testing"
echo ""
echo "To push to main branch:"
echo "  git checkout main"
echo "  git merge feature/testing"
echo "  git push -u origin main"

