# Student Instructions

This project is a **monorepo** containing a FastAPI backend and a Vite + React + TypeScript frontend.

---

## Prerequisites

You need **Python 3.8+** and **Node.js 18+** installed on your machine.

### Installing Node.js (if not already installed)

**Option 1:** Download from [nodejs.org](https://nodejs.org) (LTS version recommended)

**Option 2:** Using Homebrew (macOS):
```bash
brew install node
```

---

## Project Structure

```
basic_react/              # Root project folder
├── backend/
│   ├── main.py                  # FastAPI endpoints
│   ├── requirements.txt
│   └── basic_simulation/        # Simulation engine
│       ├── __init__.py
│       ├── agent.py             # Agent class
│       ├── environment.py       # Environment with obstacles
│       └── simulation.py        # Orchestrator + behavioral logging
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── Controls.tsx         # Game controls
│   │   ├── Controls.css
│   │   ├── index.css
│   │   └── vite-env.d.ts
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
└── Student_Instructions.md
```

---

## Backend Simulation Classes

### `Agent`
- Stores position (`x`, `y`) on the grid
- `move(direction)` — moves up/down/left/right within bounds

### `Environment`
- Manages grid dimensions and moving obstacles
- Obstacles bounce off walls each step
- `check_collision(x, y)` — detects if agent hit an obstacle

### `Simulation`
- Orchestrates agent + environment
- `step(action)` — processes user action, moves obstacles, checks collision
- `export_behavioral_data()` — saves all actions to JSON for ML training

---

## Backend API: `main.py`

**FastAPI** is a modern Python web framework that creates HTTP endpoints (APIs) for the frontend to call.

### What `main.py` does:
1. **Creates a FastAPI app** — the web server that listens for HTTP requests
2. **Configures CORS** — allows the React frontend (localhost:5173) to make requests to the backend (localhost:8000)
3. **Defines endpoints** — URL routes that handle specific actions:
   - `GET /health` — returns `{"status": "ok"}` so frontend knows backend is running
   - `POST /simulation/init` — creates a new game session, returns `session_id`
   - `POST /simulation/step` — receives user action, updates game state, returns new state
   - `POST /simulation/tick/{id}` — moves obstacles only (for continuous mode)
   - `GET /simulation/state/{id}` — returns current game state
   - `GET /simulation/export/{id}` — exports all actions for ML training
4. **Stores sessions** — keeps track of active simulations in a dictionary

### Request/Response Flow
```
Frontend (React)              Backend (FastAPI)
      │                              │
      │──── POST /simulation/init ──►│  Creates Simulation object
      │◄─── {session_id, state} ─────│
      │                              │
      │──── POST /simulation/step ──►│  Calls simulation.step(action)
      │◄─── {state} ─────────────────│  Returns updated state
```

---

## What is CORS?

**CORS** (Cross-Origin Resource Sharing) is a security feature built into web browsers.

### The Problem
By default, browsers block JavaScript from making requests to a different "origin" (domain + port):
- Frontend runs on `http://localhost:5173` (Vite)
- Backend runs on `http://localhost:8000` (FastAPI)

These are **different origins** (different ports), so the browser would block the request.

### The Solution
We configure FastAPI to explicitly allow requests from our frontend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow Vite frontend
    allow_methods=["*"],                       # Allow all HTTP methods
    allow_headers=["*"],                       # Allow all headers
)
```

This tells browsers: *"It's okay, I trust requests from localhost:5173"*.

---

## Frontend: Display Layer Only

> **Important:** The React frontend contains **no simulation logic**. It is purely a display layer that renders the state received from the Python backend.

### Architecture
```
┌─────────────────────┐        ┌─────────────────────┐
│   React Frontend    │◄──────►│   Python Backend    │
│   (Display Only)    │  HTTP  │   (All Logic Here)  │
└─────────────────────┘        └─────────────────────┘
         │                              │
         ▼                              ▼
   - Render grid                 - Agent class
   - Show agent/obstacles        - Environment class
   - Capture user clicks         - Simulation class
   - Display score/game over     - Behavioral logging
