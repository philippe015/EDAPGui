# ED_AP.py

import time
from EDKeys import EDKeys
from EDShipControl import EDShipControl
from EDGraphicsSettings import EDGraphicsSettings
from EDNavigationPanel import EDNavigationPanel
from EDGalaxyMap import GalaxyMap
from EDSystemMap import EDSystemMap
from EDInternalStatusPanel import EDInternalStatusPanel
from EDStationServicesInShip import EDStationServicesInShip
from Screen import Screen
from OCR import OCR
from Voice import Voice
from EDlogger import logger


class EDAutopilot:
    def __init__(self, cb=None):
        self.cb = cb
        self.running = False
        self.keys = EDKeys()
        self.voice = Voice()

        self.scr = Screen()
        self.gfx_settings = EDGraphicsSettings()

        self.config = {}

        self.ocr = None
        self.ed_controls = None
        self.overlay = None

        self.nav_panel = None
        self.galaxy_map = None
        self.sys_map = None
        self.internal_panel = None
        self.station_services = None

        self.ship_control = None

    def set_screen(self, scr):
        self.scr = scr

    def set_overlay(self, overlay):
        self.overlay = overlay

    def set_input(self, input_device):
        self.keys = input_device

    def load_config(self, config):
        self.config = config

    def run(self):
        if self.running:
            logger.warning("Autopilot is already running.")
            return

        self.running = True
        logger.info("Autopilot started")
        self.voice.say("Autopilot activé")

        try:
            self.ocr = OCR(self.scr, self.config.get('OCRLanguage', 'en'))

            self.ship_control = EDShipControl(self.scr, self.ocr, self.keys, self.config)
            self.nav_panel = EDNavigationPanel(self.scr, self.ocr, self.keys, self.config)
            self.galaxy_map = GalaxyMap(self.scr, self)
            self.sys_map = EDSystemMap(self.scr, self.ocr, self.keys, self.config)
            self.internal_panel = EDInternalStatusPanel(self.scr, self.ocr, self.keys, self.config)
            self.station_services = EDStationServicesInShip(self.scr, self.ocr, self.keys, self.config)

            while self.running:
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Erreur dans EDAutopilot.run: {e}")

    def stop(self):
        if not self.running:
            logger.warning("Autopilot is not running.")
            return

        self.running = False
        logger.info("Autopilot stopped")
        self.voice.say("Autopilot désactivé")

    def set_callback(self, cb):
        self.cb = cb
