#!/usr/bin/env python3
import os
import json
import urllib.request
import re
from execute_trade import write_json
from prompt_policy import policy
import market_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def validate_symbols(symbols):
    if not isinstance(symbols, list) or not 15 <= len(symbols) <= 20:
        raise ValueError("Scout must return 15 to 20 ticker symbols")
    if any(not isinstance(s, str) or not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", s)
           for s in symbols):
        raise ValueError("Scout returned an invalid ticker symbol")
    if len(set(symbols)) != len(symbols):
        raise ValueError('Scout symbols must be unique')
    return symbols

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
        raise RuntimeError(f"Scout could not fetch FMP endpoint {endpoint}") from None

def run_scout():
    or_key = env("OPENROUTER_API_KEY")
    
    if not or_key:
        raise RuntimeError("Missing API keys for Scout")

    from discovery import collect
    from datetime import datetime, timezone
    discovery = collect()
    prompt = f"""You are the Alpha Scout Agent. Select 15-20 US stock candidates for deep research.
Stay within the charter's US large-cap technology, semiconductor and AI infrastructure
universe. Sector membership alone does not establish eligibility.
Use ONLY symbols present in the supplied measured discovery channels. Consider each
available channel: momentum/news, sharp declines needing fundamental verification,
structural technology/industrial/energy suppliers, and reported insider purchases.
A price decline does not prove overreaction. Sector membership does not prove an AI
bottleneck. Insider purchase data does not prove investment quality. These are research
hypotheses to verify. Compare opportunity with counterevidence and avoid choosing only
the largest recent gainers. Preserve the aggressive fundamental research mandate.
Return ONLY a JSON array of 15 to 20 unique ticker symbols from the supplied universe.
DISCOVERY INPUTS:
{json.dumps(discovery)}"""

    print("Asking LLM to hunt for dynamic watchlist...")
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "openai/gpt-4o",
                "messages": [{"role": "system", "content": policy()},
                             {"role": "user", "content": prompt}],
                "temperature": 0.5
            }).encode("utf-8")
        )
        with urllib.request.urlopen(req, timeout=30) as res:
            answer = json.loads(res.read().decode("utf-8"))["choices"][0]["message"]["content"].strip()
            # Clean up markdown if any
            if answer.startswith("```json"): answer = answer[7:]
            if answer.startswith("```"): answer = answer[3:]
            if answer.endswith("```"): answer = answer[:-3]
            
            new_symbols = validate_symbols(json.loads(answer.strip()))
            
            if any(symbol not in discovery['membership'] for symbol in new_symbols):
                raise ValueError('Scout selected a company without discovery evidence')
            selected = list(new_symbols)
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
            write_json(os.path.join(state_dir, "watchlist.json"), sorted(set(new_symbols)))
            discovery['selected'] = selected
            discovery['retained_holdings'] = sorted(set(new_symbols)-set(selected))
            write_json(os.path.join(state_dir, 'discovery.json'), discovery)
            
            print(f"Scout Agent successfully generated dynamic pool: {len(new_symbols)} symbols.")
            print(new_symbols)
    except Exception as e:
        raise RuntimeError("Scout Agent failed; watchlist generation did not complete") from None

if __name__ == "__main__":
    run_scout()
