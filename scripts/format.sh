#!/bin/bash

# Format all code in the repository
# This script formats Python, TypeScript/JavaScript, shell scripts, and Markdown files

set -e  # Exit on any error

echo "🎨 Formatting all code in the repository..."

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

# Format Python code
print_status "Formatting Python code with black and isort..."

if command -v black &> /dev/null; then
    print_status "Running black on Python files..."
    # Format each directory separately to avoid errors if one doesn't exist
    for dir in backend scripts; do
        if [ -d "$dir" ]; then
            black "$dir/" --line-length 88 --target-version py38 || {
                print_warning "Black formatting completed with warnings for $dir"
            }
        fi
    done
    print_success "Black formatting completed"
else
    print_error "black not found. Please install it with: pip install black==23.12.1"
    exit 1
fi

if command -v isort &> /dev/null; then
    print_status "Running isort on Python files..."
    # Format each directory separately to avoid errors if one doesn't exist
    for dir in backend scripts; do
        if [ -d "$dir" ]; then
            isort "$dir/" --profile black || {
                print_warning "isort completed with warnings for $dir"
            }
        fi
    done
    print_success "isort formatting completed"
else
    print_error "isort not found. Please install it with: pip install isort==5.13.2"
    exit 1
fi

# Format frontend code
print_status "Formatting frontend code with prettier..."

if [ -d "frontend" ]; then
    cd frontend
    
    if [ -f "package.json" ]; then
        if command -v npm &> /dev/null; then
            print_status "Running prettier on frontend files..."
            npm run format || {
                print_warning "Prettier formatting completed with warnings"
            }
            print_success "Frontend formatting completed"
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

# Format shell scripts
print_status "Formatting shell scripts..."
if command -v shfmt &> /dev/null; then
    find scripts/ -name "*.sh" -type f -exec shfmt -i 4 -w {} \; || {
        print_warning "shfmt completed with warnings"
    }
    print_success "Shell script formatting completed"
else
    print_warning "shfmt not found. Install it for shell script formatting: brew install shfmt (macOS) or apt-get install shfmt (Ubuntu)"
fi

# Format Markdown files
print_status "Formatting Markdown files with prettier..."

# Check if prettier is available (use from frontend if needed)
PRETTIER_CMD=""
if command -v prettier &> /dev/null; then
    PRETTIER_CMD="prettier"
elif [ -f "frontend/node_modules/.bin/prettier" ]; then
    PRETTIER_CMD="./frontend/node_modules/.bin/prettier"
else
    print_warning "Prettier not found. Skipping Markdown formatting."
    print_warning "To enable Markdown formatting, install prettier globally: npm install -g prettier"
fi

if [ -n "$PRETTIER_CMD" ]; then
    # Find all markdown files, excluding node_modules and venv directories
    MD_FILES=$(find . -name "*.md" -type f \
        -not -path "*/node_modules/*" \
        -not -path "*/venv/*" \
        -not -path "*/.venv/*" \
        -not -path "*/htmlcov/*" \
        -not -path "*/coverage/*" \
        -not -path "*/.git/*" \
        -not -path "*/build/*" \
        -not -path "*/dist/*" \
        2>/dev/null | sort)
    
    if [ -n "$MD_FILES" ]; then
        MD_COUNT=$(echo "$MD_FILES" | wc -l | tr -d ' ')
        print_status "Found $MD_COUNT Markdown files to format"
        
        # Use prettier config from frontend if available
        PRETTIER_CONFIG=""
        if [ -f "frontend/.prettierrc" ]; then
            PRETTIER_CONFIG="--config frontend/.prettierrc"
        fi
        
        # Format each markdown file
        echo "$MD_FILES" | while read -r file; do
            echo "  Formatting: $file"
            $PRETTIER_CMD --write "$file" $PRETTIER_CONFIG --log-level silent || {
                print_warning "Failed to format $file"
            }
        done
        
        print_success "Markdown formatting completed"
    else
        print_status "No Markdown files found to format"
    fi
fi

print_success "🎉 All code formatting completed!"

echo ""
echo "📋 Summary:"
echo "  ✅ Python code formatted with black and isort"
echo "  ✅ Frontend code formatted with prettier"
if command -v shfmt &> /dev/null; then
    echo "  ✅ Shell scripts formatted with shfmt"
else
    echo "  ⚠️  Shell scripts not formatted (shfmt not installed)"
fi
if [ -n "$PRETTIER_CMD" ]; then
    echo "  ✅ Markdown files formatted with prettier"
else
    echo "  ⚠️  Markdown files not formatted (prettier not installed)"
fi
echo ""
echo "💡 Tip: Run this script before committing to ensure consistent code formatting" 