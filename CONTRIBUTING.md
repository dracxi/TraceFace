# Contributing

Thanks for your interest in contributing to the Missing Person Face Recognition System!

## Development Setup

1. Fork and clone the repository
2. Run the setup script: `./setup.sh`
3. Start services: `docker-compose up -d`
4. Start the backend: `uvicorn main:app --reload`
5. Start the frontend: `cd frontend && npm run dev`

## Code Style

**Python**:
- Follow PEP 8
- Use type hints
- Keep functions focused and small
- Format with `black .`

**TypeScript**:
- Use functional components with hooks
- Keep components small and reusable
- Format with Prettier

## Testing

Run tests before submitting:
```bash
pytest
```

Add tests for new features in the `tests/` directory.

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Add tests
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request

## Commit Messages

Use clear, descriptive commit messages:
- `feat: add face similarity threshold adjustment`
- `fix: resolve database connection timeout`
- `docs: update API endpoint documentation`

## Questions?

Open an issue for discussion before starting major changes.
