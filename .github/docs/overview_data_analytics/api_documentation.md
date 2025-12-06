# API Documentation - Enhanced Chess Analytics

## Base URL
```
http://localhost:5000/api
```

---

## Endpoints

### 1. Detailed Analytics (NEW)

**Endpoint:** `POST /api/analyze/detailed`

**Description:** Perform comprehensive analysis on chess games with 8 detailed analytics sections.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "username": "jay_fh",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "timezone": "America/New_York"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | Yes | Chess.com username (3-25 characters, alphanumeric with hyphens/underscores) |
| start_date | string | Yes | Start date in YYYY-MM-DD format |
| end_date | string | Yes | End date in YYYY-MM-DD format (max 1 year from start_date) |
| timezone | string | No | IANA timezone string (default: "UTC"). Examples: "America/New_York", "Europe/London", "Asia/Tokyo" |

#### Response

**Success (200 OK):**
```json
{
  "username": "jay_fh",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "timezone": "America/New_York",
  "total_games": 150,
  "status": "success",
  "sections": {
    "overall_performance": {
      "daily_stats": [
        {
          "date": "2025-01-01",
          "wins": 3,
          "losses": 2,
          "draws": 1
        }
      ]
    },
    "color_performance": {
      "white": {
        "daily_stats": [...],
        "win_rate": 52.5,
        "total": {
          "wins": 40,
          "losses": 30,
          "draws": 6
        }
      },
      "black": {
        "daily_stats": [...],
        "win_rate": 48.3,
        "total": {
          "wins": 36,
          "losses": 32,
          "draws": 6
        }
      }
    },
    "elo_progression": {
      "data_points": [
        {
          "date": "2025-01-01",
          "rating": 1500
        }
      ],
      "rating_change": 25
    },
    "termination_wins": {
      "checkmate": {
        "count": 25,
        "percentage": 50.0
      },
      "timeout": {
        "count": 15,
        "percentage": 30.0
      },
      "resignation": {
        "count": 10,
        "percentage": 20.0
      }
    },
    "termination_losses": {
      "checkmate": {
        "count": 20,
        "percentage": 40.0
      },
      "timeout": {
        "count": 20,
        "percentage": 40.0
      },
      "resignation": {
        "count": 10,
        "percentage": 20.0
      }
    },
    "opening_performance": {
      "best_openings": [
        {
          "name": "Italian Game",
          "games": 12,
          "wins": 9,
          "losses": 2,
          "draws": 1,
          "win_rate": 75.0
        }
      ],
      "worst_openings": [
        {
          "name": "French Defense",
          "games": 8,
          "wins": 2,
          "losses": 5,
          "draws": 1,
          "win_rate": 25.0
        }
      ]
    },
    "opponent_strength": {
      "lower_rated": {
        "games": 40,
        "wins": 28,
        "losses": 8,
        "draws": 4,
        "win_rate": 70.0
      },
      "similar_rated": {
        "games": 60,
        "wins": 28,
        "losses": 26,
        "draws": 6,
        "win_rate": 46.67
      },
      "higher_rated": {
        "games": 50,
        "wins": 20,
        "losses": 28,
        "draws": 2,
        "win_rate": 40.0
      }
    },
    "time_of_day": {
      "morning": {
        "games": 45,
        "wins": 25,
        "losses": 15,
        "draws": 5,
        "win_rate": 55.56
      },
      "afternoon": {
        "games": 60,
        "wins": 30,
        "losses": 25,
        "draws": 5,
        "win_rate": 50.0
      },
      "night": {
        "games": 45,
        "wins": 21,
        "losses": 22,
        "draws": 2,
        "win_rate": 46.67
      }
    }
  }
}
```

**Error Responses:**

**400 Bad Request - Missing JSON Body:**
```json
{
  "error": "Request body must be JSON",
  "status": "error"
}
```

**400 Bad Request - Invalid Username:**
```json
{
  "error": "Invalid username format. Username must be 3-25 characters, alphanumeric with hyphens or underscores",
  "status": "error"
}
```

**400 Bad Request - Invalid Date Range:**
```json
{
  "error": "Invalid date range. Dates must be in YYYY-MM-DD format, start must be before end, maximum 1 year range, and dates cannot be in the future",
  "status": "error"
}
```

**400 Bad Request - Invalid Timezone:**
```json
{
  "error": "Invalid timezone: Invalid/Timezone. Please provide a valid IANA timezone string (e.g., America/New_York, UTC, Europe/London)",
  "status": "error"
}
```

**404 Not Found - User Not Found:**
```json
{
  "error": "User \"jay_fh\" not found on Chess.com",
  "status": "error"
}
```

**503 Service Unavailable - API Error:**
```json
{
  "error": "Failed to connect to Chess.com API. Please try again later",
  "status": "error"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error",
  "status": "error",
  "details": "Error message"
}
```

#### Examples

