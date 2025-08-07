# EDAPGui.py

import tkinter as tk
import tkinter.ttk as ttk
import os
from ED_AP import EDAutopilot
from EDlogger import logger
from Overlay import Overlay
from directinput import DirectInput
from EDGalaxyMap import GalaxyMap
from Screen import Screen
from EDGraphicsSettings import EDGraphicsSettings
import json

CONFIG_FILE = './configs/AP.json'
SHIP_CONFIG_FILE = './configs/ship_configs.json'

class APGui:
    def __init__(self, root):
        self.root = root
        self.root.title("ED Autopilot")
        self.root.geometry("600x400")

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

        self.stop_button = ttk.Button(self.root, text="Stop Autopilot", command=self.stop_autopilot)
        self.stop_button.pack(pady=5)

    def start_autopilot(self):
        self.label.config(text="Autopilot Running")
        logger.info("Autopilot démarré")
        self.ed_ap.run()

    def stop_autopilot(self):
        self.label.config(text="Autopilot Stopped")
        logger.info("Autopilot arrêté")
        self.ed_ap.stop()

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            logger.info("Configuration chargée depuis AP.json")
            return config
        except Exception as e:
            logger.warning(f"read_config error :{e}")
            return {}

    def load_ship_configs(self):
        try:
            with open(SHIP_CONFIG_FILE, 'r') as f:
                ship_config = json.load(f)
            logger.info("Configuration des vaisseaux chargée")
            return ship_config
        except Exception as e:
            logger.warning(f"read_ship_configs error :{e}")
            return {}

    def callback(self, msg):
        logger.info(f"Callback: {msg}")


def main():
    try:
        gfx_settings = EDGraphicsSettings()
    except Exception as e:
        logger.error(str(e))
        return

    root = tk.Tk()
    app = APGui(root)
    root.mainloop()


if __name__ == '__main__':
    main()
