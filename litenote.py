#!/usr/bin/env python3
"""LiteNote v2: lightweight tabbed text editor for Ubuntu/Linux."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
from pathlib import Path


class Document:
    def __init__(self, frame, text, path=None):
        self.frame, self.text = frame, text
        self.path = Path(path) if path else None
        self.modified = False


class LiteNote:
    AUTOSAVE_MS = 30_000

    def __init__(self, root):
        self.root = root
        root.title("LiteNote")
        root.geometry("1000x680")
        root.minsize(650, 420)
        self.docs = {}
        self.dark = tk.BooleanVar(value=False)
        self.wrap = tk.BooleanVar(value=True)
        self.rtl = tk.BooleanVar(value=False)
        self.autosave = tk.BooleanVar(value=True)
        self.family = tk.StringVar(value="DejaVu Sans Mono")
        self.size = tk.IntVar(value=12)
        self._build_menu()
        self._build_toolbar()
        self.nb = ttk.Notebook(root)
        self.nb.pack(fill=tk.BOTH, expand=True)
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.status_update())
        self.status = ttk.Label(root, text="Ready", anchor=tk.W, padding=(8, 4))
        self.status.pack(side=tk.BOTTOM, fill=tk.X)
        self._bind_keys()
        self.new_tab()
        root.protocol("WM_DELETE_WINDOW", self.exit_app)
        root.after(self.AUTOSAVE_MS, self.autosave_tick)

    def _build_menu(self):
        bar = tk.Menu(self.root)
        filem = tk.Menu(bar, tearoff=False)
        filem.add_command(label="New Tab", accelerator="Ctrl+N", command=self.new_tab)
        filem.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        filem.add_separator()
        filem.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        filem.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as)
        filem.add_separator()
        filem.add_command(label="Close Tab", accelerator="Ctrl+W", command=self.close_tab)
        filem.add_command(label="Exit", command=self.exit_app)
        bar.add_cascade(label="File", menu=filem)

        edit = tk.Menu(bar, tearoff=False)
        edit.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        edit.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo)
        edit.add_separator()
        for label, seq in (("Cut", "<<Cut>>"), ("Copy", "<<Copy>>"), ("Paste", "<<Paste>>")):
            edit.add_command(label=label, command=lambda s=seq: self.text_event(s))
        edit.add_command(label="Select All", accelerator="Ctrl+A", command=self.select_all)
        edit.add_separator()
        edit.add_command(label="Find...", accelerator="Ctrl+F", command=self.find_text)
        bar.add_cascade(label="Edit", menu=edit)

        view = tk.Menu(bar, tearoff=False)
        view.add_checkbutton(label="Word Wrap", variable=self.wrap, command=self.apply_options)
        view.add_checkbutton(label="Right-to-left alignment", variable=self.rtl, command=self.apply_options)
        view.add_checkbutton(label="Dark Mode", variable=self.dark, command=self.apply_theme)
        view.add_checkbutton(label="Auto Save (30 seconds)", variable=self.autosave)
        bar.add_cascade(label="View", menu=view)

        helpm = tk.Menu(bar, tearoff=False)
        helpm.add_command(label="About LiteNote", command=self.about)
        bar.add_cascade(label="Help", menu=helpm)
        self.root.config(menu=bar)

    def _build_toolbar(self):
        bar = ttk.Frame(self.root, padding=5)
        bar.pack(side=tk.TOP, fill=tk.X)
        for label, fn in (("New", self.new_tab), ("Open", self.open_file),
                          ("Save", self.save_file), ("Undo", self.undo),
                          ("Redo", self.redo), ("Find", self.find_text)):
            ttk.Button(bar, text=label, command=fn).pack(side=tk.LEFT, padx=2)
        ttk.Separator(bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        ttk.Label(bar, text="Font").pack(side=tk.LEFT)
        families = sorted(set(font.families(self.root)))
        cb = ttk.Combobox(bar, textvariable=self.family, values=families,
                          width=18, state="readonly")
        cb.pack(side=tk.LEFT, padx=3)
        cb.bind("<<ComboboxSelected>>", lambda e: self.apply_font())
        ttk.Label(bar, text="Size").pack(side=tk.LEFT, padx=(7, 2))
        sp = ttk.Spinbox(bar, from_=7, to=36, width=4, textvariable=self.size,
                         command=self.apply_font)
        sp.pack(side=tk.LEFT)
        sp.bind("<Return>", lambda e: self.apply_font())
        sp.bind("<FocusOut>", lambda e: self.apply_font())
        ttk.Button(bar, text="A−", width=3, command=lambda: self.zoom(-1)).pack(side=tk.LEFT, padx=(6, 1))
        ttk.Button(bar, text="A+", width=3, command=lambda: self.zoom(1)).pack(side=tk.LEFT, padx=1)

    def _bind_keys(self):
        keys = {
            "<Control-n>": self.new_tab, "<Control-o>": self.open_file,
            "<Control-s>": self.save_file, "<Control-Shift-S>": self.save_as,
            "<Control-w>": self.close_tab, "<Control-f>": self.find_text,
            "<Control-a>": self.select_all, "<Control-z>": self.undo,
            "<Control-y>": self.redo, "<Control-plus>": lambda: self.zoom(1),
            "<Control-equal>": lambda: self.zoom(1), "<Control-minus>": lambda: self.zoom(-1),
        }
        for seq, fn in keys.items():
            self.root.bind(seq, lambda e, f=fn: (f(), "break")[1])

    def current(self):
        return self.docs.get(self.nb.select())

    def new_tab(self, content="", path=None):
        frame = ttk.Frame(self.nb)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        txt = tk.Text(frame, wrap=tk.WORD if self.wrap.get() else tk.NONE,
                      undo=True, autoseparators=True, maxundo=-1,
                      font=(self.family.get(), self.size.get()),
                      padx=9, pady=9, borderwidth=0, highlightthickness=0)
        ys = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=txt.yview)
        xs = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=txt.xview)
        txt.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        txt.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        doc = Document(frame, txt, path)
        self.docs[str(frame)] = doc
        self.nb.add(frame, text=self.tab_title(doc))
        self.nb.select(frame)
        txt.bind("<<Modified>>", lambda e, d=doc: self.on_modified(d))
        txt.bind("<KeyRelease>", lambda e: self.status_update())
        txt.bind("<ButtonRelease-1>", lambda e: self.status_update())
        self.context_menu(txt)
        if content:
            txt.insert("1.0", content)
        txt.edit_modified(False)
        doc.modified = False
        self.apply_options_to(txt)
        self.apply_theme_to(txt)
        txt.focus_set()
        self.status_update()
        return doc

    def context_menu(self, txt):
        menu = tk.Menu(txt, tearoff=False)
        menu.add_command(label="Cut", command=lambda: txt.event_generate("<<Cut>>"))
        menu.add_command(label="Copy", command=lambda: txt.event_generate("<<Copy>>"))
        menu.add_command(label="Paste", command=lambda: txt.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: txt.tag_add(tk.SEL, "1.0", "end-1c"))
        def popup(event):
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
        txt.bind("<Button-3>", popup)
        txt.bind("<Button-2>", popup)

    def tab_title(self, doc):
        return ("*" if doc.modified else "") + (doc.path.name if doc.path else "Untitled")

    def refresh_title(self, doc):
        try:
            self.nb.tab(doc.frame, text=self.tab_title(doc))
        except tk.TclError:
            pass
        cur = self.current()
        name = cur.path.name if cur and cur.path else "Untitled"
        self.root.title(("*" if cur and cur.modified else "") + name + " - LiteNote")

    def on_modified(self, doc):
        if doc.text.edit_modified():
            doc.modified = True
            self.refresh_title(doc)
            doc.text.edit_modified(False)

    def text_event(self, event):
        d = self.current()
        if d:
            d.text.event_generate(event)
            d.text.focus_set()

    def select_all(self):
        d = self.current()
        if d:
            d.text.tag_add(tk.SEL, "1.0", "end-1c")
            d.text.mark_set(tk.INSERT, "1.0")
            d.text.focus_set()

    def confirm_doc(self, doc):
        if not doc.modified:
            return True
        answer = messagebox.askyesnocancel(
            "Unsaved changes",
            f"Save changes to {doc.path.name if doc.path else 'Untitled'}?"
        )
        if answer is None:
            return False
        return self.save_file(doc) if answer else True

    def open_file(self):
        name = filedialog.askopenfilename(
            title="Open text file",
            filetypes=[("Text files", "*.txt *.log *.md *.csv *.py *.json *.xml *.html *.css"),
                       ("All files", "*.*")]
        )
        if not name:
            return
        path = Path(name)
        for d in self.docs.values():
            if d.path and d.path.resolve() == path.resolve():
                self.nb.select(d.frame)
                return
        try:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            messagebox.showerror("Open failed", str(exc))
            return
        self.new_tab(content, path)

    def save_file(self, doc=None):
        d = doc or self.current()
        if not d:
            return False
        if d.path is None:
            return self.save_as(d)
        try:
            d.path.write_text(d.text.get("1.0", "end-1c"), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save failed", str(exc))
            return False
        d.modified = False
        d.text.edit_modified(False)
        self.refresh_title(d)
        self.status_update("Saved")
        return True

    def save_as(self, doc=None):
        d = doc or self.current()
        if not d:
            return False
        name = filedialog.asksaveasfilename(
            title="Save text file", defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not name:
            return False
        d.path = Path(name)
        return self.save_file(d)

    def close_tab(self):
        d = self.current()
        if not d or not self.confirm_doc(d):
            return
        self.nb.forget(d.frame)
        self.docs.pop(str(d.frame), None)
        if not self.docs:
            self.new_tab()
        self.status_update()

    def undo(self):
        d = self.current()
        if d:
            try:
                d.text.edit_undo()
            except tk.TclError:
                pass
            self.status_update()

    def redo(self):
        d = self.current()
        if d:
            try:
                d.text.edit_redo()
            except tk.TclError:
                pass
            self.status_update()

    def find_text(self):
        d = self.current()
        if not d:
            return
        win = tk.Toplevel(self.root)
        win.title("Find")
        win.transient(self.root)
        win.resizable(False, False)
        ttk.Label(win, text="Find what:").grid(row=0, column=0, padx=9, pady=9)
        entry = ttk.Entry(win, width=32)
        entry.grid(row=0, column=1, padx=9, pady=9)
        entry.focus_set()
        def next_match():
            term = entry.get()
            if not term:
                return
            start = d.text.index(tk.INSERT)
            pos = d.text.search(term, start, stopindex=tk.END, nocase=True)
            if not pos:
                pos = d.text.search(term, "1.0", stopindex=start, nocase=True)
            d.text.tag_remove("match", "1.0", tk.END)
            if pos:
                end = f"{pos}+{len(term)}c"
                d.text.tag_add("match", pos, end)
                d.text.tag_config("match", background="#e6c84f", foreground="#111111")
                d.text.mark_set(tk.INSERT, end)
                d.text.see(pos)
                d.text.focus_set()
            else:
                messagebox.showinfo("Find", "No match found.", parent=win)
        ttk.Button(win, text="Find Next", command=next_match).grid(row=1, column=1, sticky=tk.E, padx=9, pady=(0, 9))
        entry.bind("<Return>", lambda e: next_match())

    def apply_font(self):
        try:
            size = max(7, min(36, int(self.size.get())))
        except (ValueError, tk.TclError):
            size = 12
        self.size.set(size)
        for d in self.docs.values():
            d.text.configure(font=(self.family.get(), size))

    def zoom(self, delta):
        self.size.set(max(7, min(36, self.size.get() + delta)))
        self.apply_font()

    def apply_options_to(self, txt):
        txt.configure(wrap=tk.WORD if self.wrap.get() else tk.NONE)
        # Tk Text supports right paragraph alignment; full Arabic/Persian
        # bidirectional shaping depends on the installed Tk implementation.
        txt.tag_configure("paragraph", justify=tk.RIGHT if self.rtl.get() else tk.LEFT)
        txt.tag_add("paragraph", "1.0", "end")

    def apply_options(self):
        for d in self.docs.values():
            self.apply_options_to(d.text)

    def apply_theme_to(self, txt):
        if self.dark.get():
            txt.configure(background="#1e1e1e", foreground="#eeeeee",
                          insertbackground="#ffffff", selectbackground="#44546a",
                          selectforeground="#ffffff")
        else:
            txt.configure(background="#ffffff", foreground="#202020",
                          insertbackground="#202020", selectbackground="#c8ddf5",
                          selectforeground="#111111")

    def apply_theme(self):
        for d in self.docs.values():
            self.apply_theme_to(d.text)

    def autosave_tick(self):
        if self.autosave.get():
            count = 0
            for d in list(self.docs.values()):
                # Untitled documents are not silently written to an unknown path.
                if d.modified and d.path:
                    try:
                        d.path.write_text(d.text.get("1.0", "end-1c"), encoding="utf-8")
                        d.modified = False
                        d.text.edit_modified(False)
                        self.refresh_title(d)
                        count += 1
                    except OSError:
                        pass
            if count:
                self.status_update(f"Auto-saved {count} document(s)")
        self.root.after(self.AUTOSAVE_MS, self.autosave_tick)

    def status_update(self, message=None):
        d = self.current()
        if not d:
            self.status.configure(text="Ready")
            return
        line, col = d.text.index(tk.INSERT).split(".")
        content = d.text.get("1.0", "end-1c")
        suffix = "  |  Modified" if d.modified else ""
        self.status.configure(text=message or
            f"Ln {line}, Col {int(col)+1}  |  {len(content.split())} words  |  {len(content)} characters{suffix}")

    def about(self):
        messagebox.showinfo("About LiteNote", "LiteNote 2.0\nLightweight tabbed text editor for Ubuntu/Linux.\nPython 3 + Tkinter")

    def exit_app(self):
        for d in list(self.docs.values()):
            if not self.confirm_doc(d):
                return
        self.root.destroy()


def main():
    root = tk.Tk()
    LiteNote(root)
    root.mainloop()


if __name__ == "__main__":
    main()
