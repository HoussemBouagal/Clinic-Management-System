# main.py

from __future__ import annotations
import csv
import os
import shutil
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Iterable, Optional

from charts import BarChart, DonutChart
from db import connect_db, init_db, log_action
from i18n import I18N, TRANSLATIONS


# ═══════════════════════════════════════════════════════════════════
#  1. Constants & configuration
# ═══════════════════════════════════════════════════════════════════

APP_TITLE_KEY = "app"
LOGIN_USERNAME = "admin"
LOGIN_PASSWORD = "admin123"
DB_FILE = "clinic.db"
LOGO_FILE = "Logo.png"

CURRENCY: dict[str, str] = {"ar": "د.ج", "en": "DZD", "fr": "DA"}

COLORS: dict[str, str] = {
    "revenue": "#27ae60",
    "expenses": "#e67e22",
    "paid": "#27ae60",
    "partial": "#f39c12",
    "unpaid": "#e74c3c",
    "ok": "#3498db",
    "low": "#f39c12",
    "expired": "#e74c3c",
    "primary": "#1677e8",
    "primary_dark": "#0d63c7",
    "danger": "#e74c3c",
    "danger_dark": "#c0392b",
    "success": "#27ae60",
    "success_dark": "#1e8449",
    "bg": "#f3f7fb",
    "sidebar": "#0f2842",
    "sidebar_alt": "#1a3a5c",
    "card": "#ffffff",
    "text": "#18324b",
    "text_muted": "#657b91",
}

LANG_LABELS: dict[str, str] = {
    "ar": "العربية",
    "en": "English",
    "fr": "Français",
}

LANG_FLAGS: dict[str, str] = {
    "ar": "🇩🇿  العربية",
    "en": "🇬🇧  English",
    "fr": "🇫🇷  Français",
}

# ═══════════════════════════════════════════════════════════════════
#  Developer info
# ═══════════════════════════════════════════════════════════════════

DEV_NAME = "Houssem Eddine Bouagal"
DEV_VERSION = "1.0.0"
DEV_YEAR = "2026"
DEV_GITHUB = "https://github.com/HoussemBouagal"
DEV_EMAIL = "mouhamedhoussem813@gmail.com"
APP_NAME = "Clinic Manager"
APP_TAGLINE = "Clinic Management System"


# ═══════════════════════════════════════════════════════════════════
#  2. Logo / icon helpers
# ═══════════════════════════════════════════════════════════════════

_icon_ref: Optional[tk.PhotoImage] = None
_logo_cache: dict[tuple[int, Optional[str]], tk.PhotoImage] = {}
_ico_path: Optional[str] = None


def _base_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _find_logo() -> Optional[str]:
    candidates = (
        os.path.join(_base_dir(), LOGO_FILE),
        os.path.join(_base_dir(), "assets", LOGO_FILE),
        os.path.join(os.getcwd(), LOGO_FILE),
    )
    return next((p for p in candidates if os.path.exists(p)), None)


