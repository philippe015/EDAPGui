EDAPGui.py

import tkinter as tk import tkinter.ttk as ttk import os from ED_AP import EDAutopilot from EDlogger import logger from Overlay import Overlay from directinput import DirectInput from EDGalaxyMap import GalaxyMap from Screen import Screen from EDGraphicsSettings import EDGraphicsSettings import json

CONFIG_FILE = './configs/AP.json' SHIP_CONFIG_FILE = './configs/ship_configs.json'

class APGui: def init(self, root): self.root = root self.root.title("ED Autopilot") self.root.geometry("600x400")

self.setup_gui()

    self.scr = Screen()
    self.overlay = Overlay()
    self.directinput = DirectInput()

    self.config = self.load_config()
    self.ship_configs = self.load_ship_configs()

    self.ed_ap = EDAutopilot(cb=self.callback)
    self.ed_ap.set_overlay(self.overlay)
    self.ed_ap.set_input(self.directinput)
    self.ed_ap.set_screen(self.scr)
    self.ed_ap.load_config(self.config)

    self.gmap = GalaxyMap(self.scr, self.ed_ap)

def setup_gui(self):
    self.label = ttk.Label(self.root, text="ED Autopilot Ready")
    self.label.pack(pady=10)

    self.start_button = ttk.Button(self.root, text="Start Autopilot", command=self.start_autopilot)
    self.start_button.pack(pady=5)

    self

