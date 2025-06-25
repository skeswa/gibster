#!/bin/bash

# Check if all code in the repository is properly formatted
# This script checks formatting without making changes - useful for CI/CD

set -e  # Exit on any error

echo "🔍 Checking code formatting in the repository..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

cd "$PROJECT_ROOT"

# Track if any formatting issues are found
FORMATTING_ISSUES=0

# Check Python code formatting
print_status "Checking Python code formatting..."

if command -v black &> /dev/null; then
    print_status "Checking black formatting..."
    if ! black backend/ tests/ scripts/ --check --line-length 88 --target-version py38; then
        print_error "Python code is not properly formatted with black"
        FORMATTING_ISSUES=1
    else
        print_success "Black formatting check passed"
    fi
else
    print_error "black not found. Please install it with: pip install black==23.12.1"
    exit 1
fi

if command -v isort &> /dev/null; then
    print_status "Checking isort formatting..."
    if ! isort backend/ tests/ scripts/ --profile black --check-only; then
        print_error "Python imports are not properly sorted with isort"
        FORMATTING_ISSUES=1
    else
        print_success "isort formatting check passed"
    fi
else
    print_error "isort not found. Please install it with: pip install isort==5.13.2"
    exit 1
fi

# Check frontend code formatting
print_status "Checking frontend code formatting..."

if [ -d "frontend" ]; then
    cd frontend
    
    if [ -f "package.json" ]; then
        if command -v npm &> /dev/null; then
            print_status "Checking prettier formatting..."
            if ! npm run format:check; then
                print_error "Frontend code is not properly formatted with prettier"
                FORMATTING_ISSUES=1
            else
                print_success "Frontend formatting check passed"
            fi
        else
            print_error "npm not found. Please install Node.js and npm"
            exit 1
        fi
    else
        print_warning "No package.json found in frontend directory"
    fi
    
    cd "$PROJECT_ROOT"
else
    print_warning "No frontend directory found"
fi

# Final result
echo ""
if [ $FORMATTING_ISSUES -eq 0 ]; then
    print_success "🎉 All formatting checks passed!"
    echo ""
    echo "📋 Summary:"
    echo "  ✅ Python code formatting (black & isort)"
    echo "  ✅ Frontend code formatting (prettier)"
    echo ""
    exit 0
else
    print_error "❌ Formatting issues found!"
    echo ""
    echo "📋 Summary:"
    echo "  ❌ Some code is not properly formatted"
    echo ""
    echo "💡 Run './scripts/format.sh' to fix formatting issues"
    exit 1
fi 