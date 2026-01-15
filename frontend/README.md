# Blackscope Frontend

React-based web interface for the Blackscope AI-powered website quality assurance platform.

## Overview

The frontend provides an interactive dashboard for submitting URLs for analysis and viewing real-time evaluation results from multiple AI agents. It features a modern, responsive UI with streaming updates and comprehensive metrics visualization.

## Features

- **🎯 URL Submission**: Simple form interface for website analysis requests
- **📊 Agent Dashboard**: Real-time visualization of agent progress and status
- **✅ Test Scenario Display**: Interactive test results with pass/fail indicators
- **📈 Metrics Display**: Comprehensive quality metrics visualization
- **🔄 Live Updates**: NDJSON streaming for real-time feedback
- **🎨 Modern UI**: Clean, responsive design with custom CSS

## Tech Stack

- **React 19**: Latest React with concurrent features
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool with HMR (using Rolldown)
- **CSS3**: Custom styling with modern layout techniques
- **Fetch API**: Native HTTP client for backend communication

## Installation

### Prerequisites
- Node.js 20+ and npm

### Install Dependencies

```bash
npm install
```

## Development

### Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

### Lint Code

```bash
npm run lint
```

## Configuration

### Backend API URL

Update the API endpoint in your components if the backend is not running on `http://localhost:8000`:

```typescript
// In components that make API calls
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
```

Add to `.env.local`:

```env
VITE_BACKEND_URL=http://localhost:8000
```

## Components

### URLForm

Form component for submitting URLs for analysis.

**Props:**
- `onSubmit: (url: string) => void` - Callback when URL is submitted

**Usage:**
```tsx
<URLForm onSubmit={(url) => handleAnalysis(url)} />
```

### AgentDashboard

Displays real-time status of all evaluation agents.

**Props:**
- `agents: Agent[]` - Array of agent status objects

**Usage:**
```tsx
<AgentDashboard agents={agentStatuses} />
```

### TestScenarioList

Shows test scenario execution results.

**Props:**
- `scenarios: Scenario[]` - Array of test scenarios

**Usage:**
```tsx
<TestScenarioList scenarios={testResults} />
```

### MetricsDisplay

Visualizes quality metrics from the analysis.

**Props:**
- `metrics: Metrics` - Object containing metric values

**Usage:**
```tsx
<MetricsDisplay metrics={qualityMetrics} />
```

## API Integration

### Streaming QA Results

The frontend consumes NDJSON streams from the backend:

```typescript
const response = await fetch('http://localhost:8000/qa', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: websiteUrl })
});

const reader = response.body?.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n').filter(line => line.trim());

  for (const line of lines) {
    const message = JSON.parse(line);
    // Process message.content
  }
}
```

### Message Format

Backend sends messages in this format:

```typescript
interface UpdateMessage {
  type: 'update';
  content: {
    agent: string;
    status: 'pending' | 'running' | 'completed' | 'error';
    message?: string;
    result?: any;
    timestamp?: string;
  };
}
```

## Styling

### CSS Architecture

- **index.css**: Global styles, resets, and CSS variables
- **App.css**: Application-specific styles
- **Component styles**: Inline or component-scoped

### CSS Variables

Define custom colors and themes:

```css
:root {
  --primary-color: #007bff;
  --success-color: #28a745;
  --danger-color: #dc3545;
  --warning-color: #ffc107;
}
```

## Docker Deployment

### Build Image

```bash
docker build -t blackscope-frontend .
```

### Run Container

```bash
docker run -p 80:80 blackscope-frontend
```

### Multi-stage Build

The Dockerfile uses a multi-stage build:

1. **Builder stage**: Installs dependencies and builds the app
2. **Production stage**: Serves static files with nginx

## Nginx Configuration

The production deployment uses nginx with:

- **SPA Routing**: Fallback to `index.html` for client-side routing
- **Gzip Compression**: Optimized asset delivery
- **Cache Headers**: Long-term caching for static assets
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, etc.

To modify nginx settings, edit `nginx.conf`.

## Environment Variables

Create `.env.local` for local development:

```env
# Backend API URL
VITE_BACKEND_URL=http://localhost:8000

# Optional: Enable debug mode
VITE_DEBUG=true
```

Access in code:
```typescript
const backendUrl = import.meta.env.VITE_BACKEND_URL;
```

## Development Tips

### Hot Module Replacement

Vite provides instant HMR. Changes to React components will be reflected immediately without full page reload.

### TypeScript Strict Mode

The project uses TypeScript strict mode. Ensure all types are properly defined:

```typescript
interface Agent {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  message?: string;
}
```

### React DevTools

Install React DevTools browser extension for component inspection and performance profiling.

### Debugging

```typescript
// Use console methods during development
console.log('Agent status:', agent);

// Or use the debugger
debugger;
```

## Performance Optimization

### Code Splitting

Lazy load components for faster initial load:

```typescript
import { lazy, Suspense } from 'react';

const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HeavyComponent />
    </Suspense>
  );
}
```

### Asset Optimization

- Images are served from `public/` directory
- Vite automatically optimizes assets during build
- Use appropriate image formats (WebP, SVG)

### Bundle Analysis

```bash
npm run build -- --analyze
```

## Testing

### ESLint

```bash
npm run lint
```

### Type Checking

```bash
npx tsc --noEmit
```

## Troubleshooting

### CORS Errors

If you see CORS errors, ensure the backend is configured with the correct `CLIENT_HOST`:

```env
# backend/.env
CLIENT_HOST=http://localhost:5173
```

### Build Failures

Clear cache and reinstall:

```bash
rm -rf node_modules package-lock.json
npm install
```

### Port Already in Use

Change the dev server port:

```bash
npm run dev -- --port 3000
```

Or in `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    port: 3000
  }
})
```

### Streaming Issues

Ensure the backend returns proper `Content-Type: application/x-ndjson` headers for streaming endpoints.

## Contributing

When contributing to the frontend:

1. Follow React best practices
2. Use TypeScript for all new components
3. Run `npm run lint` before committing
4. Keep components small and focused
5. Document props with TypeScript interfaces
6. Update this README with new features

## License

[Add your license here]
