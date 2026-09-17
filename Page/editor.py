from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"
PUBLIC_DIR = REPO_ROOT / "public"
CONFIG_PATH = CONTENT_DIR / "config.toml"
ABOUT_PATH = CONTENT_DIR / "about.toml"
ENTRIES_PATH = CONTENT_DIR / "homepage_entries.toml"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
COLLECTIONS = ("miscellanea", "research_notes")


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def string_array(values: list[str]) -> str:
    if not values:
        return "[]"
    body = "\n".join(f"  {quote(value)}" + ("," if index < len(values) - 1 else "") for index, value in enumerate(values))
    return f"[\n{body}\n]"


def render_config(name: str, email: str, avatar: str) -> str:
    return f'''[site]
title = {quote(name)}
description = {quote(f"Personal website of {name}.")}
favicon = "/favicon.svg"

[author]
name = {quote(name)}
title = ""
institution = ""
avatar = {quote(avatar)}

[social]
email = {quote(email)}

[features]
enable_likes = false
enable_one_page_mode = false

[i18n]
enabled = false
locales = ["en"]
default_locale = "en"
mode = "fixed"
fixed_locale = "en"
persist = false
switcher = false

[[navigation]]
title = "About"
type = "page"
target = "about"
href = "/"
'''


def render_about(interests: list[str]) -> str:
    return f'''type = "about"
title = "About"

[profile]
research_interests = {string_array(interests)}

[[sections]]
id = "miscellanea"
type = "entries"
title = "Miscellanea"
source = "homepage_entries.toml"
collection = "miscellanea"

[[sections]]
id = "research_notes"
type = "entries"
title = "Research Notes"
source = "homepage_entries.toml"
collection = "research_notes"
'''


