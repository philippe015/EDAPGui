from __future__ import annotations
from pathlib import Path
import xmltodict
from EDlogger import logger

class GraphicsSettingsError(Exception):
    """Exception personnalisée pour les erreurs liées aux paramètres graphiques."""
    pass

class EDGraphicsSettings:
    """ Gère les fichiers de configuration graphique d'Elite Dangerous. """

    def __init__(self, display_file_path: str | None = None, settings_file_path: str | None = None):
        # Utilisation de pathlib pour une gestion propre des chemins
        local_app_data = Path.home() / "AppData" / "Local"
        graphics_path = local_app_data / "Frontier Developments" / "Elite Dangerous" / "Options" / "Graphics"

        self.display_settings_filepath = Path(display_file_path) if display_file_path else graphics_path / "DisplaySettings.xml"
        self.settings_filepath = Path(settings_file_path) if settings_file_path else graphics_path / "Settings.xml"

        # Initialisation des attributs
        self.screen_width: int = 0
        self.screen_height: int = 0
        self.fullscreen_mode: str = ""
        self.monitor_index: int = 0
        self.fov: float = 0.0

        # Lancement de la lecture et de l'analyse
        self._load_and_parse_settings()

    def _read_xml_file(self, filepath: Path) -> dict:
        """ Lit un fichier XML et le convertit en dictionnaire. """
        if not filepath.is_file():
            logger.error(f"Le fichier de configuration est introuvable : {filepath}")
            raise GraphicsSettingsError(f"Fichier de configuration introuvable : {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return xmltodict.parse(file.read())
        except (OSError, xmltodict.expat.ExpatError) as e:
            logger.error(f"Erreur lors de la lecture ou de l'analyse du fichier XML {filepath}: {e}")
            raise GraphicsSettingsError(f"Impossible de lire ou d'analyser le fichier {filepath}") from e

    def _load_and_parse_settings(self):
        """ Orchestre la lecture et l'analyse des fichiers de configuration. """
        logger.info(f"Lecture des paramètres d'affichage depuis '{self.display_settings_filepath}'.")
        display_data = self._read_xml_file(self.display_settings_filepath)
        self._parse_display_settings(display_data)

        logger.info(f"Lecture des paramètres graphiques depuis '{self.settings_filepath}'.")
        settings_data = self._read_xml_file(self.settings_filepath)
        self._parse_graphics_options(settings_data)

        # Validation finale
        if self.fullscreen_mode.upper() != "BORDERLESS":
            logger.error("Le mode d'affichage d'Elite Dangerous n'est pas configuré sur BORDERLESS.")
            raise GraphicsSettingsError("Le mode d'affichage doit être BORDERLESS.")

    def _parse_display_settings(self, data: dict):
        """ Analyse les données de DisplaySettings.xml et peuple les attributs. """
        config = data.get('DisplayConfig', {})
        
        try:
            self.screen_width = int(config.get('ScreenWidth', 0))
            self.screen_height = int(config.get('ScreenHeight', 0))
            self.monitor_index = int(config.get('Monitor', 0))
            
            fullscreen_code = int(config.get('FullScreen', 0))
            options = {0: "Windowed", 1: "Fullscreen", 2: "Borderless"}
            self.fullscreen_mode = options.get(fullscreen_code, "Unknown")

            logger.debug(f"Résolution détectée : {self.screen_width}x{self.screen_height}")
            logger.debug(f"Mode d'affichage : {self.fullscreen_mode}")

        except (ValueError, TypeError) as e:
            raise GraphicsSettingsError("Données de configuration d'affichage invalides ou corrompues.") from e

    def _parse_graphics_options(self, data: dict):
        """ Analyse les données de Settings.xml pour le FOV. """
        config = data.get('GraphicsOptions', {})
        try:
            self.fov = float(config.get('FOV', 70.0))
            logger.debug(f"Champ de vision (FOV) : {self.fov}")
        except (ValueError, TypeError) as e:
            raise GraphicsSettingsError("Données de FOV invalides ou corrompues.") from e

def main():
    try:
        gs = EDGraphicsSettings()
        print(f"Paramètres chargés avec succès : {gs.screen_width}x{gs.screen_height}, Mode={gs.fullscreen_mode}, FOV={gs.fov}")
    except GraphicsSettingsError as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    main()
