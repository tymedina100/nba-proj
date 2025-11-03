# API Documentation

The NBA-Proj API provides programmatic access to player projections, simulations, and edge analysis.

## Starting the API

```bash
make api
```

Default configuration:
- Host: `localhost`
- Port: `8000`
- Base URL: `http://localhost:8000/api/v1`

## Authentication

Currently, the API does not require authentication. For production deployments, consider implementing API keys or OAuth.

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

### Health Check

Check API status.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-10-28T12:00:00Z",
  "version": "1.0.0"
}
```

---

### Get Player Projection

Retrieve simulation results for a specific player and date.

**Endpoint:** `GET /projections/{player_id}`

**Parameters:**
- `player_id` (path, required): NBA player ID
- `date` (query, required): Game date (YYYY-MM-DD)
- `stat` (query, optional): Specific stat (pts, reb, ast). Default: all stats

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/projections/203999?date=2025-10-28&stat=pts"
```

**Example Response:**
```json
{
  "player_id": "203999",
  "player_name": "Nikola Jokic",
  "date": "2025-10-28",
  "opponent": "LAL",
  "home_away": "home",
  "projections": {
    "pts": {
      "mean": 27.3,
      "median": 27.0,
      "std": 6.8,
      "percentiles": {
        "10": 18.0,
        "25": 23.0,
        "50": 27.0,
        "75": 32.0,
        "90": 37.0
      },
      "probability": {
        "over_25_5": 0.62,
        "over_30_5": 0.38,
        "under_25_5": 0.38
      }
    }
  },
  "minutes": {
    "mean": 34.2,
    "median": 34.0,
    "std": 3.1
  },
  "confidence": "high"
}
```

---

### Get All Projections

Retrieve projections for all players on a given date.

**Endpoint:** `GET /projections`

**Parameters:**
- `date` (query, required): Game date (YYYY-MM-DD)
- `stat` (query, optional): Filter by stat (pts, reb, ast)
- `min_confidence` (query, optional): Minimum confidence level (low, medium, high)

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/projections?date=2025-10-28&stat=pts"
```

**Example Response:**
```json
{
  "date": "2025-10-28",
  "count": 150,
  "projections": [
    {
      "player_id": "203999",
      "player_name": "Nikola Jokic",
      "team": "DEN",
      "opponent": "LAL",
      "pts_mean": 27.3,
      "pts_median": 27.0
    },
    {
      "player_id": "2544",
      "player_name": "LeBron James",
      "team": "LAL",
      "opponent": "DEN",
      "pts_mean": 24.5,
      "pts_median": 24.0
    }
  ]
}
```

---

### Get Edges

Retrieve identified betting edges for a date.

**Endpoint:** `GET /edges`

**Parameters:**
- `date` (query, required): Game date (YYYY-MM-DD)
- `min_ev` (query, optional): Minimum expected value (default: 0.05)
- `min_confidence` (query, optional): Minimum confidence (low, medium, high)
- `stat` (query, optional): Filter by stat

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/edges?date=2025-10-28&min_ev=0.10"
```

**Example Response:**
```json
{
  "date": "2025-10-28",
  "count": 12,
  "edges": [
    {
      "player_id": "203999",
      "player_name": "Nikola Jokic",
      "stat": "pts",
      "line": 25.5,
      "side": "over",
      "market_odds": -110,
      "market_implied_prob": 0.524,
      "model_prob": 0.620,
      "edge": 0.096,
      "expected_value": 0.084,
      "kelly_fraction": 0.091,
      "confidence": "high",
      "recommendation": "bet"
    },
    {
      "player_id": "1628369",
      "player_name": "Jayson Tatum",
      "stat": "reb",
      "line": 8.5,
      "side": "over",
      "market_odds": -105,
      "market_implied_prob": 0.512,
      "model_prob": 0.615,
      "edge": 0.103,
      "expected_value": 0.091,
      "kelly_fraction": 0.098,
      "confidence": "high",
      "recommendation": "bet"
    }
  ]
}
```

---

### Run Custom Simulation

Run a simulation with custom parameters.

**Endpoint:** `POST /simulate`

