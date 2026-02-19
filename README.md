# Missing Person Face Recognition System

Face recognition system for identifying missing persons using InsightFace/ArcFace embeddings and FAISS vector search.

**Stack**: FastAPI, React 18, SQLite/PostgreSQL, Redis, FAISS, InsightFace

## Quick Start

```bash
chmod +x setup.sh && ./setup.sh
uvicorn main:app --reload
cd frontend && npm run dev  # new terminal
```

Access at http://localhost:5173 | Default: `admin` / `admin123`

## API

Docs: http://localhost:8000/docs

**Public**: `POST /api/v1/search`  
**Auth**: `POST /api/v1/auth/login`  
**Admin**: CRUD on `/api/v1/admin/missing-persons` (JWT required)

## Configuration

See `.env.example`. Key settings:

```bash
DATABASE_URL=sqlite:///./missing_persons.db  # or postgresql://...
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-in-production
FACE_DETECTION_CONFIDENCE=0.9
DEFAULT_MATCH_THRESHOLD=0.6
```

For PostgreSQL: `createdb missing_persons_db && alembic upgrade head`

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html

# Database migrations (if using PostgreSQL)
alembic upgrade head
alembic revision --autogenerate -m "description"

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install
```

## Performance

- Face detection: ~100-500ms
- Embedding generation: ~50-100ms
- Vector search: <100ms (50k embeddings)
- End-to-end: <3 seconds

## Troubleshooting

**Database errors**: 
- SQLite: Check file permissions in project directory
- PostgreSQL: Verify PostgreSQL is running and credentials are correct

**Redis connection issues**: Ensure Redis server is running (`redis-server`)

**Face detection issues**: 
- Ensure clear, frontal faces with good lighting
- Adjust `FACE_DETECTION_CONFIDENCE` in `.env` (lower = more permissive)

**Model loading**: InsightFace models download on first use (requires internet connection)

**Frontend not connecting**: Check `ALLOWED_ORIGINS` includes your frontend URL (default: http://localhost:5173)

## License

MIT
