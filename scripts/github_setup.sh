#!/bin/bash

# GitHub Setup Script for EnodAI
# This script initializes git and helps push to GitHub

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  EnodAI GitHub Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed${NC}"
    echo "Please install git: sudo apt-get install git"
    exit 1
fi

echo -e "${GREEN}✅ Git is installed${NC}"
echo ""

# Check if already a git repo
if [ -d ".git" ]; then
    echo -e "${YELLOW}⚠️  Git repository already initialized${NC}"
else
    echo -e "${BLUE}Initializing git repository...${NC}"
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
fi
echo ""

# Get GitHub username
echo -e "${BLUE}Enter your GitHub username:${NC}"
read -p "> " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo -e "${RED}❌ GitHub username cannot be empty${NC}"
    exit 1
fi

# Get repository name (default: EnodAI)
echo ""
echo -e "${BLUE}Enter repository name (default: EnodAI):${NC}"
read -p "> " REPO_NAME
REPO_NAME=${REPO_NAME:-EnodAI}

# Repository URL
REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

echo ""
echo -e "${BLUE}Repository will be created at:${NC}"
echo -e "${YELLOW}${REPO_URL}${NC}"
echo ""

# Check if remote exists
if git remote | grep -q origin; then
    echo -e "${YELLOW}⚠️  Remote 'origin' already exists${NC}"
    echo -e "${BLUE}Current remote:${NC}"
    git remote -v
    echo ""
    read -p "Remove and re-add? (y/N): " REMOVE_REMOTE
    if [[ $REMOVE_REMOTE =~ ^[Yy]$ ]]; then
        git remote remove origin
        echo -e "${GREEN}✅ Remote removed${NC}"
    else
        echo -e "${YELLOW}Keeping existing remote${NC}"
    fi
fi

# Add remote if not exists
if ! git remote | grep -q origin; then
    echo -e "${BLUE}Adding remote...${NC}"
    git remote add origin "$REPO_URL"
    echo -e "${GREEN}✅ Remote added${NC}"
fi
echo ""

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${BLUE}You have uncommitted changes${NC}"
    read -p "Commit all changes? (Y/n): " COMMIT_CHANGES

    if [[ ! $COMMIT_CHANGES =~ ^[Nn]$ ]]; then
        echo -e "${BLUE}Staging all files...${NC}"
        git add .

        echo ""
        echo -e "${BLUE}Enter commit message (or press Enter for default):${NC}"
        read -p "> " COMMIT_MSG

        if [ -z "$COMMIT_MSG" ]; then
            COMMIT_MSG="Initial commit: EnodAI - AI-powered monitoring platform

Features:
- Anomaly detection with Isolation Forest
- LLM-based root cause analysis (Ollama/Llama2)
- JWT authentication & rate limiting
- Comprehensive test suite (80%+ coverage)
- CI/CD pipeline with GitHub Actions
- Kubernetes deployment manifests
- Grafana dashboards & Prometheus alerts
- Production-ready Docker Compose

Tech Stack: Go, Python, FastAPI, PostgreSQL, Redis, Prometheus, Grafana"
        fi

        git commit -m "$COMMIT_MSG"
        echo -e "${GREEN}✅ Changes committed${NC}"
    fi
else
    # Check if no commits exist
    if ! git rev-parse HEAD &>/dev/null; then
        echo -e "${BLUE}Creating initial commit...${NC}"
        git add .
        git commit -m "Initial commit: EnodAI - AI-powered monitoring platform"
        echo -e "${GREEN}✅ Initial commit created${NC}"
    fi
fi
echo ""

# Set main branch
echo -e "${BLUE}Setting branch to main...${NC}"
git branch -M main
echo -e "${GREEN}✅ Branch set to main${NC}"
echo ""

# Push
echo -e "${BLUE}Ready to push to GitHub!${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo -e "When prompted for password, use your:"
echo -e "  1. Personal Access Token (recommended)"
echo -e "  2. Or setup SSH key"
echo ""
echo -e "Create token at: ${BLUE}https://github.com/settings/tokens${NC}"
echo -e "Required scopes: ${YELLOW}repo, workflow${NC}"
echo ""

read -p "Push to GitHub now? (Y/n): " PUSH_NOW

if [[ ! $PUSH_NOW =~ ^[Nn]$ ]]; then
    echo -e "${BLUE}Pushing to GitHub...${NC}"

    if git push -u origin main; then
        echo ""
        echo -e "${GREEN}================================${NC}"
        echo -e "${GREEN}  Success! 🎉${NC}"
        echo -e "${GREEN}================================${NC}"
        echo ""
        echo -e "Repository URL:"
        echo -e "${BLUE}https://github.com/${GITHUB_USERNAME}/${REPO_NAME}${NC}"
        echo ""
        echo -e "Next steps:"
        echo -e "  1. Visit your repository"
        echo -e "  2. Add a description and topics"
        echo -e "  3. Enable GitHub Pages (optional)"
        echo -e "  4. Configure branch protection rules"
        echo ""
    else
        echo ""
        echo -e "${RED}❌ Push failed${NC}"
        echo ""
        echo -e "${YELLOW}Common issues:${NC}"
        echo -e "  1. Repository doesn't exist - Create it at:"
        echo -e "     ${BLUE}https://github.com/new${NC}"
        echo -e "  2. Wrong credentials - Use Personal Access Token"
        echo -e "  3. SSH key not configured"
        echo ""
        echo -e "After fixing, run:"
        echo -e "${YELLOW}git push -u origin main${NC}"
    fi
else
    echo ""
    echo -e "${YELLOW}Skipped push${NC}"
    echo -e "When ready, run: ${YELLOW}git push -u origin main${NC}"
fi
