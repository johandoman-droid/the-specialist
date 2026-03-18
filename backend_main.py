import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

app = FastAPI()

# --- SPECIALIST FORMULA V3 ENGINE ---
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

# --- API ROUTE ---
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
            # MOCK DATA FOR LAUNCH (Connect real BS4 selectors here for auto-scrape)
            test_data = [
                {"horse": "SPECIALIST PICK", "mr": 94, "nt": 0.82, "gm": 11, "odds": 4.5},
                {"horse": "HIDDEN DANGER", "mr": 88, "nt": 0.75, "gm": 6, "odds": 14.0},
                {"horse": "MARKET TRAP", "mr": 96, "nt": 0.65, "gm": -8, "odds": 2.2}
            ]
            return {"status": "success", "results": specialist_v3(test_data)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# --- ELITE MOBILE UI (NEON RED/BLACK) ---
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>THE SPECIALIST</title>
        <style>
            body { background-color: #000; color: #fff; font-family: ui-sans-serif, system-ui; }
            .neon-text { text-shadow: 0 0 10px rgba(220, 38, 38, 0.5); }
            .specialist-card { border-left: 4px solid #dc2626; background: linear-gradient(90deg, #111 0%, #000 100%); }
        </style>
    </head>
    <body class="pb-24">
        <header class="p-8 border-b border-zinc-900 text-center">
            <h1 class="text-4xl font-black italic tracking-tighter text-red-600 uppercase neon-text">THE SPECIALIST</h1>
            <p class="text-[9px] tracking-[0.4em] uppercase opacity-40 mt-1 font-bold">AI Racing Intelligence V3</p>
        </header>

        <div class="p-5 max-w-md mx-auto">
            <input id="urlInput" type="text" placeholder="PASTE RACINGSKEEM URL..." class="w-full bg-zinc-900 border border-zinc-800 p-4 rounded-xl text-xs mb-3 outline-none focus:ring-2 ring-red-600 transition-all text-white">
            <button onclick="runScan()" id="btn" class="w-full bg-red-600 py-4 rounded-xl font-black uppercase italic tracking-tighter shadow-lg active:scale-95 transition-all">Execute V3 Scan</button>
            
            <div id="loading" class="hidden mt-8 text-center animate-pulse text-red-500 font-bold text-xs uppercase italic tracking-widest">
                Analyzing Intelligence...
            </div>

            <div id="results" class="mt-8 space-y-3"></div>
        </div>

        <footer class="fixed bottom-0 w-full bg-black/80 backdrop-blur-xl border-t border-zinc-900 p-6 flex justify-around items-center">
            <div class="w-2 h-2 rounded-full bg-red-600 animate-pulse"></div>
            <span class="text-[10px] font-black uppercase tracking-tighter opacity-50">System Operational • V3 Engine Active</span>
        </footer>

        <script>
            async function runScan() {
                const url = document.getElementById('urlInput').value;
                const resultsDiv = document.getElementById('results');
                const loading = document.getElementById('loading');
                if(!url) return alert('Paste a URL first');

                loading.classList.remove('hidden');
                resultsDiv.innerHTML = '';

                try {
                    const res = await fetch(`/api/v1/scan?url=${url}`);
                    const data = await res.json();
                    loading.classList.add('hidden');

                    if(data.results) {
                        data.results.forEach((r, i) => {
                            resultsDiv.innerHTML += `
                                <div class="specialist-card p-5 rounded-2xl border border-zinc-900 flex justify-between items-center shadow-2xl animate-in fade-in slide-in-from-bottom-2">
                                    <div>
                                        <p class="text-[10px] font-black text-zinc-500 uppercase italic">Rank #${i+1}</p>
                                        <h3 class="text-lg font-black uppercase italic leading-none">${r.horse}</h3>
                                        <p class="text-[9px] text-zinc-600 mt-2 font-bold uppercase">SPD Rank: ${r.sr} | MR: ${r.mr}</p>
                                    </div>
                                    <div class="bg-red-600 px-3 py-1 rounded-lg text-xl font-black italic shadow-inner">${r.score}</div>
                                </div>
                            `;
                        });
                    } else { alert('Engine Error: Check URL'); }
                } catch(e) { loading.classList.add('hidden'); alert('Connection Error'); }
            }
        </script>
    </body>
    </html>
    """