```

### How It Works
1. User clicks an arrow button in React
2. React sends `POST /simulation/step` with the action to Python
3. Python moves the agent, moves obstacles, checks collisions
4. Python returns the new state to React
5. React displays the updated grid

---

## Frontend Source Files (`frontend/src/`)

### `main.tsx`
The **entry point** of the React application.
- Imports the root `App` component
- Calls `createRoot()` to mount React into the `<div id="root">` in `index.html`
- Wraps the app in `<StrictMode>` for development warnings

### `App.tsx`
The **root component** that manages the overall application.
- Uses `useState` to track health status and session ID
- Uses `useEffect` to fetch `/health` from backend on page load
- Displays backend connection status (green "ok" or red error)
- Conditionally renders the `Controls` component once backend is healthy

### `Controls.tsx`
The **main game component** containing all UI and interaction logic.
- **State management**: Stores config (grid size, obstacles), simulation state, mode, loading/error states
- **API calls**: 
  - `POST /simulation/init` — starts a new game
  - `POST /simulation/step` — sends player movement
  - `POST /simulation/tick/{id}` — triggers obstacle movement (continuous mode)
- **Continuous mode**: Uses `useEffect` + `setInterval` to tick obstacles every 500ms
- **Grid rendering**: Maps backend state to colored cells (agent=green, goal=blue, obstacles=red, collision=yellow, win=purple)
- **Game status**: Shows score, step count, win/lose messages

### `App.css` & `Controls.css`
**Styling files** with no logic.
- Define colors, gradients, animations (pulse, explode, celebrate)
- Use CSS classes like `.grid-cell.agent`, `.grid-cell.goal`, `.grid-cell.obstacle`
- Support both dark and light color schemes

### `index.css`
**Global styles** applied to the entire app.
- Sets default fonts, colors, button styles
- Defines reusable animations

### `vite-env.d.ts`
**TypeScript declaration file** (`.d.ts`) for Vite.

**What are TypeScript declarations?**
TypeScript needs to know the "shape" (types) of every variable and function. When you use a library (like Vite), TypeScript doesn't automatically know what functions it provides. Declaration files (`.d.ts`) describe the types without containing actual code.

**What this file does:**
```typescript
/// <reference types="vite/client" />
```
This single line tells TypeScript: *"Look up Vite's type definitions so you understand things like `import.meta.env` and asset imports."*

**Why it matters:**
- Without it, TypeScript would show errors like "Cannot find name 'import.meta'"
- Enables autocomplete for Vite-specific features in your IDE
- It's auto-generated by `create-vite` and you rarely need to edit it

---

## STEP 1: Running the Application

You need **two separate terminal windows** to run both servers simultaneously.

### Terminal 1: Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Backend URL:** http://localhost:8000

**Health endpoint:** http://localhost:8000/health

---

### Terminal 2: Frontend (Vite + React)

```bash
cd frontend
npm install
npm run dev
```

**Frontend URL:** http://localhost:5173

---

## Verifying Everything Works

1. Start the **backend** first (Terminal 1)
2. Start the **frontend** second (Terminal 2)
3. Open http://localhost:5173 in your browser
4. You should see the health status displayed as **"ok"** (in green)

If you see an error message instead, make sure the backend is running on port 8000.

---

## STEP 2: Playing the Game

Once the backend shows "ok", the **Simulation Controls** panel will appear.

### Configuration Sliders
- **Grid Width** (5-15): Width of the simulation grid
- **Grid Height** (5-15): Height of the simulation grid
- **Obstacles** (1-10): Number of moving obstacles

### Starting a Simulation

Choose one of two modes:

| Mode | Button | Behavior |
|------|--------|----------|
| **Step** | "Start Step Simulation" | Obstacles move only when you move |
| **Continuous** | "Start Continuous Simulation" | Obstacles move automatically every 500ms |

### Playing
- Use arrow buttons (↑ ↓ ← →) to move the agent (green)
- Avoid the moving obstacles (red)
- Each move increases your score by 1
- **Game Over** when you collide with an obstacle (yellow flash)

### Mode Differences
- **Step mode**: You control the pace. Obstacles move each time you move.
- **Continuous mode**: Real-time challenge. Obstacles move on a timer — act fast!

### Behavioral Data
All user actions are logged on the backend for ML training. Export with:
```
GET /simulation/export/{session_id}
```

---

## API Reference

| Endpoint                       | Method | Description                           |
|--------------------------------|--------|---------------------------------------|
| `/health`                      | GET    | Check backend status                  |
| `/simulation/init`             | POST   | Start new game (returns session_id)   |
| `/simulation/step`             | POST   | Move agent (+ obstacles in step mode) |
| `/simulation/tick/{id}`        | POST   | Move obstacles only (continuous mode) |
| `/simulation/state/{id}`       | GET    | Get current game state                |
| `/simulation/export/{id}`      | GET    | Export behavioral data as JSON        |

---

## STEP 3: Hosting Online (Cloud Deployment)

Want to share your game with the world? Here is how to deploy it for free.

### Backend on Render.com (Python)

*Render's Free Tier spins down after 15 minutes of inactivity. The first request might take 50 seconds to load.*

1.  **Push your code to GitHub.**
2.  **Create a free account on [Render.com](https://render.com).**
3.  **New Web Service:**
    - Connect your GitHub repo.
    - Name: `my-simulation-backend`
    - Root Directory: `.` (Leave empty. This tells Render to run commands from the main folder.)
    - Runtime: **Python 3**
    - Build Command: `pip install -r requirements.txt`
    - Start Command: `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`
    - **Instance Type:** Scroll down and select **Free** (Important!)
4.  **Wait for Deployment:** It will say "Deploying" for a few minutes. Wait until it turns **Green** ("Live").
5.  **Copy YOUR URL:** fast-copy the URL from the top-left (e.g., `https://my-backend-x82z.onrender.com`).
    *   *Warning: Do not use the example URL from this guide! Use the one Render gives you.*

