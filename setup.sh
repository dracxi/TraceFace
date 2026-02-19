#!/bin/bash

set -e

echo "Setting up Missing Person Face Recognition System..."

# Create directories
mkdir -p uploads data

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file"
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if using PostgreSQL and verify connection
if grep -q "postgresql://" .env; then
    echo "Detected PostgreSQL configuration..."
    
    # Check if PostgreSQL is installed
    if ! command -v psql &> /dev/null; then
        echo "⚠️  PostgreSQL client not found in PATH."
        echo "If PostgreSQL is installed, ensure psql is accessible."
        echo "Otherwise, install with: sudo apt install postgresql postgresql-contrib"
        echo "Or switch to SQLite by changing DATABASE_URL in .env to:"
        echo "  DATABASE_URL=sqlite:///./missing_persons.db"
    else
        echo "✓ PostgreSQL client detected"
        
        # Extract database connection details from DATABASE_URL
        DB_NAME=$(grep DATABASE_URL .env | cut -d'/' -f4 | cut -d'?' -f1)
        echo "Database configured: $DB_NAME"
    fi
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Create default admin user
echo "Creating default admin user..."
python -c "
from database.connection import SessionLocal
from services.auth import create_admin_user
from models.schemas import AdminUserCreate

db = SessionLocal()
try:
    user = AdminUserCreate(username='admin', password='admin123', email='admin@example.com')
    create_admin_user(db, user)
    print('✓ Admin user created (username: admin, password: admin123)')
    print('⚠️  Change this password in production!')
except Exception as e:
    print(f'Admin user may already exist: {e}')
finally:
    db.close()
"

# Install frontend dependencies
if [ -d "frontend" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

echo ""
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. source venv/bin/activate"
echo "  2. uvicorn main:app --reload"
echo "  3. cd frontend && npm run dev (in a new terminal)"
echo ""
echo "Access:"
echo "  API: http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo "  Frontend: http://localhost:3000"
