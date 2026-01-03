# ArbuzAV - Auto Rhythm Game Bot

ArbuzAV is an automation tool for rhythm games (Guitar Hero style) with 5 lanes (A, S, D, F, G).

## Features

- 🎮 Automatic detection of falling circles
- 🎯 Precise clicking at the hit line
- ⌨️ Hotkey support (F1 to Start, F3 to Stop)
- 🔧 Easy calibration system
- 💾 Configuration auto-save
- 🪟 Always-on-top windows

### ALL FILES MUST BE IN THE ONE FOLDER

### Prerequisites
- Python 3.8 or higher
- Windows OS (required for keyboard library)

### Setup

1. Install Python from https://www.python.org/downloads/

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Run the program:
```bash
python ArbuzAV.py
```

PS: Also, to download all requirements just run 'run.bat'.

## To make it EXE

1. Download All Files
2. Place them in one shared folder
3. Run build.bat
4. After this you will see the .exe in 'dist' folder

## Usage Guide

### Step 1: Calibrate Button Coordinates

1. Click "Calibrate Button Coordinates"
2. For each button (A, S, D, F, G):
   - Click on the button in the game
   - Press ENTER to confirm
3. Repeat for all 5 buttons

**Important:** Make sure the game is visible and the buttons are clickable!

### Step 2: Set Hit Line Area

1. Click "Set Hit Line Area"
2. Click and drag to create a horizontal rectangular area
3. This area should cover where circles need to be clicked
4. Press ENTER to confirm or ESC to cancel

**Tip:** The hit line should be just above the A/S/D/F/G buttons in the game

### Step 3: Set Scan Area

1. Click "Set Scan Area"
2. Click and drag to select the entire game area
3. This area should include all falling circles
4. Press ENTER to confirm or ESC to cancel

**Tip:** Include the entire vertical playing field from top to bottom

### Step 4: Start the Bot

1. Make sure the game is running and visible
2. Click "Start (F1)" or press F1 key
3. The bot will automatically detect and click circles
4. Press "Stop (F3)" or F3 key to stop

## How It Works

1. **Screen Capture:** Continuously captures the scan area
2. **Circle Detection:** Uses color detection (HSV green range) to find circles
3. **Lane Detection:** Determines which lane (A/S/D/F/G) the circle is in
4. **Hit Timing:** Waits until circle reaches the hit line
5. **Auto Click:** Clicks the corresponding button coordinate

## Configuration

Settings are automatically saved to `arbuzav_config.json` and loaded on startup.

You can manually edit this file if needed:
```json
{
  "button_coords": {
    "A": [x, y],
    "S": [x, y],
    ...
  },
  "hit_line_area": [x, y, width, height],
  "scan_area": [x, y, width, height]
}
```

## Troubleshooting

### Bot not clicking buttons
- Recalibrate button coordinates
- Ensure the game window is visible and not minimized
- Check that hit line area is set correctly

### Not detecting circles
- Adjust scan area to cover the entire game field
- Check if circles are green (program detects green circles)
- Try adjusting the game window position

### Program crashes
- Run as Administrator
- Check antivirus is not blocking keyboard/mouse control
- Ensure all dependencies are installed correctly


## Notes

- The bot works best with consistent lighting and clear circle visibility
- Performance depends on your screen resolution and hardware
- Some games may have anti-cheat systems that detect automation
- Use responsibly and only for personal/educational purposes

## License

This project is for educational purposes only.

---

Created by Sayson
