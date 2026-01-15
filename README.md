# Blackscope

**AI-Powered Website Quality Assurance Platform**

Blackscope is an automated web quality assurance tool that leverages AI to analyze websites for accessibility, HTML compliance, UI/UX issues, and functional testing through intelligent test scenario generation and execution.

## Features

- **🔍 Accessibility Analysis**: Automated checks for web accessibility standards
- **📝 HTML Compliance**: Validates HTML structure and adherence to web standards
- **🎨 UI/UX Analysis**: AI-powered evaluation of user interface and experience
- **🧪 Automated Testing**: Generates and executes test scenarios using Selenium
- **🤖 Multi-Agent Architecture**: Orchestrated AI agents for comprehensive website evaluation
- **📊 Real-time Streaming**: Live progress updates via NDJSON streaming
- **🌐 Headless Browser Support**: Firefox-based automation with geckodriver

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  React Frontend │ ◄─────► │  FastAPI Backend │
│   (Vite + TS)   │  HTTP   │   (Python 3.12)  │
└─────────────────┘         └──────────────────┘
                                     │
                            ┌────────┴────────┐
                            │   AI Evaluators │
                            ├─────────────────┤
                            │ • AccessCheck   │
                            │ • HTMLParser    │
                            │ • Compliance    │
                            │ • UIAnalyzer    │
                            │ • ScenarioGen   │
                            │ • ScenarioExec  │
                            └─────────────────┘
```

## Tech Stack

### Backend
- **FastAPI**: High-performance async web framework
- **LangChain**: AI orchestration with support for DeepSeek, OpenAI, and HuggingFace
- **Selenium**: Browser automation with Firefox
- **BeautifulSoup4**: HTML parsing and analysis
- **Pydantic**: Data validation and settings management

### Frontend
- **React 19**: Modern UI framework
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool with HMR
- **CSS3**: Custom styling with flexbox/grid

## Quick Start

### Prerequisites
- Docker & Docker Compose
- API keys for AI services (DeepSeek, OpenAI, or HuggingFace)

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/ramizouari/blackscope.git
   cd blackscope
   ```

2. **Configure environment**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   ```

3. **Start services**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development

#### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install uv
uv pip install -r pyproject.toml
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Configuration

Create `backend/.env` with the following variables:

```env
# AI Model Configuration
DEFAULT_MODEL=deepseek-chat
DEFAULT_VL_MODEL=Qwen/Qwen3-VL-30B-A3B-Instruct
HEADLESS_BROWSER=true

# API Keys (provide at least one)
DEEPSEEK_API_KEY=your_deepseek_key
OPENAI_API_KEY=your_openai_key
HUGGINGFACEHUB_API_TOKEN=your_hf_token

# Application
MODE=dev  # or "prod"
CLIENT_HOST=http://localhost:5173
```

## API Endpoints

### `POST /qa`
Performs comprehensive quality assurance on a provided URL.

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:** NDJSON stream with real-time updates from each evaluation agent.

### `GET /health`
Health check endpoint.

### `GET /heartbeat`
Simple heartbeat endpoint.

### `GET /docs`
Interactive API documentation (Swagger UI).

## Project Structure

```
URL-QA/
├── backend/
│   ├── services/
│   │   ├── evaluators/       # AI evaluation agents
│   │   └── llm/               # LLM integrations
│   ├── config.py              # Configuration management
│   ├── main.py                # FastAPI application
│   ├── pyproject.toml         # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```


## Docker Commands

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild specific service
docker-compose build backend
docker-compose up backend
```

## Troubleshooting

### Browser Issues
- Ensure `/dev/shm` has sufficient size for headless Firefox
- Check geckodriver version compatibility with Firefox ESR

### API Key Errors
- Verify at least one AI provider API key is set in `.env`
- Check API key validity and quota limits

### Port Conflicts
- Change ports in `docker-compose.yml` if 80 or 8000 are in use

## License

[Add your license here]

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting PRs.

## Support

For issues and questions, please open a GitHub issue.
