#!/bin/bash

# GitHub Repository Setup Script for Slide Scanner v3
# This script helps you create and push to a GitHub repository

echo "Setting up GitHub repository for Slide Scanner v3"
echo ""

# Check if git is configured
if ! git config --get user.name > /dev/null 2>&1; then
    echo "Git user.name not configured"
    echo "Please run: git config --global user.name 'Your Name'"
    exit 1
fi

if ! git config --get user.email > /dev/null 2>&1; then
    echo "Git user.email not configured"
    echo "Please run: git config --global user.email 'your.email@example.com'"
    exit 1
fi

echo "Git configuration verified"
echo ""

# Instructions for GitHub setup
echo "Follow these steps to create the GitHub repository:"
echo ""
echo "1. Go to https://github.com/new"
echo "2. Repository name: slide-scanner-v3"
echo "3. Description: Complete slide scanning system with simple grid stitch workflow"
echo "4. Make it Public or Private (your choice)"
echo "5. DO NOT initialize with README (we already have one)"
echo "6. Click 'Create repository'"
echo ""
echo "After creating the repository, run these commands:"
echo ""
echo "git remote add origin https://github.com/YOUR_USERNAME/slide-scanner-v3.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""
echo "Replace YOUR_USERNAME with your actual GitHub username"
echo ""

# Check if remote is already configured
if git remote get-url origin > /dev/null 2>&1; then
    echo "Remote origin already configured:"
    git remote get-url origin
    echo ""
    echo "To push to GitHub:"
    echo "git push -u origin main"
else
    echo "No remote origin configured yet"
    echo "Follow the instructions above to add your GitHub repository"
fi

echo ""
echo "Repository setup complete!"
echo "Your slide scanner is ready to be shared on GitHub" 