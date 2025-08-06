from tkinter import LabelFrame, Label, Entry, Button, StringVar, OptionMenu, IntVar, Spinbox
from EDlogger import logger

class FleetCarrierLoader:
    def __init__(self, parent, ed_ap, callback):
        self.ed_ap = ed_ap
        self.callback = callback
        self.frame = LabelFrame(parent, text="Chargement Fleet Carrier", padx=10, pady=10)
        self.frame.pack(padx=10, pady=5, fill="x")

        self.cargo_type = StringVar()
        self.cargo_type.set("Tritium")  # valeur par défaut
        self.cargo_options = ["Tritium", "Biens rares", "Marchandises", "Matériaux"]

        self.amount = IntVar()
        self.amount.set(50)

        # Widgets
        Label(self.frame, text="Type de cargaison :").grid(row=0, column=0, sticky="w")
        OptionMenu(self.frame, self.cargo_type, *self.cargo_options).grid(row=0, column=1, sticky="ew")

        Label(self.frame, text="Quantité :").grid(row=1, column=0, sticky="w")
        Spinbox(self.frame, from_=1, to=1000, textvariable=self.amount).grid(row=1, column=1, sticky="ew")

        Button(self.frame, text="Charger vers le Carrier", command=self.load_to_carrier).grid(row=2, column=0, columnspan=2, pady=5)

    def load_to_carrier(self):
        cargo = self.cargo_type.get()
        amount = self.amount.get()

        self.callback('log+vce', f"Chargement de {amount} unités de {cargo} vers le Fleet Carrier...")

        try:
            # Simulation de l'envoi de touches clavier pour ouvrir le menu et effectuer l'action
            self.ed_ap.keys.press('F10')  # Ouvre le menu Fleet Carrier
            self.ed_ap.keys.press('Down')
            self.ed_ap.keys.press('Down')
            self
