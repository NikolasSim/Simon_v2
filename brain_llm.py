import os

def llm_reply(prompt, system=None, timeout=30):
    key = os.environ.get("JARVIS_API_KEY")
    if not key:
        return None
    url = os.environ.get("JARVIS_API_URL") or "https://api.openai.com/v1/chat/completions"
    model = os.environ.get("JARVIS_MODEL") or "gpt-4o-mini"
    try:
        import requests
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": model, "messages": messages, "max_tokens": 500}
        r = requests.post(url, json=payload,
                          headers={"Authorization": "Bearer " + key,
                                   "Content-Type": "application/json"},
                          timeout=timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None
