# Trickster Oracle Backend

Educational probabilistic analytics engine for sports events.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run server
uvicorn app.main:app --reload
```

## Endpoints

- `GET /health` - Health check
- `GET /version` - API version info
- `POST /simulate` - Run Monte Carlo simulation (coming soon)

## Testing

```bash
pytest
```