def _ensure_ico() -> Optional[str]:
    global _ico_path
    if _ico_path and os.path.exists(_ico_path):
        return _ico_path
    logo = _find_logo()
    if not logo:
        return None
    try:
        from PIL import Image  # type: ignore

        img = Image.open(logo).convert("RGBA")
        img.thumbnail((256, 256), Image.LANCZOS)
        out = os.path.join(_base_dir(), "_app_icon.ico")
        img.save(
            out,
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
        _ico_path = out
        return out
    except Exception as exc:  # pragma: no cover
        print(f"[icon] {exc}")
        return None


def load_icon(window: tk.Misc) -> None:
    """Attach the app icon to a Tk/Toplevel window."""
    global _icon_ref
    logo = _find_logo()
    if not logo:
        return
    try:
        from PIL import Image, ImageTk  # type: ignore

        img = Image.open(logo).convert("RGBA")
        img.thumbnail((64, 64), Image.LANCZOS)
        _icon_ref = ImageTk.PhotoImage(img)
        window.iconphoto(True, _icon_ref)  # type: ignore[arg-type]
    except ImportError:
        pass
    except Exception as exc:  # pragma: no cover
        print(f"[icon] {exc}")

    if os.name == "nt":
        ico = _ensure_ico()
        if ico:
            try:
                window.iconbitmap(ico)  # type: ignore[arg-type]
            except Exception:
                pass


def get_logo_photo(size: int = 64, bg: Optional[str] = None) -> Optional[tk.PhotoImage]:
    """Return a cached PhotoImage of the logo (optionally flattened on a bg color)."""
    key = (size, bg)
    if key in _logo_cache:
        return _logo_cache[key]
    logo = _find_logo()
    if not logo:
        return None
    try:
        from PIL import Image, ImageTk  # type: ignore

        img = Image.open(logo).convert("RGBA")
        img.thumbnail((size, size), Image.LANCZOS)
        if bg:
            canvas = Image.new("RGB", img.size, bg)
            canvas.paste(img, (0, 0), img)
            photo = ImageTk.PhotoImage(canvas)
        else:
            photo = ImageTk.PhotoImage(img)
        _logo_cache[key] = photo
        return photo
    except ImportError:
        return None
    except Exception as exc:  # pragma: no cover
        print(f"[logo] {exc}")
        return None


def _reset_image_cache() -> None:
    """Clear cached PhotoImages when a new Tk root is created."""
    global _icon_ref
    _icon_ref = None
    _logo_cache.clear()


def patch_toplevel_icon() -> None:
    """Ensure every Toplevel gets the app icon automatically."""
    if getattr(tk.Toplevel, "_icon_patched", False):
        return
    original_init = tk.Toplevel.__init__

    def patched(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        original_init(self, *args, **kwargs)
        try:
            load_icon(self)
        except Exception:
            pass

    tk.Toplevel.__init__ = patched  # type: ignore[assignment]
    tk.Toplevel._icon_patched = True  # type: ignore[attr-defined]


# ═══════════════════════════════════════════════════════════════════
#  3. Reusable widgets
# ═══════════════════════════════════════════════════════════════════

class ScrollableFrame(ttk.Frame):
    """A vertical scrollable frame with safe mouse-wheel binding."""

    def __init__(self, parent: tk.Misc, bg: str = COLORS["bg"], **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self._bg = bg

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = ttk.Frame(self.canvas)
        self._window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)
        self.canvas.bind("<Button-4>", self._on_wheel)
        self.canvas.bind("<Button-5>", self._on_wheel)

    # -- internal handlers ------------------------------------------------
    def _on_inner_configure(self, _e: tk.Event | None = None) -> None:
        try:
            if self.canvas.winfo_exists():
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except tk.TclError:
            pass

    def _on_canvas_configure(self, event: tk.Event) -> None:
        try:
            if self.canvas.winfo_exists():
                self.canvas.itemconfigure(self._window_id, width=event.width)
        except tk.TclError:
            pass

    def _bind_wheel(self, _e: tk.Event | None = None) -> None:
        try:
            self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        except tk.TclError:
            pass

    def _unbind_wheel(self, _e: tk.Event | None = None) -> None:
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass

    def _on_wheel(self, event: tk.Event) -> None:
        try:
            if not self.canvas.winfo_exists():
                return
            delta = getattr(event, "delta", 0)
            if delta:
                step = int(-delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
                self.canvas.yview_scroll(step, "units")
            elif getattr(event, "num", None) == 4:
                self.canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                self.canvas.yview_scroll(1, "units")
        except tk.TclError:
            pass


def make_stat_card(
    parent: tk.Misc,
    title: str,
    value: Any,
    color: str = COLORS["primary"],
    subtitle: str = "",
) -> ttk.Frame:
    """Create a stat card widget (not packed)."""
    card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
    tk.Label(
        card,
        text=str(value),
        bg=COLORS["card"],
        fg=color,
        font=("Segoe UI", 22, "bold"),
    ).pack(anchor="w", pady=6)
    if subtitle:
        ttk.Label(card, text=subtitle, style="CardTitle.TLabel").pack(anchor="w")
    return card


def make_dev_button(
    parent: tk.Misc,
    on_click: Callable[[], None],
) -> tk.Frame:
    """
    Create a professional developer-credit card for the login screen.

    Design: bordered card with a circular `</>` badge, developer name,
    version/year line, and a chevron indicator. Hover turns it blue.
    """
    inner_bg = "#ffffff"
    accent = COLORS["primary"]
    hover_bg = COLORS["primary"]
    text_color = COLORS["sidebar"]
    sub_color = COLORS["text_muted"]
    border_color = "#d8e5f2"

    container = tk.Frame(parent, bg=border_color, bd=0, highlightthickness=0)

    inner = tk.Frame(container, bg=inner_bg, cursor="hand2")
    inner.pack(fill="both", expand=True, padx=1, pady=1)

    badge_canvas = tk.Canvas(
        inner,
        width=34,
        height=34,
        bg=inner_bg,
        highlightthickness=0,
    )
    badge_canvas.pack(side="left", padx=(10, 8), pady=10)
    badge_canvas.create_oval(1, 1, 33, 33, fill=accent, outline="")
    badge_canvas.create_text(
        17, 17, text="</>", fill="#ffffff",
        font=("Consolas", 9, "bold"),
    )

    text_frame = tk.Frame(inner, bg=inner_bg, cursor="hand2")
    text_frame.pack(side="left", fill="both", expand=True, pady=10)

    title = tk.Label(
        text_frame,
        text=DEV_NAME,
        bg=inner_bg,
        fg=text_color,
        font=("Segoe UI", 9, "bold"),
        anchor="w",
        cursor="hand2",
    )
    title.pack(anchor="w")

    subtitle = tk.Label(
        text_frame,
        text=f"About  ·  v{DEV_VERSION}  ·  {DEV_YEAR}",
        bg=inner_bg,
        fg=sub_color,
        font=("Segoe UI", 8),
        anchor="w",
        cursor="hand2",
    )
    subtitle.pack(anchor="w")

    arrow = tk.Label(
        inner,
        text="›",
        bg=inner_bg,
        fg=accent,
        font=("Segoe UI", 18, "bold"),
        cursor="hand2",
    )
    arrow.pack(side="right", padx=(4, 10))

    def _set_bg(color: str) -> None:
        for w in (inner, badge_canvas, text_frame, title, subtitle, arrow):
            try:
                w.configure(bg=color)
            except tk.TclError:
                pass

    def _enter(_e: tk.Event) -> None:
        _set_bg(hover_bg)
        title.configure(fg="#ffffff")
        subtitle.configure(fg="#e8f2fb")
        arrow.configure(fg="#ffffff")

    def _leave(_e: tk.Event) -> None:
        _set_bg(inner_bg)
        title.configure(fg=text_color)
        subtitle.configure(fg=sub_color)
        arrow.configure(fg=accent)

    def _click(_e: tk.Event) -> None:
        on_click()

    for w in (inner, badge_canvas, text_frame, title, subtitle, arrow):
        w.bind("<Enter>", _enter)
        w.bind("<Leave>", _leave)
        w.bind("<Button-1>", _click)

    return container


# ═══════════════════════════════════════════════════════════════════
#  4. Dialogs
# ═══════════════════════════════════════════════════════════════════

class BaseDialog(tk.Toplevel):
    """Common boilerplate for modal dialogs."""

    def __init__(self, parent: tk.Misc, i18n: I18N, title: str, resizable: bool = False) -> None:
        super().__init__(parent)
        self.parent = parent
        self.i18n = i18n
        self.t = i18n.t
        self.result: Any = None
        self.title(title)
        self.configure(bg=COLORS["bg"])
        self.resizable(resizable, resizable)
        self.transient(parent)  # type: ignore[arg-type]
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)


class PatientDialog(BaseDialog):
    FIELDS = (
        ("name", "full_name"),
        ("phone", "phone"),
        ("birth", "birth_date"),
        ("address", "address"),
        ("blood_type", "blood_type"),
        ("allergies", "allergies"),
        ("chronic_diseases", "chronic_diseases"),
    )
    BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", ""]

    def __init__(self, parent: tk.Misc, i18n: I18N, patient: Any = None) -> None:
        title = i18n.t("edit_patient") if patient else i18n.t("add_patient")
        super().__init__(parent, i18n, title)
        self.patient = patient
        self.vars: dict[str, tk.StringVar] = {}

        form = ttk.Frame(self, padding=18)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        for row, (lk, field) in enumerate(self.FIELDS):
            ttk.Label(form, text=self.t(lk)).grid(row=row, column=0, sticky="e", padx=8, pady=6)
            value = (patient[field] if patient and patient[field] else "") if patient else ""
            var = tk.StringVar(value=value)
            self.vars[field] = var
            if field == "blood_type":
                ttk.Combobox(form, textvariable=var, width=32, values=self.BLOOD_TYPES).grid(
                    row=row, column=1, sticky="ew", padx=8, pady=6
                )
            else:
                ttk.Entry(form, textvariable=var, width=34).grid(
                    row=row, column=1, sticky="ew", padx=8, pady=6
                )

        r = len(self.FIELDS)
        ttk.Label(form, text=self.t("notes")).grid(row=r, column=0, sticky="ne", padx=8, pady=6)
        self.notes = tk.Text(form, width=32, height=4, wrap="word")
        self.notes.grid(row=r, column=1, padx=8, pady=6, sticky="ew")
        if patient and patient["notes"]:
            self.notes.insert("1.0", patient["notes"])

        r += 1
        btns = ttk.Frame(form)
        btns.grid(row=r, column=0, columnspan=2, sticky="e", pady=12)
        ttk.Button(btns, text=self.t("cancel"), command=self.destroy).pack(side="left", padx=4)
        ttk.Button(btns, text=self.t("save"), style="Primary.TButton", command=self.save).pack(
            side="left", padx=4
        )
        self.bind("<Return>", lambda _e: self.save())
        self.focus_set()

    def save(self) -> None:
        values = {k: v.get().strip() for k, v in self.vars.items()}
        values["notes"] = self.notes.get("1.0", "end").strip()
        if not values["full_name"]:
            messagebox.showwarning(self.t("patients"), self.t("required_name"), parent=self)
            return
        self.result = values
        self.destroy()


class AppointmentDialog(BaseDialog):
    def __init__(self, parent: tk.Misc, i18n: I18N) -> None:
        super().__init__(parent, i18n, i18n.t("add_appointment"))
        self.vars: dict[str, tk.StringVar] = {}

        form = ttk.Frame(self, padding=18)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        with connect_db() as conn:
            self.patients = conn.execute(
                "SELECT id, full_name, phone FROM patients ORDER BY full_name"
            ).fetchall()

        ttk.Label(form, text=self.t("patient")).grid(row=0, column=0, sticky="e", padx=8, pady=7)
        self.patient_map: dict[str, int] = {}
        labels = []
        for p in self.patients:
            label = f'{p["full_name"]} — {p["phone"] or ""}'
            labels.append(label)
            self.patient_map[label] = p["id"]
        self.patient_var = tk.StringVar()
        ttk.Combobox(
            form, textvariable=self.patient_var, state="readonly", width=32, values=labels
        ).grid(row=0, column=1, padx=8, pady=7, sticky="ew")

        today = date.today().isoformat()
        defaults = {"date": today, "time": "09:00", "reason": ""}
        for r, (key, default) in enumerate(defaults.items(), start=1):
            ttk.Label(form, text=self.t(key)).grid(row=r, column=0, sticky="e", padx=8, pady=7)
            var = tk.StringVar(value=default)
            self.vars[key] = var
            ttk.Entry(form, textvariable=var, width=35).grid(
                row=r, column=1, padx=8, pady=7, sticky="ew"
            )

        ttk.Label(form, text=self.t("status")).grid(row=4, column=0, sticky="e", padx=8, pady=7)
        self.status_map = {
            self.t("scheduled"): "Scheduled",
            self.t("completed"): "Completed",
            self.t("cancelled"): "Cancelled",
        }
        self.status_var = tk.StringVar(value=self.t("scheduled"))
        ttk.Combobox(
            form,
            textvariable=self.status_var,
            state="readonly",
            values=list(self.status_map.keys()),
            width=32,
        ).grid(row=4, column=1, padx=8, pady=7, sticky="ew")

        btns = ttk.Frame(form)
        btns.grid(row=5, column=0, columnspan=2, sticky="e", pady=12)
        ttk.Button(btns, text=self.t("cancel"), command=self.destroy).pack(side="left", padx=4)
        ttk.Button(btns, text=self.t("save"), style="Primary.TButton", command=self.save).pack(
            side="left", padx=4
        )

    def save(self) -> None:
        sel = self.patient_var.get()
        if not sel:
            messagebox.showwarning(self.t("appointments"), self.t("no_patients"), parent=self)
            return
        values = {k: v.get().strip() for k, v in self.vars.items()}
        try:
            datetime.strptime(values["date"], "%Y-%m-%d")
            datetime.strptime(values["time"], "%H:%M")
        except ValueError:
            messagebox.showwarning(
                self.t("appointments"), "Invalid date/time format.", parent=self
            )
            return
        self.result = {
            "patient_id": self.patient_map[sel],
            "status": self.status_map[self.status_var.get()],
            **values,
        }
        self.destroy()


class MedicalRecordDialog(BaseDialog):
    FIELDS = (
        ("visit_date", "visit_date", lambda: date.today().isoformat()),
        ("diagnosis", "diagnosis", lambda: ""),
        ("prescription", "prescription", lambda: ""),
        ("blood_pressure", "blood_pressure", lambda: ""),
        ("temperature", "temperature", lambda: ""),
        ("weight", "weight", lambda: ""),
        ("sugar_level", "sugar_level", lambda: ""),
        ("heart_rate", "heart_rate", lambda: ""),
    )

    def __init__(
        self,
        parent: tk.Misc,
        i18n: I18N,
        record: Any = None,
        patient_id: Optional[int] = None,
    ) -> None:
        title = i18n.t("edit_record") if record else i18n.t("add_record")
        super().__init__(parent, i18n, title)
        self.record = record
        self.vars: dict[str, tk.StringVar] = {}

        form = ttk.Frame(self, padding=16)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(2, weight=1)
        form.columnconfigure(3, weight=1)

        with connect_db() as conn:
            patients = conn.execute(
                "SELECT id, full_name FROM patients ORDER BY full_name"
            ).fetchall()
        self.patient_map = {f'{p["full_name"]} (#{p["id"]})': p["id"] for p in patients}
        self.patient_var = tk.StringVar()

        ttk.Label(form, text=self.t("patient")).grid(row=0, column=0, sticky="e", padx=6, pady=5)
        ttk.Combobox(
            form,
            textvariable=self.patient_var,
            state="readonly",
            values=list(self.patient_map.keys()),
            width=42,
        ).grid(row=0, column=1, columnspan=3, sticky="ew", padx=6, pady=5)

        if record:
            self._preselect_patient(record["patient_id"])
        elif patient_id:
            self._preselect_patient(patient_id)

        for r, (lk, field, default_fn) in enumerate(self.FIELDS, start=1):
            ttk.Label(form, text=self.t(lk)).grid(row=r, column=0, sticky="e", padx=6, pady=5)
            value = (record[field] if record and record[field] else default_fn())
            var = tk.StringVar(value=value)
            self.vars[field] = var
            ttk.Entry(form, textvariable=var, width=44).grid(
                row=r, column=1, columnspan=3, sticky="ew", padx=6, pady=5
            )

        r = len(self.FIELDS) + 1
        ttk.Label(form, text=self.t("notes")).grid(row=r, column=0, sticky="ne", padx=6, pady=5)
        self.notes = tk.Text(form, width=44, height=4, wrap="word")
        self.notes.grid(row=r, column=1, columnspan=3, sticky="ew", padx=6, pady=5)
        if record and record["notes"]:
            self.notes.insert("1.0", record["notes"])

        r += 1
        btns = ttk.Frame(form)
        btns.grid(row=r, column=0, columnspan=4, sticky="e", pady=10)
        ttk.Button(btns, text=self.t("cancel"), command=self.destroy).pack(side="left", padx=4)
        ttk.Button(btns, text=self.t("save"), style="Primary.TButton", command=self.save).pack(
            side="left", padx=4
        )

    def _preselect_patient(self, pid: int) -> None:
        with connect_db() as conn:
            p = conn.execute("SELECT full_name FROM patients WHERE id=?", (pid,)).fetchone()
        if p:
            self.patient_var.set(f'{p["full_name"]} (#{pid})')

    def save(self) -> None:
        label = self.patient_var.get()
        if not label:
            messagebox.showwarning(
                self.t("records"), self.t("select_patient_first"), parent=self
            )
            return
        values = {k: v.get().strip() for k, v in self.vars.items()}
        values["notes"] = self.notes.get("1.0", "end").strip()
        values["patient_id"] = self.patient_map[label]
        self.result = values
        self.destroy()


class InventoryDialog(BaseDialog):
    def __init__(self, parent: tk.Misc, i18n: I18N, item: Any = None) -> None:
        title = i18n.t("edit_item") if item else i18n.t("add_item")
        super().__init__(parent, i18n, title)
        self.item = item
        self.vars: dict[str, tk.StringVar] = {}

        form = ttk.Frame(self, padding=16)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        fields = [
            ("item_name", "name", ""),
            ("category", "category", self.t("category_med")),
            ("quantity", "quantity", "0"),
            ("min_quantity", "min_quantity", "5"),
            ("purchase_price", "purchase_price", "0"),
            ("sale_price", "sale_price", "0"),
            ("expiry_date", "expiry_date", ""),
            ("supplier", "supplier", ""),
            ("batch_number", "batch_number", ""),
        ]
        for r, (lk, field, default) in enumerate(fields):
            ttk.Label(form, text=self.t(lk)).grid(row=r, column=0, sticky="e", padx=6, pady=5)
            value = str(item[field]) if item and item[field] is not None else default
            var = tk.StringVar(value=value)
            self.vars[field] = var
            if field == "category":
                ttk.Combobox(
                    form,
                    textvariable=var,
                    state="readonly",
                    values=[
                        self.t("category_med"),
                        self.t("category_supplies"),
                        self.t("category_equipment"),
                    ],
                    width=32,
                ).grid(row=r, column=1, sticky="ew", padx=6, pady=5)
            else:
                ttk.Entry(form, textvariable=var, width=34).grid(
                    row=r, column=1, sticky="ew", padx=6, pady=5
                )

        r = len(fields)
        ttk.Label(form, text=self.t("notes")).grid(row=r, column=0, sticky="ne", padx=6, pady=5)
        self.notes = tk.Text(form, width=34, height=3, wrap="word")
        self.notes.grid(row=r, column=1, sticky="ew", padx=6, pady=5)
        if item and item["notes"]:
            self.notes.insert("1.0", item["notes"])

        r += 1
        btns = ttk.Frame(form)
        btns.grid(row=r, column=0, columnspan=2, sticky="e", pady=10)
        ttk.Button(btns, text=self.t("cancel"), command=self.destroy).pack(side="left", padx=4)
        ttk.Button(btns, text=self.t("save"), style="Primary.TButton", command=self.save).pack(
            side="left", padx=4
        )

    def save(self) -> None:
        v = {k: var.get().strip() for k, var in self.vars.items()}
        if not v["name"]:
            messagebox.showwarning(self.t("inventory"), self.t("required_name"), parent=self)
            return
        try:
            v["quantity"] = int(v["quantity"] or 0)
            v["min_quantity"] = int(v["min_quantity"] or 0)
            v["purchase_price"] = float(v["purchase_price"] or 0)
            v["sale_price"] = float(v["sale_price"] or 0)
        except ValueError:
            messagebox.showwarning(self.t("inventory"), "Invalid numeric values.", parent=self)
            return
        v["notes"] = self.notes.get("1.0", "end").strip()
        self.result = v
        self.destroy()


class ExpenseDialog(BaseDialog):
    def __init__(self, parent: tk.Misc, i18n: I18N, expense: Any = None) -> None:
        title = i18n.t("edit_expense") if expense else i18n.t("add_expense")
        super().__init__(parent, i18n, title)
        self.expense = expense
        self.cur = CURRENCY[i18n.lang]
        self.vars: dict[str, tk.StringVar] = {}

        form = ttk.Frame(self, padding=16)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text=self.t("expense_date")).grid(
            row=0, column=0, sticky="e", padx=6, pady=6
        )
        self.vars["expense_date"] = tk.StringVar(
            value=expense["expense_date"] if expense else date.today().isoformat()
        )
        ttk.Entry(form, textvariable=self.vars["expense_date"], width=32).grid(
            row=0, column=1, sticky="ew", padx=6, pady=6
        )

        ttk.Label(form, text=self.t("expense_category")).grid(
            row=1, column=0, sticky="e", padx=6, pady=6
        )
        self.cat_map = {
            self.t("cat_rent"): "Rent",
            self.t("cat_salary"): "Salary",
            self.t("cat_utilities"): "Utilities",
            self.t("cat_supplies"): "Supplies",
            self.t("cat_maintenance"): "Maintenance",
            self.t("cat_other"): "Other",
        }
        self.cat_rev = {v: k for k, v in self.cat_map.items()}
        default_cat = (
            self.cat_rev.get(expense["category"], self.t("cat_other"))
            if expense
            else self.t("cat_other")
        )
        self.cat_var = tk.StringVar(value=default_cat)
        ttk.Combobox(
            form,
            textvariable=self.cat_var,
            state="readonly",
            values=list(self.cat_map.keys()),
            width=30,
        ).grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        ttk.Label(form, text=self.t("description")).grid(
            row=2, column=0, sticky="e", padx=6, pady=6
        )
        self.vars["description"] = tk.StringVar(value=expense["description"] if expense else "")
        ttk.Entry(form, textvariable=self.vars["description"], width=32).grid(
            row=2, column=1, sticky="ew", padx=6, pady=6
        )

        ttk.Label(form, text=f'{self.t("amount")} ({self.cur})').grid(
            row=3, column=0, sticky="e", padx=6, pady=6
        )
        self.vars["amount"] = tk.StringVar(value=str(expense["amount"]) if expense else "0")
        ttk.Entry(form, textvariable=self.vars["amount"], width=32).grid(
            row=3, column=1, sticky="ew", padx=6, pady=6
        )

        ttk.Label(form, text=self.t("payment_method")).grid(
            row=4, column=0, sticky="e", padx=6, pady=6
        )
        self.pm_map = {
            self.t("cash"): "Cash",
            self.t("card"): "Card",
            self.t("transfer"): "Transfer",
        }
        self.pm_rev = {v: k for k, v in self.pm_map.items()}
        default_pm = (
            self.pm_rev.get(expense["payment_method"], self.t("cash")) if expense else self.t("cash")
        )
        self.pm_var = tk.StringVar(value=default_pm)
        ttk.Combobox(
            form,
            textvariable=self.pm_var,
            state="readonly",
            values=list(self.pm_map.keys()),
            width=30,
        ).grid(row=4, column=1, sticky="ew", padx=6, pady=6)

        ttk.Label(form, text=self.t("notes")).grid(row=5, column=0, sticky="ne", padx=6, pady=6)
        self.notes = tk.Text(form, width=32, height=3, wrap="word")
        self.notes.grid(row=5, column=1, sticky="ew", padx=6, pady=6)
        if expense and expense["notes"]:
            self.notes.insert("1.0", expense["notes"])

        btns = ttk.Frame(form)
        btns.grid(row=6, column=0, columnspan=2, sticky="e", pady=10)
        ttk.Button(btns, text=self.t("cancel"), command=self.destroy).pack(side="left", padx=4)
        ttk.Button(btns, text=self.t("save"), style="Primary.TButton", command=self.save).pack(
            side="left", padx=4
        )

    def save(self) -> None:
        try:
            amount = float(self.vars["amount"].get() or 0)
        except ValueError:
            messagebox.showwarning(self.t("expenses"), "Invalid amount.", parent=self)
            return
        self.result = {
            "expense_date": self.vars["expense_date"].get().strip(),
            "category": self.cat_map[self.cat_var.get()],
            "description": self.vars["description"].get().strip(),
            "amount": amount,
            "payment_method": self.pm_map[self.pm_var.get()],
            "notes": self.notes.get("1.0", "end").strip(),
        }
        self.destroy()


class InvoiceDialog(BaseDialog):
    """Create a new invoice with line items, live totals, and responsive layout."""

    def __init__(self, parent: tk.Misc, i18n: I18N) -> None:
        super().__init__(parent, i18n, i18n.t("new_invoice"), resizable=True)
        self.cur = CURRENCY[i18n.lang]
        self.geometry("820x680")
        self.minsize(720, 600)

        top = ttk.Frame(self, padding=14)
        top.pack(fill="x")
        top.columnconfigure(1, weight=1)
        top.columnconfigure(3, weight=1)

        with connect_db() as conn:
            patients = conn.execute(
                "SELECT id, full_name FROM patients ORDER BY full_name"
            ).fetchall()
        self.patient_map = {f'{p["full_name"]} (#{p["id"]})': p["id"] for p in patients}
        self.patient_var = tk.StringVar()

        ttk.Label(top, text=self.t("patient")).grid(row=0, column=0, sticky="e", padx=6, pady=5)
        ttk.Combobox(
            top,
            textvariable=self.patient_var,
            state="readonly",
            values=list(self.patient_map.keys()),
            width=34,
        ).grid(row=0, column=1, sticky="ew", padx=6, pady=5)

        ttk.Label(top, text=self.t("invoice_date")).grid(
            row=0, column=2, sticky="e", padx=6, pady=5
        )
        self.date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(top, textvariable=self.date_var, width=16).grid(
            row=0, column=3, sticky="w", padx=6, pady=5
        )

        ttk.Label(top, text=self.t("payment_method")).grid(
            row=1, column=2, sticky="e", padx=6, pady=5
        )
        self.pm_map = {
            self.t("cash"): "Cash",
            self.t("card"): "Card",
            self.t("transfer"): "Transfer",
        }
        self.pm_var = tk.StringVar(value=self.t("cash"))
        ttk.Combobox(
            top,
            textvariable=self.pm_var,
            state="readonly",
            values=list(self.pm_map.keys()),
            width=14,
        ).grid(row=1, column=3, sticky="w", padx=6, pady=5)

        mid = ttk.Frame(self, padding=14)
        mid.pack(fill="both", expand=True)
        mid.rowconfigure(0, weight=1)
        mid.columnconfigure(0, weight=1)

        cols = ("description", "quantity", "unit_price", "line_total")
        self.tree = ttk.Treeview(mid, columns=cols, show="headings", height=8)
        for col, w, anchor in zip(cols, (300, 80, 120, 120), ("w", "center", "center", "center")):
            self.tree.heading(col, text=self.t(col))
            self.tree.column(col, width=w, anchor=anchor)
        self.tree.grid(row=0, column=0, sticky="nsew")

        lf = ttk.Frame(mid)
        lf.grid(row=1, column=0, sticky="ew", pady=8)
        self.line_desc = tk.StringVar()
        self.line_qty = tk.StringVar(value="1")
        self.line_price = tk.StringVar(value="0")
        ttk.Label(lf, text=self.t("description")).pack(side="left", padx=4)
        ttk.Entry(lf, textvariable=self.line_desc, width=28).pack(side="left", padx=4)
        ttk.Label(lf, text=self.t("quantity")).pack(side="left", padx=4)
        ttk.Entry(lf, textvariable=self.line_qty, width=6).pack(side="left", padx=4)
        ttk.Label(lf, text=self.t("unit_price")).pack(side="left", padx=4)
        ttk.Entry(lf, textvariable=self.line_price, width=10).pack(side="left", padx=4)
        ttk.Button(
            lf, text="＋ " + self.t("add_line"), style="Primary.TButton", command=self.add_line
        ).pack(side="left", padx=6)
        ttk.Button(lf, text=self.t("remove_line"), command=self.remove_line).pack(
            side="left", padx=4
        )

        bottom = ttk.Frame(self, padding=14)
        bottom.pack(fill="x")

        grid = ttk.Frame(bottom)
        grid.pack(fill="x")
        self.discount_var = tk.StringVar(value="0")
        self.tax_var = tk.StringVar(value="0")
        self.paid_var = tk.StringVar(value="0")
        self.total_var = tk.StringVar(value="0.00")
        self.remaining_var = tk.StringVar(value="0.00")

        ttk.Label(grid, text=self.t("discount") + ":").grid(row=0, column=0, sticky="e", padx=4, pady=3)
        ttk.Entry(grid, textvariable=self.discount_var, width=10).grid(row=0, column=1, padx=4, pady=3)
        ttk.Label(grid, text=self.t("tax") + " (%):").grid(row=0, column=2, sticky="e", padx=4, pady=3)
        ttk.Entry(grid, textvariable=self.tax_var, width=10).grid(row=0, column=3, padx=4, pady=3)
        ttk.Label(grid, text=self.t("paid") + ":").grid(row=0, column=4, sticky="e", padx=4, pady=3)
        ttk.Entry(grid, textvariable=self.paid_var, width=12).grid(row=0, column=5, padx=4, pady=3)

        for var in (self.discount_var, self.tax_var, self.paid_var):
            var.trace_add("write", lambda *_: self.recalc())

        summary = ttk.Frame(bottom)
        summary.pack(fill="x", pady=8)
        self.subtotal_lbl = ttk.Label(summary, text=f'{self.t("subtotal")}: 0.00 {self.cur}', font=("Segoe UI", 10))
        self.subtotal_lbl.pack(anchor="e")
        ttk.Label(
            summary,
            textvariable=self.total_var,
            font=("Segoe UI", 14, "bold"),
            foreground=COLORS["primary"],
        ).pack(anchor="e")
        ttk.Label(summary, textvariable=self.remaining_var, foreground=COLORS["danger_dark"]).pack(
            anchor="e"
        )

        b2 = ttk.Frame(bottom)
        b2.pack(fill="x")
        ttk.Button(b2, text=self.t("cancel"), command=self.destroy).pack(side="right", padx=4)
        ttk.Button(b2, text=self.t("save"), style="Primary.TButton", command=self.save).pack(
            side="right", padx=4
        )

        self.recalc()

    def add_line(self) -> None:
        try:
            q = int(self.line_qty.get() or 0)
            p = float(self.line_price.get() or 0)
        except ValueError:
            return
        desc = self.line_desc.get().strip()
        if not desc or q <= 0:
            return
        self.tree.insert("", "end", values=(desc, q, f"{p:.2f}", f"{q * p:.2f}"))
        self.line_desc.set("")
        self.line_qty.set("1")
        self.line_price.set("0")
        self.recalc()

    def remove_line(self) -> None:
        for s in self.tree.selection():
            self.tree.delete(s)
        self.recalc()

    def recalc(self) -> None:
        subtotal = sum(float(self.tree.item(i, "values")[3]) for i in self.tree.get_children())
        try:
            discount = float(self.discount_var.get() or 0)
            tax_pct = float(self.tax_var.get() or 0)
            paid = float(self.paid_var.get() or 0)
        except ValueError:
            discount = tax_pct = paid = 0
        after_disc = max(0.0, subtotal - discount)
        tax = after_disc * tax_pct / 100.0
        total = after_disc + tax
        remaining = total - paid
        self.subtotal_lbl.configure(text=f'{self.t("subtotal")}: {subtotal:.2f} {self.cur}')
        self.total_var.set(f'{self.t("total")}: {total:.2f} {self.cur}')
        self.remaining_var.set(f'{self.t("remaining")}: {remaining:.2f} {self.cur}')

    def save(self) -> None:
        label = self.patient_var.get()
        if not label:
            messagebox.showwarning(self.t("billing"), self.t("select_patient_first"), parent=self)
            return
        items = []
        subtotal = 0.0
        for it in self.tree.get_children():
            d, q, p, lt = self.tree.item(it, "values")
            items.append((d, int(q), float(p), float(lt)))
            subtotal += float(lt)
        if not items:
            messagebox.showwarning(self.t("billing"), "Add at least one item.", parent=self)
            return
        try:
            discount = float(self.discount_var.get() or 0)
            tax_pct = float(self.tax_var.get() or 0)
            paid = float(self.paid_var.get() or 0)
        except ValueError:
            discount = tax_pct = paid = 0
        after_disc = max(0.0, subtotal - discount)
        tax = after_disc * tax_pct / 100.0
        total = after_disc + tax
        self.result = {
            "patient_id": self.patient_map[label],
            "invoice_date": self.date_var.get().strip(),
            "subtotal": subtotal,
            "discount": discount,
            "tax": tax,
            "total": total,
            "paid": paid,
            "payment_method": self.pm_map[self.pm_var.get()],
            "items": items,
        }
        self.destroy()


class InvoiceDetailsDialog(BaseDialog):
    def __init__(self, parent: tk.Misc, i18n: I18N, invoice_id: int) -> None:
        super().__init__(parent, i18n, i18n.t("invoice_details"), resizable=True)
        self.cur = CURRENCY[i18n.lang]
        self.invoice_id = invoice_id
        self.geometry("660x620")
        self.minsize(560, 520)

        with connect_db() as conn:
            self.inv = conn.execute(
                """SELECT i.*, p.full_name, p.phone FROM invoices i
                   JOIN patients p ON p.id=i.patient_id WHERE i.id=?""",
                (invoice_id,),
            ).fetchone()
            self.items = conn.execute(
                """SELECT description, quantity, unit_price, line_total
                   FROM invoice_items WHERE invoice_id=?""",
                (invoice_id,),
            ).fetchall()

        header = ttk.Frame(self, padding=16)
        header.pack(fill="x")
        hrow = ttk.Frame(header)
        hrow.pack(anchor="w", fill="x")
        logo = get_logo_photo(size=42, bg=COLORS["bg"])
        if logo:
            lbl = tk.Label(hrow, image=logo, bg=COLORS["bg"])
            lbl.image = logo  # type: ignore[attr-defined]
            lbl.pack(side="left", padx=4)
        tk.Label(
            hrow,
            text=TRANSLATIONS[self.i18n.lang]["clinic_name"],
            bg=COLORS["bg"],
            fg=COLORS["sidebar"],
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left")
        ttk.Label(
            header,
            text=f'{self.t("invoice_details")} #{self.inv["id"]}',
            font=("Segoe UI", 12),
            foreground=COLORS["text_muted"],
        ).pack(anchor="w", pady=4)

        info = ttk.Frame(self, padding=16)
        info.pack(fill="x")
        ttk.Label(info, text=f'{self.t("patient")}: {self.inv["full_name"]}   |   {self.inv["phone"] or ""}').pack(anchor="w")
        ttk.Label(info, text=f'{self.t("invoice_date")}: {self.inv["invoice_date"]}').pack(anchor="w")
        ttk.Label(info, text=f'{self.t("payment_method")}: {self.inv["payment_method"] or "-"}').pack(anchor="w")
        ttk.Label(info, text=f'{self.t("status")}: {self.inv["status"]}').pack(anchor="w")

        cols = ("description", "quantity", "unit_price", "line_total")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=8)
        for col, w, anchor in zip(cols, (260, 80, 100, 100), ("w", "center", "center", "center")):
            self.tree.heading(col, text=self.t(col))
            self.tree.column(col, width=w, anchor=anchor)
        self.tree.pack(fill="both", expand=True, padx=16)
        for it in self.items:
            self.tree.insert(
                "",
                "end",
                values=(it["description"], it["quantity"], f"{it['unit_price']:.2f}", f"{it['line_total']:.2f}"),
            )

        totals = ttk.Frame(self, padding=16)
        totals.pack(fill="x")
        for label, value in [
            (self.t("subtotal"), self.inv["subtotal"]),
            (self.t("discount"), self.inv["discount"]),
            (self.t("tax"), self.inv["tax"]),
        ]:
            ttk.Label(totals, text=f"{label}: {value:.2f} {self.cur}").pack(anchor="e")
        ttk.Label(
            totals,
            text=f'{self.t("total")}: {self.inv["total"]:.2f} {self.cur}',
            font=("Segoe UI", 12, "bold"),
            foreground=COLORS["sidebar"],
        ).pack(anchor="e")
        ttk.Label(totals, text=f'{self.t("paid")}: {self.inv["paid"]:.2f} {self.cur}').pack(anchor="e")
        remaining = self.inv["total"] - self.inv["paid"]
        ttk.Label(
            totals,
            text=f'{self.t("remaining")}: {remaining:.2f} {self.cur}',
            foreground=COLORS["danger_dark"],
        ).pack(anchor="e")

        btns = ttk.Frame(self, padding=16)
        btns.pack(fill="x")
        ttk.Button(btns, text=self.t("close"), command=self.destroy).pack(side="right", padx=4)
        ttk.Button(
            btns, text="🖨 " + self.t("print"), style="Primary.TButton", command=self.print_invoice
        ).pack(side="right", padx=4)

    def print_invoice(self) -> None:
        text = self.build_print_text()
        win = tk.Toplevel(self)
        win.title(self.t("print"))
        win.geometry("500x650")
        txt = tk.Text(win, wrap="word", font=("Consolas", 10))
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", text)
        txt.configure(state="disabled")
        ttk.Button(win, text=self.t("close"), command=win.destroy).pack(pady=6)

    def build_print_text(self) -> str:
        sep = "═" * 46
        lines = [
            sep,
            "  " + TRANSLATIONS[self.i18n.lang]["clinic_name"],
            "  Clinic Manager",
            sep,
            f'{self.t("invoice_details")} #{self.inv["id"]}',
            f'{self.t("invoice_date")}: {self.inv["invoice_date"]}',
            f'{self.t("patient")}: {self.inv["full_name"]}',
            f'{self.t("phone")}: {self.inv["phone"] or "-"}',
            sep,
        ]
        for it in self.items:
            lines.append(f'{it["description"]}')
            lines.append(f'  {it["quantity"]} x {it["unit_price"]:.2f}  =  {it["line_total"]:.2f} {self.cur}')
        lines.append(sep)
        for label, value in [
            (self.t("subtotal"), self.inv["subtotal"]),
            (self.t("discount"), self.inv["discount"]),
            (self.t("tax"), self.inv["tax"]),
            (self.t("total"), self.inv["total"]),
            (self.t("paid"), self.inv["paid"]),
            (self.t("remaining"), self.inv["total"] - self.inv["paid"]),
        ]:
            lines.append(f"{label:<20} {value:.2f} {self.cur}")
        lines.extend([sep, "  Thank you / شكرًا لزيارتكم", sep])
        return "\n".join(lines)


class PatientHistoryDialog(BaseDialog):
    def __init__(self, parent: tk.Misc, i18n: I18N, patient_id: int) -> None:
        super().__init__(parent, i18n, i18n.t("patient_history"), resizable=True)
        self.geometry("820x600")
        self.minsize(640, 480)

        with connect_db() as conn:
            p = conn.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
            self.records = conn.execute(
                """SELECT * FROM medical_records
                   WHERE patient_id=? ORDER BY visit_date DESC""",
                (patient_id,),
            ).fetchall()

        top = ttk.Frame(self, padding=16)
        top.pack(fill="x")
        hrow = ttk.Frame(top)
        hrow.pack(anchor="w", fill="x")
        logo = get_logo_photo(size=36, bg=COLORS["bg"])
        if logo:
            lbl = tk.Label(hrow, image=logo, bg=COLORS["bg"])
            lbl.image = logo  # type: ignore[attr-defined]
            lbl.pack(side="left", padx=4)
        ttk.Label(
            hrow,
            text=(p["full_name"] if p else "—"),
            font=("Segoe UI", 16, "bold"),
            foreground=COLORS["sidebar"],
        ).pack(side="left")

        if p:
            ttk.Label(
                top,
                text=f'{self.t("phone")}: {p["phone"] or "-"}  |  {self.t("blood_type")}: {p["blood_type"] or "-"}',
                foreground=COLORS["text_muted"],
            ).pack(anchor="w")
            if p["allergies"]:
                ttk.Label(
                    top,
                    text=f'{self.t("allergies")}: {p["allergies"]}',
                    foreground=COLORS["danger_dark"],
                ).pack(anchor="w")

        cols = ("date", "diagnosis", "bp", "temp", "weight", "sugar", "hr")
        tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        headings = {
            "date": "visit_date",
            "diagnosis": "diagnosis",
            "bp": "blood_pressure",
            "temp": "temperature",
            "weight": "weight",
            "sugar": "sugar_level",
            "hr": "heart_rate",
        }
        for c, w in zip(cols, (100, 200, 90, 70, 70, 90, 70)):
            tree.heading(c, text=self.t(headings[c]))
            tree.column(c, width=w, anchor="center" if c != "diagnosis" else "w")
        tree.pack(fill="both", expand=True, padx=16, pady=8)
        for r in self.records:
            tree.insert(
                "",
                "end",
                values=(
                    r["visit_date"],
                    r["diagnosis"],
                    r["blood_pressure"],
                    r["temperature"],
                    r["weight"],
                    r["sugar_level"],
                    r["heart_rate"],
                ),
            )

        ttk.Button(self, text=self.t("close"), command=self.destroy).pack(pady=8)


# ═══════════════════════════════════════════════════════════════════
#  5. Language popup (shared helper)
# ═══════════════════════════════════════════════════════════════════

class LanguagePopup:
    """A small reusable language selector popup."""

    def __init__(self, parent: tk.Misc, i18n: I18N, anchor_widget: tk.Widget, on_select: Callable[[str], None]) -> None:
        self.parent = parent
        self.i18n = i18n
        self.anchor = anchor_widget
        self.on_select = on_select
        self._popup: Optional[tk.Toplevel] = None

    def open(self) -> None:
        if self._popup and self._popup.winfo_exists():
            self.close()
            return
        popup = tk.Toplevel(self.parent)
        self._popup = popup
        popup.overrideredirect(True)
        popup.configure(bg=COLORS["sidebar"])
        popup.attributes("-topmost", True)

        outer = tk.Frame(popup, bg=COLORS["sidebar_alt"])
        outer.pack(fill="both", expand=True)
        header = tk.Frame(outer, bg=COLORS["sidebar"])
        header.pack(fill="x")
        tk.Label(
            header,
            text="🌐  Language / اللغة / Langue",
            bg=COLORS["sidebar"],
            fg="#8fa8bf",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=8,
            anchor="w",
        ).pack(fill="x")
        tk.Frame(outer, bg=COLORS["sidebar"], height=1).pack(fill="x")

        for code, label, sub in (
            ("ar", LANG_FLAGS["ar"], "Arabic"),
            ("en", LANG_FLAGS["en"], "English"),
            ("fr", LANG_FLAGS["fr"], "French"),
        ):
            self._build_row(outer, code, label, sub)

        tk.Frame(outer, bg=COLORS["sidebar"], height=1).pack(fill="x")
        popup.update_idletasks()
        w = max(230, popup.winfo_reqwidth())
        h = popup.winfo_reqheight()
        btn_x = self.anchor.winfo_rootx()
        btn_y = self.anchor.winfo_rooty()
        btn_w = self.anchor.winfo_width()
        btn_h = self.anchor.winfo_height()
        x = btn_x + btn_w - w if self.i18n.lang == "ar" else btn_x
        screen_h = self.parent.winfo_screenheight()  # type: ignore[attr-defined]
        y = btn_y - h - 4 if btn_y + btn_h + h > screen_h else btn_y + btn_h + 4
        popup.geometry(f"{w}x{h}+{x}+{y}")
        popup.bind("<FocusOut>", lambda _e: self.close())
        popup.focus_set()

    def _build_row(self, parent: tk.Frame, code: str, label: str, sub: str) -> None:
        is_current = code == self.i18n.lang
        bg = COLORS["primary"] if is_current else COLORS["sidebar_alt"]
        fg = "#ffffff" if is_current else "#e8f2fb"

        row = tk.Frame(parent, bg=bg, cursor="hand2")
        row.pack(fill="x")
        check = tk.Label(
            row,
            text="✓" if is_current else " ",
            bg=bg,
            fg="#20b2aa" if is_current else bg,
            font=("Segoe UI", 11, "bold"),
            width=3,
        )
        check.pack(side="left", pady=8)
        lbl = tk.Label(
            row,
            text=label,
            bg=bg,
            fg=fg,
            font=("Segoe UI", 10, "bold" if is_current else "normal"),
            anchor="w",
            padx=4,
        )
        lbl.pack(side="left", fill="x", expand=True, pady=8)
        sub_lbl = tk.Label(row, text=sub, bg=bg, fg="#8fa8bf", font=("Segoe UI", 8), padx=10)
        sub_lbl.pack(side="right", pady=8)

        def on_enter(_e: tk.Event) -> None:
            if is_current:
                return
            for w in (row, check, lbl, sub_lbl):
                w.configure(bg=COLORS["primary"])
            check.configure(fg="#ffffff")
            lbl.configure(fg="#ffffff")
            sub_lbl.configure(fg="#d8e5f2")

        def on_leave(_e: tk.Event) -> None:
            if is_current:
                return
            for w in (row, check, lbl, sub_lbl):
                w.configure(bg=COLORS["sidebar_alt"])
            check.configure(fg=COLORS["sidebar_alt"])
            lbl.configure(fg="#e8f2fb")
            sub_lbl.configure(fg="#8fa8bf")

        def on_click(_e: tk.Event) -> None:
            self.close()
            self.on_select(code)

        for w in (row, check, lbl, sub_lbl):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

    def close(self) -> None:
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
        self._popup = None


# ═══════════════════════════════════════════════════════════════════
#  6. About Developer dialog
# ═══════════════════════════════════════════════════════════════════

class AboutDevDialog(tk.Toplevel):
    """Professional 'About the Developer' modal."""

    def __init__(self, parent: tk.Misc, i18n: I18N) -> None:
        super().__init__(parent)
        self.parent = parent
        self.i18n = i18n
        self.title("About the Developer")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.transient(parent)  # type: ignore[arg-type]
        self.grab_set()

        W, H = 420, 470
        self.geometry(f"{W}x{H}")
        self.update_idletasks()
        try:
            px = parent.winfo_rootx() + (parent.winfo_width() - W) // 2
            py = parent.winfo_rooty() + (parent.winfo_height() - H) // 2
            self.geometry(f"{W}x{H}+{max(0, px)}+{max(0, py)}")
        except tk.TclError:
            pass

        header = tk.Frame(self, bg=COLORS["sidebar"], height=120)
        header.pack(fill="x")
        header.pack_propagate(False)

        avatar = tk.Canvas(header, width=72, height=72, bg=COLORS["sidebar"],
                           highlightthickness=0)
        avatar.pack(pady=(18, 4))
        avatar.create_oval(2, 2, 70, 70, fill=COLORS["primary"], outline="")
        avatar.create_text(36, 36, text="HB", fill="#ffffff",
                           font=("Segoe UI", 22, "bold"))

        tk.Label(header, text=DEV_NAME, bg=COLORS["sidebar"], fg="#ffffff",
                 font=("Segoe UI", 14, "bold")).pack()
        tk.Label(header, text="Full-Stack Developer", bg=COLORS["sidebar"],
                 fg="#8fa8bf", font=("Segoe UI", 9)).pack(pady=(0, 6))

        body = ttk.Frame(self, padding=22)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text=APP_NAME,
                  font=("Segoe UI", 13, "bold"),
                  foreground=COLORS["sidebar"]).pack(anchor="w")
        ttk.Label(body, text=APP_TAGLINE,
                  font=("Segoe UI", 9),
                  foreground=COLORS["text_muted"]).pack(anchor="w", pady=(0, 14))

        info = ttk.Frame(body)
        info.pack(fill="x", pady=(0, 12))
        rows = (
            ("Version", DEV_VERSION),
            ("Year", DEV_YEAR),
            ("Email", DEV_EMAIL),
            ("GitHub", DEV_GITHUB),
            ("Built with", "Python · Tkinter · SQLite"),
        )
        for i, (k, v) in enumerate(rows):
            ttk.Label(info, text=f"{k}:", font=("Segoe UI", 9, "bold"),
                      foreground=COLORS["text_muted"]).grid(
                row=i, column=0, sticky="e", padx=(0, 10), pady=3)
            ttk.Label(info, text=v, font=("Segoe UI", 9),
                      foreground=COLORS["text"]).grid(
                row=i, column=1, sticky="w", pady=3)

        ttk.Separator(body, orient="horizontal").pack(fill="x", pady=10)

        tk.Label(body, text="✦  Thank you for using our software  ✦",
                 bg=COLORS["bg"], fg=COLORS["primary"],
                 font=("Segoe UI", 10, "bold")).pack(pady=(6, 0))

        btns = ttk.Frame(body)
        btns.pack(fill="x", pady=(18, 0))
        ttk.Button(btns, text="Close", style="Primary.TButton",
                   command=self.destroy).pack(side="right", padx=4)

        self.bind("<Escape>", lambda _e: self.destroy())
        self.focus_set()


