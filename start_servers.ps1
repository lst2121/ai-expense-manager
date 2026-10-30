# ==============================================================================
# One-Click Local Development Launcher (Backend + Frontend)
# ==============================================================================
Write-Host "Starting Optum / AI Expense Manager Services..." -ForegroundColor Cyan

# 1. Start FastAPI Backend in background
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; Write-Host 'FastAPI Backend Running on http://127.0.0.1:8000' -ForegroundColor Green; .\ai-expense-venv\Scripts\python.exe -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload"

# 2. Start React/Vite Frontend in background
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; Write-Host 'Vite Frontend Running on http://localhost:5173' -ForegroundColor Cyan; npm run dev"

Write-Host "Services launched successfully!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host "Backend API: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
