# Missing Person Face Recognition System

A face recognition system for identifying missing persons. Upload a photo to search against a database of missing persons, or manage records through the admin panel.

## Features

- Face search using InsightFace/ArcFace embeddings
- Admin panel for managing missing person records
- JWT authentication for admin operations
- FAISS vector database for fast similarity search
- Redis caching for improved performance
- Complete audit logging

## Tech Stack

**Backend**: Python 3.11, FastAPI, PostgreSQL, Redis, FAISS, InsightFace  
**Frontend**: React 18, TypeScript, Vite  
**Deployment**: Docker, Docker Compose

## Quick Start

```bash
# Automated setup
chmod +x setup.sh && ./setup.sh

# Start services
docker-compose up -d

# Start backend
uvicorn main:app --reload

# Start frontend (new terminal)
cd frontend && npm run dev
```

**Access**:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Default credentials**: `admin` / `admin123` (change in production!)

## Project Structure

```
├── api/                    # API endpoints
├── database/              # SQLAlchemy models & migrations
├── models/                # Pydantic schemas
├── services/              # Business logic (face detection, embeddings, etc.)
├── frontend/              # React frontend
├── tests/                 # Tests
├── main.py               # FastAPI app
└── config.py             # Configuration
```

## API Endpoints

**Public**:
- `POST /api/v1/search` - Search by face image

**Auth**:
- `POST /api/v1/auth/register` - Register admin
- `POST /api/v1/auth/login` - Login

**Admin** (requires JWT):
- `POST /api/v1/admin/missing-persons` - Upload person
- `GET /api/v1/admin/missing-persons` - List persons
- `DELETE /api/v1/admin/missing-persons/{id}` - Delete person

## Configuration

Key settings in `.env`:

```bash
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
FACE_DETECTION_CONFIDENCE=0.9
DEFAULT_MATCH_THRESHOLD=0.6
```

## Development

```bash
# Run tests
pytest

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Code formatting
black .
```

## Usage Examples

**Search**:
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -F "image=@photo.jpg" \
  -F "threshold=0.6"
```

**Upload** (admin):
```bash
# Get token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# Upload person
curl -X POST "http://localhost:8000/api/v1/admin/missing-persons" \
  -H "Authorization: Bearer $TOKEN" \
  -F "name=John Doe" \
  -F "date_reported=2024-01-15T10:00:00Z" \
  -F "contact_info=555-0123" \
  -F "photos=@photo.jpg"
```

## Performance

- Face detection: ~100-500ms
- Embedding generation: ~50-100ms
- Vector search: <100ms (50k embeddings)
- End-to-end: <3 seconds

## Troubleshooting

**Database errors**: Check PostgreSQL is running with `docker-compose ps`  
**Face detection issues**: Ensure clear, frontal faces with good lighting  
**Model loading**: InsightFace models download on first use (requires internet)

## License

MIT
