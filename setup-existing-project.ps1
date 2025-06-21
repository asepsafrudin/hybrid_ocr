# Hybrid OCR GitHub Project Setup Script - Existing Repository
# Author: Cody AI Assistant
# Description: Setup project timeline for existing hybrid-ocr-project repository

param(
    [string]$ProjectTitle = "Hybrid OCR Development Timeline",
    [string]$RepoName = "hybrid-ocr-project"
)

# Colors for output
$Red = "Red"
$Green = "Green" 
$Yellow = "Yellow"
$Blue = "Cyan"

Write-Host "🚀 Setting up Hybrid OCR Project Timeline..." -ForegroundColor $Blue

# Check if we're in the right directory
if (-not (Test-Path ".git")) {
    Write-Host "❌ Not in a git repository. Please run this from the hybrid-ocr-project directory." -ForegroundColor $Red
    exit 1
}

# Check if GitHub CLI is installed
try {
    $ghVersion = gh --version
    Write-Host "✅ GitHub CLI found: $($ghVersion[0])" -ForegroundColor $Green
} catch {
    Write-Host "❌ GitHub CLI not found. Please install it first:" -ForegroundColor $Red
    Write-Host "winget install GitHub.cli" -ForegroundColor $Yellow
    exit 1
}

# Check authentication
try {
    gh auth status 2>$null
    Write-Host "✅ GitHub CLI authenticated" -ForegroundColor $Green
} catch {
    Write-Host "🔐 Please authenticate with GitHub first:" -ForegroundColor $Yellow
    gh auth login
    return
}

# Create project structure if not exists
Write-Host "📂 Creating/updating project structure..." -ForegroundColor $Blue
$directories = @("src", "tests", "docs", "config", "examples", "scripts", ".github\workflows", ".github\ISSUE_TEMPLATE", "models", "data")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✅ Created: $dir" -ForegroundColor $Green
    }
}

# Create or update requirements.txt
Write-Host "📝 Creating/updating requirements.txt..." -ForegroundColor $Blue
@"
# Core Dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
websockets==12.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.1

# OCR Engines
easyocr==1.7.0
paddleocr==2.7.3
pytesseract==0.3.10
transformers==4.35.2
torch==2.1.1
torchvision==0.16.1

# Document Processing
pdf2image==1.16.3
Pillow==10.1.0
opencv-python==4.8.1.78

# Vector Database
chromadb==0.4.18
sentence-transformers==2.2.2

# Utilities
pydantic==2.5.0
python-dotenv==1.0.0
pyyaml==6.0.1
celery==5.3.4
redis==5.0.1

# Development
pytest==7.4.3
black==23.11.0
flake8==6.1.0
pre-commit==3.6.0
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8

# Create config.yaml
Write-Host "⚙️ Creating config.yaml..." -ForegroundColor $Blue
@"
# Hybrid OCR Configuration
processing:
  layout_confidence_threshold: 0.7
  ocr_confidence_threshold: 0.3
  max_image_size: 4096
  
features:
  enable_layout_detection: true
  enable_handwriting: true
  enable_semantic_search: true

performance:
  max_workers: 4
  batch_size: 8
  timeout_seconds: 300

database:
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30

vector_store:
  collection_name: "hybrid_ocr_documents"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"

# Model Configuration
models:
  layout_detection:
    model_name: "microsoft/layoutlmv3-base"
    confidence_threshold: 0.7
  
  handwriting_recognition:
    model_name: "microsoft/trocr-base-handwritten"
    confidence_threshold: 0.5
  
  ocr_engines:
    tesseract:
      enabled: true
      config: "--oem 3 --psm 6"
    easyocr:
      enabled: true
      languages: ["en", "id"]
    paddleocr:
      enabled: true
      lang: "en"
"@ | Out-File -FilePath "config.yaml" -Encoding UTF8

# Create .env.example
@"
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/hybrid_ocr

# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379/0

# Object Storage (MinIO/S3)
STORAGE_ENDPOINT=localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=hybrid-ocr-files

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Model Paths
LAYOUT_MODEL_PATH=./models/layoutlmv3
HANDWRITING_MODEL_PATH=./models/trocr

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/hybrid_ocr.log
"@ | Out-File -FilePath ".env.example" -Encoding UTF8

# Create GitHub Actions workflows
Write-Host "🔄 Creating GitHub Actions workflows..." -ForegroundColor $Blue

