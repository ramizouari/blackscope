# Blackscope Backend

FastAPI-based backend service for AI-powered website quality assurance.

## Overview

The backend orchestrates multiple AI agents to perform comprehensive website analysis including accessibility checks, HTML compliance validation, UI/UX analysis, and automated test scenario generation and execution.

## Architecture

### Multi-Agent Orchestration

The backend uses an **Orchestrator** pattern that coordinates specialized evaluation nodes:

```python
Orchestrator([
    AccessCheckNode,           # HTTP connectivity checks
    DriverAccessNode,          # Browser-based access
    HtmlParsingNode,           # HTML structure parsing
    HtmlComplianceNode,        # Standards compliance
    UIAnalyzerNode,            # UI/UX evaluation
    TestScenarioGenerationNode,# AI test generation
    TestScenarioExecutionNode  # Selenium automation
])
```

### Key Components

- **Evaluators** (`services/evaluators/`): Specialized agents for different QA aspects
- **LLM Integration** (`services/llm/`): AI model providers (DeepSeek, OpenAI, HuggingFace)
- **Configuration** (`config.py`): Environment-based settings management
- **API** (`main.py`): FastAPI endpoints and streaming responses

## Installation

### Using uv (Recommended)

```bash
# Install uv
pip install uv

# Install dependencies
uv pip install -r pyproject.toml
```

### Using pip

```bash
pip install -e .
```

### Development Dependencies

```bash
uv pip install -r pyproject.toml --group dev
```

## Configuration

Create a `.env` file in the backend directory:

```env
# AI Model Settings
DEFAULT_MODEL=deepseek-chat
DEFAULT_VL_MODEL=Qwen/Qwen3-VL-30B-A3B-Instruct

# Browser Configuration
HEADLESS_BROWSER=true

# API Keys (at least one required)
DEEPSEEK_API_KEY=sk-xxxxx
OPENAI_API_KEY=sk-xxxxx
HUGGINGFACEHUB_API_TOKEN=hf_xxxxx

# Application Settings
MODE=dev
CLIENT_HOST=http://localhost:5173
```

### Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_MODEL` | Primary LLM for text tasks | `deepseek-chat` |
| `DEFAULT_VL_MODEL` | Vision-Language model for screenshots | `Qwen/Qwen3-VL-30B-A3B-Instruct` |
| `HEADLESS_BROWSER` | Run Firefox without GUI | `true` |
| `MODE` | Environment mode (`dev`/`prod`) | `dev` |
| `CLIENT_HOST` | Frontend origin for CORS | `None` |

## Running

### Development Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```bash
docker build -t blackscope-backend .
docker run -p 8000:8000 --env-file .env blackscope-backend
```

## API Reference

### `POST /qa`

Performs comprehensive QA analysis on a URL.

**Request Body:**
```json
{
  "url": "https://example.com"
}
```

**Response:**

NDJSON stream of evaluation updates:

```json
{"type": "update", "content": {"agent": "AccessCheckNode", "status": "running", ...}}
{"type": "update", "content": {"agent": "HtmlParsingNode", "status": "completed", ...}}
...
```

**Message Types:**
- `status`: Agent execution status updates
- `result`: Agent completion with findings
- `error`: Error messages

### `GET /health`

Health check endpoint returning application status.

**Response:**
```json
{"status": "UP"}
```

### `GET /heartbeat`

Simple heartbeat for load balancer health checks.

**Response:** `200 OK`

## Development

### Project Structure

```
backend/
├── services/
│   ├── evaluators/
│   │   ├── base.py              # Orchestrator & base classes
│   │   ├── connectivity.py      # Access check nodes
│   │   ├── drivers.py           # Selenium driver factory
│   │   ├── html/
│   │   │   ├── compliance.py    # HTML standards validation
│   │   │   └── parser.py        # HTML parsing
│   │   └── qa/
│   │       ├── scenarios/
│   │       │   ├── generation.py # AI test generation
│   │       │   └── execution.py  # Selenium execution
│   │       └── ui.py             # UI/UX analysis
│   └── llm/                      # LLM provider integrations
├── config.py                     # Configuration management
├── main.py                       # FastAPI application
└── pyproject.toml                # Dependencies
```

### Adding a New Evaluator

1. Create a new node class inheriting from `EvaluatorNode`
2. Implement the `evaluate()` method
3. Yield `StreamableMessage` objects for progress updates
4. Add the node to the Orchestrator in `main.py`

Example:

```python
from services.evaluators.base import EvaluatorNode
from services.evaluators.messages import StreamableMessage


