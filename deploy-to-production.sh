#!/bin/bash

# deploy-to-production.sh
# Script to deploy scheduler web application to Digital Ocean
# Usage: ./deploy-to-production.sh [commit message] [--skip-build]

set -e  # Exit immediately if a command exits with a non-zero status

# Default commit message
COMMIT_MSG="Deploy to production: $(date '+%Y-%m-%d %H:%M:%S')"

# Process arguments
SKIP_BUILD=false
for arg in "$@"; do
    if [ "$arg" == "--skip-build" ]; then
        SKIP_BUILD=true
    elif [ "$COMMIT_MSG" == "Deploy to production: $(date '+%Y-%m-%d %H:%M:%S')" ]; then
        # If it's not --skip-build and we're still using default commit message
        COMMIT_MSG="$arg"
    fi
done

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}====== Starting deployment to Digital Ocean ======${NC}"

# Verify essential files exist
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}Error: docker-compose.prod.yml not found!${NC}"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Environment variables must be set on Digital Ocean.${NC}"
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

if ! $SKIP_BUILD; then
    # Build and test before pushing
    echo -e "${YELLOW}Building Docker image for production...${NC}"
    docker-compose -f docker-compose.prod.yml build web
    
    # Check if build succeeded
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Build successful!${NC}"
        
        # Test the build
        echo -e "${YELLOW}Running quick test of the build...${NC}"
        docker-compose -f docker-compose.prod.yml run --rm web python manage.py check --deploy
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}Warning: Deployment checks failed. Review the issues before continuing.${NC}"
            read -p "Continue anyway? (y/n): " CONTINUE
            if [[ $CONTINUE != "y" && $CONTINUE != "Y" ]]; then
                echo -e "${YELLOW}Deployment aborted.${NC}"
                exit 1
            fi
        else
            echo -e "${GREEN}Deployment checks passed!${NC}"
        fi
    else
        echo -e "${RED}Build failed! Deployment aborted.${NC}"
        exit 1
    fi
else
    echo -e "${BLUE}Skipping build process as requested.${NC}"
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

# Instructions for Digital Ocean deployment
echo -e "${YELLOW}====== Digital Ocean Deployment Instructions ======${NC}"
echo -e "${GREEN}Your code is now ready for deployment to Digital Ocean.${NC}"
echo -e "${BLUE}Follow these steps to complete the deployment:${NC}"
echo -e "1. Log into your Digital Ocean dashboard"
echo -e "2. Navigate to your App Platform"
echo -e "3. Select your scheduler application"
echo -e "4. Click 'Deploy' to trigger a new deployment from your production branch"
echo -e "5. Monitor the deployment logs for any issues"

echo -e "\n${YELLOW}Environment Variables Check:${NC}"
echo -e "Ensure these environment variables are set in Digital Ocean App Platform:"
echo -e "- DJANGO_SECRET_KEY\n- POSTGRES_PASSWORD\n- DB_USE_SSL (set to 'true' for Digital Ocean managed databases)\n- ALLOWED_HOSTS\n- DJANGO_SUPERUSER_USERNAME\n- DJANGO_SUPERUSER_PASSWORD\n- DJANGO_SUPERUSER_EMAIL"

echo -e "\n${GREEN}✅ All done! Your changes are now ready for deployment to Digital Ocean.${NC}"
