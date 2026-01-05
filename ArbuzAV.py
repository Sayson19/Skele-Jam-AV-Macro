import tkinter as tk
from tkinter import messagebox
import threading
import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab
import time
import json
import os
import ctypes
import webbrowser

# WIN32 API - SIMULTANEOUS KEY PRESSES
user32 = ctypes.windll.user32
SendInput = ctypes.windll.user32.SendInput

VK_CODE = {
    'a': 0x41, 's': 0x53, 'd': 0x44, 'f': 0x46, 'g': 0x47,
    'f1': 0x70, 'f3': 0x72
}

PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time",ctypes.c_ulong), ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
INPUT_KEYBOARD = 1

def press_keys_simultaneous(vk_codes, hold_ms: int = 30):
    """Press multiple keys at once via SendInput using scan codes.
    hold_ms controls how long keys stay down so the game can register the press."""
    MapVirtualKey = ctypes.windll.user32.MapVirtualKeyW
    extra = ctypes.c_ulong(0)

    # Press all
    down_inputs = []
    for vk in vk_codes:
        scan = MapVirtualKey(vk, 0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput(0, scan, KEYEVENTF_SCANCODE, 0, ctypes.pointer(extra))
        down_inputs.append(Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_))

    if down_inputs:
        arr = (Input * len(down_inputs))(*down_inputs)
        SendInput(len(down_inputs), arr, ctypes.sizeof(Input))

    # Hold keys briefly so the game registers the press
    time.sleep(max(hold_ms, 5) / 1000.0)

    # Release all
    up_inputs = []
    for vk in vk_codes:
        scan = MapVirtualKey(vk, 0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput(0, scan, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
        up_inputs.append(Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_))

    if up_inputs:
        arr = (Input * len(up_inputs))(*up_inputs)
        SendInput(len(up_inputs), arr, ctypes.sizeof(Input))

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

def key_down(letter: str):
    try:
        pyautogui.keyDown(letter)
    except Exception:
        pass

def key_up(letter: str):
    try:
        pyautogui.keyUp(letter)
    except Exception:
        pass

def press_key_down_vk(vk: int):
    MapVirtualKey = ctypes.windll.user32.MapVirtualKeyW
    extra = ctypes.c_ulong(0)
    scan = MapVirtualKey(vk, 0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, scan, KEYEVENTF_SCANCODE, 0, ctypes.pointer(extra))
    inp = Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_)
    SendInput(1, ctypes.pointer(inp), ctypes.sizeof(Input))

def press_key_up_vk(vk: int):
    MapVirtualKey = ctypes.windll.user32.MapVirtualKeyW
    extra = ctypes.c_ulong(0)
    scan = MapVirtualKey(vk, 0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, scan, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
    inp = Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_)
    SendInput(1, ctypes.pointer(inp), ctypes.sizeof(Input))

