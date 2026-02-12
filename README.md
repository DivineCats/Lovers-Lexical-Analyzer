# Lovers

A custom programming language with a lexical analyzer (lexer) backend and an interactive web editor frontend.

## Prerequisites

- **Python 3** (for backend)
- **Node.js** and **npm** (for frontend)

## Installation

### Backend dependencies

From the project root:

```bash
pip install flask
pip install flask-cors
```

### Frontend dependencies

From the project root:

```bash
cd frontend
npm install
npm install monaco-editor @monaco-editor/react
npm install @mui/material @emotion/react @emotion/styled
cd ..
```

Or install everything in one go from the project root:

```bash
pip install flask flask-cors
cd frontend && npm install && npm install monaco-editor @monaco-editor/react @mui/material @emotion/react @emotion/styled && cd ..
```

## Running the project

Run the **backend** and **frontend** in two separate terminals.

### 1. Backend

**Run from the project root** (do not `cd` into `backend`—Python needs to find the `Backend` package):

```bash
python -m Backend.Lexical.main
```

Leave this terminal running.

### 2. Frontend

In a new terminal, from the project root:

```bash
cd frontend
npm run dev
```

Then open the URL shown in the terminal (usually `http://localhost:5173`) in your browser.

## Project structure

- **`backend/`** — Flask API and Lexical (lexer) components
- **`frontend/`** — React + Vite app with Monaco editor and MUI
- **`docs/`** — Documentation and test cases