# ═══════════════════════════════════════════════════════════════════
#  7. Main application
# ═══════════════════════════════════════════════════════════════════

class ClinicApp(tk.Tk):
    PAGE_KEYS = (
        "dashboard",
        "patients",
        "appointments",
        "records",
        "billing",
        "inventory",
        "expenses",
        "reports",
        "settings",
    )
    PAGE_ICONS = {
        "dashboard": "⌂",
        "patients": "♙",
        "appointments": "▦",
        "records": "▤",
        "billing": "▧",
        "inventory": "▣",
        "expenses": "▩",
        "reports": "▥",
        "settings": "⚙",
    }

    def __init__(self, lang: str = "ar") -> None:
        _reset_image_cache()
        super().__init__()
        self.i18n = I18N(lang)
        self.t = self.i18n.t
        self.cur = CURRENCY[self.i18n.lang]
        self.title(self.t(APP_TITLE_KEY))
        self.geometry("1280x800")
        self.minsize(1024, 640)
        self.configure(bg=COLORS["bg"])
        self.current_page = "dashboard"
        self._lang_popup_handler: Optional[LanguagePopup] = None

        load_icon(self)
        patch_toplevel_icon()
        self._setup_styles()
        self._build_shell()
        self.show_page("dashboard")

    def _setup_styles(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame", background=COLORS["bg"])
        s.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Segoe UI", 10))
        s.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), foreground=COLORS["sidebar"])
        s.configure("Section.TLabel", font=("Segoe UI", 13, "bold"), foreground=COLORS["sidebar"])
        s.configure("Card.TFrame", background=COLORS["card"], relief="flat")
        s.configure("CardTitle.TLabel", background=COLORS["card"], foreground=COLORS["text_muted"], font=("Segoe UI", 10))
        s.configure("Primary.TButton", background=COLORS["primary"], foreground="#ffffff", padding=(12, 8), borderwidth=0)
        s.map("Primary.TButton", background=[("active", COLORS["primary_dark"])])
        s.configure("Success.TButton", background=COLORS["success"], foreground="#ffffff", padding=(12, 8), borderwidth=0)
        s.map("Success.TButton", background=[("active", COLORS["success_dark"])])
        s.configure("Danger.TButton", background=COLORS["danger"], foreground="#ffffff", padding=(12, 8), borderwidth=0)
        s.map("Danger.TButton", background=[("active", COLORS["danger_dark"])])
        s.configure("Ghost.TButton", background="#eaf1f8", foreground=COLORS["sidebar"], padding=(10, 9), borderwidth=0)
        s.map("Ghost.TButton", background=[("active", "#d8e5f2")])
        s.configure("Treeview", rowheight=30, background=COLORS["card"], fieldbackground=COLORS["card"], foreground=COLORS["text"])
        s.configure(
            "Treeview.Heading",
            background="#eaf1f8",
            foreground=COLORS["sidebar"],
            font=("Segoe UI", 10, "bold"),
            padding=8,
        )

    def _build_shell(self) -> None:
        self.shell = ttk.Frame(self, padding=12)
        self.shell.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(self.shell, bg=COLORS["sidebar"], width=230)
        self.sidebar.pack(side="left", fill="y", padx=(0, 12))
        self.sidebar.pack_propagate(False)

        logo = get_logo_photo(size=72, bg=COLORS["sidebar"])
        if logo:
            lbl = tk.Label(self.sidebar, image=logo, bg=COLORS["sidebar"])
            lbl.image = logo  # type: ignore[attr-defined]
            lbl.pack(pady=20)
            self.brand = tk.Label(
                self.sidebar,
                text="Clinic Manager",
                bg=COLORS["sidebar"],
                fg="white",
                font=("Segoe UI", 15, "bold"),
                wraplength=200,
                pady=8,
            )
            self.brand.pack(fill="x")
        else:
            self.brand = tk.Label(
                self.sidebar,
                text="✚  Clinic Manager",
                bg=COLORS["sidebar"],
                fg="white",
                font=("Segoe UI", 16, "bold"),
                wraplength=200,
                pady=22,
            )
            self.brand.pack(fill="x")

        self.nav_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        self.nav_frame.pack(fill="x", padx=10)
        self.nav_buttons: dict[str, tk.Button] = {}
        for key in self.PAGE_KEYS:
            btn = tk.Button(
                self.nav_frame,
                text="",
                anchor="w",
                relief="flat",
                bd=0,
                bg=COLORS["sidebar"],
                fg="#e8f2fb",
                activebackground=COLORS["primary"],
                activeforeground="white",
                padx=12,
                pady=10,
                font=("Segoe UI", 10),
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = btn

        bottom = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        bottom.pack(side="bottom", fill="x", padx=10, pady=12)

        self.lang_btn = tk.Button(
            bottom,
            text="🌐",
            relief="flat",
            bg="#163a5c",
            fg="white",
            activebackground=COLORS["primary"],
            activeforeground="white",
            font=("Segoe UI", 13),
            cursor="hand2",
            width=3,
            pady=6,
            command=self._open_language_menu,
        )
        self.lang_btn.pack(side="right", padx=(6, 0))
        self.logout_btn = tk.Button(
            bottom,
            text="⎋  Logout",
            relief="flat",
            bg=COLORS["danger_dark"],
            fg="white",
            activebackground=COLORS["danger"],
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            anchor="center",
            pady=10,
            padx=8,
            borderwidth=0,
            highlightthickness=0,
            command=self.logout,
        )
        self.logout_btn.pack(side="left", fill="x", expand=True)
        self.logout_btn.bind("<Enter>", lambda _e: self.logout_btn.configure(bg=COLORS["danger"]))
        self.logout_btn.bind("<Leave>", lambda _e: self.logout_btn.configure(bg=COLORS["danger_dark"]))

        self.main = ttk.Frame(self.shell)
        self.main.pack(side="left", fill="both", expand=True)
        self.header = ttk.Frame(self.main)
        self.header.pack(fill="x", pady=(0, 12))
        small = get_logo_photo(size=28, bg=COLORS["bg"])
        if small:
            lbl = tk.Label(self.header, image=small, bg=COLORS["bg"])
            lbl.image = small  # type: ignore[attr-defined]
            lbl.pack(side="left", padx=8)
        self.page_title = ttk.Label(self.header, text="", style="Title.TLabel")
        self.page_title.pack(side="left", padx=8, pady=10)
        self.body = ttk.Frame(self.main)
        self.body.pack(fill="both", expand=True)
        self.retranslate()

    def retranslate(self) -> None:
        t = TRANSLATIONS[self.i18n.lang]
        self.title(t[APP_TITLE_KEY])
        self.cur = CURRENCY[self.i18n.lang]
        self.logout_btn.configure(text="⎋  " + t["logout"])
        for key, btn in self.nav_buttons.items():
            btn.configure(text=f"{self.PAGE_ICONS[key]}  {t[key]}")
        self._apply_direction()
        if getattr(self, "body", None) and self.body.winfo_exists() and self.current_page:
            self.show_page(self.current_page)

    def _apply_direction(self) -> None:
        if self.i18n.lang == "ar":
            self.sidebar.pack_configure(side="right", padx=(12, 0))
            self.main.pack_configure(side="right")
            self.page_title.pack_configure(side="right")
            for b in self.nav_buttons.values():
                b.configure(anchor="e")
            self.logout_btn.pack_configure(side="right", fill="x", expand=True, padx=(0, 6))
            self.lang_btn.pack_configure(side="left", padx=(0, 0))
        else:
            self.sidebar.pack_configure(side="left", padx=(0, 12))
            self.main.pack_configure(side="left")
            self.page_title.pack_configure(side="left")
            for b in self.nav_buttons.values():
                b.configure(anchor="w")
            self.logout_btn.pack_configure(side="left", fill="x", expand=True, padx=(0, 6))
            self.lang_btn.pack_configure(side="right", padx=(0, 0))

    def _open_language_menu(self) -> None:
        self._lang_popup_handler = LanguagePopup(self, self.i18n, self.lang_btn, self.set_language)
        self._lang_popup_handler.open()

    def close_language_menu(self) -> None:
        if self._lang_popup_handler:
            self._lang_popup_handler.close()
        self._lang_popup_handler = None

    def set_language(self, code: str) -> None:
        self.close_language_menu()
        self.i18n.set(code)
        self.retranslate()

    def _open_about_dev(self) -> None:
        AboutDevDialog(self, self.i18n)

    def logout(self) -> None:
        """
        Close the main window. The outer loop in `main()` will
        re-open the login screen in the current language.
        """
        if not messagebox.askyesno(self.t("settings"), self.t("logout_confirm")):
            return
        self.close_language_menu()
        try:
            self.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
        self.destroy()

    def clear_body(self) -> None:
        for w in self.body.winfo_children():
            w.destroy()

    def show_page(self, key: str) -> None:
        self.current_page = key
        self.clear_body()
        self.page_title.configure(text=self.t(key))
        for k, btn in self.nav_buttons.items():
            btn.configure(bg=COLORS["primary"] if k == key else COLORS["sidebar"])
        render = getattr(self, f"render_{key}", None)
        if render:
            render()
        else:
            ttk.Label(
                self.body,
                text=f"Page '{key}' not implemented",
                foreground=COLORS["danger_dark"],
            ).pack(pady=20)

    def stat_card(self, parent: tk.Misc, title: str, value: Any, color: str = COLORS["primary"], subtitle: str = "") -> ttk.Frame:
        return make_stat_card(parent, title, value, color, subtitle)

    # ─────────────────────────────────────────────────────────────────
    #  DASHBOARD
    # ─────────────────────────────────────────────────────────────────
    def render_dashboard(self) -> None:
        t = self.t
        today = date.today().isoformat()

        with connect_db() as conn:
            stats = conn.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM patients) AS patient_count,
                    (SELECT COUNT(*) FROM appointments WHERE appointment_date=?) AS today_app,
                    (SELECT COALESCE(SUM(paid),0) FROM invoices WHERE invoice_date=?) AS today_rev,
                    (SELECT COALESCE(SUM(amount),0) FROM expenses WHERE expense_date=?) AS today_exp,
                    (SELECT COUNT(*) FROM inventory WHERE quantity<=min_quantity) AS low_stock,
                    (SELECT COUNT(*) FROM inventory WHERE expiry_date!='' AND expiry_date<?) AS expired,
                    (SELECT COALESCE(SUM(paid),0) FROM invoices WHERE invoice_date >= date('now','-30 day')) AS month_rev,
                    (SELECT COALESCE(SUM(amount),0) FROM expenses WHERE expense_date >= date('now','-30 day')) AS month_exp
                """,
                (today, today, today, today),
            ).fetchone()

            start = (date.today() - timedelta(days=6)).isoformat()
            rev_rows = conn.execute(
                "SELECT invoice_date, COALESCE(SUM(paid),0) s FROM invoices WHERE invoice_date>=? GROUP BY invoice_date",
                (start,),
            ).fetchall()
            exp_rows = conn.execute(
                "SELECT expense_date, COALESCE(SUM(amount),0) s FROM expenses WHERE expense_date>=? GROUP BY expense_date",
                (start,),
            ).fetchall()
            rev_map = {r["invoice_date"]: r["s"] for r in rev_rows}
            exp_map = {r["expense_date"]: r["s"] for r in exp_rows}
            labels, rev_by_day, exp_by_day = [], [], []
            for i in range(6, -1, -1):
                d = date.today() - timedelta(days=i)
                labels.append(d.strftime("%a"))
                rev_by_day.append(rev_map.get(d.isoformat(), 0))
                exp_by_day.append(exp_map.get(d.isoformat(), 0))

            inv_stats = conn.execute(
                """
                SELECT
                    SUM(CASE WHEN status='Paid' THEN 1 ELSE 0 END) AS paid,
                    SUM(CASE WHEN status='Partial' THEN 1 ELSE 0 END) AS partial,
                    SUM(CASE WHEN status='Unpaid' THEN 1 ELSE 0 END) AS unpaid
                FROM invoices
                """
            ).fetchone()
            inv_paid = inv_stats["paid"] or 0
            inv_partial = inv_stats["partial"] or 0
            inv_unpaid = inv_stats["unpaid"] or 0
            stock_total = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
            stock_ok = max(0, stock_total - (stats["low_stock"] or 0) - (stats["expired"] or 0))

            upcoming = conn.execute(
                """SELECT p.full_name, a.appointment_date, a.appointment_time, a.reason
                   FROM appointments a JOIN patients p ON p.id=a.patient_id
                   WHERE a.appointment_date >= ? AND a.status='Scheduled'
                   ORDER BY a.appointment_date, a.appointment_time LIMIT 8""",
                (today,),
            ).fetchall()

        net_today = stats["today_rev"] - stats["today_exp"]
        net_month = stats["month_rev"] - stats["month_exp"]

        scroller = ScrollableFrame(self.body, bg=COLORS["bg"])
        scroller.pack(fill="both", expand=True)
        root = scroller.inner

        ttk.Label(root, text=t("welcome"), style="Title.TLabel", wraplength=900).pack(anchor="w", padx=12, pady=12)

        row1 = ttk.Frame(root)
        row1.pack(fill="x", padx=8)
        for title, value, color in (
            (t("patient_count"), stats["patient_count"], COLORS["primary"]),
            (t("today_count"), stats["today_app"], COLORS["primary"]),
            (t("income"), f'{stats["today_rev"]:.2f} {self.cur}', COLORS["revenue"]),
            (t("total_expenses"), f'{stats["today_exp"]:.2f} {self.cur}', COLORS["expenses"]),
        ):
            self.stat_card(row1, title, value, color).pack(side="left", fill="both", expand=True, padx=5)

        row2 = ttk.Frame(root)
        row2.pack(fill="x", padx=8, pady=12)
        for title, value, color in (
            (t("net_profit"), f"{net_today:.2f} {self.cur}", COLORS["revenue"] if net_today >= 0 else COLORS["danger_dark"]),
            (t("net_profit_month"), f"{net_month:.2f} {self.cur}", COLORS["revenue"] if net_month >= 0 else COLORS["danger_dark"]),
            (t("stock_alert"), stats["low_stock"], COLORS["expenses"]),
            (t("expired_items"), stats["expired"], COLORS["danger_dark"]),
        ):
            self.stat_card(row2, title, value, color).pack(side="left", fill="both", expand=True, padx=5)

        ttk.Label(root, text="📊  " + t("quick_stats"), style="Section.TLabel").pack(anchor="w", padx=16, pady=8)
        charts = ttk.Frame(root, style="Card.TFrame", padding=14)
        charts.pack(fill="x", padx=16, pady=4)
        ttk.Label(
            charts,
            text=t("chart_revenue_expenses"),
            style="CardTitle.TLabel",
            font=("Segoe UI", 11, "bold"),
            foreground=COLORS["sidebar"],
        ).pack(anchor="w", pady=6)
        bar = BarChart(charts, width=700, height=250)
        bar.pack(fill="x", pady=4)
        bar.set_data(
            labels=labels,
            series=[
                {"name": t("revenue"), "color": COLORS["revenue"], "values": rev_by_day},
                {"name": t("expenses_label"), "color": COLORS["expenses"], "values": exp_by_day},
            ],
        )

        donuts = ttk.Frame(root)
        donuts.pack(fill="x", padx=16, pady=12)

        inv_box = ttk.Frame(donuts, style="Card.TFrame", padding=14)
        inv_box.pack(side="left", fill="both", expand=True, padx=4)
        ttk.Label(
            inv_box,
            text=t("chart_invoice_status"),
            style="CardTitle.TLabel",
            font=("Segoe UI", 11, "bold"),
            foreground=COLORS["sidebar"],
        ).pack(anchor="w", pady=6)
        inv_donut = DonutChart(inv_box, size=180)
        inv_donut.pack(anchor="center", pady=4)
        inv_donut.set_data(
            items=[
                (t("paid_inv"), inv_paid, COLORS["paid"]),
                (t("partial_inv"), inv_partial, COLORS["partial"]),
                (t("unpaid_inv"), inv_unpaid, COLORS["unpaid"]),
            ],
            center_title=t("total_invoices"),
            center_value=inv_paid + inv_partial + inv_unpaid,
        )
        self._legend(inv_box, [(t("paid_inv"), inv_paid, COLORS["paid"]), (t("partial_inv"), inv_partial, COLORS["partial"]), (t("unpaid_inv"), inv_unpaid, COLORS["unpaid"])])

        stock_box = ttk.Frame(donuts, style="Card.TFrame", padding=14)
        stock_box.pack(side="left", fill="both", expand=True, padx=4)
        ttk.Label(
            stock_box,
            text=t("chart_stock"),
            style="CardTitle.TLabel",
            font=("Segoe UI", 11, "bold"),
            foreground=COLORS["sidebar"],
        ).pack(anchor="w", pady=6)
        st_donut = DonutChart(stock_box, size=180)
        st_donut.pack(anchor="center", pady=4)
        st_donut.set_data(
            items=[
                (t("ok_stock"), stock_ok, COLORS["ok"]),
                (t("low_stock_label"), stats["low_stock"], COLORS["low"]),
                (t("expired_label"), stats["expired"], COLORS["expired"]),
            ],
            center_title=t("inventory"),
            center_value=stock_total,
        )
        self._legend(stock_box, [(t("ok_stock"), stock_ok, COLORS["ok"]), (t("low_stock_label"), stats["low_stock"], COLORS["low"]), (t("expired_label"), stats["expired"], COLORS["expired"])])

        box = ttk.Frame(root)
        box.pack(fill="both", expand=True, padx=16, pady=16)
        ttk.Label(box, text="📅  " + t("appointments"), style="Section.TLabel").pack(anchor="w", pady=6)
        tree = ttk.Treeview(box, columns=("p", "d", "t", "r"), show="headings", height=6)
        for c, h, w, anchor in (
            ("p", t("patient"), 220, "w"),
            ("d", t("date"), 120, "center"),
            ("t", t("time"), 100, "center"),
            ("r", t("reason"), 300, "w"),
        ):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor=anchor)
        tree.pack(fill="both", expand=True)
        for r in upcoming:
            tree.insert("", "end", values=(r["full_name"], r["appointment_date"], r["appointment_time"], r["reason"]))

    @staticmethod
    def _legend(parent: tk.Misc, entries: Iterable[tuple[str, int, str]]) -> None:
        leg = ttk.Frame(parent, style="Card.TFrame")
        leg.pack(pady=4)
        for label, val, color in entries:
            row = ttk.Frame(leg, style="Card.TFrame")
            row.pack(anchor="w", pady=1)
            tk.Label(row, text="■", fg=color, bg=COLORS["card"], font=("Segoe UI", 11)).pack(side="left", padx=4)
            ttk.Label(row, text=f"{label}: {val}", style="CardTitle.TLabel").pack(side="left")

    # ─────────────────────────────────────────────────────────────────
    #  PATIENTS
    # ─────────────────────────────────────────────────────────────────
    def render_patients(self) -> None:
        t = self.t
        toolbar = ttk.Frame(self.body)
        toolbar.pack(fill="x", pady=10)

        self.patient_search = tk.StringVar()
        ent = ttk.Entry(toolbar, textvariable=self.patient_search, width=34)
        ent.pack(side="left", padx=8, ipady=5)
        self._debounce_id = None
        self.patient_search.trace_add("write", lambda *_: self._debounce(self.load_patients_table))

        ttk.Button(toolbar, text="＋  " + t("add_patient"), style="Primary.TButton", command=self.add_patient).pack(side="right", padx=4)
        ttk.Button(toolbar, text="🩺 " + t("patient_history"), command=self.view_patient_history).pack(side="right", padx=4)
        ttk.Button(toolbar, text=t("edit"), command=self.edit_patient).pack(side="right", padx=4)
        ttk.Button(toolbar, text=t("delete"), command=self.delete_patient).pack(side="right", padx=4)

        cols = ("id", "full_name", "phone", "birth_date", "blood_type", "address")
        self.patient_table = ttk.Treeview(self.body, columns=cols, show="headings", selectmode="browse")
        heads = {
            "id": t("id"),
            "full_name": t("name"),
            "phone": t("phone"),
            "birth_date": t("birth"),
            "blood_type": t("blood_type"),
            "address": t("address"),
        }
        widths = {"id": 50, "full_name": 220, "phone": 130, "birth_date": 120, "blood_type": 90, "address": 260}
        for c in cols:
            self.patient_table.heading(c, text=heads[c])
            self.patient_table.column(c, width=widths[c], anchor="center")
        self.patient_table.pack(fill="both", expand=True)
        self.patient_table.bind("<Double-1>", lambda _e: self.view_patient_history())
        self.load_patients_table()

    def _debounce(self, fn: Callable[[], None], delay: int = 250) -> None:
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(delay, fn)

    def load_patients_table(self) -> None:
        if not hasattr(self, "patient_table") or not self.patient_table.winfo_exists():
            return
        self.patient_table.delete(*self.patient_table.get_children())
        q = self.patient_search.get().strip() if hasattr(self, "patient_search") else ""
        with connect_db() as conn:
            rows = conn.execute(
                """SELECT id, full_name, phone, birth_date, blood_type, address
                   FROM patients WHERE full_name LIKE ? OR phone LIKE ?
                   ORDER BY id DESC""",
                (f"%{q}%", f"%{q}%"),
            ).fetchall()
        for r in rows:
            self.patient_table.insert("", "end", iid=str(r["id"]), values=tuple(r))

    def add_patient(self) -> None:
        d = PatientDialog(self, self.i18n)
        self.wait_window(d)
        if not d.result:
            return
        v = d.result
        with connect_db() as conn:
            conn.execute(
                """INSERT INTO patients(full_name, phone, birth_date, address,
                    notes, blood_type, allergies, chronic_diseases, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    v["full_name"],
                    v["phone"],
                    v["birth_date"],
                    v["address"],
                    v["notes"],
                    v["blood_type"],
                    v["allergies"],
                    v["chronic_diseases"],
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        log_action("ADD_PATIENT", "patients", details=v["full_name"])
        messagebox.showinfo(self.t("patients"), self.t("saved"))
        self.load_patients_table()

    def _selected_patient(self) -> Any:
        s = self.patient_table.selection()
        if not s:
            messagebox.showwarning(self.t("patients"), self.t("select_row"))
            return None
        with connect_db() as conn:
            return conn.execute("SELECT * FROM patients WHERE id=?", (int(s[0]),)).fetchone()

    def edit_patient(self) -> None:
        row = self._selected_patient()
        if row is None:
            return
        d = PatientDialog(self, self.i18n, row)
        self.wait_window(d)
        if not d.result:
            return
        v = d.result
        with connect_db() as conn:
            conn.execute(
                """UPDATE patients SET full_name=?, phone=?, birth_date=?,
                    address=?, notes=?, blood_type=?, allergies=?,
                    chronic_diseases=? WHERE id=?""",
                (
                    v["full_name"],
                    v["phone"],
                    v["birth_date"],
                    v["address"],
                    v["notes"],
                    v["blood_type"],
                    v["allergies"],
                    v["chronic_diseases"],
                    row["id"],
                ),
            )
        log_action("EDIT_PATIENT", "patients", row["id"], v["full_name"])
        messagebox.showinfo(self.t("patients"), self.t("updated"))
        self.load_patients_table()

    def delete_patient(self) -> None:
        row = self._selected_patient()
        if row is None:
            return
        if not messagebox.askyesno(self.t("patients"), self.t("confirm_delete")):
            return
        with connect_db() as conn:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM appointments WHERE patient_id=?", (row["id"],)
            ).fetchone()[0]
            if cnt:
                messagebox.showwarning(
                    self.t("patients"),
                    TRANSLATIONS[self.i18n.lang].get("delete_blocked", "Patient has linked appointments."),
                )
                return
            conn.execute("DELETE FROM medical_records WHERE patient_id=?", (row["id"],))
            conn.execute("DELETE FROM invoices WHERE patient_id=?", (row["id"],))
            conn.execute("DELETE FROM patients WHERE id=?", (row["id"],))
        log_action("DELETE_PATIENT", "patients", row["id"])
        self.load_patients_table()

    def view_patient_history(self) -> None:
        row = self._selected_patient()
        if row is None:
            return
        PatientHistoryDialog(self, self.i18n, row["id"])

    # ─────────────────────────────────────────────────────────────────
    #  APPOINTMENTS
    # ─────────────────────────────────────────────────────────────────
    def render_appointments(self) -> None:
        t = self.t
        toolbar = ttk.Frame(self.body)
        toolbar.pack(fill="x", pady=10)
        ttk.Button(toolbar, text="＋  " + t("add_appointment"), style="Primary.TButton", command=self.add_appointment).pack(side="right")

        cols = ("id", "patient", "date", "time", "reason", "status")
        self.appointment_table = ttk.Treeview(self.body, columns=cols, show="headings")
        heads = {"id": t("id"), "patient": t("patient"), "date": t("date"), "time": t("time"), "reason": t("reason"), "status": t("status")}
        for c in cols:
            self.appointment_table.heading(c, text=heads[c])
            self.appointment_table.column(c, width=130 if c != "reason" else 260, anchor="center")
        self.appointment_table.tag_configure("st_scheduled", background="#eaf3ff")
        self.appointment_table.tag_configure("st_completed", background="#eafaf0")
        self.appointment_table.tag_configure("st_cancelled", background="#fdecea")
        self.appointment_table.pack(fill="both", expand=True)
        self.load_appointments_table()

    def load_appointments_table(self) -> None:
        if not hasattr(self, "appointment_table") or not self.appointment_table.winfo_exists():
            return
        self.appointment_table.delete(*self.appointment_table.get_children())
        with connect_db() as conn:
            rows = conn.execute(
                """SELECT a.id, p.full_name, a.appointment_date,
                          a.appointment_time, a.reason, a.status
                   FROM appointments a JOIN patients p ON p.id=a.patient_id
                   ORDER BY a.appointment_date DESC, a.appointment_time"""
            ).fetchall()
        tag_map = {"Scheduled": "st_scheduled", "Completed": "st_completed", "Cancelled": "st_cancelled"}
        for r in rows:
            self.appointment_table.insert("", "end", values=tuple(r), tags=(tag_map.get(r["status"], ""),))

    def add_appointment(self) -> None:
        with connect_db() as conn:
            if conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
                messagebox.showwarning(self.t("appointments"), self.t("no_patients"))
                return
        d = AppointmentDialog(self, self.i18n)
        self.wait_window(d)
        if not d.result:
            return
        v = d.result
        with connect_db() as conn:
            conflict = conn.execute(
                """SELECT COUNT(*) FROM appointments
                   WHERE appointment_date=? AND appointment_time=? AND status!='Cancelled'""",
                (v["date"], v["time"]),
            ).fetchone()[0]
            if conflict:
                messagebox.showwarning(self.t("appointments"), self.t("conflict"))
                return
            conn.execute(
                """INSERT INTO appointments(patient_id, appointment_date,
                    appointment_time, reason, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    v["patient_id"],
                    v["date"],
                    v["time"],
                    v["reason"],
                    v["status"],
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        log_action("ADD_APPOINTMENT", "appointments")
        messagebox.showinfo(self.t("appointments"), self.t("appointment_saved"))
        self.load_appointments_table()

    # ─────────────────────────────────────────────────────────────────
    #  MEDICAL RECORDS
    # ─────────────────────────────────────────────────────────────────
    def render_records(self) -> None:
        t = self.t
        toolbar = ttk.Frame(self.body)
        toolbar.pack(fill="x", pady=10)
        ttk.Button(toolbar, text="＋  " + t("add_record"), style="Primary.TButton", command=self.add_record).pack(side="right", padx=4)
        ttk.Button(toolbar, text=t("view_record"), command=self.view_record).pack(side="right", padx=4)
        ttk.Button(toolbar, text=t("edit"), command=self.edit_record).pack(side="right", padx=4)
        ttk.Button(toolbar, text=t("delete"), command=self.delete_record).pack(side="right", padx=4)

        cols = ("id", "patient", "visit_date", "diagnosis", "blood_pressure", "temperature", "weight")
        self.record_table = ttk.Treeview(self.body, columns=cols, show="headings", selectmode="browse")
        heads = {
            "id": t("id"),
            "patient": t("patient"),
            "visit_date": t("visit_date"),
            "diagnosis": t("diagnosis"),
            "blood_pressure": t("blood_pressure"),
            "temperature": t("temperature"),
            "weight": t("weight"),
        }
        for c in cols:
            self.record_table.heading(c, text=heads[c])
            self.record_table.column(c, width=140 if c != "diagnosis" else 260, anchor="center")
        self.record_table.pack(fill="both", expand=True)
        self.record_table.bind("<Double-1>", lambda _e: self.view_record())
        self.load_records_table()

    def load_records_table(self) -> None:
        if not hasattr(self, "record_table") or not self.record_table.winfo_exists():
            return
        self.record_table.delete(*self.record_table.get_children())
        with connect_db() as conn:
            rows = conn.execute(
                """SELECT m.id, p.full_name, m.visit_date, m.diagnosis,
                          m.blood_pressure, m.temperature, m.weight
                   FROM medical_records m JOIN patients p ON p.id=m.patient_id
                   ORDER BY m.visit_date DESC, m.id DESC"""
            ).fetchall()
        for r in rows:
            self.record_table.insert("", "end", iid=str(r["id"]), values=tuple(r))

    def add_record(self) -> None:
        with connect_db() as conn:
            if conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
                messagebox.showwarning(self.t("records"), self.t("no_patients"))
                return
        d = MedicalRecordDialog(self, self.i18n)
        self.wait_window(d)
        if not d.result:
            return
        v = d.result
        with connect_db() as conn:
            conn.execute(
                """INSERT INTO medical_records(patient_id, visit_date,
                    diagnosis, prescription, blood_pressure, temperature,
                    weight, sugar_level, heart_rate, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    v["patient_id"],
                    v["visit_date"],
                    v["diagnosis"],
                    v["prescription"],
                    v["blood_pressure"],
                    v["temperature"],
                    v["weight"],
                    v["sugar_level"],
                    v["heart_rate"],
                    v["notes"],
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        log_action("ADD_RECORD", "medical_records")
        messagebox.showinfo(self.t("records"), self.t("record_saved"))
        self.load_records_table()

    def _selected_record(self) -> Any:
        s = self.record_table.selection()
        if not s:
            messagebox.showwarning(self.t("records"), self.t("select_row"))
            return None
        with connect_db() as conn:
            return conn.execute("SELECT * FROM medical_records WHERE id=?", (int(s[0]),)).fetchone()

    def edit_record(self) -> None:
        row = self._selected_record()
        if row is None:
            return
        d = MedicalRecordDialog(self, self.i18n, record=row)
        self.wait_window(d)
        if not d.result:
            return
        v = d.result
        with connect_db() as conn:
            conn.execute(
                """UPDATE medical_records SET patient_id=?, visit_date=?,
                    diagnosis=?, prescription=?, blood_pressure=?,
                    temperature=?, weight=?, sugar_level=?, heart_rate=?,
                    notes=? WHERE id=?""",
                (
                    v["patient_id"],
                    v["visit_date"],
                    v["diagnosis"],
                    v["prescription"],
                    v["blood_pressure"],
                    v["temperature"],
                    v["weight"],
                    v["sugar_level"],
                    v["heart_rate"],
                    v["notes"],
                    row["id"],
                ),
            )
        log_action("EDIT_RECORD", "medical_records", row["id"])
        messagebox.showinfo(self.t("records"), self.t("updated"))
        self.load_records_table()

    def delete_record(self) -> None:
        row = self._selected_record()
        if row is None:
            return
        if not messagebox.askyesno(self.t("records"), self.t("confirm_delete")):
            return
        with connect_db() as conn:
            conn.execute("DELETE FROM medical_records WHERE id=?", (row["id"],))
        log_action("DELETE_RECORD", "medical_records", row["id"])
        self.load_records_table()

    def view_record(self) -> None:
        row = self._selected_record()
        if row is None:
            return
        win = tk.Toplevel(self)
        win.title(self.t("view_record"))
        win.geometry("560x600")
        win.configure(bg=COLORS["bg"])
        win.transient(self)
        with connect_db() as conn:
            p = conn.execute("SELECT full_name FROM patients WHERE id=?", (row["patient_id"],)).fetchone()
        name = p["full_name"] if p else "—"
        frame = ttk.Frame(win, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="✚  " + self.t("view_record"), style="Section.TLabel").pack(anchor="w", pady=10)
        for label, val in (
            (self.t("patient"), name),
            (self.t("visit_date"), row["visit_date"]),
            (self.t("diagnosis"), row["diagnosis"]),
            (self.t("prescription"), row["prescription"]),
            (self.t("blood_pressure"), row["blood_pressure"]),
            (self.t("temperature"), row["temperature"]),
            (self.t("weight"), row["weight"]),
            (self.t("sugar_level"), row["sugar_level"]),
            (self.t("heart_rate"), row["heart_rate"]),
            (self.t("notes"), row["notes"]),
        ):
            ttk.Label(frame, text=f"{label}:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=6)
            ttk.Label(frame, text=val or "—", wraplength=500).pack(anchor="w")
        ttk.Button(frame, text=self.t("close"), command=win.destroy).pack(anchor="e", pady=12)

    # ─────────────────────────────────────────────────────────────────
    #  INVENTORY
    # ─────────────────────────────────────────────────────────────────
    def render_inventory(self) -> None:
        t = self.t
        toolbar = ttk.Frame(self.body)
        toolbar.pack(fill="x", pady=10)
        ttk.Button(toolbar, text="＋  " + t("add_item"), style="Primary.TButton", command=self.add_item).pack(side="right", padx=4)
        ttk.Button(toolbar, text=t("edit"), command=self.edit_item).pack(side="right", padx=4)
        ttk.Button(toolbar, text=t("delete"), command=self.delete_item).pack(side="right", padx=4)

        cols = ("id", "name", "category", "quantity", "min_quantity", "purchase_price", "sale_price", "expiry_date", "supplier", "batch_number")
        self.inventory_table = ttk.Treeview(self.body, columns=cols, show="headings", selectmode="browse")
        heads = {
            "id": t("id"),
            "name": t("item_name"),
            "category": t("category"),
            "quantity": t("quantity"),
            "min_quantity": t("min_quantity"),
            "purchase_price": t("purchase_price"),
            "sale_price": t("sale_price"),
            "expiry_date": t("expiry_date"),
            "supplier": t("supplier"),
            "batch_number": t("batch_number"),
        }
        widths = {"id": 45, "name": 180, "category": 110, "quantity": 70, "min_quantity": 80, "purchase_price": 100, "sale_price": 90, "expiry_date": 110, "supplier": 120, "batch_number": 100}
        for c in cols:
            self.inventory_table.heading(c, text=heads[c])
            self.inventory_table.column(c, width=widths[c], anchor="center")
        self.inventory_table.tag_configure("low", background="#fff4e5")
        self.inventory_table.tag_configure("expired", background="#fdecea")
        self.inventory_table.pack(fill="both", expand=True)
        self.load_inventory_table()

    def load_inventory_table(self) -> None:
        if not hasattr(self, "inventory_table") or not self.inventory_table.winfo_exists():
            return
        self.inventory_table.delete(*self.inventory_table.get_children())
        today = date.today().isoformat()
        with connect_db() as conn:
            rows = conn.execute(
                """SELECT id, name, category, quantity, min_quantity,
                          purchase_price, sale_price, expiry_date,
                          supplier, batch_number
                   FROM inventory ORDER BY name"""
            ).fetchall()
        for r in rows:
            tags = []
            if r["quantity"] <= r["min_quantity"]:
                tags.append("low")
            if r["expiry_date"] and r["expiry_date"] < today:
                tags.append("expired")
            self.inventory_table.insert("", "end", iid=str(r["id"]), values=tuple(r), tags=tuple(tags))

    def add_item(self) -> None:
        d = InventoryDialog(self, self.i18n)
        self.wait_window(d)
        if not d.result:
            return
        v = d.result
        with connect_db() as conn:
            conn.execute(
                """INSERT INTO inventory(name, category, quantity,
                    min_quantity, purchase_price, sale_price, expiry_date,
                    supplier, batch_number, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    v["name"],
                    v["category"],
                    v["quantity"],
                    v["min_quantity"],
                    v["purchase_price"],
                    v["sale_price"],
                    v["expiry_date"],
                    v["supplier"],
                    v["batch_number"],
                    v["notes"],
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        log_action("ADD_ITEM", "inventory", details=v["name"])
        messagebox.showinfo(self.t("inventory"), self.t("item_saved"))
        self.load_inventory_table()

    def _selected_item(self) -> Any:
        s = self.inventory_table.selection()
        if not s:
            messagebox.showwarning(self.t("inventory"), self.t("select_row"))
            return None
        with connect_db() as conn:
            return conn.execute("SELECT * FROM inventory WHERE id=?", (int(s[0]),)).fetchone()

    def edit_item(self) -> None:
        row = self._selected_item()
        if row is None:
            return
        d = InventoryDialog(self, self.i18n, row)
        self.wait_window(d)
        if not d.result:
            return
        v = d.result
        with connect_db() as conn:
            conn.execute(
                """UPDATE inventory SET name=?, category=?, quantity=?,
                    min_quantity=?, purchase_price=?, sale_price=?,
                    expiry_date=?, supplier=?, batch_number=?, notes=?
                   WHERE id=?""",
                (
                    v["name"],
                    v["category"],
                    v["quantity"],
                    v["min_quantity"],
                    v["purchase_price"],
                    v["sale_price"],
                    v["expiry_date"],
                    v["supplier"],
                    v["batch_number"],
                    v["notes"],
                    row["id"],
                ),
            )
        log_action("EDIT_ITEM", "inventory", row["id"])
        messagebox.showinfo(self.t("inventory"), self.t("updated"))
        self.load_inventory_table()

    def delete_item(self) -> None:
        row = self._selected_item()
        if row is None:
            return
        if not messagebox.askyesno(self.t("inventory"), self.t("confirm_delete")):
            return
        with connect_db() as conn:
            conn.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
        log_action("DELETE_ITEM", "inventory", row["id"])
        self.load_inventory_table()

    # ─────────────────────────────────────────────────────────────────
    #  BILLING
    # ─────────────────────────────────────────────────────────────────
    def render_billing(self) -> None:
        t = self.t
        toolbar = ttk.Frame(self.body)
        toolbar.pack(fill="x", pady=10)
        ttk.Button(toolbar, text="＋  " + t("new_invoice"), style="Primary.TButton", command=self.add_invoice).pack(side="right", padx=4)
        ttk.Button(toolbar, text=t("view_record"), command=self.view_invoice).pack(side="right", padx=4)
        ttk.Button(toolbar, text=t("delete"), command=self.delete_invoice).pack(side="right", padx=4)

        cols = ("id", "patient", "invoice_date", "total", "paid", "remaining", "status", "payment_method")
        self.invoice_table = ttk.Treeview(self.body, columns=cols, show="headings", selectmode="browse")
        heads = {
            "id": t("id"),
            "patient": t("patient"),
            "invoice_date": t("invoice_date"),
            "total": t("total"),
            "paid": t("paid"),
            "remaining": t("remaining"),
            "status": t("status"),
            "payment_method": t("payment_method"),
        }
        for c in cols:
            self.invoice_table.heading(c, text=heads[c])
            self.invoice_table.column(c, width=130, anchor="center")
        self.invoice_table.tag_configure("unpaid", background="#fdecea")
        self.invoice_table.tag_configure("partial", background="#fff4e5")
        self.invoice_table.tag_configure("paid", background="#eafaf0")
        self.invoice_table.pack(fill="both", expand=True)
        self.invoice_table.bind("<Double-1>", lambda _e: self.view_invoice())
        self.load_invoices_table()

    def load_invoices_table(self) -> None:
        if not hasattr(self, "invoice_table") or not self.invoice_table.winfo_exists():
            return
        self.invoice_table.delete(*self.invoice_table.get_children())
        with connect_db() as conn:
            rows = conn.execute(
                """SELECT i.id, p.full_name, i.invoice_date, i.total, i.paid,
                          (i.total - i.paid) AS remaining, i.status,
                          i.payment_method
                   FROM invoices i JOIN patients p ON p.id=i.patient_id
                   ORDER BY i.invoice_date DESC, i.id DESC"""
            ).fetchall()
        tag_map = {"Unpaid": "unpaid", "Partial": "partial", "Paid": "paid"}
        for r in rows:
            self.invoice_table.insert("", "end", iid=str(r["id"]), values=tuple(r), tags=(tag_map.get(r["status"], ""),))

    def add_invoice(self) -> None:
        with connect_db() as conn:
            if conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
                messagebox.showwarning(self.t("billing"), self.t("no_patients"))
                return
        d = InvoiceDialog(self, self.i18n)
        self.wait_window(d)
        if not d.result:
            return
        v = d.result
        remaining = v["total"] - v["paid"]
        if v["paid"] <= 0:
            status = "Unpaid"
        elif remaining <= 0:
            status = "Paid"
        else:
            status = "Partial"
        with connect_db() as conn:
            cur = conn.execute(
                """INSERT INTO invoices(patient_id, invoice_date, subtotal,
                    discount, tax, total, paid, status, payment_method,
                    notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?)""",
                (
                    v["patient_id"],
                    v["invoice_date"],
                    v["subtotal"],
                    v["discount"],
                    v["tax"],
                    v["total"],
                    v["paid"],
                    status,
                    v["payment_method"],
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            inv_id = cur.lastrowid
            conn.executemany(
                """INSERT INTO invoice_items(invoice_id, description,
                    quantity, unit_price, line_total)
                   VALUES (?, ?, ?, ?, ?)""",
                [(inv_id, d_, q, p, lt) for d_, q, p, lt in v["items"]],
            )
        log_action("ADD_INVOICE", "invoices", inv_id, f'{v["total"]:.2f} {self.cur}')
        messagebox.showinfo(self.t("billing"), self.t("invoice_saved"))
        self.load_invoices_table()

    def _selected_invoice(self) -> Optional[int]:
        s = self.invoice_table.selection()
        if not s:
            messagebox.showwarning(self.t("billing"), self.t("select_row"))
            return None
        return int(s[0])

    def view_invoice(self) -> None:
        inv_id = self._selected_invoice()
        if inv_id is None:
            return
        InvoiceDetailsDialog(self, self.i18n, inv_id)

    def delete_invoice(self) -> None:
        inv_id = self._selected_invoice()
        if inv_id is None:
            return
        if not messagebox.askyesno(self.t("billing"), self.t("confirm_delete")):
            return
        with connect_db() as conn:
            conn.execute("DELETE FROM invoice_items WHERE invoice_id=?", (inv_id,))
            conn.execute("DELETE FROM invoices WHERE id=?", (inv_id,))
        log_action("DELETE_INVOICE", "invoices", inv_id)
        self.load_invoices_table()

    # ─────────────────────────────────────────────────────────────────
    #  EXPENSES
    # ─────────────────────────────────────────────────────────────────
    def render_expenses(self) -> None:
        t = self.t
        toolbar = ttk.Frame(self.body)
        toolbar.pack(fill="x", pady=10)
        ttk.Button(toolbar, text="＋  " + t("add_expense"), style="Primary.TButton", command=self.add_expense).pack(side="right", padx=4)
        ttk.Button(toolbar, text=t("edit"), command=self.edit_expense).pack(side="right", padx=4)
        ttk.Button(toolbar, text=t("delete"), command=self.delete_expense).pack(side="right", padx=4)

        with connect_db() as conn:
            row = conn.execute(
                """SELECT
                       COALESCE((SELECT SUM(amount) FROM expenses), 0) AS total_all,
                       COALESCE((SELECT SUM(amount) FROM expenses
                                 WHERE expense_date >= date('now','-30 day')), 0) AS month_total"""
            ).fetchone()
        top = ttk.Frame(self.body)
        top.pack(fill="x", pady=8)
        self.stat_card(top, t("total_expenses") + " (30d)", f'{row["month_total"]:.2f} {self.cur}', COLORS["expenses"]).pack(side="left", fill="both", expand=True, padx=5)
        self.stat_card(top, "Total", f'{row["total_all"]:.2f} {self.cur}', COLORS["danger_dark"]).pack(side="left", fill="both", expand=True, padx=5)

        cols = ("id", "expense_date", "category", "description", "amount", "payment_method")
        self.expense_table = ttk.Treeview(self.body, columns=cols, show="headings", selectmode="browse")
        heads = {
            "id": t("id"),
            "expense_date": t("expense_date"),
            "category": t("expense_category"),
            "description": t("description"),
            "amount": f'{t("amount")} ({self.cur})',
            "payment_method": t("payment_method"),
        }
        for c in cols:
            self.expense_table.heading(c, text=heads[c])
            self.expense_table.column(c, width=160, anchor="center")
        self.expense_table.pack(fill="both", expand=True)
        self.load_expenses_table()

    def load_expenses_table(self) -> None:
        if not hasattr(self, "expense_table") or not self.expense_table.winfo_exists():
            return
        self.expense_table.delete(*self.expense_table.get_children())
        with connect_db() as conn:
            rows = conn.execute(
                """SELECT id, expense_date, category, description, amount,
                          payment_method
                   FROM expenses ORDER BY expense_date DESC, id DESC"""
            ).fetchall()
        for r in rows:
            self.expense_table.insert("", "end", iid=str(r["id"]), values=tuple(r))

    def add_expense(self) -> None:
        d = ExpenseDialog(self, self.i18n)
        self.wait_window(d)
        if not d.result:
            return
        v = d.result
        with connect_db() as conn:
            conn.execute(
                """INSERT INTO expenses(expense_date, category, description,
                    amount, payment_method, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    v["expense_date"],
                    v["category"],
                    v["description"],
                    v["amount"],
                    v["payment_method"],
                    v["notes"],
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        log_action("ADD_EXPENSE", "expenses", details=f'{v["amount"]:.2f} {self.cur}')
        messagebox.showinfo(self.t("expenses"), self.t("expense_saved"))
        self.load_expenses_table()

    def _selected_expense(self) -> Any:
        s = self.expense_table.selection()
        if not s:
            messagebox.showwarning(self.t("expenses"), self.t("select_row"))
            return None
        with connect_db() as conn:
            return conn.execute("SELECT * FROM expenses WHERE id=?", (int(s[0]),)).fetchone()

    def edit_expense(self) -> None:
        row = self._selected_expense()
        if row is None:
            return
        d = ExpenseDialog(self, self.i18n, row)
        self.wait_window(d)
        if not d.result:
            return
        v = d.result
        with connect_db() as conn:
            conn.execute(
                """UPDATE expenses SET expense_date=?, category=?,
                    description=?, amount=?, payment_method=?, notes=?
                   WHERE id=?""",
                (
                    v["expense_date"],
                    v["category"],
                    v["description"],
                    v["amount"],
                    v["payment_method"],
                    v["notes"],
                    row["id"],
                ),
            )
        log_action("EDIT_EXPENSE", "expenses", row["id"])
        messagebox.showinfo(self.t("expenses"), self.t("updated"))
        self.load_expenses_table()

    def delete_expense(self) -> None:
        row = self._selected_expense()
        if row is None:
            return
        if not messagebox.askyesno(self.t("expenses"), self.t("confirm_delete")):
            return
        with connect_db() as conn:
            conn.execute("DELETE FROM expenses WHERE id=?", (row["id"],))
        log_action("DELETE_EXPENSE", "expenses", row["id"])
        self.load_expenses_table()

    # ─────────────────────────────────────────────────────────────────
    #  REPORTS
    # ─────────────────────────────────────────────────────────────────
    def render_reports(self) -> None:
        t = self.t
        container = ttk.Frame(self.body)
        container.pack(fill="both", expand=True)

        filt = ttk.Frame(container)
        filt.pack(fill="x", pady=12)
        ttk.Label(filt, text=t("from_date") + ":").pack(side="left", padx=4)
        self.from_var = tk.StringVar(value=(date.today() - timedelta(days=30)).isoformat())
        ttk.Entry(filt, textvariable=self.from_var, width=14).pack(side="left", padx=4)
        ttk.Label(filt, text=t("to_date") + ":").pack(side="left", padx=4)
        self.to_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(filt, textvariable=self.to_var, width=14).pack(side="left", padx=4)
        ttk.Button(filt, text=t("filter"), style="Primary.TButton", command=self.refresh_reports).pack(side="left", padx=8)
        ttk.Button(filt, text="⬇ " + t("export_csv"), command=self.export_reports_csv).pack(side="right", padx=4)

        self.report_area = ttk.Frame(container)
        self.report_area.pack(fill="both", expand=True)
        self.refresh_reports()

    def refresh_reports(self) -> None:
        for w in self.report_area.winfo_children():
            w.destroy()
        t = self.t
        d1 = self.from_var.get().strip() or "1970-01-01"
        d2 = self.to_var.get().strip() or date.today().isoformat()

        with connect_db() as conn:
            summary = conn.execute(
                """SELECT
                       COALESCE((SELECT SUM(paid) FROM invoices
                                 WHERE invoice_date BETWEEN ? AND ?), 0) AS rev,
                       COALESCE((SELECT COUNT(*) FROM invoices
                                 WHERE invoice_date BETWEEN ? AND ?), 0) AS inv_cnt,
                       COALESCE((SELECT SUM(total - paid) FROM invoices
                                 WHERE total > paid
                                   AND invoice_date BETWEEN ? AND ?), 0) AS unpaid,
                       COALESCE((SELECT SUM(amount) FROM expenses
                                 WHERE expense_date BETWEEN ? AND ?), 0) AS exp,
                       (SELECT COUNT(*) FROM inventory
                        WHERE quantity <= min_quantity) AS low,
                       (SELECT COUNT(*) FROM inventory
                        WHERE expiry_date != '' AND expiry_date < ?) AS expd""",
                (d1, d2, d1, d2, d1, d2, d1, d2, date.today().isoformat()),
            ).fetchone()

            top_patients = conn.execute(
                """SELECT p.full_name, COUNT(a.id) c FROM patients p
                   LEFT JOIN appointments a ON a.patient_id=p.id
                   GROUP BY p.id ORDER BY c DESC LIMIT 5"""
            ).fetchall()
            by_cat = conn.execute(
                """SELECT category, COALESCE(SUM(amount),0) s FROM expenses
                   WHERE expense_date BETWEEN ? AND ? GROUP BY category""",
                (d1, d2),
            ).fetchall()

        net = summary["rev"] - summary["exp"]

        cards1 = ttk.Frame(self.report_area)
        cards1.pack(fill="x")
        self.stat_card(cards1, t("total_revenue"), f'{summary["rev"]:.2f} {self.cur}', COLORS["revenue"]).pack(side="left", fill="both", expand=True, padx=4)
        self.stat_card(cards1, t("total_expenses_month"), f'{summary["exp"]:.2f} {self.cur}', COLORS["expenses"]).pack(side="left", fill="both", expand=True, padx=4)
        self.stat_card(cards1, t("net_profit_month"), f"{net:.2f} {self.cur}", COLORS["revenue"] if net >= 0 else COLORS["danger_dark"]).pack(side="left", fill="both", expand=True, padx=4)

        cards2 = ttk.Frame(self.report_area)
        cards2.pack(fill="x", pady=12)
        self.stat_card(cards2, t("total_invoices"), summary["inv_cnt"]).pack(side="left", fill="both", expand=True, padx=4)
        self.stat_card(cards2, t("unpaid_amount"), f'{summary["unpaid"]:.2f} {self.cur}', COLORS["danger_dark"]).pack(side="left", fill="both", expand=True, padx=4)
        self.stat_card(cards2, t("low_stock_items"), summary["low"], COLORS["expenses"]).pack(side="left", fill="both", expand=True, padx=4)
        self.stat_card(cards2, t("expired_items"), summary["expd"], COLORS["danger_dark"]).pack(side="left", fill="both", expand=True, padx=4)

        ttk.Label(self.report_area, text=t("top_patients"), style="Section.TLabel").pack(anchor="w", pady=18)
        tree = ttk.Treeview(self.report_area, columns=("p", "c"), show="headings", height=5)
        tree.heading("p", text=t("patient"))
        tree.heading("c", text=t("appointments"))
        tree.column("p", width=300, anchor="w")
        tree.column("c", width=120, anchor="center")
        tree.pack(fill="x")
        for r in top_patients:
            tree.insert("", "end", values=(r["full_name"], r["c"]))

        ttk.Label(self.report_area, text=t("expense_category"), style="Section.TLabel").pack(anchor="w", pady=14)
        tree2 = ttk.Treeview(self.report_area, columns=("cat", "s"), show="headings", height=6)
        tree2.heading("cat", text=t("category"))
        tree2.heading("s", text=t("amount"))
        tree2.column("cat", width=300, anchor="w")
        tree2.column("s", width=150, anchor="center")
        tree2.pack(fill="x")
        cat_rev = {
            v: k
            for k, v in {
                t("cat_rent"): "Rent",
                t("cat_salary"): "Salary",
                t("cat_utilities"): "Utilities",
                t("cat_supplies"): "Supplies",
                t("cat_maintenance"): "Maintenance",
                t("cat_other"): "Other",
            }.items()
        }
        for r in by_cat:
            tree2.insert("", "end", values=(cat_rev.get(r["category"], r["category"]), f'{r["s"]:.2f} {self.cur}'))

    def export_reports_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"clinic_report_{date.today().isoformat()}.csv",
        )
        if not path:
            return
        d1 = self.from_var.get().strip() or "1970-01-01"
        d2 = self.to_var.get().strip() or date.today().isoformat()
        with connect_db() as conn, open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["Clinic Report", d1, "→", d2, f"Currency: {self.cur}"])
            w.writerow([])
            w.writerow(["Section", "Key", "Value"])
            row = conn.execute(
                """SELECT
                       COALESCE((SELECT SUM(paid) FROM invoices
                                 WHERE invoice_date BETWEEN ? AND ?), 0) AS rev,
                       COALESCE((SELECT SUM(amount) FROM expenses
                                 WHERE expense_date BETWEEN ? AND ?), 0) AS exp,
                       COALESCE((SELECT SUM(total - paid) FROM invoices
                                 WHERE total > paid), 0) AS unpaid""",
                (d1, d2, d1, d2),
            ).fetchone()
            w.writerow(["Summary", "Revenue", f'{row["rev"]:.2f}'])
            w.writerow(["Summary", "Expenses", f'{row["exp"]:.2f}'])
            w.writerow(["Summary", "NetProfit", f'{row["rev"] - row["exp"]:.2f}'])
            w.writerow(["Summary", "Unpaid", f'{row["unpaid"]:.2f}'])
            w.writerow([])
            w.writerow(["Invoices", "ID", "Patient", "Date", "Total", "Paid", "Status"])
            for r in conn.execute(
                """SELECT i.id, p.full_name, i.invoice_date, i.total, i.paid, i.status
                   FROM invoices i JOIN patients p ON p.id=i.patient_id
                   WHERE i.invoice_date BETWEEN ? AND ?""",
                (d1, d2),
            ).fetchall():
                w.writerow(["Invoice", r["id"], r["full_name"], r["invoice_date"], r["total"], r["paid"], r["status"]])
            w.writerow([])
            w.writerow(["Expenses", "ID", "Date", "Category", "Description", "Amount"])
            for r in conn.execute(
                """SELECT id, expense_date, category, description, amount
                   FROM expenses WHERE expense_date BETWEEN ? AND ?""",
                (d1, d2),
            ).fetchall():
                w.writerow(["Expense", r["id"], r["expense_date"], r["category"], r["description"], r["amount"]])
            w.writerow([])
            w.writerow(["Inventory", "Name", "Category", "Qty", "Min", "Expiry", "SalePrice"])
            for r in conn.execute(
                """SELECT name, category, quantity, min_quantity, expiry_date, sale_price
                   FROM inventory"""
            ).fetchall():
                w.writerow(["Item", r["name"], r["category"], r["quantity"], r["min_quantity"], r["expiry_date"], r["sale_price"]])
        log_action("EXPORT_REPORT", "reports")
        messagebox.showinfo(self.t("reports"), self.t("exported"))

    # ─────────────────────────────────────────────────────────────────
    #  SETTINGS
    # ─────────────────────────────────────────────────────────────────
    def render_settings(self) -> None:
        t = self.t
        frame = ttk.Frame(self.body, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=t("settings_title"), style="Title.TLabel").pack(anchor="w", pady=18)

        card = ttk.Frame(frame, style="Card.TFrame", padding=18)
        card.pack(fill="x", pady=6)
        ttk.Label(card, text=t("change_language"), style="Section.TLabel").pack(anchor="w", pady=10)
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(anchor="w")
        for code, label in (("ar", "العربية"), ("en", "English"), ("fr", "Français")):
            b = ttk.Button(row, text=label, style="Ghost.TButton", command=lambda c=code: self.set_language(c), width=14)
            b.pack(side="left", padx=4)
            if code == self.i18n.lang:
                b.configure(style="Primary.TButton")

        card2 = ttk.Frame(frame, style="Card.TFrame", padding=18)
        card2.pack(fill="x", pady=6)
        ttk.Label(card2, text=t("backup_db"), style="Section.TLabel").pack(anchor="w", pady=10)
        ttk.Button(card2, text="💾 " + t("backup_db"), style="Primary.TButton", command=self.backup_database).pack(anchor="w")

        card3 = ttk.Frame(frame, style="Card.TFrame", padding=18)
        card3.pack(fill="x", pady=6)
        ttk.Label(card3, text="ℹ️  System Information", style="Section.TLabel").pack(anchor="w", pady=10)
        db_size = os.path.getsize(DB_FILE) if os.path.exists(DB_FILE) else 0
        for k, v in (("App", t(APP_TITLE_KEY)), ("Currency", self.cur), ("DB Size", f"{db_size / 1024:.1f} KB"), ("Version", DEV_VERSION)):
            ttk.Label(card3, text=f"{k}: {v}", style="CardTitle.TLabel").pack(anchor="w", pady=2)

    def backup_database(self) -> None:
        if not os.path.exists(DB_FILE):
            messagebox.showerror(self.t("settings"), f"Database file not found: {DB_FILE}")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db")],
            initialfile=f"clinic_backup_{date.today().isoformat()}.db",
        )
        if not path:
            return
        try:
            shutil.copy2(DB_FILE, path)
            log_action("BACKUP_DB", "settings", details=path)
            messagebox.showinfo(self.t("settings"), self.t("backup_done"))
        except Exception as exc:  # pragma: no cover
            messagebox.showerror(self.t("settings"), str(exc))


# ═══════════════════════════════════════════════════════════════════
#  8. Login window
# ═══════════════════════════════════════════════════════════════════

class LoginWindow(tk.Tk):
    def __init__(self, lang: str = "ar") -> None:
        _reset_image_cache()
        super().__init__()
        self.i18n = I18N(lang)               # ✅ اللغة من البداية
        self.authenticated = False
        self._lang_popup_handler: Optional[LanguagePopup] = None
        self.title(self.i18n.t("login_title"))
        self.geometry("460x780")
        self.resizable(False, False)
        self.configure(bg=COLORS["sidebar"])

        load_icon(self)
        patch_toplevel_icon()

        self._center()
        self._setup_styles()
        self.build_ui()

    def _center(self) -> None:
        self.update_idletasks()
        w, h = 460, 780
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{max(0, (sh - h) // 2)}")

    def _setup_styles(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Login.TFrame", background=COLORS["card"])
        s.configure("Login.TLabel", background=COLORS["card"], foreground=COLORS["text"], font=("Segoe UI", 10))
        s.configure("LoginTitle.TLabel", background=COLORS["card"], foreground=COLORS["sidebar"], font=("Segoe UI", 20, "bold"))
        s.configure("LoginSub.TLabel", background=COLORS["card"], foreground=COLORS["text_muted"], font=("Segoe UI", 9))
        s.configure("Login.TButton", background=COLORS["primary"], foreground="#ffffff", padding=(10, 10), borderwidth=0, font=("Segoe UI", 11, "bold"))
        s.map("Login.TButton", background=[("active", COLORS["primary_dark"])])
        s.configure("Ghost.TButton", background="#eaf1f8", foreground=COLORS["sidebar"], padding=(10, 9), borderwidth=0, font=("Segoe UI", 10))
        s.map("Ghost.TButton", background=[("active", "#d8e5f2")])

    def t(self, key: str) -> str:
        return self.i18n.t(key)

    def build_ui(self) -> None:
        # ✅ تحديث العنوان في كل مرة تُعاد بناء الواجهة
        self.title(self.t("login_title"))

        for w in self.winfo_children():
            w.destroy()

        header = tk.Frame(self, bg=COLORS["sidebar"], height=170)
        header.pack(fill="x")
        header.pack_propagate(False)

        logo = get_logo_photo(size=84, bg=COLORS["sidebar"])
        if logo:
            lbl = tk.Label(header, image=logo, bg=COLORS["sidebar"])
            lbl.image = logo  # type: ignore[attr-defined]
            lbl.pack(pady=8)
        else:
            tk.Label(header, text="✚", bg=COLORS["sidebar"], fg="#20b2aa", font=("Segoe UI", 34, "bold")).pack(pady=8)

        tk.Label(header, text=self.t("clinic_name"), bg=COLORS["sidebar"], fg="white", font=("Segoe UI", 15, "bold")).pack()
        tk.Label(header, text="Clinic Management System", bg=COLORS["sidebar"], fg="#8fa8bf", font=("Segoe UI", 9)).pack()

        card = ttk.Frame(self, style="Login.TFrame", padding=28)
        card.pack(fill="both", expand=True, padx=22, pady=18)

        ttk.Label(card, text=self.t("login_title"), style="LoginTitle.TLabel").pack(anchor="w")
        ttk.Label(card, text=self.t("login_subtitle"), style="LoginSub.TLabel", wraplength=330).pack(anchor="w", pady=(4, 18))

        ttk.Label(card, text=self.t("username"), style="Login.TLabel").pack(anchor="w")
        self.user_var = tk.StringVar()
        user_entry = ttk.Entry(card, textvariable=self.user_var, width=34)
        user_entry.pack(fill="x", ipady=7, pady=(4, 12))

        ttk.Label(card, text=self.t("password"), style="Login.TLabel").pack(anchor="w")
        self.pass_var = tk.StringVar()
        self.pass_entry = ttk.Entry(card, textvariable=self.pass_var, width=34, show="●")
        self.pass_entry.pack(fill="x", ipady=7, pady=(4, 6))

        self.show_pass_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, text=self.t("show_password"), variable=self.show_pass_var, command=self.toggle_password).pack(anchor="w", pady=(0, 14))

        ttk.Button(card, text="→  " + self.t("login"), style="Login.TButton", command=self.attempt_login).pack(fill="x", pady=(0, 6))
        ttk.Button(card, text=self.t("exit"), style="Ghost.TButton", command=self.destroy).pack(fill="x")

        self.lang_btn = tk.Button(
            card,
            text="🌐   " + LANG_LABELS.get(self.i18n.lang, "Language"),
            relief="flat",
            bg="#eaf1f8",
            fg=COLORS["sidebar"],
            activebackground=COLORS["primary"],
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            pady=9,
            cursor="hand2",
            command=self._open_language_menu,
        )
        self.lang_btn.pack(fill="x", pady=10)

        self.status = ttk.Label(card, text="", style="Login.TLabel", foreground=COLORS["danger_dark"], wraplength=330)
        self.status.pack(anchor="w", pady=8)

        self.dev_btn = make_dev_button(card, self._open_about_dev)
        self.dev_btn.pack(fill="x", pady=(10, 0))

        user_entry.focus_set()
        self.bind("<Return>", lambda _e: self.attempt_login())

    def toggle_password(self) -> None:
        self.pass_entry.configure(show="" if self.show_pass_var.get() else "●")

    def _open_language_menu(self) -> None:
        self._lang_popup_handler = LanguagePopup(self, self.i18n, self.lang_btn, self.set_language)
        self._lang_popup_handler.open()

    def _open_about_dev(self) -> None:
        AboutDevDialog(self, self.i18n)

    def close_language_menu(self) -> None:
        if self._lang_popup_handler:
            self._lang_popup_handler.close()
        self._lang_popup_handler = None

    def set_language(self, code: str) -> None:
        self.close_language_menu()
        self.i18n.set(code)
        self.build_ui()                     # ✅ العنوان يُحدَّث داخل build_ui

    def attempt_login(self) -> None:
        self.close_language_menu()
        user = self.user_var.get().strip()
        pwd = self.pass_var.get().strip()
        if not user or not pwd:
            self.status.configure(text=self.t("login_empty"))
            return
        if user == LOGIN_USERNAME and pwd == LOGIN_PASSWORD:
            self.authenticated = True
            self.destroy()
        else:
            self.status.configure(text=self.t("login_error"))
            self.pass_var.set("")
            self.pass_entry.focus_set()


# ═══════════════════════════════════════════════════════════════════
#  9. Entry point
# ═══════════════════════════════════════════════════════════════════

def main() -> None:
    init_db()
    lang = "ar"
    while True:
        login = LoginWindow(lang=lang)
        login.mainloop()
        if not login.authenticated:
            raise SystemExit(0)
        lang = login.i18n.lang
        app = ClinicApp(lang=lang)
        app.mainloop()

if __name__ == "__main__":
    main()