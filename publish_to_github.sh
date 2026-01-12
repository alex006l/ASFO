#!/usr/bin/env bash
set -e

# Script to publish slicer service to GitHub

echo "🚀 Publishing Slicer Service to GitHub"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
  echo "📦 Initializing git repository..."
  git init
  git branch -M main
else
  echo "✅ Git already initialized"
fi

# Check for GitHub CLI
if command -v gh &> /dev/null; then
  echo ""
  echo "GitHub CLI detected. What would you like to do?"
  echo "1) Create new repo and push (recommended)"
  echo "2) Just add files and commit (manual repo creation)"
  read -p "Choice [1-2]: " choice
  
  case $choice in
    1)
      read -p "Repository name [slicer-service]: " repo_name
      repo_name=${repo_name:-slicer-service}
      
      read -p "Make repository public? [Y/n]: " public
      public=${public:-Y}
      
      if [[ $public =~ ^[Yy]$ ]]; then
        visibility="--public"
      else
        visibility="--private"
      fi
      
      echo ""
      echo "📤 Creating GitHub repository and pushing..."
      git add .
      git commit -m "Initial commit: Slicer service with CuraEngine and feedback loop" || echo "Nothing to commit"
      
      gh repo create "$repo_name" $visibility --source=. --remote=origin --push
      
      echo ""
      echo "✅ Repository created and pushed!"
      echo ""
      echo "📝 Next steps:"
      echo "1. Update YOUR_USERNAME in these files with your actual GitHub username:"
      echo "   - install_slicer_service.sh"
      echo "   - README_MAIN.md"
      echo "   - QUICKSTART.md"
      echo ""
      echo "2. Commit and push the changes:"
      echo "   git add ."
      echo "   git commit -m 'Update GitHub username in install URLs'"
      echo "   git push"
      echo ""
      echo "3. Test one-line install on your Pi:"
      github_user=$(gh api user -q .login)
      echo "   curl -fsSL https://raw.githubusercontent.com/$github_user/$repo_name/main/install_slicer_service.sh | sudo bash"
      ;;
    2)
      git add .
      git commit -m "Initial commit: Slicer service with CuraEngine and feedback loop" || echo "Nothing to commit"
      
      echo ""
      echo "✅ Files committed locally"
      echo ""
      echo "📝 Next steps:"
      echo "1. Create repository on GitHub: https://github.com/new"
      echo "2. Run these commands (replace YOUR_USERNAME):"
      echo "   git remote add origin https://github.com/YOUR_USERNAME/slicer-service.git"
      echo "   git push -u origin main"
      echo ""
      echo "3. Update YOUR_USERNAME in install_slicer_service.sh, README_MAIN.md, QUICKSTART.md"
      echo "4. Commit and push the changes"
      ;;
  esac
else
  echo "⚠️  GitHub CLI not found. Manual setup required."
  echo ""
  echo "📝 Steps to publish:"
  echo ""
  echo "1. Add and commit files:"
  echo "   git add ."
  echo "   git commit -m 'Initial commit: Slicer service with CuraEngine and feedback loop'"
  echo ""
  echo "2. Create repository on GitHub: https://github.com/new"
  echo "   Name it: slicer-service"
  echo ""
  echo "3. Add remote and push (replace YOUR_USERNAME):"
  echo "   git remote add origin https://github.com/YOUR_USERNAME/slicer-service.git"
  echo "   git push -u origin main"
  echo ""
  echo "4. Update YOUR_USERNAME in:"
  echo "   - install_slicer_service.sh"
  echo "   - README_MAIN.md"
  echo "   - QUICKSTART.md"
  echo ""
  echo "5. Commit and push the changes:"
  echo "   git add ."
  echo "   git commit -m 'Update GitHub username in install URLs'"
  echo "   git push"
  echo ""
  echo "To install GitHub CLI: https://cli.github.com/"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "For more details, see DEPLOYMENT.md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
