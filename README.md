# LiteNote v2

Lightweight tabbed text editor for Ubuntu/Linux, built with Python 3 and Tkinter.

## Features
- Multiple tabs; create, open and close documents
- New, Open, Save and Save As
- UTF-8 text files, including Persian text
- Cut, Copy, Paste and Select All (menus, shortcuts and right-click menu)
- Undo / Redo and Find Next
- Font family and size selection in the toolbar
- Word Wrap, right-aligned paragraph mode and Dark Mode
- Auto-save every 30 seconds for files that have already been saved to a path
- Status bar: line, column, word and character count
- Unsaved-change confirmation

## Install requirements on Ubuntu
```bash
sudo apt update
sudo apt install python3 python3-tk
```

## Run
```bash
python3 litenote.py
```

## Keyboard shortcuts
| Action | Shortcut |
|---|---|
| New tab | Ctrl+N |
| Open | Ctrl+O |
| Save | Ctrl+S |
| Save As | Ctrl+Shift+S |
| Close tab | Ctrl+W |
| Find | Ctrl+F |
| Select all | Ctrl+A |
| Cut / Copy / Paste | Ctrl+X / Ctrl+C / Ctrl+V |
| Undo / Redo | Ctrl+Z / Ctrl+Y |
| Zoom in / out | Ctrl++ / Ctrl+- |

## Notes
Auto-save runs every 30 seconds and saves modified documents that already have a filename.
For a new untitled document, use Save once to choose its location. Right alignment is supported;
full Persian/Arabic bidirectional shaping depends on the Tk version/build installed on the system.
