import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

app = FastAPI()

# --- 1. SPECIALIST FORMULA V3 ENGINE ---
def specialist_v3(runners):
    # Hidden Speed Rank Logic
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
        
        scored.append({
            "horse": r['horse'], 
            "score": s, 
            "sr": sr, 
            "mr": r['mr'], 
            "nt": r['nt']
        })
    return sorted(scored, key=lambda x: x['score'], reverse=True)

# --- 2. REAL AUTO-SCRAPER ROUTE ---
@app.get("/api/v1/scan")
def scan(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1")
        page = context.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(2) # Wait for table to load
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            browser.close()

            # Target RacingSkeem Table
            runners = []
            rows = soup.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 5: continue
                
                # Find Horse Name
                name_link = row.find("a", href=lambda x: x and "/horse/" in x)
                if not name_link: continue
                horse = name_link.text.strip()

                # Find MR and N-Time
                mr, nt = 0, 0.0
                for td in cells:
                    txt = td.text.strip()
                    if txt.isdigit() and 60 < int(txt) < 130: mr = int(txt)
                    if "." in txt and txt.startswith("0"): 
                        try: nt = float(txt)
                        except: pass
                
                runners.append({"horse": horse, "mr": mr, "nt": nt, "odds": 0.0, "gm": 0.0})

            if not runners: return {"status": "error", "message": "No runners found"}
            
            results = specialist_v3(runners)
            return {"status": "success", "results": results}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# --- 3. ELITE MOBILE UI (NEON RED/BLACK) ---
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>THE SPECIALIST HORSE PICKS</title>
        <style>
            body { background-color: #000; color: #fff; font-family: sans-serif; }
            .neon-border { box-shadow: 0 0 15px rgba(220, 38, 38, 0.3); }
            .card-gradient { background: linear-gradient(135deg, #111 0%, #050505 100%); }
        </style>
    </head>
    <body class="pb-24">
        <header class="p-8 border-b border-zinc-900 text-center">
            <h1 class="text-4xl font-black italic tracking-tighter text-red-600 uppercase">THE SPECIALIST</h1>
            <p class="text-[10px] tracking-[0.4em] uppercase opacity-40 mt-1 font-bold">Horse Picks Intelligence</p>
        </header>

        <div class="p-5 max-w-md mx-auto">
            <input id="urlInput" type="text" placeholder="PASTE RACINGSKEEM URL..." class="w-full bg-zinc-900 border border-zinc-800 p-4 rounded-xl text-xs mb-3 outline-none focus:ring-2 ring-red-600 text-white">
            <button onclick="runScan()" id="btn" class="w-full bg-red-600 py-4 rounded-xl font-black uppercase italic tracking-tighter shadow-lg active:scale-95 transition-all">Execute V3 Scan</button>
            
            <div id="loading" class="hidden mt-10 text-center">
                <div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-red-600 border-r-transparent"></div>
                <p class="mt-4 text-[10px] text-red-500 font-bold uppercase tracking-widest">Scraping Track Data...</p>
            </div>

            <div id="results" class="mt-8 space-y-3"></div>
        </div>

        <nav class="fixed bottom-0 w-full bg-black/90 backdrop-blur-md border-t border-zinc-900 p-6 flex justify-around">
            <span class="text-[10px] font-black uppercase text-red-500">Live Mode</span>
            <span class="text-[10px] font-black uppercase text-zinc-600">Portfolio</span>
            <span class="text-[10px] font-black uppercase text-zinc-600">AI Lab</span>
        </nav>

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

                    if(data.results && data.results.length > 0) {
                        data.results.forEach((r, i) => {
                            resultsDiv.innerHTML += `
                                <div class="card-gradient p-5 rounded-2xl border border-zinc-900 flex justify-between items-center shadow-2xl neon-border">
                                    <div>
                                        <p class="text-[10px] font-bold text-zinc-600 uppercase">Rank #${i+1}</p>
                                        <h3 class="text-lg font-black uppercase italic">${r.horse}</h3>
                                        <p class="text-[9px] text-zinc-500 mt-1 uppercase font-bold">MR: ${r.mr} | SPD Rank: ${r.sr} | NT: ${r.nt}</p>
                                    </div>
                                    <div class="bg-red-600 px-4 py-2 rounded-lg text-xl font-black italic">${r.score}</div>
                                </div>
                            `;
                        });
                    } else { alert('No Runners Found. Ensure it is a specific Race Page.'); }
                } catch(e) { loading.classList.add('hidden'); alert('Scraper Busy. Try again.'); }
            }
        </script>
    </body>
    </html>
    """
