# Bijoy Keyboard Mapper

## What It Does
This application implements the **Bijoy typing method** for Bengali text input. It automatically converts English key combinations into Bengali characters as you type, allowing you to write Bengali text using the popular Bijoy system without installing special fonts or keyboard layouts.

**Example:** Type `gS` + SPACE → Get `ঊ` | Type `Yh` + SPACE → Get `ছব`

## Quick Setup

### Prerequisites
- Python 3.6+ installed
- Administrator/sudo privileges (required for keyboard monitoring)

### Installation
Users will need these Linux packages:
```bash
sudo apt install xdotool xclip  # Ubuntu/Debian
sudo dnf install xdotool xclip  # Fedora
sudo pacman -S xdotool xclip    # Arch
```

```bash
# Navigate to project folder
cd path/to/bijoy-keyboard-mapper

# Create virtual environment
python -m venv env

# Activate environment
# Windows:
env\Scripts\activate
# macOS/Linux:
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run Application
```bash
python main.py
```

**Success message:**
```
Bijoy Keyboard Mapper is running!
Press F12 to toggle on/off
```

## How to Use
1. **Type Bijoy combinations** in any application (Word, browser, etc.)
2. **Press SPACE** to convert English letters to Bengali
3. **Works everywhere** - no need to switch keyboards or install fonts

### Examples
- `gS + SPACE` → `ঊ`
- `Yh + SPACE` → `ছব`
- `kb + SPACE` → `কব`

### Controls
- **F12**: Toggle mapper on/off

## Troubleshooting

### Permission Issues
- **Windows**: Run Command Prompt as Administrator
- **macOS/Linux**: Use `sudo python main.py`

### Not Working?
- Ensure `bijoyClassic_parsed.json` exists in project folder
- Check console for error messages
- Try F12 to toggle off/on

## Quick Test
1. Run the application
2. Open Notepad or any text editor
3. Type `gS` and press SPACE
4. You should see `ঊ` appear with `gS` completely removed

## References
https://github.com/Mad-FOX/bijoy2unicode

https://github.com/abdullah-if/ibus-victory-bn

---
**Now you can type Bengali anywhere using the traditional Bijoy method!** 🎉