import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def specialist_v3(runners):
    valid = [r for r in runners if r['nt'] > 0]
    ranked = sorted(valid, key=lambda x: (x['nt'], x['mr']), reverse=True)
    speed_map = {r['horse']: idx + 1 for idx, r in enumerate(ranked)}
    scored = []
    for r in runners:
        s = 0
        sr = speed_map.get(r['horse'], 9)
        if sr == 1: s += 5
        elif sr == 2: s += 4
        if r['nt'] >= 0.80: s += 4
        elif r['nt'] >= 0.73: s += 3
        if r['mr'] >= 90: s += 2
        if r['gm'] >= 10: s += 3
        scored.append({"horse": r['horse'], "score": s, "sr": sr, "mr": r['mr'], "nt": r['nt'], "gm": r['gm'], "odds": r['odds']})
    return sorted(scored, key=lambda x: x['score'], reverse=True)

@app.get("/api/v1/scan")
def scan(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(user_agent="Mozilla/5.0")
        page = context.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            soup = BeautifulSoup(page.content(), 'html.parser')
            browser.close()
            # Simulated data for testing (Replace with real BeautifulSoup selectors)
            test_data = [
                {"horse": "SPECIALIST PICK", "mr": 94, "nt": 0.82, "gm": 11, "odds": 4.5},
                {"horse": "HIDDEN DANGER", "mr": 88, "nt": 0.75, "gm": 6, "odds": 14.0}
            ]
            results = specialist_v3(test_data)
            return {"status": "success", "results": results}
        except Exception as e:
            return {"status": "error", "message": str(e)}

@app.get("/")
def health(): return {"status": "Specialist Engine Online"}
