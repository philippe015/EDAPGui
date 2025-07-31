from __future__ import annotations
import threading
from time import sleep
from dataclasses import dataclass
import win32api
import win32con
import win32gui
import win32ui

# Utilisation d'un dataclass pour une structure de données plus propre et plus moderne
@dataclass
class Vector:
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0

class Overlay:
    """
    Crée une superposition (overlay) transparente pour dessiner des formes et du texte
    sur une autre fenêtre ou sur l'écran entier.
    """
    def __init__(self, parent_window_title: str | None = None):
        self.parent_title = parent_window_title
        self.h_window = None
        self.target_hwnd = None
        self.target_rect = Vector()

        # Attributs d'instance pour le dessin (remplace les variables globales)
        self.lines = {}
        self.texts = {}
        self.floating_texts = {}
        self.font = ("Times New Roman", 12)
        self.text_pos = (0, 0)

        # Verrou pour la sécurité du threading
        self.lock = threading.Lock()

        # Démarrage du thread de l'interface graphique
        self.overlay_thread = threading.Thread(target=self._run_win32_loop, daemon=True)
        self.overlay_thread.start()
        sleep(0.1) # Laisse le temps à la fenêtre d'être créée

    def _run_win32_loop(self):
        """ Boucle principale pour la fenêtre WinAPI, gère les messages Windows. """
        h_instance = win32api.GetModuleHandle()
        class_name = 'OverlayWindowClass'

        wnd_class = win32gui.WNDCLASS()
        wnd_class.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wnd_class.lpfnWndProc = self._wnd_proc # Méthode d'instance
        wnd_class.hInstance = h_instance
        wnd_class.hCursor = win32gui.LoadCursor(None, win32con.IDC_ARROW)
        wnd_class.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
        wnd_class.lpszClassName = class_name
        wnd_class_atom = win32gui.RegisterClass(wnd_class)

        ex_style = (win32con.WS_EX_COMPOSITED | win32con.WS_EX_LAYERED | 
                    win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOPMOST | win32con.WS_EX_TRANSPARENT)
        style = win32con.WS_DISABLED | win32con.WS_POPUP | win32con.WS_VISIBLE

        self.h_window = win32gui.CreateWindowEx(
            ex_style, wnd_class_atom, None, style,
            0, 0, win32api.GetSystemMetrics(win32con.SM_CXSCREEN), win32api.GetSystemMetrics(win32con.SM_CYSCREEN),
            None, None, h_instance, None
        )

        win32gui.SetLayeredWindowAttributes(self.h_window, 0x00ffffff, 255, win32con.LWA_COLORKEY | win32con.LWA_ALPHA)
        win32gui.SetWindowPos(self.h_window, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
        
        # Initialiser la position de la fenêtre sur la fenêtre cible si elle est spécifiée
        self._update_target_window()
        win32gui.PumpMessages()

    def _update_target_window(self):
        """ Met à jour la position de l'overlay pour qu'elle corresponde à la fenêtre cible. """
        if self.parent_title:
            self.target_hwnd = win32gui.FindWindow(None, self.parent_title)
            if self.target_hwnd:
                rect = win32gui.GetWindowRect(self.target_hwnd)
                new_rect = Vector(rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])
                if self.target_rect != new_rect:
                    self.target_rect = new_rect
                    win32gui.MoveWindow(self.h_window, self.target_rect.x, self.target_rect.y, self.target_rect.w, self.target_rect.h, True)

    def _wnd_proc(self, hWnd, message, wParam, lParam):
        """ Procédure de fenêtre, maintenant une méthode d'instance. """
        if message == win32con.WM_PAINT:
            hdc, paint_struct = win32gui.BeginPaint(hWnd)
            self._draw_all(hdc)
            win32gui.EndPaint(hWnd, paint_struct)
            return 0
        elif message == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        else:
            return win32gui.DefWindowProc(hWnd, message, wParam, lParam)

    def _draw_all(self, hdc):
        """ Centralise toutes les opérations de dessin. """
        with self.lock:
            # Dessiner les rectangles
            for key, (pt1, pt2, color, thick) in self.lines.items():
                self._draw_rect(hdc, pt1, pt2, color, thick)

            # Dessiner les textes fixes
            font_handle = self._create_font_handle(hdc, self.font[0], self.font[1])
            win32gui.SelectObject(hdc, font_handle)
            for key, (txt, row, col, color) in self.texts.items():
                self._draw_text(hdc, txt, row, col, color)

            # Dessiner les textes flottants
            for key, (txt, x, y, color) in self.floating_texts.items():
                self._draw_floating_text(hdc, txt, x, y, color)
            
            # Important : Supprimer l'objet GDI après utilisation
            win32gui.DeleteObject(font_handle)

    def _create_font_handle(self, hdc, fontname, size):
        lf = win32gui.LOGFONT()
        lf.lfFaceName = fontname
        lf.lfHeight = int(round(win32ui.GetDeviceCaps(hdc, win32con.LOGPIXELSX) / 60.0 * size))
        lf.lfQuality = win32con.NONANTIALIASED_QUALITY
        return win32gui.CreateFontIndirect(lf)

    def _draw_rect(self, hdc, pt1, pt2, color, thick):
        """ Dessine un rectangle simple avec une gestion correcte des ressources. """
        pen = win32gui.CreatePen(win32con.PS_SOLID, thick, win32api.RGB(*color))
        try:
            win32gui.SelectObject(hdc, pen)
            # Dessin d'un rectangle simple pour la clarté, la logique complexe peut être réintégrée ici
            win32gui.MoveToEx(hdc, pt1[0], pt1[1])
            win32gui.LineTo(hdc, pt2[0], pt1[1])
            win32gui.LineTo(hdc, pt2[0], pt2[1])
            win32gui.LineTo(hdc, pt1[0], pt2[1])
            win32gui.LineTo(hdc, pt1[0], pt1[1])
        finally:
            # Assure que le stylo est toujours détruit
            win32gui.DeleteObject(pen)
    
    # Méthodes publiques pour interagir avec l'overlay
    def add_rect(self, key: str, pt1: tuple[int, int], pt2: tuple[int, int], color: tuple[int, int, int], thickness: int):
        with self.lock:
            self.lines[key] = (pt1, pt2, color, thickness)

    def set_font(self, fontname: str, size: int):
        with self.lock:
            self.font = (fontname, size)
    
    def add_text(self, key: str, text: str, x: int, y: int, color: tuple[int, int, int]):
        with self.lock:
            self.floating_texts[key] = (text, x, y, color)

    def remove_item(self, key: str):
        with self.lock:
            self.lines.pop(key, None)
            self.texts.pop(key, None)
            self.floating_texts.pop(key, None)

    def clear(self):
        with self.lock:
            self.lines.clear()
            self.texts.clear()
            self.floating_texts.clear()

    def paint(self):
        """ Demande à la fenêtre de se redessiner. """
        self._update_target_window()
        if self.h_window:
            win32gui.RedrawWindow(self.h_window, None, None, win32con.RDW_INVALIDATE | win32con.RDW_ERASE)

    def quit(self):
        """ Ferme la fenêtre de l'overlay proprement. """
        if self.h_window:
            win32gui.PostMessage(self.h_window, win32con.WM_CLOSE, 0, 0)

# Exemple d'utilisation
def main():
    print("Démarrage de l'overlay. Il se superposera à la fenêtre 'Elite - Dangerous (CLIENT)' si elle est trouvée.")
    print("Sinon, il couvrira tout l'écran. L'overlay se fermera après 10 secondes.")
    
    ov = Overlay("Elite - Dangerous (CLIENT)")
    
    # Ajoute des éléments de manière dynamique
    ov.set_font("Arial", 16)
    ov.add_rect('box1', (100, 100), (400, 300), (0, 255, 0), 2)
    ov.add_text('label1', "Ceci est un test", 110, 110, (255, 255, 255))
    
    # Demande à l'overlay de se redessiner
    ov.paint()
    sleep(5)

    # Modifie les éléments
    print("Modification des éléments...")
    ov.add_rect('box1', (150, 150), (450, 350), (255, 0, 0), 4)
    ov.add_text('label1', "Le texte a changé !", 160, 160, (255, 255, 0))
    ov.add_text('new_label', "Nouveau texte", 500, 500, (0, 180, 255))
    ov.paint()
    sleep(5)

    print("Fermeture de l'overlay.")
    ov.quit()

if __name__ == "__main__":
    main()
