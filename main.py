import os

def get_agent():
    from agent import SimonAgent
    return SimonAgent(use_voice=True)

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

class SimonApp(App):
    title = "Simon"

    def build(self):
        self.agent = None
        root = BoxLayout(orientation="vertical", padding=8, spacing=8)
        self.log = Label(text="Симон к вашим услугам, сэр.", halign="left",
                         valign="top", size_hint_y=None)
        self.log.bind(width=lambda i, w: setattr(self.log, "text_size", (w, None)))
        self.log.bind(texture_size=lambda i, s: setattr(self.log, "height", s[1]))
        scroll = ScrollView()
        scroll.add_widget(self.log)
        root.add_widget(scroll)
        row = BoxLayout(size_hint_y=None, height=44, spacing=6)
        self.input = TextInput(multiline=False)
        self.input.bind(on_text_validate=self.send)
        row.add_widget(self.input)
        btn = Button(text="Отправить", size_hint_x=None, width=110)
        btn.bind(on_press=self.send)
        row.add_widget(btn)
        root.add_widget(row)
        return root

    def send(self, *a):
        text = self.input.text.strip()
        if not text:
            return
        self.input.text = ""
        if self.agent is None:
            self.agent = get_agent()
        reply = self.agent.handle(text) or "..."
        self.log.text += "\n\n[в] " + text + "\n[Симон] " + reply
        try:
            self.agent.voice.say(reply)
        except Exception:
            pass

if __name__ == "__main__":
    SimonApp().run()
