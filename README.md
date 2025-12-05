# Chess Analytics Website

A Flask-based web application that analyzes chess games from Chess.com. Users can enter their Chess.com username and date range to get detailed statistics and insights about their chess performance.

## Features

- 📊 Comprehensive game statistics (wins, losses, draws, win rate)
- 🎨 Performance analysis by color (white/black)
- ⏱️ Performance breakdown by time control
- 🎯 Clean, modern, responsive UI
- 🚀 Fast API integration with Chess.com
- 💾 Built-in caching to reduce API calls

## Technology Stack

- **Backend**: Flask (Python 3.8+)
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **API**: Chess.com Public API
- **Testing**: Playwright (for E2E tests)

## Project Structure

```
chesstic_v2/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── routes/               # Route blueprints
│   │   ├── __init__.py
│   │   ├── views.py          # HTML view routes
│   │   └── api.py            # API endpoints
│   ├── services/             # Business logic
│   │   ├── __init__.py
│   │   └── chess_service.py  # Chess.com API integration
│   ├── models/               # Data models
│   │   └── __init__.py
│   └── utils/                # Utility functions
│       ├── __init__.py
│       ├── validators.py     # Input validation
│       └── cache.py          # Caching decorator
├── static/
│   ├── css/
│   │   └── style.css         # Styles
│   └── js/
│       └── main.js           # Frontend logic
├── templates/
│   ├── index.html            # Main page
│   └── analytics.html        # Analytics page
├── tests/                    # Test files
├── .github/
│   ├── agents/               # AI agent configurations
│   │   ├── prd-agent.md
│   │   ├── engineer-agent.md
│   │   └── playwright-tester-agent.md
│   └── copilot-instructions.md
├── config.py                 # Configuration
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone or navigate to the repository**
   ```powershell
   cd C:\anaconda_backup\Project\chesstic_v2
   ```

2. **Create a virtual environment**
   ```powershell
   python -m venv venv
   ```

3. **Activate the virtual environment**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Create environment file**
   ```powershell
   Copy-Item .env.example .env
   ```
   
   Edit `.env` and update the `SECRET_KEY` with a secure random string:
   ```
   SECRET_KEY=your-very-secret-key-here
   ```

### Running the Application

1. **Start the Flask development server**
   ```powershell
   python run.py
   ```

2. **Open your browser**
   
   Navigate to: `http://localhost:5000`

The application should now be running! Enter your Chess.com username and date range to analyze your games.

## Usage

1. **Enter your Chess.com username** in the input field
2. **Select start and end dates** for the analysis period
3. **Click "Analyze Games"** to fetch and analyze your games
4. **View your statistics** including:
   - Total games played
   - Wins, losses, and draws
   - Win rate percentage
   - Performance by color (white vs black)
   - Performance by time control

## API Endpoints

### POST `/api/analyze`
Analyze games for a given username and date range.

**Request Body:**
```json
{
  "username": "chess_username",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

**Response:**
```json
{
  "username": "chess_username",
  "total_games": 50,
  "statistics": {
    "wins": 25,
    "losses": 20,
    "draws": 5,
    "win_rate": 50.0,
    "by_color": { ... },
    "by_time_control": { ... }
  }
}
```

### GET `/api/player/<username>`
Get player profile information.

**Response:**
```json
{
  "username": "chess_username",
  "player_id": 123456,
  ...
}
```

## AI Agents

This project uses three specialized AI agents to assist with development:

### 1. PRD Agent
Creates and maintains Product Requirements Documents. Use this agent when:
- Planning new features
- Documenting requirements
- Clarifying specifications

**Usage:** Reference `.github/agents/prd-agent.md`

### 2. Engineer Agent
Implements features and fixes bugs. Use this agent when:
- Developing new features
- Fixing bugs
- Refactoring code
- Writing tests

**Usage:** Reference `.github/agents/engineer-agent.md`

### 3. Playwright Tester Agent
Creates and maintains end-to-end tests using Playwright. Use this agent when:
- Writing E2E tests
- Testing user flows
- Debugging test failures

**Usage:** Reference `.github/agents/playwright-tester-agent.md`

## Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions small and focused

### Testing
- Write unit tests for services and utilities
- Use Playwright for end-to-end testing
- Test error scenarios and edge cases

### Git Workflow
1. Create feature branch from main
2. Make changes with clear commits
3. Test locally
4. Submit pull request

## Configuration

Key configuration options in `config.py`:

- `SECRET_KEY`: Flask secret key for sessions
- `CORS_ORIGINS`: Allowed CORS origins
- `CACHE_DEFAULT_TIMEOUT`: Cache TTL in seconds
- `RATE_LIMIT_PER_MINUTE`: API rate limit

## Troubleshooting

### Issue: Import errors
**Solution:** Ensure virtual environment is activated and dependencies are installed

### Issue: API returns 404
**Solution:** Verify the Chess.com username is correct

### Issue: Slow response times
**Solution:** Caching is enabled by default. First request may be slower.

### Issue: CORS errors
**Solution:** Update `CORS_ORIGINS` in `.env` or `config.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

## License

This project is for educational and personal use. Chess.com data is accessed via their public API.

## Acknowledgments

- Chess.com for providing the public API
- Flask framework and community
- GitHub Copilot for AI-assisted development

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Consult AI agents for development help

---

**Note:** This application uses the Chess.com Public API. Please respect their rate limits and terms of service.