### Frontend on Vercel (React)

*Vercel's Hobby Tier is free for personal projects.*

1.  **Create a free account on [Vercel.com](https://vercel.com).**
2.  **Add New Project:**
    - Import your GitHub repo.
3.  **Configure:**
    - Root Directory: `frontend`
    - Framework Preset: **Vite**
    - **Environment Variables:**
        - Name: `VITE_API_URL`
        - Value: `https://my-backend-x82z.onrender.com` (Paste **YOUR** Render URL here. No trailing slash.)
4.  **Deploy!** Vercel will give you a live URL (e.g., `https://my-game.vercel.app`).

### Final Step: Connect Them

1.  Go back to your local code.
2.  Open `backend/api/main.py`.
3.  Add your Vercel URL to the `allow_origins` list:
    ```python
    allow_origins=[
        "http://localhost:5173",
        "https://my-game.vercel.app"
    ]
    ```
4.  Push to GitHub. Render will auto-redeploy, and your game is now live!

---

## STEP 5: Saving Data (Database or Google Sheets)

By default, data is lost when the free server restarts. To save it, choose **one** option and set Environment Variables in Render.

### Option A: MongoDB (Recommended)
1.  **Create Account:** Go to [MongoDB Atlas](https://www.mongodb.com/atlas) and sign up (Free Shared Tier).
2.  **Create Cluster:** Click "Build a Database" -> "Shared" -> "Create".
3.  **Create User:** In "Database Access", create a new database user (e.g., `admin`) and save the password.
4.  **Network Access:** In "Network Access", add IP Address `0.0.0.0/0` (Allow Access from Anywhere) so Render can connect.
5.  **Get Connection String:**
    *   Click "Connect" -> "Drivers" -> "Python".
    *   Copy the string: `mongodb+srv://admin:<password>@cluster0.example.mongodb.net/?retryWrites=true&w=majority`
    *   Replace `<password>` with your real password.
6.  **Set in Render:** In Render Dashboard -> Environment Variables:
    *   Key: `MONGODB_URI`
    *   Value: (Your connection string)

### Option B: Google Sheets
This is great for seeing results in a spreadsheet.

1.  **Google Cloud Console:**
    *   Go to [console.cloud.google.com](https://console.cloud.google.com/).
    *   Create a **New Project**.
2.  **Enable APIs:**
    *   Go to "APIs & Services" -> "Library".
    *   Search for **"Google Sheets API"** -> Click Enable.
    *   Search for **"Google Drive API"** -> Click Enable.
3.  **Create Service Account:**
    *   Go to "APIs & Services" -> "Credentials".
    *   Click "Create Credentials" -> "Service Account".
    *   Name it `simulation-logger`. Click Done.
4.  **Download Keys:**
    *   Click on your new Service Account (email address).
    *   Go to "Keys" tab -> "Add Key" -> "Create new key" -> **JSON**.
    *   A `.json` file will download to your computer. **Keep this secret!**
5.  **Share the Sheet:**
    *   Create a new Google Sheet.
    *   Click "Share" and paste the **Service Account Email** (found in the JSON file, e.g., `simulation-logger@project.iam.gserviceaccount.com`).
    *   Give it "Editor" access.
6.  **Set in Render:**
    *   Key: `GOOGLE_SHEET_ID` -> Value: (The long string in your Sheet URL)
    *   Key: `GOOGLE_SHEETS_CREDENTIALS` -> Value: (Open the JSON file with a text editor, copy the **entire content**, and paste it here).

