# Modern Frontend Setup - React 19 + Tailwind v4 + Shadcn/ui

**Branch**: `claude/frontend-rewrite-01LfvCiYZwoB33mNdJGXJuPc`
**Status**: In Progress
**Stack**: React 19, Vite 7, TypeScript 5.9, Tailwind CSS v4, TanStack Router, Shadcn/ui

---

## Technology Stack (Latest Versions)

### Core Framework
- **React 19.2.0** - Latest React with automatic batching and concurrent features
- **React DOM 19.2.0** - DOM rendering with React 19
- **TypeScript 5.9.3** - Latest TypeScript with improved type inference
- **Vite 7.2.2** - Ultra-fast build tool and dev server

### Routing & State Management
- **TanStack Router 1.136.8** - Type-safe routing with file-based routing
- **TanStack Query 5.90.10** - Powerful async state management
- **Zustand 5.0.3** - Lightweight state management

### Styling & UI
- **Tailwind CSS 4.1.17** - Latest Tailwind v4 with CSS-first configuration
- **@tailwindcss/vite 4.1.17** - Vite plugin for Tailwind v4
- **Shadcn/ui** - Beautiful, accessible component library
- **Framer Motion 12.1.0** - Production-ready animations
- **Lucide React 0.468.0** - Beautiful icon library

### Voice & AI
- **@xenova/transformers 2.17.2** - Whisper STT in browser (will run in Web Worker)
- **Wavesurfer.js 7.11.1** - Audio visualization

### Forms & Validation
- **React Hook Form 7.54.2** - Performant form management
- **Zod 3.24.1** - TypeScript-first schema validation
- **@hookform/resolvers 3.10.0** - Zod integration with React Hook Form

### HTTP & API
- **Axios 1.7.9** - Promise-based HTTP client
- **API Proxy** - Configured to proxy `/api` requests to backend (localhost:8000)

### Utilities
- **clsx 2.1.1** - Conditional className utility
- **tailwind-merge 3.0.2** - Merge Tailwind classes intelligently
- **class-variance-authority 0.7.1** - CVA for variant-based components
- **date-fns 4.1.0** - Modern date utility library

### Testing
- **Vitest 3.0.7** - Vite-native testing framework
- **@testing-library/react 16.1.0** - React Testing Library for React 19
- **@testing-library/jest-dom 6.6.5** - Custom Jest matchers
- **@testing-library/user-event 14.5.2** - User event simulation

---

## Project Structure

```
frontend-new/
├── src/
│   ├── features/              # Feature-based modules
│   │   ├── chat/
│   │   │   └── components/    # Chat UI components
│   │   ├── voice/
│   │   │   └── components/    # Voice recording components
│   │   └── settings/
│   │       └── components/    # Settings components
│   ├── components/
│   │   └── ui/               # Shadcn/ui components
│   ├── lib/
│   │   └── utils.ts          # cn() utility and helpers
│   ├── routes/               # TanStack Router routes
│   ├── stores/               # Zustand stores
│   ├── workers/              # Web Workers (Whisper STT)
│   ├── index.css             # Tailwind v4 with @theme
│   ├── main.tsx              # App entry point
│   └── App.tsx               # Root component
├── public/                    # Static assets
├── components.json            # Shadcn/ui configuration
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript configuration
└── package.json              # Dependencies

```

---

## Configuration

### Vite Configuration (`vite.config.ts`)

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),  // Tailwind v4 Vite plugin
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),  // @ alias for imports
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',  // Backend API
        changeOrigin: true,
      },
    },
  },
})
```

### Tailwind v4 Configuration (`src/index.css`)

Tailwind v4 uses CSS-first configuration with `@theme` and `@import`:

```css
@import "tailwindcss";

@theme {
  --font-sans: system-ui, -apple-system, ...;

  /* Custom colors */
  --color-primary-500: #0ea5e9;
  /* ... more theme variables */

  /* Custom animations */
  --animate-slide-in-from-right: slide-in-from-right 0.3s ease-out;
}

/* Custom keyframes and utilities */
```

### TypeScript Configuration (`tsconfig.app.json`)

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]  // Path alias support
    },
    // ... other options
  }
}
```

---

## Key Features to Implement

