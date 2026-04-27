import time
import os
import json
import queue
import threading
import webbrowser
import sqlite3
import numpy as np
import tkinter as tk
from tkinter import scrolledtext
import pyttsx3
import speech_recognition as sr
from openai import OpenAI


# =========================
# CONFIG
# =========================

class Config:
    OPENAI_API_KEY = "BURAYA_KEY"
    MODEL = "gpt-4o-mini"


# =========================
# VOICE ENGINE
# =========================

class Voice:
    def __init__(self):
        self.engine = pyttsx3.init()

    def speak(self, text):
        print("AKILLI:", text)

        def run():
            self.engine.say(text)
            self.engine.runAndWait()

        threading.Thread(target=run, daemon=True).start()


# =========================
# AUDIO INPUT
# =========================

class Audio:
    def __init__(self):
        self.rec = sr.Recognizer()

    def listen(self):
        try:
            with sr.Microphone() as source:
                print("Dinleniyor...")
                self.rec.adjust_for_ambient_noise(source)
                audio = self.rec.listen(source)

            text = self.rec.recognize_google(audio, language="tr-TR")
            print("Sen:", text)
            return text.lower()

        except:
            return ""


# =========================
# MEMORY BRAIN (SQLite + Vector-lite)
# =========================

class Memory:
    def __init__(self):
        self.db = sqlite3.connect("brain.db", check_same_thread=False)
        self.cur = self.db.cursor()

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS memory(
            id INTEGER PRIMARY KEY,
            text TEXT,
            ts REAL
        )
        """)
        self.db.commit()

    def add(self, text):
        self.cur.execute("INSERT INTO memory(text, ts) VALUES(?,?)",
                         (text, time.time()))
        self.db.commit()

    def last(self, n=5):
        self.cur.execute("SELECT text FROM memory ORDER BY id DESC LIMIT ?", (n,))
        return [x[0] for x in self.cur.fetchall()]


# =========================
# PLUGIN SYSTEM
# =========================

class PluginSystem:
    def __init__(self):
        self.plugins = {}

    def register(self, name, func):
        self.plugins[name] = func

    def run(self, name, text):
        if name in self.plugins:
            return self.plugins[name](text)
        return None


# =========================
# TOOLS
# =========================

class Tools:
    def time(self):
        return time.strftime("%H:%M:%S")

    def date(self):
        return time.strftime("%d.%m.%Y")

    def youtube(self):
        webbrowser.open("https://youtube.com")
        return "YouTube açıldı"

    def google(self):
        webbrowser.open("https://google.com")
        return "Google açıldı"


# =========================
# LLM ENGINE
# =========================

class LLM:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def ask(self, prompt, memory):
        try:
            res = self.client.chat.completions.create(
                model=Config.MODEL,
                messages=[
                    {"role": "system", "content": "Sen AKILLI 9.0 isimli gelişmiş bir AI assistantsin."},
                    {"role": "user", "content": f"Memory: {memory}\n\nUser: {prompt}"}
                ]
            )
            return res.choices[0].message.content

        except Exception as e:
            return str(e)


# =========================
# AI CORE
# =========================

class Agent:
    def __init__(self):
        self.voice = Voice()
        self.audio = Audio()
        self.memory = Memory()
        self.llm = LLM()
        self.tools = Tools()
        self.plugins = PluginSystem()

        self._load_plugins()

    def _load_plugins(self):
        self.plugins.register("youtube", lambda x: self.tools.youtube())
        self.plugins.register("google", lambda x: self.tools.google())

    def router(self, text):

        if "saat" in text:
            return self.tools.time()

        if "tarih" in text:
            return self.tools.date()

        if "youtube" in text:
            return self.plugins.run("youtube", text)

        if "google" in text:
            return self.plugins.run("google", text)

        return None

    def think(self, text):

        tool = self.router(text)
        if tool:
            return tool

        return self.llm.ask(text, self.memory.last(5))

    def run(self, text):
        self.memory.add(text)
        return self.think(text)


# =========================
# GUI (JARVIS STYLE)
# =========================

class GUI:
    def __init__(self):
        self.ai = Agent()

        self.root = tk.Tk()
        self.root.title("AKILLI 9.0")
        self.root.geometry("600x700")

        self.chat = scrolledtext.ScrolledText(self.root)
        self.chat.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.entry = tk.Entry(self.root)
        self.entry.pack(fill=tk.X, padx=10)

        self.entry.bind("<Return>", self.send)

        self.btn = tk.Button(self.root, text="Gönder", command=self.send)
        self.btn.pack()

        self.voice = Voice()
        self.audio = Audio()

        threading.Thread(target=self.voice_loop, daemon=True).start()

    def send(self, event=None):
        text = self.entry.get()
        self.entry.delete(0, tk.END)

        self.chat.insert(tk.END, f"Sen: {text}\n")

        response = self.ai.run(text)

        self.chat.insert(tk.END, f"AKILLI: {response}\n\n")

        self.voice.speak(response)

    def voice_loop(self):
        while True:
            text = self.audio.listen()

            if text:
                self.chat.insert(tk.END, f"Sen (ses): {text}\n")

                response = self.ai.run(text)

                self.chat.insert(tk.END, f"AKILLI: {response}\n\n")

                self.voice.speak(response)

    def run(self):
        self.voice.speak("AKILLI 9.0 aktif")
        self.root.mainloop()


# =========================
# START
# =========================

if __name__ == "__main__":
    GUI().run()