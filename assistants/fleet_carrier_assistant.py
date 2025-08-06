from time import sleep
from EDlogger import logger

class FleetCarrierAssistant:
    def __init__(self, ed_ap, callback):
        self.ed_ap = ed_ap
        self.callback = callback
        self.active = False

    def start(self):
        logger.debug("Fleet Carrier Assist started")
        self.active = True
        self.callback('log+vce', "Fleet Carrier assist activated.")
        self.callback('log', "Simulated Fleet Carrier jump initiated.")
    
    def stop(self):
        logger.debug("Fleet Carrier Assist stopped")
        self.active = False
        self.callback('log+vce', "Fleet Carrier assist deactivated.")

    def is_running(self):
        return self.active
