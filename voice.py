import os, subprocess, json

def _detect_backend():
    try:
        from jnius import autoclass  # noqa
        return "android"
    except Exception:
        pass
    if os.path.isdir("/data/data/com.termux/files/usr"):
        return "termux"
    return "stub"

class Voice:
    def __init__(self, name="Симон", force=None):
        self.name = name
        self.backend = force or _detect_backend()
        self._tts = None

    def say(self, text):
        if self.backend == "android":
            try:
                from jnius import autoclass
                if self._tts is None:
                    Locale = autoclass("java.util.Locale")
                    PythonActivity = autoclass("org.kivy.android.PythonActivity")
                    TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
                    self._tts = TextToSpeech(PythonActivity.mActivity, None)
                    self._tts.setLanguage(Locale("ru"))
                self._tts.speak(text, 0, None, None)
                return
            except Exception:
                pass
        if self.backend == "termux":
            try:
                subprocess.run(["termux-tts-speak", text], timeout=30)
                return
            except Exception:
                pass
        print(self.name + ": " + text)

    def alert(self, level):
        # 1 — мягкий сигнал, 2 — двойной сигнал, 3 — сирена
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "assets", "alert_%d.wav" % min(level, 3))
        if self.backend == "android":
            try:
                from jnius import autoclass
                MediaPlayer = autoclass("android.media.MediaPlayer")
                mp = MediaPlayer()
                mp.setDataSource(path)
                mp.prepare()
                mp.start()
                return
            except Exception:
                pass
        if self.backend == "termux":
            try:
                subprocess.run(["play-audio", path], timeout=30)
                return
            except Exception:
                pass
        print("[звук внимания, уровень %d]" % level)

    def listen(self, prompt, timeout):
        if self.backend == "termux":
            try:
                r = subprocess.run(["termux-dialog", "speech", "-t", prompt],
                                   capture_output=True, text=True, timeout=timeout + 10)
                try:
                    d = json.loads(r.stdout)
                    return (d.get("text") or "").strip()
                except Exception:
                    return None
            except Exception:
                return None
        # резервный ввод с таймаутом (posix)
        try:
            import select, sys
            print(self.name + " (вопрос): " + prompt)
            r, _, _ = select.select([sys.stdin], [], [], timeout)
            if r:
                return sys.stdin.readline().strip()
        except Exception:
            pass
        return None
