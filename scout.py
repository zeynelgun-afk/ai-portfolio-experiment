#!/usr/bin/env python3
import os
import json
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def env(key, default=""):
    val = os.environ.get(key)
    if val: return val
    try:
        with open(os.path.join(BASE_DIR, ".env")) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.strip().split("=", 1)[1]
    except Exception:
        pass
    return default

def get_fmp(endpoint, api_key, limit=20):
    url = f"https://financialmodelingprep.com/stable/{endpoint}"
    params = f"?apikey={api_key}&limit={limit}" if "?" not in url else f"&apikey={api_key}&limit={limit}"
    try:
        req = urllib.request.Request(url + params)
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        print(f"FMP error {endpoint}: {e}")
        return []

def run_scout():
    fmp_key = env("FMP_API_KEY")
    or_key = env("OPENROUTER_API_KEY")
    
    if not fmp_key or not or_key:
        print("Missing API keys for Scout.")
        return

    print("Fetching market pulse for Scout Agent...")
    articles = get_fmp("fmp-articles", fmp_key, 30)
    gainers = get_fmp("biggest-gainers", fmp_key, 10)
    
    news_text = "\n".join([f"- {a.get('title')}: {a.get('content', '')[:200]}" for a in articles])
    gainers_text = ", ".join([g.get("symbol", "") for g in gainers])

    prompt = f"""You are the Alpha Scout Agent. Your job is to find 15-20 highly asymmetric, bottleneck-solving, or pivoting US stock tickers based on current market trends.
Do not pick boring mega-caps unless they are doing something new. Look for:
- Companies solving critical bottlenecks (e.g. power, cooling, optical interconnects).
- Companies pivoting their business model (e.g. miners becoming AI datacenters).
- Companies acting as 'pick and shovel' plays for huge trends.

Recent Macro News:
{news_text}

Top Gainers Today:
{gainers_text}

Based on this pulse and your deep knowledge of supply chains, return a JSON array of 15 to 20 ticker symbols.
DO NOT return markdown blocks. Return ONLY a valid JSON array like: ["VRT", "COHR", "ARM", "SMCI"]"""

    print("Asking LLM to hunt for dynamic watchlist...")
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "openai/gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5
            }).encode("utf-8")
        )
        with urllib.request.urlopen(req, timeout=30) as res:
            answer = json.loads(res.read().decode("utf-8"))["choices"][0]["message"]["content"].strip()
            # Clean up markdown if any
            if answer.startswith("```json"): answer = answer[7:]
            if answer.startswith("```"): answer = answer[3:]
            if answer.endswith("```"): answer = answer[:-3]
            
            new_symbols = json.loads(answer.strip())
            
            # Must always include current portfolio!
            port_path = os.path.join(BASE_DIR, "portfolio.json")
            if os.path.exists(port_path):
                with open(port_path) as f:
                    port = json.load(f)
                    for pos in port.get("positions", []):
                        if pos["symbol"] not in new_symbols:
                            new_symbols.append(pos["symbol"])
            
            # Save to watchlist
            state_dir = os.path.join(BASE_DIR, "state")
            os.makedirs(state_dir, exist_ok=True)
            with open(os.path.join(state_dir, "watchlist.json"), "w") as f:
                json.dump(list(set(new_symbols)), f, indent=2)
            
            print(f"Scout Agent successfully generated dynamic pool: {len(new_symbols)} symbols.")
            print(new_symbols)
    except Exception as e:
        print(f"Scout Agent failed: {e}")

if __name__ == "__main__":
    run_scout()
