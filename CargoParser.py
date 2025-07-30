from __future__ import annotations
import json
import threading
from time import sleep
from pathlib import Path
from sys import platform
from EDlogger import logger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# S'assure que WindowsKnownPaths est importé uniquement sur Windows
if platform == "win32":
    from WindowsKnownPaths import get_path, FOLDERID, UserHandle

class CargoParser:
    """ Analyse le fichier Cargo.json du jeu et se met à jour automatiquement. """

    def __init__(self, file_path: str | None = None):
        self.file_path = self._get_default_path() if file_path is None else Path(file_path)
        
        # Données du cargo
        self.timestamp: str | None = None
        self.vessel: str | None = None
        self._inventory: dict[str, dict] = {}
        self._lock = threading.Lock() # Verrou pour un accès thread-safe

        # Chargement initial des données
        self._load_cargo_data()

        # Mise en place du "watcher" qui mettra à jour les données automatiquement
        self._start_watcher()

    def _get_default_path(self) -> Path:
        """ Détermine le chemin par défaut du fichier Cargo.json selon l'OS. """
        if platform == "win32":
            try:
                # Chemin standard pour Elite Dangerous sur Windows
                saved_games = get_path(FOLDERID.SavedGames, UserHandle.current)
                return Path(saved_games) / "Frontier Developments" / "Elite Dangerous" / "Cargo.json"
            except (ImportError, FileNotFoundError):
                logger.error("Impossible de trouver le dossier 'Saved Games' de Windows.")
                return Path("./Cargo.json") # Chemin de secours
        else:
            # Chemin par défaut pour Linux/macOS
            return Path("./linux_ed/Cargo.json")

    def _load_cargo_data(self) -> bool:
        """ Charge et traite le contenu du fichier Cargo.json. """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
            logger.error(f"Erreur lors de la lecture de {self.file_path}: {e}")
            return False

        # Utilise un verrou pour modifier les données en toute sécurité (thread-safe)
        with self._lock:
            self.timestamp = data.get("timestamp")
            self.vessel = data.get("Vessel")
            # Transforme la liste en dictionnaire pour un accès instantané
            self._inventory = {
                item['Name'].lower(): item for item in data.get('Inventory', [])
            }
        
        logger.debug("Données du fichier Cargo.json mises à jour.")
        return True

    def _start_watcher(self):
        """ Démarre le thread qui surveille les modifications du fichier. """
        event_handler = self._CargoFileEventHandler(self)
        observer = Observer()
        observer.schedule(event_handler, path=str(self.file_path.parent), recursive=False)
        observer.daemon = True
        observer.start()
        logger.info(f"Surveillance du fichier {self.file_path} démarrée.")

    def get_item(self, item_name: str) -> dict | None:
        """
        Récupère les détails d'un objet en soute par son nom.
        La recherche est quasi-instantanée grâce à la nouvelle structure de données.
        Retourne None si l'objet n'est pas trouvé.
        """
        with self._lock:
            return self._inventory.get(item_name.lower())

    def get_all_items(self) -> list[dict]:
        """ Retourne la liste de tous les objets actuellement en soute. """
        with self._lock:
            return list(self._inventory.values())

    @property
    def cargo_count(self) -> int:
        """ Retourne le nombre total d'unités dans la soute. """
        with self._lock:
            return sum(item.get('Count', 0) for item in self._inventory.values())

    class _CargoFileEventHandler(FileSystemEventHandler):
        """ Classe interne pour gérer les événements de modification de fichier. """
        def __init__(self, parser_instance: CargoParser):
            self.parser = parser_instance

        def on_modified(self, event):
            # Vérifie si le fichier modifié est bien celui que l'on surveille
            if Path(event.src_path) == self.parser.file_path:
                logger.debug(f"Modification détectée pour {self.parser.file_path}.")
                # Utilise un backoff pour gérer le cas où le jeu écrit encore dans le fichier
                backoff = 0.1
                for _ in range(5): # Tente 5 fois max
                    sleep(backoff)
                    if self.parser._load_cargo_data():
                        break
                    backoff *= 2


# Exemple d'utilisation
if __name__ == "__main__":
    cargo_parser = CargoParser()
    
    # Le watcher travaille en arrière-plan, plus besoin de boucle manuelle !
    try:
        while True:
            # On peut maintenant accéder aux données quand on le souhaite,
            # elles sont toujours à jour.
            tritium_details = cargo_parser.get_item('Tritium')
            total_items = cargo_parser.cargo_count

            if tritium_details:
                print(f"Tritium en soute : {tritium_details['Count']} unités.")
            else:
                print("Pas de Tritium en soute.")
            
            print(f"Nombre total d'unités en soute : {total_items}")
            print("-" * 20)
            
            sleep(5) # On attend 5 secondes avant de ré-afficher les infos
    except KeyboardInterrupt:
        print("\nProgramme arrêté.")
