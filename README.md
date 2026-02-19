# Missing Person Face Recognition System

Face recognition system for identifying missing persons using InsightFace/ArcFace embeddings and FAISS vector search.

**Stack**: FastAPI, React 18, SQLite/PostgreSQL, Redis, FAISS, InsightFace

## Quick Start

```bash
chmod +x setup.sh && ./setup.sh
uvicorn main:app --reload
cd frontend && npm run dev 
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
pytest --cov=.
alembic revision --autogenerate -m "description"
```

## Performance

End-to-end search: <3s (detection ~100-500ms, embedding ~50-100ms, FAISS <100ms for 50k vectors)

## Troubleshooting

- Lower `FACE_DETECTION_CONFIDENCE` for difficult images
- InsightFace models auto-download on first use
- Check Redis is running: `redis-server`

## License

MIT
