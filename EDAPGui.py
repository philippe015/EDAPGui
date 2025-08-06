import queue import sys import os import threading import kthread from datetime import datetime from time import sleep import cv2 import json from pathlib import Path import keyboard import webbrowser import requests

from PIL import Image, ImageGrab, ImageTk import tkinter as tk from tkinter import * from tkinter import filedialog as fd from tkinter import messagebox from tkinter import ttk from idlelib.tooltip import Hovertip

from Voice import * from MousePt import MousePoint

from Image_Templates import * from Screen import * from Screen_Regions import * from EDKeys import * from EDJournal import * from ED_AP import *

from EDlogger import logger

---------------------------------------------------------------------------

EDAP_VERSION = "V1.6.1" FORM_TYPE_CHECKBOX = 0 FORM_TYPE_SPINBOX = 1 FORM_TYPE_ENTRY = 2

---------------------------------------------------------------------------

def hyperlink_callback(url): webbrowser.open_new(url)

class APGui: def init(self, root): self.root = root root.title(f"EDAutopilot {EDAP_VERSION}") root.protocol("WM_DELETE_WINDOW", self.close_window) root.resizable(False, False)

self.gui_loaded = False
    self.log_buffer = queue.Queue()
    self.callback('log', f'Starting ED Autopilot {EDAP_VERSION}.')

    self.ed_ap = EDAutopilot(cb=self.callback)
    self.mouse = MousePoint()

    self.init_gui_vars()
    self.msgList = self.gui_gen(root)
    self.load_config_to_gui()
    self.setup_hotkeys()
    self.check_updates()

    self.ed_ap.gui_loaded = True
    self.gui_loaded = True
    self.callback('log', 'ED Autopilot loaded successfully.')

def init_gui_vars(self):
    self.checkboxvar = {}
    self.radiobuttonvar = {}
    self.entries = {}
    self.lab_ck = {}
    self.single_waypoint_system = StringVar()
    self.single_waypoint_station = StringVar()
    self.TCE_Destination_Filepath = StringVar()
    self.cv_view = False

def callback(self, msg, body=None):
    if msg == 'log':
        self.log_msg(body)
    elif msg == 'log+vce':
        self.log_msg(body)
        self.ed_ap.vce.say(body)
    elif msg == 'statusline':
        self.update_statusline(body)

def log_msg(self, msg):
    message = datetime.now().strftime("%H:%M:%S: ") + msg
    if not self.gui_loaded:
        self.log_buffer.put(message)
        logger.info(msg)
    else:
        while not self.log_buffer.empty():
            self.msgList.insert(END, self.log_buffer.get())
        self.msgList.insert(END, message)
        self.msgList.yview(END)
        logger.info(msg)

def gui_gen(self, win):
    main_frame = tk.Frame(win)
    main_frame.pack(fill=BOTH, expand=True)
    msg_listbox = Listbox(main_frame, width=80, height=20)
    msg_listbox.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar = Scrollbar(main_frame, command=msg_listbox.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    msg_listbox.config(yscrollcommand=scrollbar.set)
    return msg_listbox

def load_config_to_gui(self):
    self.TCE_Destination_Filepath.set(self.ed_ap.config.get('TCEDestinationFilepath', ''))

def setup_hotkeys(self):
    try:
        keyboard.add_hotkey(self.ed_ap.config['HotKey_StopAllAssists'], self.close_window)
    except KeyError:
        self.callback('log', 'Hotkey configuration missing in config file.')

def check_updates(self):
    try:
        response = requests.get("https://api.github.com/repos/SumZer0-git/EDAPGui/releases/latest")
        latest_version = response.json().get("name", "")
        if EDAP_VERSION != latest_version:
            messagebox.showinfo("Update Available", f"New version available: {latest_version}")
    except Exception as e:
        self.callback('log', f"Update check failed: {e}")

def close_window(self):
    self.ed_ap.quit()
    sleep(0.1)
    self.root.destroy()

def main(): root = tk.Tk() app = APGui(root) root.mainloop()

if name == "main": main()