class MyCustomNode(EvaluatorNode):
    def evaluate(self, url: str, session, driver):
        yield StreamableMessage(
            agent="MyCustomNode",
            status="running",
            message="Starting custom analysis"
        )

        # Perform analysis
        result = analyze(url)

        yield StreamableMessage(
            agent="MyCustomNode",
            status="completed",
            result=result
        )
```

### Code Quality

```bash
# Format code
black .

# Run in Jupyter for experimentation
jupyter notebook
```

## Dependencies

### Core
- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **pydantic** - Data validation
- **pydantic-settings** - Configuration
- **requests** - HTTP client

### AI/ML
- **langchain** - LLM orchestration
- **deepseek** - DeepSeek API integration
- **openai** - OpenAI API integration
- **huggingface** - HuggingFace models

### Web Automation
- **selenium** - Browser automation
- **webdriver-manager** - Automatic driver management
- **beautifulsoup4** - HTML parsing
- **pillow** - Screenshot handling

## Browser Configuration

### Geckodriver

The application requires **geckodriver** for Firefox automation:

```bash
# Install geckodriver (Linux)
wget https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-linux64.tar.gz
tar -xzf geckodriver-v0.35.0-linux64.tar.gz
sudo mv geckodriver /usr/local/bin/

# Verify installation
geckodriver --version
```

### Firefox

Install Firefox ESR for stability:

```bash
# Debian/Ubuntu
sudo apt-get install firefox-esr

# Fedora
sudo dnf install firefox
```

## Troubleshooting

### Selenium/Browser Issues

**Error:** `selenium.common.exceptions.WebDriverException: Message: 'geckodriver' executable needs to be in PATH`

**Solution:** Install geckodriver and ensure it's in your system PATH.

**Error:** `selenium.common.exceptions.SessionNotCreatedException: Message: Unable to find a matching set of capabilities`

**Solution:** Update Firefox and geckodriver to compatible versions.

### Memory Issues with Headless Browser

If experiencing browser crashes, increase shared memory:

```bash
# When running in Docker, mount larger /dev/shm
docker run -v /dev/shm:/dev/shm ...
```

### API Key Errors

**Error:** `ValueError: No API key found`

**Solution:** Ensure at least one AI provider API key is set in `.env`.

### CORS Issues

**Error:** `Access to fetch at 'http://localhost:8000' from origin 'http://localhost:5173' has been blocked`

**Solution:** Set `CLIENT_HOST` in `.env` to match your frontend origin.

## Performance Tips

1. **Use connection pooling**: The orchestrator reuses `requests.Session` and Selenium driver
2. **Stream responses**: NDJSON streaming provides immediate feedback
3. **Parallel evaluation**: Agents run sequentially but can be parallelized if needed
4. **Headless mode**: Always use `HEADLESS_BROWSER=true` in production

## Security Considerations

- Never commit `.env` files with API keys
- Use environment variables in production
- Validate and sanitize URL inputs
- Implement rate limiting for the `/qa` endpoint
- Use HTTPS in production deployments

## Contributing

When contributing to the backend:

1. Follow PEP 8 style guidelines
2. Format code with `black`
3. Add type hints to all functions
4. Document new evaluator nodes
5. Update this README with new features

## License

[Add your license here]
