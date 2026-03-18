import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

# --- 1. DATABASE SETUP (The Memory) ---
DATABASE_URL = "sqlite:///./data/specialist.db"
os.makedirs("./data", exist_ok=True)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Race(Base):
    __tablename__ = "races"
    id = Column(Integer, primary_key=True)
    venue = Column(String)
    race_num = Column(String)
    time = Column(String)
    url = Column(String, unique=True)
    runners_json = Column(String) # Simple storage for picks

Base.metadata.create_all(bind=engine)
app = FastAPI()

# --- 2. SPECIALIST FORMULA V3 ---
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
        scored.append({"horse": r['horse'], "score": s, "sr": sr, "mr": r['mr'], "nt": r['nt']})
    return sorted(scored, key=lambda x: x['score'], reverse=True)

# --- 3. AUTO-DISCOVERY SCRAPER ---
@app.get("/api/v1/sync")
def sync_today():
    db = SessionLocal()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(user_agent="Mozilla/5.0")
        page = context.new_page()
        stealth_sync(page)
        
        try:
            # Step A: Find Today's Meeting Links
            page.goto("https://racingskeem.co.za/", wait_until="networkidle")
            links = page.query_selector_all("a[href*='/racemeetings/meeting/']")
            meeting_urls = list(set(["https://racingskeem.co.za" + l.get_attribute("href") for l in links]))

            for m_url in meeting_urls:
                page.goto(m_url, wait_until="networkidle")
                race_links = page.query_selector_all("a[href*='/race/']")
                race_urls = list(set(["https://racingskeem.co.za" + l.get_attribute("href") for l in race_links]))

                for r_url in race_urls:
                    if db.query(Race).filter(Race.url == r_url).first(): continue
                    
                    page.goto(r_url, wait_until="networkidle")
                    page.wait_for_selector("a[href*='/horse/']", timeout=10000)
                    
                    soup = BeautifulSoup(page.content(), 'html.parser')
                    venue = soup.select_one(".venue-name").text.strip() if soup.select_one(".venue-name") else "Unknown"
                    
                    runners = []
                    for row in soup.find_all("tr"):
                        cells = row.find_all("td")
                        if len(cells) < 5: continue
                        name_link = row.find("a", href=lambda x: x and "/horse/" in x)
                        if not name_link: continue
                        
                        mr, nt = 0, 0.0
                        for td in cells:
                            txt = td.text.strip()
                            if txt.isdigit() and 60 < int(txt) < 130: mr = int(txt)
                            if "." in txt and txt.startswith("0"): 
                                try: nt = float(txt)
                                except: pass
                        runners.append({"horse": name_link.text.strip(), "mr": mr, "nt": nt})

                    if runners:
                        scored = specialist_v3(runners)
                        new_race = Race(venue=venue, url=r_url, runners_json=str(scored))
                        db.add(new_race)
                        db.commit()
            
            browser.close()
            return {"status": "success", "message": "Today's races synced"}
        except Exception as e:
            browser.close()
            return {"status": "error", "message": str(e)}

@app.get("/api/v1/races")
def get_races():
    db = SessionLocal()
    return db.query(Race).all()

# --- 4. THE AUTOMATED DASHBOARD UI ---
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>THE SPECIALIST</title>
        <style>
            body { background-color: #000; color: #fff; }
            .specialist-card { border-left: 4px solid #dc2626; background: #0a0a0a; }
            .neon-red { color: #ff0000; text-shadow: 0 0 10px rgba(255,0,0,0.5); }
        </style>
    </head>
    <body class="pb-32">
        <header class="p-8 border-b border-zinc-900 text-center sticky top-0 bg-black/90 backdrop-blur-md z-50">
            <h1 class="text-4xl font-black italic tracking-tighter text-red-600 uppercase neon-red">THE SPECIALIST</h1>
            <div class="flex justify-center gap-4 mt-2">
                <button onclick="syncData()" class="text-[9px] bg-zinc-900 px-3 py-1 rounded-full font-bold uppercase border border-zinc-800 text-zinc-400">Sync Today's Card</button>
            </div>
        </header>

        <div id="container" class="p-5 max-w-md mx-auto space-y-6">
            <div id="loading" class="text-center p-10 text-zinc-600 animate-pulse font-bold uppercase text-xs tracking-widest">
                Loading Intelligence...
            </div>
        </div>

        <nav class="fixed bottom-0 w-full bg-black border-t border-zinc-900 p-6 flex justify-around">
            <span class="text-[10px] font-black uppercase text-red-500">Today's Picks</span>
            <span class="text-[10px] font-black uppercase text-zinc-700 font-bold">Portfolio</span>
        </nav>

        <script>
            async function loadRaces() {
                const res = await fetch('/api/v1/races');
                const races = await res.json();
                const container = document.getElementById('container');
                container.innerHTML = '';
                
                if(races.length === 0) {
                    container.innerHTML = '<div class="text-center text-zinc-500 py-20 uppercase font-bold text-xs">No races synced yet. Tap "Sync Today\'s Card" above.</div>';
                    return;
                }

                races.forEach(race => {
                    const picks = eval(race.runners_json);
                    let runnersHtml = '';
                    picks.slice(0, 3).forEach((p, i) => {
                        runnersHtml += `
                            <div class="flex justify-between items-center py-2 border-b border-zinc-900 last:border-0">
                                <span class="text-sm font-bold uppercase italic text-zinc-200">#${i+1} ${p.horse}</span>
                                <span class="text-red-600 font-black italic">${p.score}</span>
                            </div>
                        `;
                    });

                    container.innerHTML += `
                        <div class="specialist-card p-5 rounded-2xl border border-zinc-900 shadow-2xl">
                            <h3 class="text-xs font-black text-zinc-500 uppercase tracking-widest mb-3">${race.venue}</h3>
                            <div class="space-y-1">${runnersHtml}</div>
                        </div>
                    `;
                });
            }

            async function syncData() {
                const btn = document.querySelector('button');
                btn.innerText = 'Syncing...';
                await fetch('/api/v1/sync');
                btn.innerText = 'Sync Today\\'s Card';
                loadRaces();
            }

            loadRaces();
        </script>
    </body>
    </html>
    """
