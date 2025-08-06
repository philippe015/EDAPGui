from tkinter import LabelFrame, Label, Button, StringVar, OptionMenu, IntVar, Spinbox
from EDlogger import logger

class FleetCarrierLoader:
    """UI component to manage loading cargo into the player's Fleet Carrier."""

    def __init__(self, parent, ed_ap, callback):
        """
        Create the loader panel.
        Parameters
        ----------
        parent : tkinter.Widget
            Parent widget into which the panel will be packed.
        ed_ap : EDAutopilot
            Reference to the autopilot core.  The loader uses `ed_ap.keys`
            to simulate key presses for cargo transfer.
        callback : function
            Function used to send log messages back to the main GUI.
        """
        self.ed_ap = ed_ap
        self.callback = callback
        self.frame = LabelFrame(parent, text="Chargement Fleet Carrier", padx=10, pady=10)
        self.frame.pack(padx=10, pady=5, fill="x")
        self.cargo_type = StringVar(value="Tritium")
        # Available cargo options, including materials used for colonisation
        self.cargo_options = [
            "Tritium",
            "Biens rares",
            "Marchandises",
            "Matériaux",
            "Matériaux de construction",
            "Modules d'habitation",
            "Céramiques industrielles",
        ]
        self.amount = IntVar(value=50)
        Label(self.frame, text="Type de cargaison :").grid(row=0, column=0, sticky="w")
        OptionMenu(self.frame, self.cargo_type, *self.cargo_options).grid(row=0, column=1, sticky="ew")
        Label(self.frame, text="Quantité :").grid(row=1, column=0, sticky="w")
        Spinbox(self.frame, from_=1, to=10000, textvariable=self.amount).grid(row=1, column=1, sticky="ew")
        Button(
            self.frame,
            text="Charger vers le Carrier",
            command=self.load_to_carrier
        ).grid(row=2, column=0, columnspan=2, pady=5)

    def load_to_carrier(self):
        """
        Triggered when the user clicks the "Charger vers le Carrier" button.
        Logs the selected cargo and quantity, announces via voice (if
        enabled) and simulates the key presses required to load the
        selected cargo into the Fleet Carrier's hold.
        """
        cargo = self.cargo_type.get()
        amount = self.amount.get()
        self.callback('log+vce', f"Chargement de {amount} unités de {cargo} vers le Fleet Carrier...")
        try:
            self.ed_ap.keys.press('F10')
            self.ed_ap.keys.press('Down')
            self.ed_ap.keys.press('Down')
            self.ed_ap.keys.press('Enter')  # enter cargo transfer
            self.ed_ap.keys.press('Enter')  # confirm
            self.callback('log', f"Commande clavier envoyée pour charger {amount} {cargo}.")
        except Exception as e:
            logger.exception("Erreur lors du chargement du Fleet Carrier")
            self.callback('log+vce', f"Erreur lors du chargement : {e}")
