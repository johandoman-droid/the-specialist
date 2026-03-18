"use client";
import { useState } from 'react';

export default function App() {
  const [activeTab, setActiveTab] = useState('live');
  const [url, setUrl] = useState('');
  const [results, setResults] = useState([]);

  const runScan = async () => {
    const res = await fetch(`/api/v1/scan?url=${url}`);
    const data = await res.json();
    if (data.results) setResults(data.results);
  };

  return (
    <div className="min-h-screen bg-black text-white font-sans max-w-md mx-auto border-x border-zinc-900 shadow-2xl pb-24">
      <header className="p-8 border-b border-red-600/20 text-center">
        <h1 className="text-4xl font-black italic tracking-tight text-red-600 uppercase italic">The Specialist</h1>
        <p className="text-[9px] tracking-[0.4em] uppercase opacity-40 mt-1 font-bold">AI Racing Intelligence V3</p>
      </header>

      <nav className="flex border-b border-zinc-900 bg-zinc-950/50 sticky top-0 z-50 backdrop-blur-md">
        {['live', 'portfolio', 'lab'].map((t) => (
          <button key={t} onClick={() => setActiveTab(t)} className={`flex-1 py-4 text-[10px] font-black uppercase tracking-widest ${activeTab === t ? 'text-red-500 border-b-2 border-red-600 bg-red-600/5' : 'text-zinc-600'}`}>
            [{t}]
          </button>
        ))}
      </nav>

      <main className="p-5">
        <input className="w-full bg-zinc-900 border border-zinc-800 p-4 rounded-xl text-xs mb-3 focus:ring-2 ring-red-600 outline-none" placeholder="PASTE RACINGSKEEM URL..." value={url} onChange={(e) => setUrl(e.target.value)} />
        <button onClick={runScan} className="w-full bg-red-600 py-4 rounded-xl font-black uppercase italic tracking-tighter shadow-lg active:scale-95 transition-all">Execute V3 Scan</button>
        
        <div className="mt-8 space-y-3">
          {results.map((r, i) => (
            <div key={i} className="bg-zinc-900 p-5 rounded-2xl border-l-4 border-red-600 flex justify-between items-center shadow-xl">
              <div>
                <p className="text-[10px] font-black text-zinc-500 uppercase italic">Rank #{i+1}</p>
                <h3 className="text-lg font-black uppercase italic leading-none">{r.horse}</h3>
              </div>
              <div className="bg-red-600 px-3 py-1 rounded-lg text-xl font-black italic shadow-inner">{r.score}</div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
