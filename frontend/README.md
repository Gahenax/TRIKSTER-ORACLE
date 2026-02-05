# Trickster Oracle — Frontend

Educational probabilistic analytics UI built with React, TypeScript, and Vite.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── components/     # Reusable UI components
│   │   │   └── FooterDisclaimer.tsx
│   │   ├── pages/          # Page components
│   │   │   ├── Home.tsx
│   │   │   ├── Simulator.tsx
│   │   │   └── Result.tsx
│   │   ├── lib/            # Utilities and API client
│   │   │   ├── api.ts
│   │   │   └── types.ts
│   │   └── App.tsx         # Main app component
│   ├── index.css           # Global styles + design system
│   └── main.tsx            # React entry point
├── public/                 # Static assets
├── index.html              # HTML template
├── vite.config.ts          # Vite configuration
├── tsconfig.json           # TypeScript configuration
└── package.json            # Dependencies
```

## 🎨 Design System

The UI uses a custom design system with:
- **Dark mode** by default
- **CSS variables** for consistent theming
- **Glassmorphism** effects
- **Gradient accents**
- **Premium typography** (Inter + JetBrains Mono)
- **Responsive** grid layouts
- **Micro-animations**

All design tokens are defined in `src/index.css`.

## 🔌 API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000` (proxied via Vite).

### Mock Mode
When the backend is not running, the app automatically uses mock data from `api.simulateMock()`.

### Environment Variables

Create `.env.local`:
```
VITE_API_URL=http://localhost:8000/api
```

## 📊 Features

- ✅ **Home**: Landing page with feature showcase
- ✅ **Simulator**: Event configuration and simulation trigger
- ✅ **Result**: Display probabilities, risk, explanation, scenarios
- ⏳ **Charts**: Distribution visualization (coming soon)
- ⏳ **Tokens**: Daily token limits (FASE 5)

## 🧪 Development

### Backend Health Check
The app checks backend health on load and displays status in the header.

### Hot Module Replacement (HMR)
Vite provides instant feedback during development.

### Type Safety
Full TypeScript coverage with strict mode enabled.

## 🚢 Deployment

```bash
# Build for production
npm run build

# Output: dist/
```

Upload `dist/` contents to:
```
/home/u314799704/domains/gahenaxaisolutions.com/public_html/tricksteranalytics
```

## 📝 Next Steps

1. Add Chart.js visualizations for probability distributions
2. Implement token system (LocalStorage + UI)
3. Add sensitivity factor visualization
4. Improve mobile responsiveness
5. Add loading skeletons
6. Implement error boundaries
7. Add analytics (privacy-focused)

## 🐛 Known Issues

- Charts not yet implemented (placeholder data ready)
- No router (using simple state-based navigation for demo)
- Form validation is basic (relies on backend)

## 📚 Learn More

- [React Docs](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Guide](https://vitejs.dev/guide/)
- [Project Roadmap](../ROADMAP.py)

---

**Version**: 0.1.0 (Demo)  
**License**: MIT
