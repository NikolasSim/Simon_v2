import json, socket, urllib.request, urllib.parse

TIMEOUT = 5
HEADERS = {"User-Agent": "SimonAssistant/1.0"}

def is_online():
    try:
        socket.create_connection(("ru.wikipedia.org", 443), timeout=3)
        return True
    except Exception:
        return False

def wiki_lookup(question):
    try:
        q = urllib.parse.quote(question)
        url = ("https://ru.wikipedia.org/w/api.php?action=query&list=search"
               "&srsearch=" + q + "&format=json&utf8=1&srlimit=1")
        req = urllib.request.Request(url, headers=HEADERS)
        data = json.load(urllib.request.urlopen(req, timeout=TIMEOUT))
        hits = data.get("query", {}).get("search", [])
        if not hits:
            return None
        title = urllib.parse.quote(hits[0]["title"])
        url2 = "https://ru.wikipedia.org/api/rest_v1/page/summary/" + title
        req2 = urllib.request.Request(url2, headers=HEADERS)
        d2 = json.load(urllib.request.urlopen(req2, timeout=TIMEOUT))
        text = (d2.get("extract") or "")[:400]
        if text:
            return {"text": text, "source": "https://ru.wikipedia.org/wiki/" + title}
    except Exception:
        pass
    return None

def ddg_lookup(question):
    try:
        q = urllib.parse.quote(question)
        url = "https://api.duckduckgo.com/?q=" + q + "&format=json&no_redirect=1&no_html=1"
        req = urllib.request.Request(url, headers=HEADERS)
        d = json.load(urllib.request.urlopen(req, timeout=TIMEOUT))
        text = (d.get("AbstractText") or d.get("Abstract") or "")[:400]
        src = d.get("AbstractURL") or "https://duckduckgo.com"
        if text:
            return {"text": text, "source": src}
    except Exception:
        pass
    return None

def lookup(question):
    return wiki_lookup(question) or ddg_lookup(question)

def learn_pending(memory, limit=5):
    learned = []
    if not is_online():
        return learned
    while len(learned) < limit:
        q = memory.take_pending()
        if not q:
            break
        res = lookup(q)
        if res:
            memory.remember_fact(q + ": " + res["text"], source=res["source"])
            learned.append(q)
    return learned