**Request Body:**
```json
{
  "player_id": "203999",
  "date": "2025-10-28",
  "stat": "pts",
  "n_simulations": 10000,
  "adjustments": {
    "minutes_modifier": 1.0,
    "pace_modifier": 1.05,
    "matchup_factor": 1.1
  }
}
```

**Example Response:**
```json
{
  "player_id": "203999",
  "stat": "pts",
  "n_simulations": 10000,
  "results": {
    "mean": 28.5,
    "median": 28.0,
    "std": 7.1,
    "distribution": [22, 25, 27, 28, 30, 31, 33, 29, 26],
    "percentiles": {
      "5": 16.0,
      "10": 18.0,
      "25": 23.0,
      "50": 28.0,
      "75": 33.0,
      "90": 38.0,
      "95": 41.0
    }
  }
}
```

---

### Get Historical Performance

Retrieve backtesting results and historical accuracy.

**Endpoint:** `GET /backtest`

**Parameters:**
- `start_date` (query, required): Start date (YYYY-MM-DD)
- `end_date` (query, required): End date (YYYY-MM-DD)
- `stat` (query, optional): Filter by stat

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/backtest?start_date=2025-10-01&end_date=2025-10-28"
```

**Example Response:**
```json
{
  "start_date": "2025-10-01",
  "end_date": "2025-10-28",
  "n_games": 150,
  "metrics": {
    "calibration_score": 0.92,
    "brier_score": 0.18,
    "log_loss": 0.45,
    "roi": 0.087,
    "hit_rate": 0.541
  },
  "by_stat": {
    "pts": {
      "calibration": 0.94,
      "roi": 0.091
    },
    "reb": {
      "calibration": 0.89,
      "roi": 0.075
    },
    "ast": {
      "calibration": 0.91,
      "roi": 0.094
    }
  }
}
```

---

### Get Player Info

Retrieve player metadata and recent performance.

**Endpoint:** `GET /players/{player_id}`

**Example Response:**
```json
{
  "player_id": "203999",
  "name": "Nikola Jokic",
  "team": "DEN",
  "position": "C",
  "stats_last_10": {
    "pts": 26.8,
    "reb": 12.3,
    "ast": 9.1,
    "minutes": 33.5
  }
}
```

---

## Response Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Rate Limiting

Current implementation does not enforce rate limits. For production, implement rate limiting based on your requirements.

## Error Response Format

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2025-10-28T12:00:00Z"
}
```

## WebSocket Support (Future)

Real-time updates for live games will be available via WebSocket connections:

```
ws://localhost:8000/ws/live
```

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Get projection
response = requests.get(
    f"{BASE_URL}/projections/203999",
    params={"date": "2025-10-28", "stat": "pts"}
)
projection = response.json()

print(f"Mean: {projection['projections']['pts']['mean']}")
print(f"P(>25.5): {projection['projections']['pts']['probability']['over_25_5']}")

# Get edges
response = requests.get(
    f"{BASE_URL}/edges",
    params={"date": "2025-10-28", "min_ev": 0.10}
)
edges = response.json()

for edge in edges['edges']:
    print(f"{edge['player_name']} {edge['stat']} {edge['side']} {edge['line']}: +EV {edge['expected_value']:.3f}")
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Get projection
const response = await fetch(
  `${BASE_URL}/projections/203999?date=2025-10-28&stat=pts`
);
const projection = await response.json();

console.log(`Mean: ${projection.projections.pts.mean}`);

// Get edges
const edgesResponse = await fetch(
  `${BASE_URL}/edges?date=2025-10-28&min_ev=0.10`
);
const edges = await edgesResponse.json();

edges.edges.forEach(edge => {
  console.log(`${edge.player_name} ${edge.stat} ${edge.side} ${edge.line}: +EV ${edge.expected_value.toFixed(3)}`);
});
```

### cURL

```bash
# Get today's projections
curl "http://localhost:8000/api/v1/projections?date=$(date +%Y-%m-%d)"

# Get high-value edges
curl "http://localhost:8000/api/v1/edges?date=$(date +%Y-%m-%d)&min_ev=0.08"

# Custom simulation
curl -X POST "http://localhost:8000/api/v1/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": "203999",
    "date": "2025-10-28",
    "stat": "pts",
    "n_simulations": 50000
  }'
```

## Support

For API issues or questions, open an issue on GitHub or refer to the main documentation.