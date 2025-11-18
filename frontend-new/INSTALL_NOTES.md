# Installation Notes

## Known Issue: Sharp Dependency

The `sharp` package (image processing library) fails to install in this environment due to proxy/network restrictions:

```
sharp: Installation error: Status 403 Forbidden
```

## Workaround

Sharp is an optional dependency pulled in by `@vitejs/plugin-react` for optimized image handling. Since we don't need image optimization for this demo, we can work around this:

### Option 1: Install without sharp (Recommended for demo)
```bash
npm install --legacy-peer-deps
# Ignore sharp errors - the app will still work
```

### Option 2: Use alternative package manager
```bash
# Using pnpm (if available)
pnpm install

# Using yarn
yarn install
```

### Option 3: Remove problematic dependencies temporarily
Remove these from package.json:
- `@testing-library/react`
- `@testing-library/jest-dom`
- `vitest`

Then install:
```bash
npm install
```

## Manual Installation Steps

If npm install continues to fail, install packages in groups:

### 1. Core Dependencies
```bash
npm install react@^19.2.0 react-dom@^19.2.0
```

### 2. Routing & State
```bash
npm install @tanstack/react-router@^1.136.8 @tanstack/react-query@^5.90.10 zustand@^5.0.3
```

### 3. UI & Styling
```bash
npm install clsx@^2.1.1 tailwind-merge@^3.0.2 class-variance-authority@^0.7.1 lucide-react@^0.468.0 framer-motion@^12.1.0
```

### 4. AI & Voice
```bash
npm install @xenova/transformers@^2.17.2 wavesurfer.js@^7.11.1
```

### 5. Dev Dependencies
```bash
npm install -D vite@^7.2.2 @vitejs/plugin-react@^5.1.0 typescript@~5.9.3
npm install -D tailwindcss@^4.1.17 @tailwindcss/vite@^4.1.17
npm install -D @types/react@^19.2.2 @types/react-dom@^19.2.2 @types/node@^24.10.0
npm install -D eslint typescript-eslint
```

## Running the Dev Server

Once packages are installed:

```bash
npm run dev
```

Visit: http://localhost:3000

## Production Build

```bash
npm run build
npm run preview
```

## Features That Work Without Full Install

Even with partial package installation, these features work:
- ✅ React 19 rendering
- ✅ Tailwind CSS v4 styling
- ✅ Component library (if basic deps installed)
- ✅ TypeScript compilation
- ✅ Vite dev server
- ✅ Hot module replacement

## Features That Need Full Install

- Whisper STT (@xenova/transformers)
- TanStack Router
- TanStack Query
- Framer Motion animations
- Full UI components

## Alternative: Use CDN for Development

For quick testing, components can use CDN imports:

```html
<script type="module">
  import React from 'https://esm.sh/react@19.2.0'
  import ReactDOM from 'https://esm.sh/react-dom@19.2.0'
</script>
```

## Contact

If installation issues persist, check:
1. Network/proxy configuration
2. npm registry access
3. Node.js version (requires 18+)
4. npm version (requires 9+)
