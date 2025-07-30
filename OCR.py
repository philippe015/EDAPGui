from __future__ import annotations
import time
import cv2
import numpy as np
from paddleocr import PaddleOCR
from strsimpy.sorensendice import SorensenDice

from EDlogger import logger

class OCR:
    """ Gère le traitement OCR en utilisant PaddleOCR. """
    
    # NOUVEAU : Les couleurs de détection sont maintenant des attributs de classe faciles à modifier
    LOWER_HSV_HIGHLIGHT = np.array([0, 100, 180])
    UPPER_HSV_HIGHLIGHT = np.array([255, 255, 255])

    def __init__(self, screen, language: str = 'en', use_gpu: bool = False):
        self.screen = screen
        # MODIFIÉ : L'utilisation du GPU est maintenant configurable
        self.paddleocr = PaddleOCR(use_angle_cls=True, lang=language, use_gpu=use_gpu, 
                                   show_log=False, use_dilation=True, use_space_char=True)
        self.sorensendice = SorensenDice()

    def string_similarity(self, s1: str, s2: str) -> float:
        """ Calcule la similarité entre deux chaînes de caractères. """
        return self.sorensendice.similarity(s1, s2)

    # NOUVEAU : Méthode privée pour centraliser l'appel à l'OCR et éviter la duplication
    def _run_ocr(self, image: np.ndarray) -> list | None:
        """ Exécute l'OCR sur une image et retourne le résultat brut de PaddleOCR. """
        try:
            return self.paddleocr.ocr(image)
        except Exception as e:
            logger.error(f"Une erreur est survenue lors de l'appel à PaddleOCR : {e}")
            return None

    # MODIFIÉ : Utilise la nouvelle méthode privée _run_ocr
    def image_ocr(self, image: np.ndarray) -> tuple[list | None, list[str] | None]:
        """ Exécute l'OCR et retourne les données complètes ainsi qu'une liste de textes. """
        ocr_data = self._run_ocr(image)

        if not ocr_data or not ocr_data[0]:
            return None, None
        
        # Le résultat de paddle est une liste contenant une autre liste de résultats
        lines = ocr_data[0]
        ocr_textlist = [line[1][0] for line in lines]
        return lines, ocr_textlist

    # MODIFIÉ : Utilise la nouvelle méthode privée _run_ocr
    def image_simple_ocr(self, image: np.ndarray) -> list[str] | None:
        """ Exécute l'OCR et retourne une simple liste de chaînes de caractères. """
        _, ocr_textlist = self.image_ocr(image)
        return ocr_textlist

    def get_highlighted_item_in_image(self, image: np.ndarray, min_w: int, min_h: int) -> tuple[np.ndarray, int, int] | None:
        """ Trouve un élément en surbrillance (orange/bleu) dans une image. """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.LOWER_HSV_HIGHLIGHT, self.UPPER_HSV_HIGHLIGHT)
        masked_image = cv2.bitwise_and(image, image, mask=mask)
        
        gray = cv2.cvtColor(masked_image, cv2.COLOR_BGR2GRAY)
        _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)
        
        contours, _ = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > (min_w * 0.9) and h > (min_h * 0.9):
                cropped = image[y:y + h, x:x + w]
                return cropped, x, y
        
        # MODIFIÉ : Retour plus propre en cas d'échec
        return None

    def get_highlighted_item_data(self, image: np.ndarray, min_w: int, min_h: int) -> tuple[np.ndarray | None, list | None, list[str] | None]:
        """ Combine la recherche d'élément en surbrillance et l'OCR. """
        highlight_result = self.get_highlighted_item_in_image(image, min_w, min_h)
        if highlight_result:
            img_selected, _, _ = highlight_result
            ocr_data, ocr_textlist = self.image_ocr(img_selected)
            return img_selected, ocr_data, ocr_textlist
        
        return None, None, None

    def capture_region_pct(self, region: dict) -> np.ndarray:
        """ Capture une image à partir d'une région définie en pourcentages. """
        return self.screen.get_screen_rect_pct(region['rect'])

    # MODIFIÉ : Recherche de texte plus fiable
    def is_text_in_list(self, text_to_find: str, text_list: list[str], threshold=0.8) -> bool:
        """ Vérifie si un texte est présent dans une liste de textes, avec un seuil de similarité. """
        if not text_list:
            return False
            
        text_to_find = text_to_find.upper()
        for text in text_list:
            # Vérification simple de l'inclusion OU vérification par similarité
            if text_to_find in text.upper() or self.string_similarity(text_to_find, text.upper()) >= threshold:
                logger.debug(f"Texte '{text_to_find}' trouvé dans '{text}'.")
                return True
        return False

    def is_text_in_region(self, text: str, region: dict) -> tuple[bool, list[str] | None]:
        """ Vérifie si un texte est présent dans une région de l'écran. """
        img = self.capture_region_pct(region)
        ocr_textlist = self.image_simple_ocr(img)
        
        found = self.is_text_in_list(text, ocr_textlist)
        if not found:
            logger.debug(f"Texte '{text}' non trouvé dans la région. Contenu lu : {ocr_textlist}")
            
        return found, ocr_textlist

    def select_item_in_list(self, text: str, region: dict, keys, min_w: int, min_h: int) -> bool:
        """ Tente de trouver et de sélectionner un objet dans une liste. """
        in_list = False
        # MODIFIÉ : while True est plus commun que while 1
        while True:
            img = self.capture_region_pct(region)
            if img is None: return False

            highlight_result = self.get_highlighted_item_in_image(img, min_w, min_h)
            if highlight_result is None:
                if in_list: # Si on a déjà vu un objet et qu'il n'y en a plus, on a atteint la fin
                    logger.debug(f"Fin de la liste atteinte sans trouver '{text}'.")
                    return False
                # Si on n'a encore rien vu, on continue (au cas où le premier objet n'est pas sélectionné)
            else:
                img_selected, _, _ = highlight_result
                ocr_textlist = self.image_simple_ocr(img_selected)
                if self.is_text_in_list(text, ocr_textlist):
                    logger.debug(f"Objet '{text}' trouvé et sélectionné.")
                    return True

            # Si non trouvé, passer à l'objet suivant
            in_list = True
            keys.send("UI_Down")
            time.sleep(0.1) # Petite pause pour laisser l'UI se mettre à jour

    def wait_for_text(self, texts: list[str], region: dict, timeout: int = 30) -> bool:
        """ Attend qu'un des textes d'une liste apparaisse dans une région. """
        start_time = time.time()
        while time.time() < (start_time + timeout):
            found, _ = self.is_text_in_region(texts[0], region) # Simplifié pour l'exemple, peut être étendu
            if any(self.is_text_in_region(text, region)[0] for text in texts):
                return True
            time.sleep(0.25)
        
        logger.warning(f"Timeout atteint en attendant les textes {texts} dans la région.")
        return False
