#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Facebook Scraper GitHub Setup Script${NC}"
echo -e "This script will help you push your code to GitHub for Render deployment."
echo -e "==============================================================="

# Get GitHub repository information
read -p "Enter your GitHub username: " GH_USERNAME
read -p "Enter the name for your new repository: " REPO_NAME

# Check if git remote already exists and remove it
echo -e "${YELLOW}Checking for existing git remote...${NC}"
if git remote | grep -q "origin"; then
    echo -e "Remote 'origin' already exists. Removing it..."
    git remote remove origin
fi

# Add the new GitHub repository as a remote
echo -e "${YELLOW}Adding GitHub repository as remote...${NC}"
REPO_URL="https://github.com/$GH_USERNAME/$REPO_NAME.git"
git remote add origin $REPO_URL
echo -e "Added remote: $REPO_URL"

# Push code to GitHub
echo -e "${YELLOW}Pushing code to GitHub...${NC}"
echo -e "Note: You'll need to create the repository on GitHub first if you haven't already."
echo -e "Create it at: https://github.com/new"
echo -e "Make sure to create an EMPTY repository (no README, no license)."
read -p "Have you created the repository on GitHub? (y/n): " CREATED_REPO

if [ "$CREATED_REPO" = "y" ] || [ "$CREATED_REPO" = "Y" ]; then
    git branch -M main
    git push -u origin main
    echo -e "${GREEN}Code pushed to GitHub!${NC}"
    echo -e "Now you can deploy on Render using this repository:"
    echo -e "1. Go to: https://dashboard.render.com/select-repo?type=web"
    echo -e "2. Connect your GitHub account"
    echo -e "3. Select the repository: $GH_USERNAME/$REPO_NAME"
    echo -e "4. Render will automatically detect the Dockerfile"
    echo -e "5. Set the service name, choose free plan, and add environment variables:"
    echo -e "   FB_EMAIL and FB_PASSWORD"
    echo -e "6. Click 'Create Web Service'"
else
    echo -e "${YELLOW}Please create the repository first, then run this script again.${NC}"
fi

echo -e "${GREEN}Setup complete!${NC}" 