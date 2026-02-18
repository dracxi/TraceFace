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

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
python -c "from database.connection import Base, engine; Base.metadata.create_all(bind=engine)"

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
echo "  1. docker-compose up -d"
echo "  2. uvicorn main:app --reload"
echo "  3. cd frontend && npm run dev"
echo ""
echo "Access:"
echo "  API: http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo "  Frontend: http://localhost:3000"
