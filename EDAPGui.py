"""
Improved version of EDAPGui integrating Fleet Carrier Assistant and Loader.

This file corrects formatting issues present in the repository version and adds
clean separation of imports, class methods, and initialization logic.
It can be used as a reference for updating the repository.
"""

# Standard library imports
import queue
import sys
import os
import threading
from datetime import datetime
from time import sleep
from pathlib import Path

# Third-party imports
import keyboard
import webbrowser
import requests
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import messagebox
from tkinter import ttk
from idlelib.tooltip import Hovertip
from PIL import Image, ImageGrab, ImageTk

# Project-specific imports
from Voice import *  # noqa: F401,F403  # import voice module for side-effects
from MousePt import MousePoint
from Image_Templates import *  # noqa: F401,F403  # import templates for side-effects
from Screen import *  # noqa: F401,F403
from Screen_Regions import *  # noqa: F401,F403
from EDKeys import *  # noqa: F401,F403
from EDJournal import *  # noqa: F401,F403
from ED_AP import EDAutopilot
from EDlogger import logger
from assistants.fleet_carrier_assistant import FleetCarrierAssistant
from fc_loader import FleetCarrierLoader


# Version information
EDAP_VERSION = "V1.6.1"


def hyperlink_callback(url: str) -> None:
    """Open a URL in the default web browser."""
    webbrowser.open_new(url)


class APGui:
    """Graphical user interface for controlling the ED Autopilot."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"EDAutopilot {EDAP_VERSION}")
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)
        self.root.resizable(False, False)

        # Apply a modern theme to ttk widgets.  Attempt to use the 'clam' theme
        # which provides a clean, modern appearance; fall back silently if unavailable.
        try:
            style = ttk.Style(self.root)
            style.theme_use('clam')
        except Exception:
            pass

        # Internal flags
        self.gui_loaded = False
        self.log_buffer: queue.Queue[str] = queue.Queue()

        # Initialize the autopilot core and helpers
        self.ed_ap = EDAutopilot(cb=self.callback)
        self.mouse = MousePoint()
        self.fc_assist = FleetCarrierAssistant(self.ed_ap, self.callback)

        # Initialize GUI state variables
        self.init_gui_vars()

        # Create the GUI components
        self.msgList = self.gui_gen(root)
        self.load_config_to_gui()
        self.setup_hotkeys()
        self.check_updates()

        # Add Fleet Carrier Assist checkbox
        self.checkboxvar['Fleet Carrier Assist'] = tk.BooleanVar()
        # Use ttk.Checkbutton for a themed appearance
        self.lab_ck['Fleet Carrier Assist'] = ttk.Checkbutton(
            root,
            text="Fleet Carrier Assist",
            variable=self.checkboxvar['Fleet Carrier Assist'],
            command=lambda field='Fleet Carrier Assist': self.check_cb(field)
        )
        self.lab_ck['Fleet Carrier Assist'].pack()

        # Add Fleet Carrier Loader panel
        self.fc_loader = FleetCarrierLoader(root, self.ed_ap, self.callback)

        # Mark GUI as loaded and flush any buffered logs
        self.ed_ap.gui_loaded = True
        self.gui_loaded = True
        self.callback('log', 'ED Autopilot loaded successfully.')

    def init_gui_vars(self) -> None:
        """Initialize state variables used by the GUI."""
        self.checkboxvar: dict[str, tk.Variable] = {}
        self.radiobuttonvar: dict[str, tk.Variable] = {}
        self.entries: dict[str, dict[str, tk.Widget]] = {}
        self.lab_ck: dict[str, tk.Widget] = {}
        self.single_waypoint_system = tk.StringVar()
        self.single_waypoint_station = tk.StringVar()
        self.TCE_Destination_Filepath = tk.StringVar()
        self.cv_view: bool = False

    def callback(self, msg: str, body: str | None = None) -> None:
        """Handle callback messages from the EDAP core."""
        if msg == 'log':
            assert body is not None
            self.log_msg(body)
        elif msg == 'log+vce':
            assert body is not None
            self.log_msg(body)
            self.ed_ap.vce.say(body)
        elif msg == 'statusline':
            assert body is not None
            self.update_statusline(body)

    def log_msg(self, msg: str) -> None:
        """Display a log message in the log listbox."""
        message = datetime.now().strftime("%H:%M:%S: ") + msg
        if not self.gui_loaded:
            self.log_buffer.put(message)
            logger.info(msg)
            return

        # Flush any queued messages first
        while not self.log_buffer.empty():
            self.msgList.insert(tk.END, self.log_buffer.get())

        self.msgList.insert(tk.END, message)
        self.msgList.yview(tk.END)
        logger.info(msg)

    def gui_gen(self, win: tk.Tk) -> tk.Listbox:
        """Create the base log listbox used to display log messages."""
        # Use ttk.Frame and ttk.Scrollbar for modern themed widgets.  The Listbox
        # remains a standard Tk widget as ttk does not provide one.
        main_frame = ttk.Frame(win)
        main_frame.pack(fill=tk.BOTH, expand=True)
        msg_listbox = tk.Listbox(main_frame, width=80, height=20)
        msg_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(main_frame, command=msg_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        msg_listbox.config(yscrollcommand=scrollbar.set)
        return msg_listbox

    def load_config_to_gui(self) -> None:
        """Load persisted configuration values into GUI state."""
        self.TCE_Destination_Filepath.set(
            self.ed_ap.config.get('TCEDestinationFilepath', '')
        )

    def setup_hotkeys(self) -> None:
        """Register global hotkeys from the configuration."""
        try:
            keyboard.add_hotkey(
                self.ed_ap.config['HotKey_StopAllAssists'],
                self.close_window
            )
        except KeyError:
            self.callback('log', 'Hotkey configuration missing in config file.')

    def check_updates(self) -> None:
        """Check GitHub for a newer version of EDAP."""
        try:
            response = requests.get(
                "https://api.github.com/repos/SumZer0-git/EDAPGui/releases/latest",
                timeout=10,
            )
            latest_version = response.json().get("name", "")
            if EDAP_VERSION != latest_version:
                messagebox.showinfo(
                    "Update Available",
                    f"New version available: {latest_version}"
                )
        except Exception as e:  # broad except to catch network errors
            self.callback('log', f"Update check failed: {e}")

    def check_cb(self, field: str) -> None:
        """Handle checkbox state changes for the custom Fleet Carrier Assist."""
        if field == 'Fleet Carrier Assist':
            if (
                self.checkboxvar['Fleet Carrier Assist'].get()
                and not self.fc_assist.is_running()
            ):
                self.fc_assist.start()
            elif self.fc_assist.is_running():
                self.fc_assist.stop()

    def update_statusline(self, txt: str) -> None:
        """Placeholder to update a status line on the GUI if implemented."""
        # Implementation would update a status label; omitted in this simplified version
        pass

    def close_window(self) -> None:
        """Cleanly shut down the autopilot and close the GUI."""
        self.ed_ap.quit()
        sleep(0.1)
        self.root.destroy()


def main() -> None:
    """Program entry point."""
    root = tk.Tk()
    app = APGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