### 1. Non-Blocking Whisper (Web Worker)

**Problem**: Whisper model (190MB) blocks UI during load

**Solution**: Load and run Whisper in Web Worker

```typescript
// src/workers/whisper.worker.ts
import { pipeline } from '@xenova/transformers';

let transcriber: any = null;

self.addEventListener('message', async (event) => {
  const { type, data } = event.data;

  if (type === 'INIT') {
    self.postMessage({ type: 'LOADING' });
    transcriber = await pipeline('automatic-speech-recognition', data.model);
    self.postMessage({ type: 'READY' });
  }

  if (type === 'TRANSCRIBE') {
    const result = await transcriber(data.audio, {
      language: data.language,
      task: 'transcribe',
    });
    self.postMessage({ type: 'RESULT', result });
  }
});
```

### 2. Modern Chat UI with Shadcn/ui

**Components to Build**:
- `MessageBubble` - Animated message display
- `MessageList` - Virtualized message list
- `ChatInput` - Text + voice input
- `VoiceRecorder` - Recording with visualization
- `AudioPlayer` - TTS playback controls

### 3. TanStack Router Setup

**Type-safe routing with file-based routes**:

```typescript
// src/routes/__root.tsx
import { createRootRoute, Outlet } from '@tanstack/react-router'

export const Route = createRootRoute({
  component: () => (
    <div className="min-h-screen bg-background">
      <Outlet />
    </div>
  ),
})

// src/routes/index.tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: ChatPage,
})
```

### 4. State Management

**TanStack Query for API state**:
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['chat', conversationId],
  queryFn: () => fetchConversation(conversationId),
})
```

**Zustand for client state**:
```typescript
const useStore = create((set) => ({
  isRecording: false,
  startRecording: () => set({ isRecording: true }),
  stopRecording: () => set({ isRecording: false }),
}))
```

---

## Development Workflow

### Install Dependencies

```bash
cd frontend-new
npm install
```

### Run Development Server

```bash
npm run dev
```

**Runs on**: http://localhost:3000
**API Proxy**: /api → http://localhost:8000

### Build for Production

```bash
npm run build
```

### Run Tests

```bash
npm test           # Run tests
npm run test:ui    # Run with Vitest UI
```

### Type Checking

```bash
npm run type-check
```

---

## Shadcn/ui Usage

### Add Components

```bash
npx shadcn@latest add button
npx shadcn@latest add input
npx shadcn@latest add card
npx shadcn@latest add dialog
```

### Use Components

```typescript
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

function MyComponent() {
  return (
    <div>
      <Input placeholder="Type a message..." />
      <Button>Send</Button>
    </div>
  )
}
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| First Contentful Paint | < 1.5s |
| Time to Interactive | < 3s |
| Whisper Loading | Background (non-blocking) |
| Initial Bundle | < 500KB |
| Lighthouse Score | > 95 |

---

## Next Steps

1. ✅ Project setup with React 19 + Vite
2. ✅ Tailwind CSS v4 configuration
3. ✅ TypeScript path aliases
4. ✅ Utility functions (cn())
5. ⏳ Complete npm install
6. ⏳ Add Shadcn/ui components (Button, Input, Card, etc.)
7. ⏳ Set up TanStack Router with routes
8. ⏳ Create Web Worker for Whisper
9. ⏳ Build chat interface
10. ⏳ Implement voice recording
11. ⏳ Add audio visualization
12. ⏳ Connect to backend API

---

## Modern Practices

### CSS-First Configuration (Tailwind v4)
- No more `tailwind.config.js`
- Use `@theme` in CSS
- Native CSS variables
- Better performance

### Type-Safe Routing (TanStack Router)
- File-based routing
- Automatic type inference
- Type-safe navigation
- Better DX

### Component Composition (Shadcn/ui)
- Copy & modify components
- Full control over code
- No package lock-in
- Customizable

### Performance-First
- Code splitting
- Lazy loading
- Web Workers for heavy tasks
- Optimized bundle sizes

---

**Status**: Configuration complete, installing dependencies
**Branch**: `claude/frontend-rewrite-01LfvCiYZwoB33mNdJGXJuPc`
**Next**: Build modern chat UI with Shadcn/ui components