def render_entries(collection_data: dict[str, dict[str, Any]]) -> str:
    blocks: list[str] = []
    for collection in COLLECTIONS:
        data = collection_data[collection]
        lines = [f"[{collection}]", f"intro = {quote(str(data.get('intro', '')))}"]
        for entry in data.get("entries", []):
            lines.extend([
                "",
                f"[[{collection}.entries]]",
                f"title = {quote(str(entry.get('title', '')))}",
                f"date = {quote(str(entry.get('date', '')))}",
                f"url = {quote(str(entry.get('url', '')))}",
                f"description = {quote(str(entry.get('description', '')))}",
            ])
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def site_owned_avatars() -> list[Path]:
    return [
        path for path in PUBLIC_DIR.glob("avatar.*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ]


def validate() -> None:
    config = load_toml(CONFIG_PATH)
    about = load_toml(ABOUT_PATH)
    entries = load_toml(ENTRIES_PATH)

    for section, fields in {
        "site": ("title", "description", "favicon"),
        "author": ("name", "title", "institution", "avatar"),
        "social": ("email",),
        "features": ("enable_likes", "enable_one_page_mode"),
        "i18n": ("enabled", "locales", "default_locale", "mode", "fixed_locale", "persist", "switcher"),
    }.items():
        value = config.get(section)
        if not isinstance(value, dict) or any(field not in value for field in fields):
            raise ValueError(f"content/config.toml is missing [{section}] fields")

    navigation = config.get("navigation")
    if not isinstance(navigation, list) or len(navigation) != 1 or navigation[0].get("target") != "about":
        raise ValueError("content/config.toml must contain only About navigation")

    profile = about.get("profile")
    sections = about.get("sections")
    if not isinstance(profile, dict) or not isinstance(profile.get("research_interests"), list):
        raise ValueError("content/about.toml is missing profile research interests")
    if not isinstance(sections, list) or [item.get("collection") for item in sections] != list(COLLECTIONS):
        raise ValueError("content/about.toml has invalid entries sections")

    if set(entries) != set(COLLECTIONS):
        raise ValueError("content/homepage_entries.toml must contain exactly two collections")
    for collection in COLLECTIONS:
        value = entries.get(collection)
        if not isinstance(value, dict) or not isinstance(value.get("intro"), str) or not isinstance(value.get("entries"), list):
            raise ValueError(f"invalid {collection} collection")
        for entry in value["entries"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("title"), str):
                raise ValueError(f"invalid entry in {collection}")
            if any(field in entry and not isinstance(entry[field], str) for field in ("date", "url", "description")):
                raise ValueError(f"invalid entry fields in {collection}")

    avatar = config["author"]["avatar"]
    if not isinstance(avatar, str):
        raise ValueError("author.avatar must be a string")
    if avatar:
        avatar_path = (PUBLIC_DIR / avatar.lstrip("/")).resolve()
        if PUBLIC_DIR.resolve() not in avatar_path.parents or not avatar_path.is_file():
            raise ValueError(f"configured avatar does not exist: {avatar}")


def run_gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    config = load_toml(CONFIG_PATH)
    about = load_toml(ABOUT_PATH)
    entries_data = load_toml(ENTRIES_PATH)

    root = tk.Tk()
    root.title("PRISM Homepage Editor")
    root.geometry("850x720")

    name_var = tk.StringVar(value=config["author"].get("name", ""))
    email_var = tk.StringVar(value=config["social"].get("email", ""))
    current_avatar = str(config["author"].get("avatar", ""))
    avatar_var = tk.StringVar(value=current_avatar or "No avatar selected")
    avatar_selection: dict[str, Any] = {"source": None, "cleared": not bool(current_avatar)}

    profile_frame = ttk.LabelFrame(root, text="Profile", padding=10)
    profile_frame.pack(fill="x", padx=12, pady=(12, 6))
    ttk.Label(profile_frame, text="Name").grid(row=0, column=0, sticky="w")
    ttk.Entry(profile_frame, textvariable=name_var).grid(row=0, column=1, sticky="ew", padx=8)
    ttk.Label(profile_frame, text="Email").grid(row=1, column=0, sticky="w", pady=(6, 0))
    ttk.Entry(profile_frame, textvariable=email_var).grid(row=1, column=1, sticky="ew", padx=8, pady=(6, 0))
    ttk.Label(profile_frame, text="Research interests (one per line)").grid(row=2, column=0, sticky="nw", pady=(6, 0))
    interests_text = tk.Text(profile_frame, height=4, width=50)
    interests_text.grid(row=2, column=1, sticky="ew", padx=8, pady=(6, 0))
    interests_text.insert("1.0", "\n".join(about["profile"].get("research_interests", [])))
    profile_frame.columnconfigure(1, weight=1)

    avatar_frame = ttk.Frame(profile_frame)
    avatar_frame.grid(row=3, column=1, sticky="ew", padx=8, pady=(8, 0))
    ttk.Label(avatar_frame, textvariable=avatar_var).pack(side="left", fill="x", expand=True)

    def select_image() -> None:
        filename = filedialog.askopenfilename(
            title="Select avatar image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")],
        )
        if filename:
            source = Path(filename)
            if source.suffix.lower() not in IMAGE_SUFFIXES:
                messagebox.showerror("Invalid image", "Choose a JPG, JPEG, PNG, or WebP image.")
                return
            avatar_selection.update(source=source, cleared=False)
            avatar_var.set(str(source))

    def clear_image() -> None:
        avatar_selection.update(source=None, cleared=True)
        avatar_var.set("No avatar selected")

    ttk.Button(avatar_frame, text="Select Image", command=select_image).pack(side="left", padx=(8, 4))
    ttk.Button(avatar_frame, text="Clear Image", command=clear_image).pack(side="left")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=12, pady=6)
    editors: dict[str, Any] = {}

    class CollectionEditor:
        def __init__(self, parent: Any, data: dict[str, Any]) -> None:
            self.entries = [dict(item) for item in data.get("entries", [])]
            self.frame = ttk.Frame(parent, padding=10)
            self.intro_var = tk.StringVar(value=data.get("intro", ""))
            self.title_var = tk.StringVar()
            self.date_var = tk.StringVar()
            self.url_var = tk.StringVar()

            ttk.Label(self.frame, text="Intro").grid(row=0, column=0, sticky="w")
            ttk.Entry(self.frame, textvariable=self.intro_var).grid(row=0, column=1, columnspan=3, sticky="ew", pady=(0, 8))
            self.listbox = tk.Listbox(self.frame, height=7, exportselection=False)
            self.listbox.grid(row=1, column=0, columnspan=4, sticky="nsew")
            self.listbox.bind("<<ListboxSelect>>", self.load_selected)
            ttk.Label(self.frame, text="Title").grid(row=2, column=0, sticky="w", pady=(8, 0))
            ttk.Entry(self.frame, textvariable=self.title_var).grid(row=2, column=1, columnspan=3, sticky="ew", pady=(8, 0))
            ttk.Label(self.frame, text="Date").grid(row=3, column=0, sticky="w", pady=(6, 0))
            ttk.Entry(self.frame, textvariable=self.date_var).grid(row=3, column=1, columnspan=3, sticky="ew", pady=(6, 0))
            ttk.Label(self.frame, text="URL").grid(row=4, column=0, sticky="w", pady=(6, 0))
            ttk.Entry(self.frame, textvariable=self.url_var).grid(row=4, column=1, columnspan=3, sticky="ew", pady=(6, 0))
            ttk.Label(self.frame, text="Description").grid(row=5, column=0, sticky="nw", pady=(6, 0))
            self.description = tk.Text(self.frame, height=7)
            self.description.grid(row=5, column=1, columnspan=3, sticky="nsew", pady=(6, 0))
            ttk.Button(self.frame, text="Add", command=self.add).grid(row=6, column=1, sticky="e", pady=8)
            ttk.Button(self.frame, text="Update", command=self.update).grid(row=6, column=2, padx=6, pady=8)
            ttk.Button(self.frame, text="Delete", command=self.delete).grid(row=6, column=3, sticky="w", pady=8)
            self.frame.columnconfigure(1, weight=1)
            self.frame.rowconfigure(1, weight=1)
            self.frame.rowconfigure(5, weight=1)
            self.refresh()

        def refresh(self) -> None:
            self.listbox.delete(0, tk.END)
            for item in self.entries:
                self.listbox.insert(tk.END, item.get("title", ""))

        def selected_index(self) -> int | None:
            selected = self.listbox.curselection()
            return int(selected[0]) if selected else None

        def load_selected(self, _event: Any = None) -> None:
            index = self.selected_index()
            if index is None:
                return
            item = self.entries[index]
            self.title_var.set(item.get("title", ""))
            self.date_var.set(item.get("date", ""))
            self.url_var.set(item.get("url", ""))
            self.description.delete("1.0", tk.END)
            self.description.insert("1.0", item.get("description", ""))

        def form_data(self) -> dict[str, str] | None:
            title = self.title_var.get().strip()
            if not title:
                messagebox.showerror("Missing title", "Entry title is required.")
                return None
            return {
                "title": title,
                "date": self.date_var.get().strip(),
                "url": self.url_var.get().strip(),
                "description": self.description.get("1.0", "end-1c"),
            }

        def add(self) -> None:
            item = self.form_data()
            if item is not None:
                self.entries.append(item)
                self.refresh()

        def update(self) -> None:
            index = self.selected_index()
            if index is None:
                messagebox.showerror("No selection", "Select an entry to update.")
                return
            item = self.form_data()
            if item is not None:
                self.entries[index] = item
                self.refresh()
                self.listbox.selection_set(index)

        def delete(self) -> None:
            index = self.selected_index()
            if index is None:
                messagebox.showerror("No selection", "Select an entry to delete.")
                return
            del self.entries[index]
            self.refresh()

    for key, label in (("miscellanea", "Miscellanea"), ("research_notes", "Research Notes")):
        editor = CollectionEditor(notebook, entries_data[key])
        editors[key] = editor
        notebook.add(editor.frame, text=label)

    def save() -> None:
        try:
            name = name_var.get().strip()
            email = email_var.get().strip()
            if not name or not email:
                raise ValueError("Name and email are required.")
            interests = [line.strip() for line in interests_text.get("1.0", "end-1c").splitlines() if line.strip()]

            source = avatar_selection["source"]
            if source is not None:
                suffix = source.suffix.lower()
                target = PUBLIC_DIR / f"avatar{suffix}"
                PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
                if source.resolve() != target.resolve():
                    shutil.copy2(source, target)
                for old_avatar in site_owned_avatars():
                    if old_avatar.resolve() != target.resolve():
                        old_avatar.unlink()
                avatar = f"/{target.name}"
            elif avatar_selection["cleared"]:
                for old_avatar in site_owned_avatars():
                    old_avatar.unlink()
                avatar = ""
            else:
                avatar = current_avatar

            updated_entries = {
                key: {"intro": editors[key].intro_var.get(), "entries": editors[key].entries}
                for key in COLLECTIONS
            }
            atomic_write(CONFIG_PATH, render_config(name, email, avatar))
            atomic_write(ABOUT_PATH, render_about(interests))
            atomic_write(ENTRIES_PATH, render_entries(updated_entries))
            validate()
            messagebox.showinfo("Saved", "Homepage content saved successfully.")
        except Exception as error:
            messagebox.showerror("Save failed", str(error))

    ttk.Button(root, text="Save", command=save).pack(pady=(6, 12))
    root.mainloop()


def main() -> int:
    parser = argparse.ArgumentParser(description="Local PRISM homepage editor")
    parser.add_argument("--check", action="store_true", help="validate editor-managed content without launching the GUI")
    args = parser.parse_args()
    if args.check:
        try:
            validate()
        except Exception as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print("OK")
        return 0
    try:
        run_gui()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
