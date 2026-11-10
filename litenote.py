#!/usr/bin/env python3
"""LiteNote - a lightweight Notepad-style text editor for Ubuntu/Linux."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
from pathlib import Path


class LiteNote:
    def __init__(self, root):
        self.root = root
        self.root.title("LiteNote - Untitled")
        self.root.geometry("900x600")
        self.root.minsize(520, 350)

        self.current_file = None
        self.modified = False
        self.word_wrap = tk.BooleanVar(value=True)
        self.font_size = 12

        self._build_menu()
        self._build_toolbar()
        self._build_editor()
        self._build_statusbar()
        self._bind_shortcuts()

        self.text.focus_set()
        self.update_status()

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self.text.event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self.text.event_generate("<<Copy>>"))
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=lambda: self.text.event_generate("<<Paste>>"))
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=self.select_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find...", accelerator="Ctrl+F", command=self.find_text)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_checkbutton(label="Word Wrap", variable=self.word_wrap, command=self.toggle_wrap)
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In", accelerator="Ctrl++", command=lambda: self.change_font(1))
        view_menu.add_command(label="Zoom Out", accelerator="Ctrl+-", command=lambda: self.change_font(-1))
        view_menu.add_command(label="Reset Zoom", command=self.reset_font)
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About LiteNote", command=self.about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_toolbar(self):
        bar = ttk.Frame(self.root, padding=(6, 5))
        bar.pack(side=tk.TOP, fill=tk.X)

        buttons = [
            ("New", self.new_file),
            ("Open", self.open_file),
            ("Save", self.save_file),
            ("|", None),
            ("Undo", self.undo),
            ("Redo", self.redo),
            ("|", None),
            ("Find", self.find_text),
        ]
        for label, command in buttons:
            if command is None:
                ttk.Separator(bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
            else:
                ttk.Button(bar, text=label, command=command).pack(side=tk.LEFT, padx=2)

    def _build_editor(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        self.text_font = font.Font(family="DejaVu Sans Mono", size=self.font_size)
        self.text = tk.Text(
            frame,
            wrap=tk.WORD,
            undo=True,
            autoseparators=True,
            maxundo=-1,
            font=self.text_font,
            padx=8,
            pady=8,
            borderwidth=0,
            highlightthickness=0,
        )
        yscroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.text.yview)
        xscroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.text.xview)
        self.text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self.text.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.text.bind("<<Modified>>", self.on_modified)
        self.text.bind("<KeyRelease>", lambda _e: self.update_status())
        self.text.bind("<ButtonRelease-1>", lambda _e: self.update_status())

    def _build_statusbar(self):
        self.status = ttk.Label(self.root, text="Ln 1, Col 1", anchor=tk.W, padding=(8, 4))
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def _bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda _e: self.new_file())
        self.root.bind("<Control-o>", lambda _e: self.open_file())
        self.root.bind("<Control-s>", lambda _e: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda _e: self.save_as())
        self.root.bind("<Control-f>", lambda _e: self.find_text())
        self.root.bind("<Control-a>", lambda _e: self.select_all())
        self.root.bind("<Control-plus>", lambda _e: self.change_font(1))
        self.root.bind("<Control-equal>", lambda _e: self.change_font(1))
        self.root.bind("<Control-minus>", lambda _e: self.change_font(-1))

    def on_modified(self, _event=None):
        if self.text.edit_modified():
            self.modified = True
            self.update_title()
            self.text.edit_modified(False)

    def update_title(self):
        name = self.current_file.name if self.current_file else "Untitled"
        mark = "*" if self.modified else ""
        self.root.title(f"{mark}{name} - LiteNote")

    def update_status(self):
        try:
            line, col = self.text.index(tk.INSERT).split(".")
            content = self.text.get("1.0", "end-1c")
            words = len(content.split())
            chars = len(content)
            self.status.config(text=f"Ln {line}, Col {int(col) + 1}    |    {words} words    |    {chars} characters")
        except tk.TclError:
            self.status.config(text="Ln 1, Col 1")

    def confirm_discard(self):
        if not self.modified:
            return True
        answer = messagebox.askyesnocancel(
            "Unsaved changes",
            "This document has unsaved changes. Save before continuing?"
        )
        if answer is None:
            return False
        if answer:
            return self.save_file()
        return True

    def new_file(self):
        if not self.confirm_discard():
            return
        self.text.delete("1.0", tk.END)
        self.current_file = None
        self.modified = False
        self.text.edit_reset()
        self.text.edit_modified(False)
        self.update_title()
        self.update_status()

    def open_file(self):
        if not self.confirm_discard():
            return
        filename = filedialog.askopenfilename(
            title="Open text file",
            filetypes=[
                ("Text files", "*.txt *.log *.md *.csv *.py *.json *.xml *.html *.css"),
                ("All files", "*.*"),
            ],
        )
        if not filename:
            return
        try:
            content = Path(filename).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = Path(filename).read_text(encoding="utf-8-sig")
            except Exception as exc:
                messagebox.showerror("Open failed", f"Could not read this file:\n{exc}")
                return
        except OSError as exc:
            messagebox.showerror("Open failed", f"Could not open this file:\n{exc}")
            return

        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)
        self.current_file = Path(filename)
        self.modified = False
        self.text.edit_reset()
        self.text.edit_modified(False)
        self.update_title()
        self.update_status()

    def save_file(self):
        if self.current_file is None:
            return self.save_as()
        try:
            self.current_file.write_text(self.text.get("1.0", "end-1c"), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save failed", f"Could not save this file:\n{exc}")
            return False
        self.modified = False
        self.update_title()
        return True

    def save_as(self):
        filename = filedialog.asksaveasfilename(
            title="Save text file",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not filename:
            return False
        self.current_file = Path(filename)
        return self.save_file()

    def undo(self):
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass
        self.update_status()

    def redo(self):
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass
        self.update_status()

    def select_all(self):
        self.text.tag_add(tk.SEL, "1.0", tk.END)
        self.text.mark_set(tk.INSERT, "1.0")
        self.text.see(tk.INSERT)
        return "break"

    def find_text(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Find")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.grab_set()

        ttk.Label(dialog, text="Find what:").grid(row=0, column=0, padx=10, pady=10)
        query = ttk.Entry(dialog, width=32)
        query.grid(row=0, column=1, padx=10, pady=10)
        query.focus_set()

        def search_next():
            term = query.get()
            if not term:
                return
            start = self.text.index(tk.INSERT)
            pos = self.text.search(term, start, stopindex=tk.END, nocase=True)
            if not pos:
                pos = self.text.search(term, "1.0", stopindex=start, nocase=True)
            self.text.tag_remove("find_match", "1.0", tk.END)
            if pos:
                end = f"{pos}+{len(term)}c"
                self.text.tag_add("find_match", pos, end)
                self.text.tag_config("find_match", background="#ffe680", foreground="#111111")
                self.text.mark_set(tk.INSERT, end)
                self.text.see(pos)
                self.text.focus_set()
            else:
                messagebox.showinfo("Find", "No match found.", parent=dialog)

        ttk.Button(dialog, text="Find Next", command=search_next).grid(row=1, column=1, sticky=tk.E, padx=10, pady=(0, 10))
        query.bind("<Return>", lambda _e: search_next())
        dialog.bind("<Escape>", lambda _e: dialog.destroy())

    def toggle_wrap(self):
        self.text.configure(wrap=tk.WORD if self.word_wrap.get() else tk.NONE)

    def change_font(self, delta):
        self.font_size = max(7, min(36, self.font_size + delta))
        self.text_font.configure(size=self.font_size)

    def reset_font(self):
        self.font_size = 12
        self.text_font.configure(size=self.font_size)

    def about(self):
        messagebox.showinfo(
            "About LiteNote",
            "LiteNote 1.0\nA lightweight text editor for Ubuntu/Linux.\nBuilt with Python and Tkinter."
        )

    def exit_app(self):
        if self.confirm_discard():
            self.root.destroy()


def main():
    root = tk.Tk()
    LiteNote(root)
    root.mainloop()


if __name__ == "__main__":
    main()
