import json
from pathlib import Path

class LocalizationManager:
    """
    Gère le chargement et l'accès aux fichiers de localisation pour différentes langues.
    """

    def __init__(self, folder_path: str, language: str) -> None:
        self.folder_path = Path(folder_path)
        if not self.folder_path.is_dir():
            raise FileNotFoundError(f"Dossier de localisation introuvable : {self.folder_path}")

        self.available_languages: list[str] = []
        self.language = language
        self._data: dict[str, str] = {}

        self._load_available_languages()
        self._check_bijectivity()
        self.change_language(self.language)

    def _load_available_languages(self) -> None:
        """Trouve toutes les langues disponibles dans le dossier spécifié."""
        self.available_languages = [p.stem for p in self.folder_path.glob("*.json")]

    def _check_bijectivity(self) -> None:
        """
        Vérifie si tous les fichiers de localisation ont le même jeu de clés.
        Cette version est optimisée pour la performance et fournit des erreurs détaillées.
        """
        if not self.available_languages:
            return

        try:
            # Utilise les clés du premier fichier comme référence.
            with open(self.folder_path / f"{self.available_languages[0]}.json", "r", encoding='utf-8') as f:
                reference_keys = set(json.load(f).keys())

            # Compare chaque fichier suivant à la référence.
            for lang in self.available_languages[1:]:
                with open(self.folder_path / f"{lang}.json", "r", encoding='utf-8') as f:
                    current_keys = set(json.load(f).keys())
                if current_keys != reference_keys:
                    # Identifie les différences pour un message d'erreur plus utile.
                    diff = reference_keys.symmetric_difference(current_keys)
                    raise ValueError(f"Incohérence des clés dans '{lang}.json'. Différence : {diff}")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise IOError(f"Échec de la vérification de la cohérence : {e}")

    def __getitem__(self, key: str) -> str:
        """
        Récupère la chaîne de caractères localisée pour une clé.
        Si non trouvée, retourne la clé elle-même pour faciliter le débogage.
        """
        return self._data.get(key, key)

    def refresh(self) -> None:
        """Recharge le fichier de localisation pour la langue actuelle."""
        file_path = self.folder_path / f"{self.language}.json"
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                self._data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Le fichier de langue est introuvable : {file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Erreur de décodage JSON dans le fichier : {file_path}")

    def change_language(self, language: str) -> None:
        """Change la langue actuelle et recharge les données."""
        if language not in self.available_languages:
            raise ValueError(f"La langue '{language}' n'est pas disponible. Langues trouvées : {self.available_languages}")
        self.language = language
        self.refresh()
