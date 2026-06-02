# PHASE 2: Complete Next.js Frontend Migration Strategy

**Status**: Comprehensive Architecture Design  
**Timeline**: 2-3 weeks implementation  
**Target**: Production-grade React frontend with clean architecture

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Framework & Tooling Decisions](#framework--tooling-decisions)
3. [App Router vs Pages Router Decision](#app-router-vs-pages-router-decision)
4. [Folder Structure & Organization](#folder-structure--organization)
5. [Component Architecture](#component-architecture)
6. [State Management Strategy](#state-management-strategy)
7. [API Layer & Client Design](#api-layer--client-design)
8. [Server/Client Component Strategy](#serverclient-component-strategy)
9. [Error Handling & Boundaries](#error-handling--boundaries)
10. [Loading States & Suspense](#loading-states--suspense)
11. [Authentication Architecture](#authentication-architecture)
12. [WebSocket & Real-time Strategy](#websocket--real-time-strategy)
13. [Performance Optimization](#performance-optimization)
14. [Styling & Animation](#styling--animation)
15. [Testing Strategy](#testing-strategy)
16. [Migration Roadmap](#migration-roadmap)

---

## EXECUTIVE SUMMARY

### Current State
- Single React component (VoiceAssistant.jsx, 900+ lines)
- No type safety (JavaScript, no TypeScript)
- Monolithic state management (useState everywhere)
- No error boundaries, no Suspense
- Direct API calls in component
- Vite-based build (works but not ideal for full-stack)

### Desired State (Phase 2 Output)
- ✅ Next.js 15 with App Router (server-first paradigm)
- ✅ Full TypeScript with strict mode
- ✅ Zustand for global state (lightweight, no boilerplate)
- ✅ Modular component architecture (presentational, container, hooks)
- ✅ Centralized API client with error handling
- ✅ Error boundaries, Suspense, streaming responses
- ✅ Server Components where possible (faster, smaller JS bundle)
- ✅ Client Components for interactivity (hooks, state)
- ✅ Multi-layout support (main dashboard, onboarding, settings)
- ✅ Real-time WebSocket integration
- ✅ Comprehensive error handling & retry logic
- ✅ Performance: Lazy loading, code splitting, image optimization
- ✅ SEO: Metadata, Open Graph support

### Key Architectural Principles
1. **Server-First**: Use Server Components by default, Client Components only when needed
2. **Type Safety**: Full TypeScript with strict tsconfig
3. **Single Responsibility**: Each component does one thing well
4. **DRY (Don't Repeat Yourself)**: Shared hooks, utilities, services
5. **Error Resilience**: Every async operation has error boundaries
6. **Progressive Enhancement**: Works without JavaScript (where applicable)
7. **Performance**: Optimize for LCP (Largest Contentful Paint) and FID

---

## FRAMEWORK & TOOLING DECISIONS

### Why Next.js 15?

| Feature | Vite (Current) | Next.js 15 | Decision |
|---------|----------------|-----------|----------|
| **Build Speed** | ⚡ Very fast | ⚡ Fast (with turbopack) | Tie, Next.js slightly slower |
| **API Routes** | ❌ Not native | ✅ Built-in | ✅ Next.js (auth, proxying) |
| **Server Components** | ❌ No | ✅ Yes | ✅ Next.js (bundle size) |
| **Image Optimization** | ❌ No | ✅ Yes | ✅ Next.js |
| **Middleware** | ❌ No | ✅ Yes | ✅ Next.js (auth gates) |
| **Analytics** | ❌ No | ✅ Built-in | ✅ Next.js |
| **Deployment** | Any (Vercel, Netlify, etc.) | Optimized for Vercel | ✅ Both good |
| **Learning Curve** | ⚡ Easier | Moderate | Depends on team |
| **Dev Experience** | ✅ Good | ✅ Excellent | ✅ Next.js |
| **File-based Routing** | ❌ Manual | ✅ Automatic | ✅ Next.js |

**Decision**: **Next.js 15 with App Router (released Jan 2025)**

### Technology Stack

```
Frontend:
├─ Next.js 15.0.0 (latest stable)
├─ React 19 (already in use, perfect)
├─ TypeScript 5.3+ (strict mode)
├─ Zustand 4.x (state management)
├─ TanStack Query v5 (server state sync)
├─ Axios (HTTP client)
├─ Zod (runtime validation)
└─ Tailwind CSS 4.3 (styling, already in use)

UI & Animation:
├─ Lucide React (icons, already in use)
├─ Framer Motion (complex animations)
├─ Radix UI (headless components) [optional]
└─ React Hot Toast (notifications)

Development:
├─ ESLint (with Next.js config)
├─ Prettier (code formatting)
├─ Husky (pre-commit hooks)
├─ Jest (unit tests)
├─ React Testing Library (component tests)
└─ Playwright (E2E tests)

Testing:
├─ Vitest (faster than Jest, recommended)
├─ React Testing Library
├─ Playwright (E2E)
└─ Testing Playground (debugging)
```

### Version Pinning
```json
{
  "next": "^15.0.0",
  "react": "^19.2.0",
  "typescript": "^5.3.0",
  "zustand": "^4.4.0",
  "@tanstack/react-query": "^5.30.0",
  "zod": "^3.22.0",
  "tailwindcss": "^4.3.0"
}
```

---

## APP ROUTER VS PAGES ROUTER DECISION

### Comparison Matrix

| Aspect | Pages Router | App Router | Recommendation |
|--------|--------------|-----------|-----------------|
| **Release Status** | Stable (legacy) | Stable (current) | ✅ App Router |
| **File Structure** | `pages/` folder | `app/` folder | ✅ App Router |
| **Default Rendering** | Client-side | Server-side | ✅ App Router (smaller JS) |
| **API Routes** | `pages/api/` | `app/api/` | Same |
| **Middleware** | Via `_middleware.js` | Via `middleware.ts` (cleaner) | ✅ App Router |
| **Layout System** | Per-page | Nested layouts | ✅ App Router (powerful) |
| **Data Fetching** | getServerSideProps | fetch() in Server Components | ✅ App Router (simpler) |
| **Streaming** | ❌ No | ✅ Yes | ✅ App Router |
| **Error Handling** | try/catch | error.tsx boundaries | ✅ App Router |
| **Maturity** | Production-ready | Production-ready | Tie |
| **Learning Curve** | Familiar | Slightly steeper | Pages Router easier, but App Router better |
| **Performance** | Good | Better (server components) | ✅ App Router |
| **Future-proof** | Maintained but legacy | Active development | ✅ App Router |

**DECISION: App Router (with backward compatibility for legacy routes if needed)**

### Why App Router?

1. **Server Components by Default**: Smaller JS bundles (important for mobile)
2. **Better Caching**: Built-in ISR and revalidation
3. **Nested Layouts**: Support multi-level UI layouts (dashboard + sidebar)
4. **Streaming**: Can send UI incrementally (faster perceived performance)
5. **Error Boundaries**: Automatic error.tsx handling
6. **Parallel Routes**: Render multiple segments simultaneously
7. **Future-Proof**: Vercel's focus, continuous improvements

### Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Team unfamiliar with Server Components | Training doc + examples in codebase |
| Third-party libs don't support use client | Use compatibility layer or alternatives |
| Harder to debug streaming issues | Centralized error logging with Sentry |
| More TypeScript required | Strict tsconfig.json for clarity |

---

## FOLDER STRUCTURE & ORGANIZATION

### Proposed Directory Layout

```
frontend/
│
├── app/                                    # Next.js App Router
│   ├── layout.tsx                          # Root layout (header, providers)
│   ├── page.tsx                            # Home page (landing/dashboard)
│   ├── not-found.tsx                       # 404 page
│   ├── error.tsx                           # Global error boundary
│   │
│   ├── (auth)/                             # Route group: authentication
│   │   ├── login/page.tsx
│   │   ├── signup/page.tsx
│   │   └── layout.tsx                      # Auth-specific layout
│   │
│   ├── (dashboard)/                        # Route group: authenticated app
│   │   ├── layout.tsx                      # Dashboard layout (sidebar, nav)
│   │   ├── page.tsx                        # Dashboard home
│   │   ├── session/[id]/page.tsx          # Session detail view
│   │   ├── history/page.tsx                # Conversation history
│   │   ├── settings/page.tsx               # User settings
│   │   ├── emotions/page.tsx               # Emotion analytics
│   │   └── error.tsx                       # Dashboard error boundary
│   │
│   ├── api/                                # API routes (proxy to backend)
│   │   ├── auth/
│   │   │   ├── login/route.ts
│   │   │   ├── logout/route.ts
│   │   │   └── refresh/route.ts
│   │   ├── voice/
│   │   │   ├── process/route.ts            # POST /api/voice/process
│   │   │   ├── preview/route.ts
│   │   │   └── status/route.ts
│   │   ├── memories/
│   │   │   └── retrieve/route.ts
│   │   ├── sessions/
│   │   │   ├── create/route.ts
│   │   │   └── [id]/route.ts
│   │   └── health/route.ts                 # Health check
│   │
│   ├── voice-recorder/                     # Main voice feature (route group)
│   │   ├── page.tsx                        # Voice recorder page
│   │   ├── layout.tsx
│   │   └── error.tsx
│   │
│   └── loading.tsx                         # Global loading skeleton
│
├── src/
│   │
│   ├── components/                         # React components (organized by domain)
│   │   ├── common/                         # Shared, reusable components
│   │   │   ├── Button/
│   │   │   │   ├── Button.tsx              # Component
│   │   │   │   ├── Button.test.tsx         # Tests
│   │   │   │   └── Button.module.css
│   │   │   ├── Card/
│   │   │   ├── Modal/
│   │   │   ├── Toast/
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── Suspense.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   │
│   │   ├── audio/                          # Audio-related components
│   │   │   ├── VoiceRecorder.tsx           # Main recording component
│   │   │   ├── AudioVisualizer.tsx         # Waveform visualization
│   │   │   ├── TranscriptDisplay.tsx
│   │   │   ├── EmotionIndicator.tsx
│   │   │   └── ResponsePlayback.tsx
│   │   │
│   │   ├── video/                          # Video emotion detection (future)
│   │   │   ├── VideoRecorder.tsx
│   │   │   ├── FaceDetector.tsx
│   │   │   └── VideoAnalysis.tsx
│   │   │
│   │   ├── dashboard/                      # Dashboard-specific
│   │   │   ├── SessionCard.tsx
│   │   │   ├── EmotionChart.tsx
│   │   │   ├── MemoryFeed.tsx
│   │   │   └── QuickStats.tsx
│   │   │
│   │   ├── layouts/                        # Page layouts
│   │   │   ├── MainLayout.tsx              # With sidebar, header
│   │   │   ├── AuthLayout.tsx              # Centered, minimal
│   │   │   └── BlankLayout.tsx
│   │   │
│   │   └── providers/                      # Context providers
│   │       ├── AuthProvider.tsx
│   │       ├── ThemeProvider.tsx
│   │       ├── NotificationProvider.tsx
│   │       └── AppProviders.tsx            # Combines all
│   │
│   ├── hooks/                              # Custom React hooks
│   │   ├── useVoiceRecorder.ts             # Voice recording logic
│   │   ├── useAudioAnalysis.ts             # Audio feature extraction
│   │   ├── useEmotionDetection.ts          # Emotion prediction
│   │   ├── useAuth.ts                      # Auth context hook
│   │   ├── useFetch.ts                     # Data fetching wrapper
│   │   ├── useLocalStorage.ts              # Persistent state
│   │   ├── usePrevious.ts
│   │   ├── useMediaRecorder.ts             # Web Audio API wrapper
│   │   └── index.ts                        # Re-export all
│   │
│   ├── services/                           # Business logic layer
│   │   ├── api/
│   │   │   ├── client.ts                   # Axios instance with interceptors
│   │   │   ├── endpoints.ts                # API route constants
│   │   │   ├── voiceAPI.ts                 # Voice processing endpoints
│   │   │   ├── sessionAPI.ts               # Session management
│   │   │   ├── authAPI.ts                  # Authentication
│   │   │   └── memoriesAPI.ts              # Memory retrieval
│   │   │
│   │   ├── audio/
│   │   │   ├── audioProcessor.ts           # Web Audio API wrapper
│   │   │   ├── audioAnalyzer.ts            # Feature extraction
│   │   │   ├── audioRecorder.ts            # MediaRecorder wrapper
│   │   │   └── audioUtils.ts               # Helpers
│   │   │
│   │   ├── ml/
│   │   │   ├── emotionDetector.ts          # ML inference (client or server)
│   │   │   └── videoAnalyzer.ts            # Video feature extraction (future)
│   │   │
│   │   ├── ws/
│   │   │   ├── wsClient.ts                 # WebSocket connection
│   │   │   └── wsEvents.ts                 # Event types
│   │   │
│   │   └── storage/
│   │       ├── localStorage.ts
│   │       └── sessionStorage.ts
│   │
│   ├── store/                              # Zustand state management
│   │   ├── useAuthStore.ts                 # Authentication state
│   │   ├── useAudioStore.ts                # Audio/recording state
│   │   ├── useUIStore.ts                   # UI state (modals, toasts)
│   │   ├── useSessionStore.ts              # Session/conversation state
│   │   ├── useEmotionStore.ts              # Emotion data
│   │   └── index.ts
│   │
│   ├── types/                              # TypeScript definitions
│   │   ├── api.ts                          # API response types
│   │   ├── audio.ts                        # Audio feature types
│   │   ├── emotion.ts                      # Emotion types
│   │   ├── session.ts                      # Session types
│   │   ├── user.ts                         # User types
│   │   ├── common.ts                       # Generic types
│   │   └── index.ts
│   │
│   ├── utils/                              # Utility functions
│   │   ├── formatting.ts                   # Format numbers, dates, etc
│   │   ├── validation.ts                   # Input validation (Zod schemas)
│   │   ├── errors.ts                       # Custom error classes
│   │   ├── logger.ts                       # Client-side logging
│   │   ├── constants.ts                    # App constants
│   │   ├── config.ts                       # Environment config
│   │   └── helpers.ts                      # Generic helpers
│   │
│   ├── lib/                                # Third-party integrations
│   │   ├── sentry.ts                       # Error tracking
│   │   ├── analytics.ts                    # Event tracking
│   │   ├── supabase.ts                     # Supabase client
│   │   └── websocket.ts                    # WebSocket factory
│   │
│   └── styles/                             # Global styles
│       ├── globals.css
│       ├── animations.css
│       └── variables.css                   # CSS variables (theme)
│
├── public/                                 # Static assets
│   ├── images/
│   ├── icons/
│   ├── sounds/
│   └── fonts/
│
├── tests/                                  # Test files (mirrors src structure)
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                                   # Documentation
│   ├── ARCHITECTURE.md
│   ├── COMPONENT_GUIDE.md
│   ├── STATE_MANAGEMENT.md
│   ├── API_INTEGRATION.md
│   └── TESTING.md
│
├── .env.example                            # Environment template
├── .env.local                              # Local secrets (gitignored)
├── .env.production                         # Production config
├── .eslintrc.json
├── .prettierrc
├── tailwind.config.ts
├── tsconfig.json                           # TypeScript strict mode
├── next.config.ts
├── jest.config.ts
├── playwright.config.ts
└── package.json
```

### Organization Principles

1. **Domain-Driven**: Components grouped by feature (audio, video, dashboard)
2. **Scalability**: Easy to add new features without modifying existing structure
3. **Testability**: Tests live alongside components/hooks
4. **Separation of Concerns**:
   - `components/`: UI only (no business logic)
   - `hooks/`: Reusable stateful logic
   - `services/`: Business logic, API calls, external integrations
   - `store/`: Global state (Zustand)
   - `types/`: TypeScript definitions
   - `utils/`: Stateless helper functions
5. **Colocation**: Related files close together (test next to component)

---

## COMPONENT ARCHITECTURE

### Component Types & Patterns

#### 1. Presentational Components (Dumb Components)

Pure UI components that receive data via props and render. No business logic.

```typescript
// src/components/common/Button/Button.tsx
import React from 'react'
import { cn } from '@/utils/helpers'
import styles from './Button.module.css'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
  children: React.ReactNode
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  className,
  children,
  ...props
}) => (
  <button
    className={cn(
      styles.button,
      styles[variant],
      styles[size],
      isLoading && styles.loading,
      className
    )}
    disabled={disabled || isLoading}
    {...props}
  >
    {isLoading ? '...' : children}
  </button>
)

Button.displayName = 'Button'
```

#### 2. Container Components (Smart Components)

Manage state, fetch data, and compose presentational components.

```typescript
// src/components/audio/VoiceRecorderContainer.tsx
'use client'

import React, { useEffect } from 'react'
import { VoiceRecorder } from './VoiceRecorder'
import { useVoiceRecorder } from '@/hooks/useVoiceRecorder'
import { useAudioStore } from '@/store/useAudioStore'

export const VoiceRecorderContainer: React.FC = () => {
  const {
    isRecording,
    transcript,
    emotion,
    response,
    loading,
    error,
    startRecording,
    stopRecording,
    clearState,
  } = useVoiceRecorder()

  const { setAudioFeatures } = useAudioStore()

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      if (isRecording) {
        stopRecording()
      }
    }
  }, [isRecording, stopRecording])

  return (
    <VoiceRecorder
      isRecording={isRecording}
      transcript={transcript}
      emotion={emotion}
      response={response}
      loading={loading}
      error={error}
      onStart={startRecording}
      onStop={stopRecording}
      onClear={clearState}
    />
  )
}
```

#### 3. Server Components (New in App Router)

Fetch data server-side, don't ship JavaScript to browser.

```typescript
// app/(dashboard)/emotions/page.tsx
import React from 'react'
import { EmotionChart } from '@/components/dashboard/EmotionChart'
import { fetchUserEmotions } from '@/services/api/emotionAPI'

export default async function EmotionsPage() {
  const emotions = await fetchUserEmotions()

  if (!emotions || emotions.length === 0) {
    return <div>No emotion data available</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Emotion Trends</h1>
      <EmotionChart data={emotions} />
    </div>
  )
}
```

#### 4. Error Boundaries

Catch errors in child components gracefully.

```typescript
// src/components/common/ErrorBoundary.tsx
'use client'

import React from 'react'

interface Props {
  children: React.ReactNode
  fallback?: React.ReactNode
}

export class ErrorBoundary extends React.Component<Props, { hasError: boolean }> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error: Error) {
    console.error('ErrorBoundary caught:', error)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || <div>Something went wrong. Please refresh.</div>
    }

    return this.props.children
  }
}
```

#### 5. Layout Components

Multi-level layouts for different sections.

```typescript
// app/(dashboard)/layout.tsx
import React from 'react'
import { Sidebar } from '@/components/layouts/Sidebar'
import { Header } from '@/components/layouts/Header'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-slate-50">
      <Sidebar />
      <div className="flex flex-col flex-1">
        <Header />
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  )
}
```

### Component Naming Convention

```
Pattern: [Domain][Type].tsx

Examples:
├─ VoiceRecorder.tsx           # Presentational component
├─ VoiceRecorderContainer.tsx  # Container wrapping it
├─ useVoiceRecorder.ts         # Custom hook for logic
├─ voiceAPI.ts                 # API service
├─ useVoiceStore.ts            # Zustand store
└─ voice.types.ts              # TypeScript types
```

---

## STATE MANAGEMENT STRATEGY

### Why Zustand (Not Redux/Jotai)?

| Criteria | Redux | Zustand | Jotai | Decision |
|----------|-------|---------|-------|----------|
| **Bundle Size** | 40KB | 2KB | 8KB | ✅ Zustand |
| **Learning Curve** | Steep | Gentle | Moderate | ✅ Zustand |
| **Boilerplate** | High | Low | Low | ✅ Zustand |
| **DevTools** | Excellent | Good | Good | Redux better, but Zustand sufficient |
| **Time-travel Debugging** | ✅ | ⚠️ Plugin | ⚠️ Plugin | Redux better, not critical |
| **Async Actions** | Middleware | Optional | Primitives | All good |
| **Learning for Team** | Weeks | Days | Days | ✅ Zustand |
| **Suitable for NeuroNest** | Overkill | Perfect | Also good | ✅ Zustand |

**DECISION: Zustand** (pragmatic choice for this project)

### Zustand Store Design

#### 1. Auth Store

```typescript
// src/store/useAuthStore.ts
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  name: string
}

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  error: string | null
  isAuthenticated: boolean

  // Actions
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
  setError: (error: string | null) => void
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set, get) => ({
        user: null,
        token: null,
        isLoading: false,
        error: null,
        isAuthenticated: false,

        login: async (email, password) => {
          set({ isLoading: true, error: null })
          try {
            const response = await fetch('/api/auth/login', {
              method: 'POST',
              body: JSON.stringify({ email, password }),
            })
            if (!response.ok) throw new Error('Login failed')
            const { user, token } = await response.json()
            set({ user, token, isAuthenticated: true })
          } catch (error) {
            set({ error: (error as Error).message })
            throw error
          } finally {
            set({ isLoading: false })
          }
        },

        logout: () => set({ user: null, token: null, isAuthenticated: false }),
        setUser: (user) => set({ user }),
        setError: (error) => set({ error }),
        clearError: () => set({ error: null }),
      }),
      {
        name: 'auth-storage', // localStorage key
      }
    )
  )
)
```

#### 2. Audio Store

```typescript
// src/store/useAudioStore.ts
import { create } from 'zustand'

interface AudioFeatures {
  pitch_mean: number
  jitter: number
  loudness: number
  volume_std_dev: number
  pitch_std_dev: number
  is_trembling: boolean
  is_singing: boolean
  is_crying: boolean
  is_whispering: boolean
  voice_description: string
}

interface AudioState {
  isRecording: boolean
  audioFeatures: AudioFeatures | null
  transcript: string
  emotion: any
  response: string
  audioUrl: string | null
  loading: boolean
  error: string | null

  // Actions
  setIsRecording: (value: boolean) => void
  setAudioFeatures: (features: AudioFeatures) => void
  setTranscript: (text: string) => void
  setEmotion: (emotion: any) => void
  setResponse: (text: string) => void
  setAudioUrl: (url: string | null) => void
  setLoading: (value: boolean) => void
  setError: (error: string | null) => void
  reset: () => void
}

export const useAudioStore = create<AudioState>((set) => ({
  isRecording: false,
  audioFeatures: null,
  transcript: '',
  emotion: null,
  response: '',
  audioUrl: null,
  loading: false,
  error: null,

  setIsRecording: (value) => set({ isRecording: value }),
  setAudioFeatures: (features) => set({ audioFeatures: features }),
  setTranscript: (transcript) => set({ transcript }),
  setEmotion: (emotion) => set({ emotion }),
  setResponse: (response) => set({ response }),
  setAudioUrl: (audioUrl) => set({ audioUrl }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  reset: () => set({
    isRecording: false,
    audioFeatures: null,
    transcript: '',
    emotion: null,
    response: '',
    audioUrl: null,
    loading: false,
    error: null,
  }),
}))
```

#### 3. UI Store

```typescript
// src/store/useUIStore.ts
import { create } from 'zustand'

interface UIState {
  isSidebarOpen: boolean
  isMobileMenuOpen: boolean
  activeTab: string
  selectedVoice: string
  theme: 'light' | 'dark'

  // Actions
  toggleSidebar: () => void
  toggleMobileMenu: () => void
  setActiveTab: (tab: string) => void
  setSelectedVoice: (voice: string) => void
  setTheme: (theme: 'light' | 'dark') => void
}

export const useUIStore = create<UIState>((set) => ({
  isSidebarOpen: true,
  isMobileMenuOpen: false,
  activeTab: 'home',
  selectedVoice: 'Rachel',
  theme: 'light',

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  toggleMobileMenu: () => set((state) => ({ isMobileMenuOpen: !state.isMobileMenuOpen })),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setSelectedVoice: (voice) => set({ selectedVoice: voice }),
  setTheme: (theme) => set({ theme }),
}))
```

### Store Usage in Components

```typescript
// In a component
import { useAudioStore } from '@/store/useAudioStore'

export function MyComponent() {
  const { isRecording, setIsRecording } = useAudioStore()

  return (
    <button onClick={() => setIsRecording(!isRecording)}>
      {isRecording ? 'Recording...' : 'Start'}
    </button>
  )
}
```

### When to Use Zustand vs Props

| Situation | Use Zustand | Use Props |
|-----------|------------|----------|
| **Global UI state** (modal open) | ✅ Yes | ❌ No |
| **User auth** | ✅ Yes | ❌ No |
| **Recording state** | ✅ Yes | ❌ No |
| **Passing data down 1-2 levels** | ❌ No | ✅ Yes |
| **Highly reusable component** | ❌ No | ✅ Yes (props) |
| **Server Component data** | N/A | ✅ Yes (no Zustand) |

---

## API LAYER & CLIENT DESIGN

### Centralized API Client

```typescript
// src/services/api/client.ts
import axios, { AxiosInstance, AxiosError } from 'axios'
import { useAuthStore } from '@/store/useAuthStore'

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor: Add auth token
    this.client.interceptors.request.use((config) => {
      const { token } = useAuthStore.getState()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Response interceptor: Handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired, clear auth
          useAuthStore.getState().logout()
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  get<T>(url: string, config?: any) {
    return this.client.get<T>(url, config)
  }

  post<T>(url: string, data?: any, config?: any) {
    return this.client.post<T>(url, data, config)
  }

  put<T>(url: string, data?: any, config?: any) {
    return this.client.put<T>(url, data, config)
  }

  patch<T>(url: string, data?: any, config?: any) {
    return this.client.patch<T>(url, data, config)
  }

  delete<T>(url: string, config?: any) {
    return this.client.delete<T>(url, config)
  }
}

export const apiClient = new APIClient()
```

### API Endpoints Module

```typescript
// src/services/api/endpoints.ts
export const API_ENDPOINTS = {
  // Auth
  auth: {
    login: '/api/auth/login',
    logout: '/api/auth/logout',
    refresh: '/api/auth/refresh',
  },

  // Voice Processing
  voice: {
    process: '/api/voice/process',
    preview: '/api/voice/preview',
    status: '/api/voice/status',
  },

  // Sessions
  sessions: {
    create: '/api/sessions/create',
    get: (id: string) => `/api/sessions/${id}`,
    list: '/api/sessions',
    delete: (id: string) => `/api/sessions/${id}`,
  },

  // Memories
  memories: {
    retrieve: '/api/memories/retrieve',
    search: '/api/memories/search',
  },

  // Health
  health: '/api/health',
} as const
```

### Service Layer APIs

```typescript
// src/services/api/voiceAPI.ts
import { apiClient } from './client'
import { API_ENDPOINTS } from './endpoints'
import type { ProcessVoiceRequest, ProcessVoiceResponse } from '@/types/api'

export const voiceAPI = {
  processVoice: async (formData: FormData): Promise<ProcessVoiceResponse> => {
    const response = await apiClient.post<ProcessVoiceResponse>(
      API_ENDPOINTS.voice.process,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
    return response.data
  },

  previewVoice: async (voiceName: string): Promise<{ audio_url: string }> => {
    const formData = new FormData()
    formData.append('voice_name', voiceName)
    const response = await apiClient.post(API_ENDPOINTS.voice.preview, formData)
    return response.data
  },

  getStatus: async (): Promise<{ status: string }> => {
    const response = await apiClient.get(API_ENDPOINTS.voice.status)
    return response.data
  },
}

// src/services/api/sessionAPI.ts
export const sessionAPI = {
  createSession: async () => {
    const response = await apiClient.post(API_ENDPOINTS.sessions.create)
    return response.data
  },

  getSession: async (id: string) => {
    const response = await apiClient.get(API_ENDPOINTS.sessions.get(id))
    return response.data
  },

  listSessions: async () => {
    const response = await apiClient.get(API_ENDPOINTS.sessions.list)
    return response.data
  },
}
```

### Error Handling

```typescript
// src/utils/errors.ts
export class APIError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network error') {
    super(message)
    this.name = 'NetworkError'
  }
}

export function handleAPIError(error: unknown): Error {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return new NetworkError('No response from server')
    }
    return new APIError(
      error.response.status,
      error.response.data?.message || error.message,
      error.response.data
    )
  }
  return error as Error
}
```

---

## SERVER/CLIENT COMPONENT STRATEGY

### Decision Tree

```
Are you...
├─ Fetching data?
│  └─ Server Component (no need for useState)
├─ Using hooks (useState, useEffect)?
│  └─ Client Component ('use client')
├─ Listening to browser events (click)?
│  └─ Client Component
├─ Just rendering static UI?
│  └─ Server Component (smaller JS)
└─ Building a layout?
   └─ Server Component (unless it has interactive features)
```

### Component Distribution

```
App Router Structure:

app/ (Server by default)
├── (dashboard)/layout.tsx               (Server - composes layout)
│   ├── page.tsx                         (Server - just rendering data)
│   ├── emotions/page.tsx                (Server - fetch + render)
│   │   └── <EmotionChart />             (Client - interactive chart)
│   └── session/[id]/
│       └── page.tsx                     (Server - fetch session data)
│           └── <SessionDetail />        (Client - interactive details)
│
├── (auth)/layout.tsx                    (Server)
│   ├── login/page.tsx                   (Client - form interactions)
│   └── signup/page.tsx                  (Client - form interactions)
│
└── voice-recorder/
    ├── layout.tsx                       (Server - basic layout)
    ├── page.tsx                         (Client - entire recorder page)
    └── <VoiceRecorderContainer />       (Client - manages recording state)
```

### Example: Server + Client Mix

```typescript
// app/(dashboard)/emotions/page.tsx (Server Component)
import { EmotionChart } from '@/components/dashboard/EmotionChart'
import { fetchUserEmotions } from '@/services/api/emotionAPI'

export default async function EmotionsPage() {
  // Fetch data server-side (no JavaScript sent)
  const emotions = await fetchUserEmotions()

  return (
    <div>
      <h1>Emotion Trends</h1>
      {/* Client component for interactivity */}
      <EmotionChart data={emotions} />
    </div>
  )
}
```

```typescript
// src/components/dashboard/EmotionChart.tsx (Client Component)
'use client'

import React, { useState } from 'react'
import { LineChart, Line, XAxis, YAxis } from 'recharts'

interface Props {
  data: Array<{ date: string; stress_level: number }>
}

export function EmotionChart({ data }: Props) {
  const [hoveredPoint, setHoveredPoint] = useState<number | null>(null)

  return (
    <div>
      <LineChart data={data}>
        <XAxis dataKey="date" />
        <YAxis domain={[0, 100]} />
        <Line type="monotone" dataKey="stress_level" stroke="#8884d8" />
      </LineChart>
      {hoveredPoint !== null && <div>Stress: {hoveredPoint}</div>}
    </div>
  )
}
```

### Benefits of Server Components in NeuroNest

1. **Smaller JS Bundle**: Emotion history page is server-rendered (no JS needed)
2. **Faster LCP**: Data fetched server-side, HTML sent directly
3. **Secure Secrets**: API keys stay on server (not exposed to client)
4. **Direct DB Access**: No API latency for server-side data fetches
5. **Better SEO**: Full HTML content in response

---

## ERROR HANDLING & BOUNDARIES

### Error Boundary Implementation

```typescript
// app/(dashboard)/error.tsx (catches errors in (dashboard) routes)
'use client'

import React from 'react'
import { Button } from '@/components/common/Button'

interface Props {
  error: Error
  reset: () => void
}

export default function DashboardError({ error, reset }: Props) {
  React.useEffect(() => {
    // Log error to external service
    console.error('Dashboard error:', error)
  }, [error])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-4">Something went wrong</h2>
        <p className="text-slate-600 mb-6">{error.message}</p>
        <Button onClick={reset}>Try again</Button>
      </div>
    </div>
  )
}
```

### Custom Error Types

```typescript
// src/utils/errors.ts
export class ValidationError extends Error {
  constructor(message: string, public field?: string) {
    super(message)
    this.name = 'ValidationError'
  }
}

export class AuthenticationError extends Error {
  constructor(message: string = 'Not authenticated') {
    super(message)
    this.name = 'AuthenticationError'
  }
}

export class PermissionError extends Error {
  constructor(message: string = 'Not authorized') {
    super(message)
    this.name = 'PermissionError'
  }
}

export class NotFoundError extends Error {
  constructor(resource: string) {
    super(`${resource} not found`)
    this.name = 'NotFoundError'
  }
}

export function isCustomError(
  error: unknown,
  type: typeof ValidationError
): error is InstanceType<typeof typeof ValidationError> {
  return error instanceof type
}
```

### Async Error Handling Hook

```typescript
// src/hooks/useAsyncError.ts
import { useCallback, useState } from 'react'

export function useAsyncError() {
  const [error, setError] = useState<Error | null>(null)

  const handleError = useCallback((err: unknown) => {
    if (err instanceof Error) {
      setError(err)
    } else {
      setError(new Error(String(err)))
    }
  }, [])

  const clearError = useCallback(() => setError(null), [])

  return { error, handleError, clearError }
}

// Usage in component
const { error, handleError, clearError } = useAsyncError()

useEffect(() => {
  voiceAPI
    .processVoice(formData)
    .catch(handleError)
}, [])

if (error) {
  return <ErrorDisplay error={error} onDismiss={clearError} />
}
```

---

## LOADING STATES & SUSPENSE

### Suspense Boundaries

```typescript
// app/voice-recorder/page.tsx
import { Suspense } from 'react'
import { VoiceRecorder } from '@/components/audio/VoiceRecorder'
import { VoiceRecorderSkeleton } from '@/components/audio/VoiceRecorderSkeleton'

export default function VoiceRecorderPage() {
  return (
    <Suspense fallback={<VoiceRecorderSkeleton />}>
      <VoiceRecorder />
    </Suspense>
  )
}
```

### Loading Skeleton

```typescript
// src/components/audio/VoiceRecorderSkeleton.tsx
export function VoiceRecorderSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-40 bg-slate-200 rounded-lg" />
      <div className="h-10 bg-slate-200 rounded-lg" />
      <div className="h-20 bg-slate-200 rounded-lg" />
    </div>
  )
}
```

### Progressive Enhancement Pattern

```typescript
// src/components/audio/VoiceRecorder.tsx
'use client'

import { useEffect, useState } from 'react'

export function VoiceRecorder() {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    // Only run client-side code after hydration
    setIsClient(true)
  }, [])

  if (!isClient) {
    return <div>Loading recorder...</div>
  }

  return (
    // Client-side recorder code
    <div>Recorder ready</div>
  )
}
```

---

## AUTHENTICATION ARCHITECTURE

### Multi-Layer Auth Strategy

```typescript
// src/middleware.ts (runs on every request)
import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth_token')?.value
  const { pathname } = request.nextUrl

  // Redirect unauthenticated users
  if (!token && pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Redirect authenticated users away from auth pages
  if (token && (pathname === '/login' || pathname === '/signup')) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/(dashboard|auth)/:path*'],
}
```

### Protected Route Component

```typescript
// src/components/common/ProtectedRoute.tsx
'use client'

import { useAuthStore } from '@/store/useAuthStore'
import { useRouter } from 'next/navigation'
import { ReactNode, useEffect } from 'react'

interface Props {
  children: ReactNode
  requiredRole?: string[]
}

export function ProtectedRoute({ children, requiredRole }: Props) {
  const { isAuthenticated, user } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, router])

  if (!isAuthenticated) {
    return <div>Redirecting to login...</div>
  }

  return <>{children}</>
}
```

### Login Flow

```typescript
// app/(auth)/login/page.tsx
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/useAuthStore'
import { Button } from '@/components/common/Button'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const router = useRouter()
  const { login, isLoading, error } = useAuthStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login(email, password)
      router.push('/dashboard')
    } catch (err) {
      // Error handled by store
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <div className="text-red-600">{error}</div>}
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
      <Button type="submit" isLoading={isLoading}>
        Login
      </Button>
    </form>
  )
}
```

---

## WEBSOCKET & REAL-TIME STRATEGY

### WebSocket Client Factory

```typescript
// src/lib/websocket.ts
class WebSocketClient {
  private ws: WebSocket | null = null
  private listeners: Map<string, Set<Function>> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  connect(url: string) {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(url)
        
        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.reconnectAttempts = 0
          resolve(true)
        }

        this.ws.onmessage = (event) => {
          const { type, data } = JSON.parse(event.data)
          this.emit(type, data)
        }

        this.ws.onerror = () => reject(new Error('WebSocket error'))
        this.ws.onclose = () => this.reconnect(url)
      } catch (err) {
        reject(err)
      }
    })
  }

  send(type: string, data: any) {
    if (!this.ws) return
    this.ws.send(JSON.stringify({ type, data }))
  }

  on(type: string, callback: Function) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set())
    }
    this.listeners.get(type)!.add(callback)
  }

  off(type: string, callback: Function) {
    this.listeners.get(type)?.delete(callback)
  }

  private emit(type: string, data: any) {
    this.listeners.get(type)?.forEach((cb) => cb(data))
  }

  private reconnect(url: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => this.connect(url), 1000 * this.reconnectAttempts)
    }
  }

  disconnect() {
    this.ws?.close()
    this.ws = null
  }
}

export const wsClient = new WebSocketClient()
```

### Real-time Hook

```typescript
// src/hooks/useWebSocket.ts
import { useEffect } from 'react'
import { wsClient } from '@/lib/websocket'

export function useWebSocket(event: string, callback: Function) {
  useEffect(() => {
    wsClient.on(event, callback)
    return () => wsClient.off(event, callback)
  }, [event, callback])
}

// Usage
function EmotionLiveUpdate() {
  const [emotion, setEmotion] = useState(null)

  useWebSocket('emotion_update', (data) => {
    setEmotion(data)
  })

  return <div>Emotion: {emotion}</div>
}
```

---

## PERFORMANCE OPTIMIZATION

### Key Metrics to Optimize

```
Core Web Vitals:
├─ LCP (Largest Contentful Paint) < 2.5s
├─ FID (First Input Delay) < 100ms
├─ CLS (Cumulative Layout Shift) < 0.1
├─ TTFB (Time to First Byte) < 600ms
└─ FCP (First Contentful Paint) < 1.8s
```

### Optimization Strategies

#### 1. Code Splitting

```typescript
// app/emotions/page.tsx
import dynamic from 'next/dynamic'

const EmotionChart = dynamic(
  () => import('@/components/dashboard/EmotionChart'),
  { loading: () => <div>Loading chart...</div> }
)

// Chart library loaded only when route accessed
```

#### 2. Image Optimization

```typescript
import Image from 'next/image'

export function Avatar({ src, alt }: Props) {
  return (
    <Image
      src={src}
      alt={alt}
      width={40}
      height={40}
      priority // For above-the-fold images
    />
  )
}
```

#### 3. Server-side Data Caching

```typescript
// app/emotions/page.tsx
import { cache } from 'react'

const getEmotions = cache(async () => {
  // Deduplicates identical requests in single render
  return fetch(`${API_URL}/emotions`)
})

export default async function Page() {
  const emotions = await getEmotions()
  return <EmotionChart data={emotions} />
}
```

#### 4. Font Optimization

```typescript
// app/layout.tsx
import { Geist, Geist_Mono } from 'next/font/google'

const geist = Geist({
  subsets: ['latin'],
  variable: '--font-geist',
})

export default function RootLayout() {
  return (
    <html className={geist.variable}>
      <body>...</body>
    </html>
  )
}
```

#### 5. Bundle Analysis

```bash
# Add to package.json scripts
"analyze": "ANALYZE=true next build"

# Run to see bundle size
npm run analyze
```

---

## STYLING & ANIMATION

### Tailwind CSS + CSS Variables

```typescript
// app/layout.tsx
import './globals.css'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>{children}</body>
    </html>
  )
}
```

```css
/* src/styles/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --color-primary: #6366f1;
    --color-secondary: #8b5cf6;
    --color-danger: #ef4444;
  }

  body {
    @apply bg-slate-50 text-slate-900;
  }
}

@layer components {
  .card {
    @apply bg-white rounded-lg shadow-md p-4;
  }

  .btn-primary {
    @apply bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700;
  }
}
```

### Framer Motion Animations

```typescript
// src/components/audio/AudioVisualizer.tsx
'use client'

import { motion } from 'framer-motion'

export function AudioVisualizer({ amplitude }: { amplitude: number }) {
  return (
    <motion.div
      animate={{ scaleY: amplitude }}
      transition={{ type: 'spring', stiffness: 200 }}
      className="w-2 h-20 bg-indigo-500 rounded"
    />
  )
}
```

---

## TESTING STRATEGY

### Test Pyramid

```
        🔺 E2E Tests
       (10-15%)
      ╱───────────╲
     ╱             ╲
    ╱   Integration  ╲
   ╱     Tests       ╲
  ╱     (30-40%)       ╲
 ╱─────────────────────╲
        Unit Tests
        (50-60%)
```

### Unit Test Example

```typescript
// src/utils/formatting.test.ts
import { formatStressLevel } from './formatting'

describe('formatStressLevel', () => {
  it('returns low for values under 30', () => {
    expect(formatStressLevel(20)).toBe('Low')
  })

  it('returns high for values over 70', () => {
    expect(formatStressLevel(80)).toBe('High')
  })

  it('returns moderate for values between 30-70', () => {
    expect(formatStressLevel(50)).toBe('Moderate')
  })
})
```

### Component Test Example

```typescript
// src/components/common/Button.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from './Button'

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick when clicked', async () => {
    const onClick = jest.fn()
    render(<Button onClick={onClick}>Click</Button>)
    await userEvent.click(screen.getByText('Click'))
    expect(onClick).toHaveBeenCalled()
  })

  it('shows loading state', () => {
    render(<Button isLoading>Submit</Button>)
    expect(screen.getByText('...')).toBeInTheDocument()
  })
})
```

---

## MIGRATION ROADMAP

### Step-by-Step Implementation

#### Week 1: Foundation
- [ ] Initialize Next.js 15 project
- [ ] Setup TypeScript, ESLint, Prettier
- [ ] Create folder structure
- [ ] Setup Zustand stores
- [ ] Migrate common components

#### Week 2: Core Features
- [ ] Implement API layer (client.ts, endpoints)
- [ ] Migrate VoiceRecorder component
- [ ] Setup authentication middleware
- [ ] Create error boundaries

#### Week 3: Polish & Optimization
- [ ] Add Suspense/loading states
- [ ] Implement Server Components
- [ ] Setup monitoring (Sentry)
- [ ] Performance optimization

#### Week 4+: Testing & Refinement
- [ ] Write unit tests
- [ ] E2E tests with Playwright
- [ ] Deploy to staging
- [ ] Production release

---

## NEXT STEPS FOR PHASE 2

1. **Confirm** App Router decision ✅ (recommended)
2. **Setup** Next.js 15 project from scratch
3. **Migrate** existing React components incrementally
4. **Implement** TypeScript throughout
5. **Setup** API abstraction layer
6. **Add** proper error handling
7. **Implement** authentication
8. **Test** entire flow
9. **Deploy** to staging/production

---

## KEY DECISIONS SUMMARY

| Decision | Rationale |
|----------|-----------|
| **Next.js 15 App Router** | Server components, smaller JS, better DX |
| **TypeScript Strict Mode** | Type safety, prevents bugs |
| **Zustand** | Lightweight, pragmatic state management |
| **TanStack Query** | Server state sync, caching, deduplication |
| **Zod** | Runtime validation, type inference |
| **Tailwind CSS** | Already in use, highly productive |
| **Framer Motion** | Smooth animations without complexity |
| **Vitest** | Faster than Jest, better DX |
| **Playwright** | E2E testing, cross-browser support |

---

**Ready for Phase 3?** I'll design:
- Video-based emotion detection system
- Real-time facial analysis pipeline
- Multimodal fusion with voice
- Privacy-first video architecture

Shall I proceed?