**cURL:**
```bash
curl -X POST http://localhost:5000/api/analyze/detailed \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jay_fh",
    "start_date": "2025-01-01",
    "end_date": "2025-03-31",
    "timezone": "America/New_York"
  }'
```

**Python (requests):**
```python
import requests

url = "http://localhost:5000/api/analyze/detailed"
payload = {
    "username": "jay_fh",
    "start_date": "2025-01-01",
    "end_date": "2025-03-31",
    "timezone": "America/New_York"
}

response = requests.post(url, json=payload)
data = response.json()

print(f"Total games: {data['total_games']}")
```

**JavaScript (Fetch API):**
```javascript
const url = 'http://localhost:5000/api/analyze/detailed';
const payload = {
  username: 'jay_fh',
  start_date: '2025-01-01',
  end_date: '2025-03-31',
  timezone: 'America/New_York'
};

fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(payload)
})
  .then(response => response.json())
  .then(data => {
    console.log(`Total games: ${data.total_games}`);
    console.log('Sections:', data.sections);
  })
  .catch(error => console.error('Error:', error));
```

---

### 2. Basic Analytics (Existing)

**Endpoint:** `POST /api/analyze`

**Description:** Analyze chess games with basic statistics.

#### Request

**Body:**
```json
{
  "username": "jay_fh",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31"
}
```

#### Response

**Success (200 OK):**
```json
{
  "username": "jay_fh",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "total_games": 150,
  "statistics": {
    "wins": 76,
    "losses": 62,
    "draws": 12,
    "win_rate": 50.67,
    "by_color": {
      "white": {
        "wins": 40,
        "losses": 30,
        "draws": 6
      },
      "black": {
        "wins": 36,
        "losses": 32,
        "draws": 6
      }
    },
    "by_time_control": {
      "600": {
        "wins": 45,
        "losses": 35,
        "draws": 8
      }
    }
  },
  "games": [...]
}
```

---

### 3. Player Profile

**Endpoint:** `GET /api/player/<username>`

**Description:** Get player profile information from Chess.com.

#### Request

**Path Parameter:**
- `username`: Chess.com username

#### Response

**Success (200 OK):**
```json
{
  "@id": "https://api.chess.com/pub/player/jay_fh",
  "url": "https://www.chess.com/member/jay_fh",
  "username": "jay_fh",
  "player_id": 123456,
  "title": null,
  "status": "premium",
  "name": "Full Name",
  "avatar": "https://...",
  "location": "Location",
  "country": "https://api.chess.com/pub/country/US",
  "joined": 1234567890,
  "last_online": 1234567890,
  "followers": 100,
  "is_streamer": false,
  "verified": false
}
```

**Example:**
```bash
curl http://localhost:5000/api/player/jay_fh
```

---

## Rate Limiting

Currently, rate limiting is handled through caching:
- Player profiles: Cached for 5 minutes
- Game data: Cached for 1 minute
- Analysis results: Not cached (calculated on demand)

Future implementation will include:
- 30 requests per minute per IP address
- 429 Too Many Requests response when limit exceeded

---

## Error Handling

All endpoints follow consistent error response format:

```json
{
  "error": "Human-readable error message",
  "status": "error",
  "details": "Technical details (optional)"
}
```

**HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (validation error)
- `404`: Not Found (user/resource not found)
- `500`: Internal Server Error
- `503`: Service Unavailable (external API error)

---

## Performance Guidelines

- **Target response time:** < 6 seconds for 3-month analysis
- **Actual performance:**
  - 100 games: ~0.5 seconds
  - 500 games: ~2 seconds
  - 1000 games: ~5 seconds

**Tips for optimal performance:**
- Use shorter date ranges when possible
- Specify timezone to avoid UTC conversion overhead
- Cache results on client-side for repeated requests

---

## Data Accuracy Notes

1. **Opening Names:** Extracted from PGN headers. Some games may show "Unknown" if PGN data is incomplete.

2. **Termination Types:** Categorized into: checkmate, timeout, resignation, abandoned, agreed, repetition, insufficient, stalemate, other.

3. **Opponent Strength Categories:**
   - Lower rated: Opponent rating < Player rating - 100
   - Similar rated: Player rating ± 100
   - Higher rated: Opponent rating > Player rating + 100

4. **Time of Day Categories:**
   - Morning: 6:00 AM - 2:00 PM
   - Afternoon: 2:00 PM - 10:00 PM
   - Night: 10:00 PM - 6:00 AM
   - All times converted to user's specified timezone

5. **Opening Performance:**
   - Only openings with 3+ games are included in rankings
   - Top/bottom 5 openings displayed based on win rate

---

## Changelog

### Version 1.1 (Milestone 2 - December 6, 2025)
- Added `/api/analyze/detailed` endpoint with 8 analytics sections
- Added timezone support for time-based analysis
- Improved error messages with detailed validation feedback
- Added comprehensive input validation
- Added user existence check before processing

### Version 1.0 (Initial Release)
- Basic `/api/analyze` endpoint
- `/api/player/<username>` endpoint
- Simple caching mechanism