# CI/CD Pipeline
@"
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_hybrid_ocr
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python `${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: `${{ matrix.python-version }}
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y poppler-utils tesseract-ocr
    
    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: `${{ runner.os }}-pip-`${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          `${{ runner.os }}-pip-
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest-cov
    
    - name: Run linting
      run: |
        flake8 src/ tests/
        black --check src/ tests/
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src/ --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        
  build-docs:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        pip install mkdocs mkdocs-material
    - name: Build documentation
      run: mkdocs build
"@ | Out-File -FilePath ".github\workflows\ci.yml" -Encoding UTF8

# Project Automation
@"
name: Project Automation

on:
  issues:
    types: [opened, closed, assigned, labeled]
  pull_request:
    types: [opened, closed, merged, ready_for_review]

jobs:
  add-to-project:
    runs-on: ubuntu-latest
    steps:
      - name: Add to Project
        uses: actions/add-to-project@v0.5.0
        with:
          project-url: `${{ vars.PROJECT_URL }}
          github-token: `${{ secrets.GITHUB_TOKEN }}
          
      - name: Set status based on issue state
        if: github.event_name == 'issues'
        run: |
          if [ "`${{ github.event.action }}" == "opened" ]; then
            echo "New issue created - status: Todo"
          elif [ "`${{ github.event.action }}" == "closed" ]; then
            echo "Issue closed - status: Done"
          fi
"@ | Out-File -FilePath ".github\workflows\project-automation.yml" -Encoding UTF8

# Create issue templates
Write-Host "📋 Creating issue templates..." -ForegroundColor $Blue

# Feature template
@"
name: 🚀 Feature Request
description: Suggest a new feature for Hybrid OCR
title: "[FEATURE] "
labels: ["enhancement", "needs-triage"]
assignees: ["asepsafrudin"]
body:
  - type: markdown
    attributes:
      value: |
        ## 🎯 Feature Request
        Thanks for suggesting a feature! Please provide detailed information below.
  
  - type: dropdown
    id: phase
    attributes:
      label: 📋 Project Phase
      description: Which development phase does this feature belong to?
      options:
        - "🏗️ Foundation"
        - "⚙️ Core Development" 
        - "🔗 Integration"
        - "🧪 Testing"
        - "🚀 Deployment"
    validations:
      required: true
  
  - type: dropdown
    id: priority
    attributes:
      label: ⚡ Priority Level
      options:
        - "🔴 High - Critical for MVP"
        - "🟡 Medium - Important but not blocking"
        - "🟢 Low - Nice to have"
    validations:
      required: true
      
  - type: dropdown
    id: component
    attributes:
      label: 🧩 Component
      description: Which component does this feature affect?
      options:
        - "OCR Engine"
        - "Layout Detection"
        - "Handwriting Recognition"
        - "API Server"
        - "Database"
        - "Vector Store"
        - "Frontend"
        - "Documentation"
        - "DevOps/CI"
    validations:
      required: true
  
  - type: textarea
    id: description
    attributes:
      label: 📝 Feature Description
      description: Describe the feature you'd like to see implemented
      placeholder: "A clear and concise description of what you want to happen..."
    validations:
      required: true
  
  - type: textarea
    id: use-case
    attributes:
      label: 🎯 Use Case
      description: Describe the problem this feature would solve
      placeholder: "As a [user type], I want [goal] so that [benefit]..."
    validations:
      required: true
  
  - type: textarea
    id: acceptance-criteria
    attributes:
      label: ✅ Acceptance Criteria
      description: What needs to be done for this feature to be considered complete?
      placeholder: |
        - [ ] Criterion 1: Feature works as described
        - [ ] Criterion 2: Tests are written and passing
        - [ ] Criterion 3: Documentation is updated
        - [ ] Criterion 4: Performance requirements are met
    validations:
      required: true
      
  - type: textarea
    id: additional-context
    attributes:
      label: 📎 Additional Context
      description: Add any other context, screenshots, or examples
      placeholder: "Any additional information that might be helpful..."
"@ | Out-File -FilePath ".github\ISSUE_TEMPLATE\feature.yml" -Encoding UTF8

# Bug report template
@"
name: 🐛 Bug Report
description: Report a bug in Hybrid OCR
title: "[BUG] "
labels: ["bug", "needs-triage"]
assignees: ["asepsafrudin"]
body:
  - type: markdown
    attributes:
      value: |
        ## 🐛 Bug Report
        Thanks for reporting a bug! Please provide detailed information to help us fix it.
  
  - type: dropdown
    id: severity
    attributes:
      label: 🚨 Severity
      options:
        - "🔴 Critical - System unusable"
        - "🟠 High - Major functionality broken"
        - "🟡 Medium - Minor functionality affected"
        - "🟢 Low - Cosmetic issue"
    validations:
      required: true
      
  - type: dropdown
    id: component
    attributes:
      label: 🧩 Component
      description: Which component is affected?
      options:
        - "OCR Engine"
        - "Layout Detection"
        - "Handwriting Recognition"
        - "API Server"
        - "Database"
        - "Vector Store"
        - "Frontend"
        - "Installation/Setup"
    validations:
      required: true
  
  - type: textarea
    id: description
    attributes:
      label: 📝 Bug Description
      description: A clear and concise description of what the bug is
      placeholder: "Describe what happened and what you expected to happen..."
    validations:
      required: true
  
  - type: textarea
    id: reproduction
    attributes:
      label: 🔄 Steps to Reproduce
      description: Detailed steps to reproduce the behavior
      placeholder: |
        1. Go to '...'
        2. Upload file '...'
        3. Click on '...'
        4. See error
    validations:
      required: true
  
  - type: textarea
    id: expected
    attributes:
      label: ✅ Expected Behavior
      description: What you expected to happen
      placeholder: "A clear description of what you expected to happen..."
    validations:
      required: true
      
  - type: textarea
    id: actual
    attributes:
      label: ❌ Actual Behavior
      description: What actually happened
      placeholder: "A clear description of what actually happened..."
    validations:
      required: true
  
  - type: textarea
    id: environment
    attributes:
      label: 🖥️ Environment
      description: Your system information
      placeholder: |
        - OS: [e.g. Windows