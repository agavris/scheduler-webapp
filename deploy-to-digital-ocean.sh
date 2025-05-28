#!/bin/bash

# deploy-to-digital-ocean.sh
# Script to deploy scheduler web application to Digital Ocean App Platform
# Usage: ./deploy-to-digital-ocean.sh [commit message]

set -e  # Exit immediately if a command exits with a non-zero status

# Default commit message
COMMIT_MSG="Deploy to Digital Ocean: $(date '+%Y-%m-%d %H:%M:%S')"

# Use provided commit message if available
if [ "$1" != "" ]; then
    COMMIT_MSG="$1"
fi

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}====== Starting deployment to Digital Ocean ======${NC}"

# Verify essential files exist
if [ ! -f "app.yaml" ]; then
    echo -e "${RED}Error: app.yaml not found!${NC}"
    exit 1
fi

# Check if we have any uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}Uncommitted changes detected. Committing them now...${NC}"
    git add .
    git commit -m "$COMMIT_MSG"
    echo -e "${GREEN}Changes committed successfully.${NC}"
else
    echo -e "${GREEN}No uncommitted changes.${NC}"
fi

# Get current branch name
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${YELLOW}Current branch: ${CURRENT_BRANCH}${NC}"

# Check if production branch exists
if git show-ref --verify --quiet refs/heads/production; then
    echo -e "${YELLOW}Production branch exists. Switching to it...${NC}"
    git checkout production
else
    echo -e "${YELLOW}Creating production branch...${NC}"
    git checkout -b production
fi

# If we were on a different branch (like dev), merge it into production
if [ "$CURRENT_BRANCH" != "production" ]; then
    echo -e "${YELLOW}Merging changes from ${CURRENT_BRANCH} into production...${NC}"
    git merge "$CURRENT_BRANCH" -m "Merge $CURRENT_BRANCH into production"
fi

# Apply JavaScript security measures
echo -e "${YELLOW}Applying JavaScript security measures...${NC}"

# Run the JavaScript security script if it exists
if [ -f "./secure-js-predeploy.sh" ]; then
    chmod +x ./secure-js-predeploy.sh
    ./secure-js-predeploy.sh
    echo -e "${GREEN}JavaScript files secured successfully.${NC}"
else
    echo -e "${YELLOW}JavaScript security script not found. Running basic collectstatic...${NC}"
    python manage.py collectstatic --noinput
    
    # Try to run the obfuscation command if available
    if python manage.py help | grep -q obfuscate_js; then
        echo -e "${YELLOW}Running JavaScript obfuscation...${NC}"
        python manage.py obfuscate_js
    fi
fi

# Verify all required apps are in settings
echo -e "${YELLOW}Verifying required applications in settings...${NC}"
if ! grep -q "'axes'" scheduler_project/settings_prod.py; then
    echo -e "${RED}Warning: 'axes' app is missing from INSTALLED_APPS in production settings!${NC}"
    echo -e "${YELLOW}Please add it before continuing with deployment.${NC}"
    exit 1
fi

# Push to remote if it exists
if git remote -v | grep -q origin; then
    echo -e "${YELLOW}Pushing production branch to remote...${NC}"
    git push -u origin production
    echo -e "${GREEN}Code pushed to production branch!${NC}"
else
    echo -e "${YELLOW}No remote repository found. Skipping push.${NC}"
fi

# Return to original branch if not production
if [ "$CURRENT_BRANCH" != "production" ]; then
    echo -e "${YELLOW}Switching back to ${CURRENT_BRANCH} branch...${NC}"
    git checkout "$CURRENT_BRANCH"
fi

# Digital Ocean deployment instructions
echo -e "${YELLOW}====== Digital Ocean Deployment Instructions ======${NC}"
echo -e "${GREEN}Your code is now ready for deployment to Digital Ocean App Platform.${NC}"
echo -e "${BLUE}Follow these steps to complete the deployment:${NC}"

echo -e "1. Log into your Digital Ocean dashboard at https://cloud.digitalocean.com/"
echo -e "2. Navigate to Apps -> Your scheduler app"
echo -e "3. If this is your first deployment:"
echo -e "   a. Click 'Create App'"
echo -e "   b. Choose 'GitHub' as your source"
echo -e "   c. Select your repository and the 'production' branch"
echo -e "   d. Select 'Dockerfile' as your deployment method"
echo -e "   e. Configure your app according to app.yaml"
echo -e "4. If you're updating an existing app:"
echo -e "   a. Click on your app"
echo -e "   b. Go to the 'Settings' tab"
echo -e "   c. Click 'Force Rebuild and Deploy'"
echo -e "5. Wait for the deployment to complete and check the logs for any issues"

echo -e "\n${YELLOW}Environment Variables Check:${NC}"
echo -e "Ensure these environment variables are set in Digital Ocean App Platform:"
echo -e "- DJANGO_SECRET_KEY"
echo -e "- DATABASE_URL (provided automatically by Digital Ocean)"
echo -e "- REDIS_URL (if using Redis)"
echo -e "- ALLOWED_HOSTS (should include your app's domain)"
echo -e "- CSRF_TRUSTED_ORIGINS (with https:// prefix for your domains)"
echo -e "- DJANGO_SUPERUSER_USERNAME"
echo -e "- DJANGO_SUPERUSER_PASSWORD"
echo -e "- DJANGO_SUPERUSER_EMAIL"

echo -e "\n${GREEN}✅ All done! Your changes are now ready for deployment to Digital Ocean.${NC}"
