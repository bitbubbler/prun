# Coding Guidelines for GitHub Copilot

This file contains coding guidelines and rules for this project.

## Python Guidelines

### Pydantic v2
We use pydantic v2. This means we should not use any deprecated patterns from pydantic v1.

### Modern Python Types (Python 3.12+)
This project is using python 3.12. In Python 3.12 and above:

* **Do not** use `import typing` or `from typing import List, Dict, Optional, …` for container or union types.  
* **Use** PEP-585 built-in generics:
  - `list[int]` instead of `List[int]`
  - `dict[str, int]` instead of `Dict[str, int]`
  - `str | None` instead of `Optional[str]`
  - `tuple[int, …]` instead of `Tuple[int, …]`

## Project Structure

### Frontend Structure
The frontend is organized around these key files:

- `frontend/src/App.tsx`: Main application component that uses DataProvider and handles tab navigation
- `frontend/src/context/DataContext.tsx`: Central data context that manages API interactions and state 
- Component directory: `frontend/src/components/` contains individual feature components:
  - `InternalOffers.tsx`: Component for managing internal offers
  - Other tab components (Planets, Buildings, etc.)

### Data Flow
- Data is fetched and stored in the DataContext
- Components subscribe to the context using the `useDataContext` hook

### Frontend Setup
- The frontend code is located in the `frontend/` directory
- All package management and dependency installation must be done within the `frontend/` directory
- `frontend/package.json` contains all frontend dependencies
- Do not attempt to install packages at the root level or create a root-level package.json

### Package Management
- All npm commands should be run from the `frontend/` directory
- Installation command: `cd frontend && npm install`

### Dependencies
- React 19.x
- Material-UI v7.x
- Data Grid v8.x
- TypeScript 5.x

## Server Management

### Critical Rule: Do NOT Start Servers

Under no circumstances should you attempt to start any servers in this project. The servers are already running and managed by the user. Specifically:

1. Do NOT run commands like:
   - `npm run dev`
   - `npm start` 
   - Any command that would start the frontend React application
   - Any command that would start the backend Python application

2. When making changes to the codebase:
   - Code changes will be automatically applied
   - The user handles server restarts when needed
   - Do not suggest starting or restarting servers

### Project Structure
This project consists of:
- A React frontend in the `frontend/` directory 
- A Python backend in the `fly/` directory
- Both are already running and managed separately by the user
