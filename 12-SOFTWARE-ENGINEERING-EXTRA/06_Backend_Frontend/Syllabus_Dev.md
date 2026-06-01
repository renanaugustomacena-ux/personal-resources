# Phase 6: Modern Backend & Frontend — Syllabus

> **Last updated:** 2026-05-29

Code that runs on the server vs Code that runs in the browser.

## Module 6.1: Backend Concurrency Models

**Goal:** Handle 10k concurrent connections.

| File | Focus |
|---|---|
| [01_Backend_Concurrency.md](01_Backend_Concurrency.md) | Go goroutines/M:N scheduler, Java virtual threads, Node.js event loop, Python free-threaded, Erlang BEAM |

*   **Node.js (Event Driven):** Libuv, event loop phases, `process.nextTick()` vs `Promise.then()`.
*   **Go (CSP):** Goroutines (2KB stack), M:N Scheduler, channels.
*   **Java (Project Loom):** Virtual Threads — blocking code that doesn't block OS threads.
*   **Python 3.14:** Free-threaded mode (no-GIL), asyncio.
*   **Erlang/BEAM:** Preemptive scheduling, supervision trees, let-it-crash.

## Module 6.2: Frontend Engineering

**Goal:** 60 FPS and instant interactions.

| File | Focus |
|---|---|
| [02_Frontend_Engineering.md](02_Frontend_Engineering.md) | Rendering patterns (CSR/SSR/SSG/ISR), React 19, Vite 6, hydration, CWV, Module Federation |

*   **Rendering Patterns:** CSR, SSR, SSG, ISR, streaming SSR, RSC.
*   **Critical Rendering Path:** DOM + CSSOM = Render Tree. Layout. Paint. Composite.
*   **State Management:** Signals, Zustand, server state (TanStack Query).

## Module 6.3: Mobile & Cross-Platform

**Goal:** Ship to iOS and Android from a shared codebase.

| File | Focus |
|---|---|
| [03_Mobile_CrossPlatform.md](03_Mobile_CrossPlatform.md) | Flutter 3.x, React Native 0.79 (new arch), Kotlin Multiplatform, offline-first, mobile security |

*   **Flutter:** Dart, Skia/Impeller, widget tree, platform channels.
*   **React Native:** New Architecture (JSI, Fabric, TurboModules), Hermes.
*   **Kotlin Multiplatform:** Shared business logic, platform-specific UI.