class ArbuzAV:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ArbuzAV Pro")
        self.root.geometry("700x980")
        # Allow user resizing; lower the floor so the window can be made smaller
        self.root.resizable(True, True)
        # Allow even smaller window; scrollbar keeps content reachable
        self.root.minsize(360, 520)
        self.root.attributes('-topmost', True)

        # Theme
        self.dark_mode = tk.BooleanVar(value=True)
        self.palette_dark = {
            'bg': '#121212',
            'panel': '#1E1E1E',
            'fg': '#E8E8E8',
            'muted': '#9E9E9E'
        }
        self.palette_light = {
            'bg': '#F5F5F5',
            'panel': '#FFFFFF',
            'fg': '#111111',
            'muted': '#555555'
        }
        
        self.config_file = "arbuzav_config.json"
        self.button_coords = {'A': None, 'S': None, 'D': None, 'F': None, 'G': None}
        self.hit_line_area = None
        self.scan_area = None
        
        self.running = False
        self.calibration_window = None
        self.calibration_step = 0
        self.calibration_buttons = ['A', 'S', 'D', 'F', 'G']
        self.calibration_listening = False
        
        # IMPROVED DEFAULTS
        self.threshold_value = 55  # Lower = detect more circles
        self.hit_tolerance = 110  # Window around hit line (smaller = меньше ранних)
        self.cooldown_time = 250  # ms between same key presses
        self.lane_tolerance = 150  # Max X distance to lane
        self.debug_mode = True  # Show all detected circles
        
        self.start_hotkey_monitor()
        self.load_config()
        self.create_gui()
        self.apply_theme()
    
    def start_hotkey_monitor(self):
        def monitor():
            print("Hotkeys: F1=Start, F3=Stop")
            f1_was = f3_was = False
            while True:
                try:
                    f1 = user32.GetAsyncKeyState(VK_CODE['f1']) & 0x8000 != 0
                    if f1 and not f1_was:
                        self.root.after(0, self.start_bot)
                    f1_was = f1
                    
                    f3 = user32.GetAsyncKeyState(VK_CODE['f3']) & 0x8000 != 0
                    if f3 and not f3_was:
                        self.root.after(0, self.stop_bot)
                    f3_was = f3
                    time.sleep(0.05)
                except:
                    time.sleep(0.1)
        threading.Thread(target=monitor, daemon=True).start()
        
    def create_gui(self):
        # Scrollable wrapper so controls remain reachable when the window is small
        outer = tk.Frame(self.root)
        outer.pack(fill='both', expand=True)

        canvas = tk.Canvas(outer, borderwidth=0, highlightthickness=0)
        self.canvas = canvas
        vscroll = tk.Scrollbar(outer, orient='vertical', command=canvas.yview)
        hscroll = tk.Scrollbar(outer, orient='horizontal', command=canvas.xview)
        canvas.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        vscroll.pack(side='right', fill='y')
        hscroll.pack(side='bottom', fill='x')
        canvas.pack(side='left', fill='both', expand=True)

        self.content_frame = tk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=self.content_frame, anchor='nw', tags=("content",))

        def sync_scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox('all'))
            # Keep content at least its requested width so horizontal scroll can appear when needed
            req_w = self.content_frame.winfo_reqwidth()
            canvas.itemconfig(canvas_window, width=max(req_w, canvas.winfo_width()))

        self.content_frame.bind('<Configure>', sync_scrollregion)
        canvas.bind('<Configure>', sync_scrollregion)

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all('<MouseWheel>', _on_mousewheel)
        # Shift+wheel for horizontal scroll
        def _on_shift_mousewheel(event):
            if event.state & 0x0001:  # Shift pressed
                canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all('<Shift-MouseWheel>', _on_shift_mousewheel)

        header = tk.Frame(self.content_frame)
        header.pack(fill='x', pady=(10, 4))
        tk.Label(header, text="ArbuzAV Pro", font=("Arial", 24, "bold"), 
            fg="#2196F3").pack(side='left', padx=12)
        tk.Label(header, text="⚡ Simultaneous Multi-Key Press Supported!", 
            font=("Arial", 10), fg="green").pack(side='left', padx=8)
        tk.Checkbutton(header, text="Dark mode", variable=self.dark_mode, command=self.apply_theme).pack(side='right', padx=12)
        
        # Settings
        settings_frame = tk.LabelFrame(self.content_frame, text="⚙️ Detection Settings", 
                          font=("Arial", 11, "bold"), padx=15, pady=12)
        settings_frame.pack(pady=10, padx=20, fill="x")
        
        # Threshold
        tk.Label(settings_frame, text="Detection Threshold:", 
                font=("Arial", 9, "bold")).grid(row=0, column=0, sticky='w', pady=5)
        
        threshold_frame = tk.Frame(settings_frame)
        threshold_frame.grid(row=0, column=1, sticky='w', padx=10)
        
        self.threshold_var = tk.IntVar(value=self.threshold_value)
        tk.Scale(threshold_frame, from_=40, to=120, orient='horizontal',
                variable=self.threshold_var, length=220,
                command=lambda v: self.threshold_label.config(text=f"{int(float(v))}")
                ).pack(side='left')
        self.threshold_label = tk.Label(threshold_frame, text=f"{self.threshold_value}", 
                                       font=("Arial", 9, "bold"), width=4)
        self.threshold_label.pack(side='left', padx=5)
        tk.Label(settings_frame, text="Lower = More circles detected", 
                font=("Arial", 8), fg="gray").grid(row=1, column=1, sticky='w', padx=10)
        
        # Hit Tolerance
        tk.Label(settings_frame, text="Hit Window:", 
                font=("Arial", 9, "bold")).grid(row=2, column=0, sticky='w', pady=5)
        
        tolerance_frame = tk.Frame(settings_frame)
        tolerance_frame.grid(row=2, column=1, sticky='w', padx=10)
        
        self.tolerance_var = tk.IntVar(value=self.hit_tolerance)
        tk.Scale(tolerance_frame, from_=60, to=200, orient='horizontal',
                variable=self.tolerance_var, length=220,
                command=lambda v: self.tolerance_label.config(text=f"{int(float(v))}px")
                ).pack(side='left')
        self.tolerance_label = tk.Label(tolerance_frame, text=f"{self.hit_tolerance}px", 
                                       font=("Arial", 9, "bold"), width=6)
        self.tolerance_label.pack(side='left', padx=5)
        tk.Label(settings_frame, text="Bigger = Earlier press", 
                font=("Arial", 8), fg="gray").grid(row=3, column=1, sticky='w', padx=10)
        
        # Cooldown
        tk.Label(settings_frame, text="Anti-Double Cooldown:", 
                font=("Arial", 9, "bold")).grid(row=4, column=0, sticky='w', pady=5)
        
        cooldown_frame = tk.Frame(settings_frame)
        cooldown_frame.grid(row=4, column=1, sticky='w', padx=10)
        
        self.cooldown_var = tk.IntVar(value=self.cooldown_time)
        tk.Scale(cooldown_frame, from_=80, to=300, orient='horizontal',
                variable=self.cooldown_var, length=220,
                command=lambda v: self.cooldown_label.config(text=f"{int(float(v))}ms")
                ).pack(side='left')
        self.cooldown_label = tk.Label(cooldown_frame, text=f"{self.cooldown_time}ms", 
                                      font=("Arial", 9, "bold"), width=6)
        self.cooldown_label.pack(side='left', padx=5)
        tk.Label(settings_frame, text="Higher = No repeats", 
                font=("Arial", 8), fg="gray").grid(row=5, column=1, sticky='w', padx=10)
        
        # Tips
        tip_frame = tk.Frame(settings_frame, bg="#E3F2FD", relief='ridge', bd=2)
        tip_frame.grid(row=6, column=0, columnspan=2, sticky='ew', pady=10, padx=5)
        
        tk.Label(tip_frame, text="💡 Tips:", font=("Arial", 9, "bold"), 
                bg="#E3F2FD").pack(anchor='w', padx=5, pady=2)
        tk.Label(tip_frame, text="• Missing circles? → Lower threshold (40-60)", 
                font=("Arial", 8), bg="#E3F2FD").pack(anchor='w', padx=10)
        tk.Label(tip_frame, text="• Late presses? → Increase hit window (130-160)", 
                font=("Arial", 8), bg="#E3F2FD").pack(anchor='w', padx=10)
        tk.Label(tip_frame, text="• Double presses? → Increase cooldown (200-250)", 
                font=("Arial", 8), bg="#E3F2FD").pack(anchor='w', padx=10)
        
        # Start/Stop
        control_frame = tk.Frame(self.content_frame)
        control_frame.pack(pady=12)
        
        self.start_btn = tk.Button(control_frame, text="▶ START (F1)", command=self.start_bot, 
                                   bg="#4CAF50", fg="white", font=("Arial", 14, "bold"), 
                                   width=15, height=2)
        self.start_btn.grid(row=0, column=0, padx=10)
        
        self.stop_btn = tk.Button(control_frame, text="⬛ STOP (F3)", command=self.stop_bot, 
                                  bg="#f44336", fg="white", font=("Arial", 14, "bold"), 
                                  width=15, height=2)
        self.stop_btn.grid(row=0, column=1, padx=10)
        
        # Button coords
        coords_frame = tk.LabelFrame(self.content_frame, text="Button Coordinates", 
                                    font=("Arial", 10, "bold"), padx=10, pady=8)
        coords_frame.pack(pady=8, padx=20, fill="both")
        
        self.coord_labels = {}
        for button in ['A', 'S', 'D', 'F', 'G']:
            row_frame = tk.Frame(coords_frame)
            row_frame.pack(fill="x", pady=2)
            tk.Label(row_frame, text=f"{button}:", font=("Arial", 9, "bold"), 
                    width=3).pack(side="left", padx=5)
            coord_text = "Not set"
            if self.button_coords[button]:
                coord_text = f"X: {self.button_coords[button][0]}, Y: {self.button_coords[button][1]}"
            label = tk.Label(row_frame, text=coord_text, font=("Arial", 8), 
                           width=28, anchor="w")
            label.pack(side="left", padx=5)
            self.coord_labels[button] = label
        
        tk.Button(coords_frame, text="📍 Calibrate", 
                 command=self.start_calibration, bg="#2196F3", fg="white", 
                 font=("Arial", 9, "bold"), width=28).pack(pady=8)
        
        # Areas
        areas_frame = tk.Frame(self.content_frame)
        areas_frame.pack(pady=8, padx=20, fill="x")
        
        hit_frame = tk.LabelFrame(areas_frame, text="Hit Line", font=("Arial", 9, "bold"), padx=8, pady=6)
        hit_frame.pack(side='left', expand=True, fill='both', padx=5)
        self.hitline_label = tk.Label(hit_frame, text="Not set", font=("Arial", 8))
        self.hitline_label.pack(pady=3)
        tk.Button(hit_frame, text="Set", command=self.set_hit_line_area, 
                 bg="#FF9800", fg="white", font=("Arial", 8, "bold"), width=15).pack()
        
        scan_frame = tk.LabelFrame(areas_frame, text="Scan Area", font=("Arial", 9, "bold"), padx=8, pady=6)
        scan_frame.pack(side='left', expand=True, fill='both', padx=5)
        self.scan_label = tk.Label(scan_frame, text="Not set", font=("Arial", 8))
        self.scan_label.pack(pady=3)
        tk.Button(scan_frame, text="Set", command=self.set_scan_area, 
                 bg="#9C27B0", fg="white", font=("Arial", 8, "bold"), width=15).pack()
        
        # Status
        status_frame = tk.Frame(self.content_frame, bg="#F5F5F5", relief='sunken', bd=2)
        status_frame.pack(pady=10, padx=20, fill="x")

        self.status_label = tk.Label(status_frame, text="⏸ Idle",
                         font=("Arial", 12, "bold"), fg="blue", bg="#F5F5F5")
        self.status_label.pack(pady=5)

        self.stats_label = tk.Label(status_frame, text="Hits: 0 | Multi: 0",
                        font=("Arial", 9), fg="gray", bg="#F5F5F5")
        self.stats_label.pack(pady=3)

        # Subscribe
        subscribe_frame = tk.Frame(self.content_frame)
        subscribe_frame.pack(pady=(4, 12))
        tk.Button(subscribe_frame, text="Subscribe to the author",
              command=lambda: self.open_link("https://www.youtube.com/@sayson6129"),
              bg="#E53935", fg="white", font=("Arial", 10, "bold"), width=24).pack()

    def apply_theme(self):
        palette = self.palette_dark if self.dark_mode.get() else self.palette_light

        def recolor(widget, is_panel=False):
            try:
                if isinstance(widget, (tk.Frame, tk.LabelFrame)):
                    widget.configure(bg=palette['panel' if is_panel else 'bg'])
                elif isinstance(widget, tk.Canvas):
                    widget.configure(bg=palette['bg'], highlightbackground=palette['bg'])
                elif isinstance(widget, tk.Label):
                    widget.configure(bg=widget.master.cget('bg'), fg=palette['fg'])
                elif isinstance(widget, tk.Scale):
                    widget.configure(bg=widget.master.cget('bg'), fg=palette['fg'], troughcolor=palette['bg'], highlightthickness=0)
                elif isinstance(widget, tk.Entry):
                    widget.configure(bg=palette['panel'], fg=palette['fg'], insertbackground=palette['fg'])
            except Exception:
                pass
            for child in widget.winfo_children():
                recolor(child, isinstance(child, (tk.Frame, tk.LabelFrame)))

        self.root.configure(bg=palette['bg'])
        recolor(self.root, False)

    def open_link(self, url: str):
        try:
            webbrowser.open(url)
        except Exception:
            pass
        
    def start_calibration(self):
        if self.calibration_window:
            return
        self.calibration_step = 0
        self.calibration_window = tk.Toplevel(self.root)
        # Fullscreen transparent overlay; do not set overrideredirect to keep fullscreen working
        self.calibration_window.attributes('-fullscreen', True)
        self.calibration_window.attributes('-topmost', True)
        self.calibration_window.attributes('-alpha', 0.15)
        self.calibration_window.configure(bg='black')
        self.calibration_window.protocol("WM_DELETE_WINDOW", self.cancel_calibration)

        # Instruction panel (dock top)
        top_panel = tk.Frame(self.calibration_window, bg='#000000', highlightthickness=0)
        top_panel.pack(side='top', fill='x')
        tk.Label(top_panel, text="Calibration: click the in-game button, then ENTER = save, SPACE = skip, ESC = exit", 
             font=("Arial", 13, "bold"), fg="white", bg='#000000').pack(pady=8)

        info_panel = tk.Frame(self.calibration_window, bg='#000000', highlightthickness=0)
        info_panel.pack(side='top', pady=6)
        self.calibration_info_label = tk.Label(info_panel, text="", font=("Arial", 18, "bold"), fg="white", bg='#000000')
        self.calibration_info_label.pack()
        self.calibration_coord_label = tk.Label(info_panel, text="", font=("Arial", 14), fg="#4CAF50", bg='#000000')
        self.calibration_coord_label.pack()

        hint_panel = tk.Frame(self.calibration_window, bg='#000000', highlightthickness=0)
        hint_panel.pack(side='bottom', pady=10)
        tk.Label(hint_panel, text="Hint: click the game button first, then press ENTER / SPACE / ESC", 
             font=("Arial", 11), fg="white", bg='#000000').pack()

        # Hotkey monitor for calibration (global polling)
        self.calibration_hotkeys_active = True
        threading.Thread(target=self.calibration_hotkey_monitor, daemon=True).start()

        self.next_calibration_step()
        
    def next_calibration_step(self):
        if self.calibration_step >= len(self.calibration_buttons):
            self.finish_calibration()
            return
        button = self.calibration_buttons[self.calibration_step]
        self.calibration_info_label.config(text=f"{self.calibration_step + 1}/5: '{button}'")
        self.calibration_listening = True
        self.track_mouse()
        self.calibration_window.bind('<Return>', lambda e: self.confirm_calibration())

    def calibration_hotkey_monitor(self):
        enter_was = space_was = esc_was = False
        while getattr(self, 'calibration_hotkeys_active', False):
            enter = user32.GetAsyncKeyState(0x0D) & 0x8000 != 0
            space = user32.GetAsyncKeyState(0x20) & 0x8000 != 0
            esc = user32.GetAsyncKeyState(0x1B) & 0x8000 != 0

            if enter and not enter_was and self.calibration_listening:
                self.root.after(0, self.confirm_calibration)
            if space and not space_was and self.calibration_listening:
                self.root.after(0, self.skip_calibration_step)
            if esc and not esc_was:
                self.root.after(0, self.cancel_calibration)

            enter_was, space_was, esc_was = enter, space, esc
            time.sleep(0.05)
        
    def track_mouse(self):
        if self.calibration_listening and self.calibration_window:
            try:
                x, y = pyautogui.position()
                self.current_calibration_coords = (x, y)
                self.calibration_coord_label.config(text=f"X={x}, Y={y}", fg="green")
                self.calibration_window.after(50, self.track_mouse)
            except:
                pass
    
    def skip_calibration_step(self):
        button = self.calibration_buttons[self.calibration_step]
        self.button_coords[button] = None
        self.coord_labels[button].config(text="Skipped")
        self.calibration_listening = False
        self.calibration_step += 1
        if self.calibration_step < len(self.calibration_buttons):
            time.sleep(0.2)
            self.next_calibration_step()
        else:
            self.finish_calibration()
    
    def confirm_calibration(self):
        if hasattr(self, 'current_calibration_coords'):
            button = self.calibration_buttons[self.calibration_step]
            self.button_coords[button] = self.current_calibration_coords
            self.coord_labels[button].config(
                text=f"X: {self.current_calibration_coords[0]}, Y: {self.current_calibration_coords[1]}")
            self.calibration_listening = False
            self.calibration_step += 1
            if self.calibration_step < len(self.calibration_buttons):
                time.sleep(0.2)
                self.next_calibration_step()
            else:
                self.finish_calibration()
                
    def cancel_calibration(self):
        self.calibration_listening = False
        self.calibration_hotkeys_active = False
        if self.calibration_window:
            self.calibration_window.destroy()
            self.calibration_window = None
            
    def finish_calibration(self):
        self.save_config()
        # Close overlay first so messagebox is clickable
        self.cancel_calibration()
        messagebox.showinfo("✓", "Saved!")
        
    def set_hit_line_area(self):
        messagebox.showinfo("Hit Line", "Drag line. ENTER=OK")
        self.select_area('hitline')
        
    def set_scan_area(self):
        messagebox.showinfo("Scan", "Drag area. ENTER=OK")
        self.select_area('scan')
        
    def select_area(self, area_type):
        selector = tk.Toplevel(self.root)
        selector.attributes('-fullscreen', True)
        selector.attributes('-topmost', True)
        selector.configure(bg='black')
        selector.attributes('-alpha', 0.4)
        
        canvas = tk.Canvas(selector, cursor="cross", bg='black', highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        canvas.create_text(selector.winfo_screenwidth() // 2, 50, 
                          text="DRAG | ENTER=OK | ESC=Cancel", 
                          fill='yellow', font=('Arial', 18, 'bold'))
        
        rect = None
        start_x = start_y = 0
        info_text = None
        
        def on_down(e):
            nonlocal start_x, start_y, rect, info_text
            start_x, start_y = e.x, e.y
            if rect:
                canvas.delete(rect)
            if info_text:
                canvas.delete(info_text)
            rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, 
                                          outline='lime', width=4, dash=(5, 5))
        
        def on_move(e):
            nonlocal rect, info_text
            if rect:
                canvas.coords(rect, start_x, start_y, e.x, e.y)
                if info_text:
                    canvas.delete(info_text)
                w, h = abs(e.x - start_x), abs(e.y - start_y)
                info_text = canvas.create_text((start_x + e.x) // 2, min(start_y, e.y) - 20, 
                                              text=f"{w} x {h}", fill='yellow', font=('Arial', 14, 'bold'))
        
        def on_confirm(e=None):
            if rect:
                coords = canvas.coords(rect)
                x1, y1, x2, y2 = map(int, coords)
                x, y = min(x1, x2), min(y1, y2)
                w, h = abs(x2 - x1), abs(y2 - y1)
                if w > 10 and h > 10:
                    if area_type == 'hitline':
                        self.hit_line_area = (x, y, w, h)
                        self.hitline_label.config(text=f"X:{x} Y:{y}\n{w}x{h}")
                    else:
                        self.scan_area = (x, y, w, h)
                        self.scan_label.config(text=f"X:{x} Y:{y}\n{w}x{h}")
                    self.save_config()
                    messagebox.showinfo("✓", "Saved!")
            selector.destroy()
        
        canvas.bind('<Button-1>', on_down)
        canvas.bind('<B1-Motion>', on_move)
        selector.bind('<Return>', on_confirm)
        selector.bind('<Escape>', lambda e: selector.destroy())
    
    def start_bot(self):
        if self.running:
            return
        if not all(self.button_coords.values()):
            messagebox.showerror("Error", "Calibrate all!")
            return
        if not self.hit_line_area or not self.scan_area:
            messagebox.showerror("Error", "Set areas!")
            return
        
        self.threshold_value = self.threshold_var.get()
        self.hit_tolerance = self.tolerance_var.get()
        self.cooldown_time = self.cooldown_var.get()
        
        self.running = True
        self.status_label.config(text="▶ Running", fg="green")
        threading.Thread(target=self.bot_loop, daemon=True).start()
        
    def stop_bot(self):
        self.running = False
        self.status_label.config(text="⏸ Stopped", fg="red")
        
    def bot_loop(self):
        """PRO bot with simultaneous multi-key press"""
        lanes = {btn: coords[0] for btn, coords in self.button_coords.items() if coords}
        hit_y = self.hit_line_area[1] + self.hit_line_area[3] // 2
        
        key_cooldown = {}
        hit_count = 0
        multi_count = 0
        
        print("="*70)
        print("🎮 BOT STARTED - PRO with SIMULTANEOUS PRESS")
        print(f"Threshold: {self.threshold_value} | Tolerance: ±{self.hit_tolerance}px | Cooldown: {self.cooldown_time}ms")
        print(f"Lane tolerance: {self.lane_tolerance}px")
        print(f"Scan area: x={self.scan_area[0]}, y={self.scan_area[1]}, w={self.scan_area[2]}, h={self.scan_area[3]}")
        print(f"Hit line Y: {hit_y}")
        print(f"Lanes X: {lanes}")
        print("="*70)
        
        while self.running:
            try:
                x, y, w, h = self.scan_area
                screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # CLAHE for better contrast
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                gray = clahe.apply(gray)
                
                _, thresh = cv2.threshold(gray, self.threshold_value, 255, cv2.THRESH_BINARY)
                
                kernel = np.ones((5, 5), np.uint8)
                thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
                
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                current_time = time.time()
                
                # Cleanup cooldowns
                for key in list(key_cooldown.keys()):
                    if (current_time - key_cooldown[key]) * 1000 > self.cooldown_time:
                        del key_cooldown[key]
                
                # DEBUG: Show contour count
                if len(contours) > 0 and int(current_time * 10) % 20 == 0:
                    print(f"[DEBUG] Contours found: {len(contours)}")

                # Find circles to press
                circles_to_press = {}

                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area < 50 or area > 50000:  # More permissive area filter
                        continue
                    
                    M = cv2.moments(contour)
                    if M["m00"] == 0:
                        continue
                    
                    cx = int(M["m10"] / M["m00"]) + x
                    cy = int(M["m01"] / M["m00"]) + y
                    
                    # Y offset relative to hit line
                    y_offset = cy - hit_y  # >0 means below/at line
                    
                    # Reject circles far above line (early hits) and far below
                    if y_offset < -25 or y_offset > self.hit_tolerance:
                        continue
                    
                    closest = None
                    min_dist = float('inf')
                    
                    for btn, lane_x in lanes.items():
                        dist = abs(cx - lane_x)
                        if dist < min_dist and dist < self.lane_tolerance:
                            min_dist = dist
                            closest = btn
                    
                    if closest and closest not in key_cooldown:
                        # Prefer the circle that is closest to the hit line (smallest positive offset)
                        if closest not in circles_to_press or y_offset < circles_to_press[closest][1]:
                            circles_to_press[closest] = (cx, y_offset, cy)
                
                # Press simultaneously!
                if circles_to_press:
                    # Use virtual-key codes to stay layout-independent
                    keys_to_press = [VK_CODE[btn.lower()] for btn in circles_to_press.keys()]
                    press_keys_simultaneous(keys_to_press, hold_ms=30)
                    
                    for btn in circles_to_press.keys():
                        key_cooldown[btn] = current_time
                    
                    hit_count += len(circles_to_press)
                    if len(circles_to_press) > 1:
                        multi_count += 1
                    
                    keys_str = "+".join(circles_to_press.keys())
                    # Debug: show Y position and distance for each pressed key
                    debug_info = ", ".join([f"{k}(cy:{v[2]}, y_offset:{v[1]:.0f})" for k, v in circles_to_press.items()])
                    print(f"[HIT] {keys_str} | hit_y={hit_y} | {debug_info}")
                    
                    self.root.after(0, lambda: self.stats_label.config(
                        text=f"Hits: {hit_count} | Multi: {multi_count}"))
                    
                    # Small delay after sending input to prevent bouncing
                    time.sleep(0.02)
                
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(0.05)
            
            # FIXED: Add small sleep to prevent CPU overload and ensure stable timing
            time.sleep(0.005)  # ~200 FPS max, enough for rhythm games
        
        print("="*70)
        print(f"⏸ STOPPED | Hits: {hit_count} | Multi-press: {multi_count}")
        print("="*70)
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.button_coords = config.get('button_coords', self.button_coords)
                    self.hit_line_area = config.get('hit_line_area')
                    self.scan_area = config.get('scan_area')
                    
                    for btn, coords in self.button_coords.items():
                        if coords:
                            self.coord_labels[btn].config(text=f"X: {coords[0]}, Y: {coords[1]}")
                    
                    if self.hit_line_area:
                        x, y, w, h = self.hit_line_area
                        self.hitline_label.config(text=f"X:{x} Y:{y}\n{w}x{h}")
                    
                    if self.scan_area:
                        x, y, w, h = self.scan_area
                        self.scan_label.config(text=f"X:{x} Y:{y}\n{w}x{h}")
            except:
                pass
    
    def save_config(self):
        config = {
            'button_coords': self.button_coords,
            'hit_line_area': self.hit_line_area,
            'scan_area': self.scan_area
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    print("="*70)
    print("🎮 ArbuzAV PRO - Multi-Key Simultaneous Press")
    print("✨ CLAHE enhancement + Improved detection")
    print("F1=Start | F3=Stop")
    print("="*70)
    app = ArbuzAV()
    app.run()
