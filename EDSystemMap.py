from __future__ import annotations
from time import sleep
from EDlogger import logger
from StatusParser import StatusParser, GuiFocusSystemMap

# NOUVEAU : Classe dédiée à la gestion du panneau de navigation pour une meilleure structure.
class EDNavPanel:
    """ Gère les interactions avec le panneau de navigation. """
    def __init__(self, ed_ap):
        self.ap = ed_ap
        self.keys = ed_ap.keys

    def select_bookmark_by_position(self, position: int) -> bool:
        """ Sélectionne un marque-page dans le panneau de navigation par sa position. """
        logger.info(f"Sélection du marque-page de navigation en position {position}.")
        self.ap.ship_control.goto_cockpit_view()

        # Accéder au panneau de navigation
        self.keys.send("HeadLookReset")
        self.keys.send("UIFocus", state=1)
        self.keys.send("UI_Left")
        self.keys.send("UIFocus", state=0)
        
        # Sélectionner le marque-page
        self.keys.send('UI_Up', hold=4) # Aller en haut de la liste
        if position > 1:
            self.keys.send('UI_Down', repeat=position - 1)
        
        sleep(1.0) # Un sleep peut rester pertinent ici pour la sélection finale
        self.keys.send('UI_Select')
        sleep(0.25)
        self.keys.send('UI_Select') # Confirmer la destination

        # Retourner à la vue normale
        self.keys.send("UI_Back")
        self.keys.send("HeadLookReset")
        return True

class EDSystemMap:
    """ Gère les interactions avec la Carte du Système. """

    # NOUVEAU : Utilisation d'un dictionnaire pour une logique plus propre
    BOOKMARK_CATEGORY_NAV = {
        "BODIES": 1,
        "STATIONS": 2,
        "SETTLEMENTS": 3,
    }

    def __init__(self, ed_ap, screen, keys, cb, is_odyssey=True):
        self.ap = ed_ap
        self.ocr = ed_ap.ocr
        self.keys = keys
        self.screen = screen
        self.status_parser = StatusParser()
        self.is_odyssey = is_odyssey
        
        # NOUVEAU : Instanciation de la classe pour le panneau de navigation
        self.nav_panel = EDNavPanel(ed_ap)

    def goto_system_map(self):
        """ Ouvre la Carte du Système si elle n'est pas déjà ouverte. """
        if self.status_parser.get_gui_focus() != GuiFocusSystemMap:
            logger.debug("Ouverture de la Carte du Système.")
            self.ap.ship_control.goto_cockpit_view()
            self.keys.send('SystemMapOpen')
            
            # MODIFIÉ : Attente active au lieu d'un sleep fixe
            # TODO: Définir la région et le texte à attendre pour confirmer l'ouverture
            # exemple: self.ocr.wait_for_text(["SYSTEM MAP"], {"rect": [0,0,0.1,0.1]})
            sleep(3.5) # Temporaire, à remplacer par une attente OCR
        else:
            logger.debug("La Carte du Système est déjà ouverte.")
            # Réinitialiser la vue au cas où
            self.keys.send('UI_Left', hold=2)
            self.keys.send('UI_Up', hold=2)

    def _navigate_to_bookmark_category(self, category_name: str) -> bool:
        """ Navigue jusqu'à la catégorie de marque-pages souhaitée. """
        self.keys.send('UI_Left')  # Aller à l'onglet MARQUE-PAGES
        sleep(0.5)
        self.keys.send('UI_Select')
        sleep(0.25)
        self.keys.send('UI_Right')  # Aller à la colonne des catégories
        sleep(0.25)

        presses = self.BOOKMARK_CATEGORY_NAV.get(category_name.upper(), 0)
        if presses > 0:
            self.keys.send('UI_Down', repeat=presses)
        
        sleep(0.25)
        self.keys.send('UI_Select') # Sélectionne la catégorie, déplace le focus sur la liste
        return True

    def _select_bookmark_from_list(self, position: int) -> bool:
        """ Sélectionne un marque-page dans la liste par sa position. """
        # S'assurer que le focus est bien sur la liste
        self.keys.send('UI_Left')
        self.keys.send('UI_Right')
        sleep(0.25)

        if position > 1:
            self.keys.send('UI_Down', repeat=position - 1)
        
        sleep(0.25)
        self.keys.send('UI_Select', hold=3.0) # Maintenir pour définir la destination
        return True

    def set_sys_map_dest_bookmark(self, bookmark_type: str, bookmark_position: int) -> bool:
        """
        Définit la destination en utilisant un marque-page.
        La méthode est maintenant un orchestrateur qui appelle des sous-méthodes.
        """
        if not self.is_odyssey or bookmark_position == -1:
            return False

        # MODIFIÉ : Logique déléguée à la classe EDNavPanel
        if bookmark_type.lower().startswith("nav"):
            return self.nav_panel.select_bookmark_by_position(bookmark_position)
        
        # Logique pour la Carte du Système
        self.goto_system_map()
        
        category_map = {
            "bod": "BODIES",
            "sta": "STATIONS",
            "set": "SETTLEMENTS"
        }
        category = next((v for k, v in category_map.items() if bookmark_type.lower().startswith(k)), "FAVORITES")
        
        if self._navigate_to_bookmark_category(category):
            self._select_bookmark_from_list(bookmark_position)
            
            # Fermer la Carte du Système
            self.keys.send('SystemMapOpen')
            sleep(0.5)
            return True
            
        return False
