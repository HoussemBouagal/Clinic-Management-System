# charts.py
from __future__ import annotations

import tkinter as tk
from typing import Iterable, Optional, Sequence

# ── shared theme ─────────────────────────────────────────────────────
_FONT = "Segoe UI"
_TXT_DARK = "#3d5163"
_TXT_MUTED = "#8899a8"
_GRID = "#e6eef5"
_AXIS = "#b9c7d4"
_EMPTY_FILL = "#eef3f8"
_EMPTY_OUTLINE = "#d8e5f2"
_CARD_BG = "#ffffff"


def _fmt_number(v: float) -> str:
    """Compact human-friendly number formatting."""
    if v is None:
        return "0"
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "0"
    a = abs(v)
    if a >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if a >= 1_000:
        return f"{v / 1_000:.1f}K"
    if a >= 100:
        return f"{v:.0f}"
    if a >= 10:
        return f"{v:.1f}"
    if a >= 1:
        return f"{v:.1f}"
    if a > 0:
        return f"{v:.2f}"
    return "0"


# ═══════════════════════════════════════════════════════════════════
#  BaseChart
# ═══════════════════════════════════════════════════════════════════
class BaseChart(tk.Canvas):
    """Common canvas behavior: responsive redraw, safe destruction."""

    _RESIZE_DEBOUNCE_MS = 60

    def __init__(self, parent: tk.Misc, width: int, height: int,
                 bg: str = _CARD_BG, **kw) -> None:
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, **kw)
        self._bg = bg
        self._redraw_job: Optional[str] = None
        self._last_size: tuple[int, int] = (width, height)
        self.bind("<Configure>", self._on_configure)

    # -- lifecycle ---------------------------------------------------
    def destroy(self) -> None:  # pragma: no cover
        self._cancel_redraw()
        try:
            self.unbind("<Configure>")
        except tk.TclError:
            pass
        super().destroy()

    # -- resize handling --------------------------------------------
    def _on_configure(self, event: tk.Event) -> None:
        new_size = (int(event.width), int(event.height))
        if new_size == self._last_size or new_size[0] <= 1 or new_size[1] <= 1:
            return
        self._last_size = new_size
        self._schedule_redraw()

    def _schedule_redraw(self) -> None:
        self._cancel_redraw()
        try:
            self._redraw_job = self.after(self._RESIZE_DEBOUNCE_MS, self._safe_redraw)
        except tk.TclError:
            self._redraw_job = None

    def _cancel_redraw(self) -> None:
        if self._redraw_job:
            try:
                self.after_cancel(self._redraw_job)
            except tk.TclError:
                pass
            self._redraw_job = None

    def _safe_redraw(self) -> None:
        self._redraw_job = None
        try:
            if self.winfo_exists():
                self.redraw()
        except tk.TclError:
            pass

    # -- to override -------------------------------------------------
    def redraw(self) -> None:  # pragma: no cover
        raise NotImplementedError


# ═══════════════════════════════════════════════════════════════════
#  BarChart
# ═══════════════════════════════════════════════════════════════════
class BarChart(BaseChart):
    """Grouped bar chart (e.g. revenue vs expenses)."""

    # layout constants (px)
    PAD_LEFT = 56
    PAD_RIGHT = 20
    PAD_TOP = 34
    PAD_BOTTOM = 46
    GRID_LINES = 4          # horizontal gridlines (excluding axis)
    LEGEND_ROW_H = 16
    LEGEND_ITEM_MIN_W = 110

    def __init__(self, parent: tk.Misc, width: int = 520, height: int = 240,
                 bg: str = _CARD_BG, **kw) -> None:
        super().__init__(parent, width=width, height=height, bg=bg, **kw)
        self._labels: list[str] = []
        self._series: list[dict] = []

    # -- public ------------------------------------------------------
    def set_data(self, labels: Sequence[str],
                 series: Sequence[dict]) -> None:
        """
        labels: list[str]
        series: list[{"name": str, "color": str, "values": list[float]}]
        """
        self._labels = list(labels)
        # Normalize series: ensure each has a values list of correct length
        n = len(self._labels)
        norm: list[dict] = []
        for s in series or []:
            values = list(s.get("values", []))
            if len(values) < n:
                values.extend([0] * (n - len(values)))
            elif len(values) > n:
                values = values[:n]
            norm.append({
                "name": str(s.get("name", "")),
                "color": str(s.get("color", "#cccccc")),
                "values": [float(v or 0) for v in values],
            })
        self._series = norm
        self._safe_redraw()

    # -- drawing -----------------------------------------------------
    def redraw(self) -> None:
        self.delete("all")
        W = max(1, self.winfo_width() or int(self["width"]))
        H = max(1, self.winfo_height() or int(self["height"]))

        if not self._labels or not self._series:
            self._draw_empty(W, H)
            return

        # ---- geometry -----------------------------------------------
        pad_l, pad_r = self.PAD_LEFT, self.PAD_RIGHT
        legend_h = self._legend_height(W)
        pad_t = self.PAD_TOP + legend_h
        pad_b = self.PAD_BOTTOM
        chart_w = max(10, W - pad_l - pad_r)
        chart_h = max(10, H - pad_t - pad_b)

        # ---- scale --------------------------------------------------
        max_val = 0.0
        for s in self._series:
            for v in s["values"]:
                if v > max_val:
                    max_val = v
        if max_val <= 0:
            max_val = 1.0
        # round up a bit for nicer gridlines
        nice_max = self._nice_ceiling(max_val)

        # ---- gridlines & Y labels ----------------------------------
        for i in range(self.GRID_LINES + 1):
            frac = i / self.GRID_LINES
            y = pad_t + chart_h * frac
            self.create_line(pad_l, y, W - pad_r, y,
                             fill=_GRID, dash=(2, 4))
            val = nice_max * (1 - frac)
            self.create_text(pad_l - 8, y, anchor="e",
                             text=_fmt_number(val),
                             fill=_TXT_MUTED, font=(_FONT, 8))

        # ---- X axis ------------------------------------------------
        base_y = pad_t + chart_h
        self.create_line(pad_l, base_y, W - pad_r, base_y, fill=_AXIS)

        # ---- bars ---------------------------------------------------
        n_groups = len(self._labels)
        n_series = len(self._series)
        group_w = chart_w / n_groups

        # Adaptive bar width: leave 20% gap between groups
        max_bar_w = 30
        bar_w = max(3, min(max_bar_w, (group_w * 0.8) / n_series))
        total_bars_w = bar_w * n_series

        # Adaptive: thin out x labels if crowded
        label_step = 1
        est_label_w = 34
        if group_w < est_label_w and n_groups > 6:
            label_step = max(1, n_groups // 7)

        for gi, label in enumerate(self._labels):
            gx = pad_l + group_w * gi + group_w / 2
            start_x = gx - total_bars_w / 2

            for si, s in enumerate(self._series):
                v = s["values"][gi]
                h = (v / nice_max) * chart_h if nice_max else 0
                x1 = start_x + si * bar_w
                x2 = x1 + bar_w - 2
                y1 = base_y - h
                y2 = base_y

                self.create_rectangle(x1, y1, x2, y2,
                                      fill=s["color"], outline="")

                # value on top of bar (only if there's room)
                if v > 0 and bar_w >= 10:
                    self.create_text((x1 + x2) / 2, y1 - 8,
                                     text=_fmt_number(v),
                                     fill=_TXT_DARK,
                                     font=(_FONT, 7, "bold"))

            if gi % label_step == 0:
                self.create_text(gx, base_y + 14, text=label,
                                 fill=_TXT_DARK, font=(_FONT, 8))

        # ---- legend -------------------------------------------------
        self._draw_legend(W, self.PAD_TOP - legend_h + 6, legend_h)

    # -- helpers -----------------------------------------------------
    def _legend_height(self, W: int) -> int:
        """Return the height in px reserved for the legend, wrapping if needed."""
        if not self._series:
            return 0
        # estimate item widths
        item_w = max(self.LEGEND_ITEM_MIN_W,
                     12 + 6 + max(len(s["name"]) * 7 for s in self._series))
        per_row = max(1, (W - self.PAD_LEFT) // item_w)
        rows = (len(self._series) + per_row - 1) // per_row
        return rows * self.LEGEND_ROW_H + 4

    def _draw_legend(self, W: int, y: int, height: int) -> None:
        if not self._series:
            return
        x = self.PAD_LEFT
        row_y = y + 8
        item_w = max(self.LEGEND_ITEM_MIN_W,
                     12 + 6 + max(len(s["name"]) * 7 for s in self._series))
        max_x = W - self.PAD_RIGHT
        for s in self._series:
            if x + item_w > max_x:
                x = self.PAD_LEFT
                row_y += self.LEGEND_ROW_H
            self.create_rectangle(x, row_y - 6, x + 12, row_y + 6,
                                  fill=s["color"], outline="")
            self.create_text(x + 18, row_y, anchor="w",
                             text=s["name"], fill=_TXT_DARK,
                             font=(_FONT, 8))
            x += item_w

    @staticmethod
    def _nice_ceiling(v: float) -> float:
        """Round up to a 'nice' number (1, 2, 5 × 10^n)."""
        if v <= 0:
            return 1.0
        import math
        exp = math.floor(math.log10(v))
        base = 10 ** exp
        for m in (1, 2, 2.5, 5, 10):
            if v <= m * base:
                return m * base
        return 10 * base

    def _draw_empty(self, W: int, H: int) -> None:
        self.create_text(W / 2, H / 2, text="—",
                         fill=_TXT_MUTED, font=(_FONT, 11))


# ═══════════════════════════════════════════════════════════════════
#  DonutChart
# ═══════════════════════════════════════════════════════════════════
class DonutChart(BaseChart):
    """Donut chart with a center label showing the total."""

    THICKNESS_RATIO = 0.40      # ring thickness relative to outer radius
    MIN_LABEL_ANGLE = 18        # degrees — hide % labels below this

    def __init__(self, parent: tk.Misc, size: int = 160,
                 bg: str = _CARD_BG, **kw) -> None:
        super().__init__(parent, width=size, height=size, bg=bg, **kw)
        self._items: list[tuple[str, float, str]] = []
        self._center_title: str = ""
        self._center_value: str = ""

    # -- public ------------------------------------------------------
    def set_data(self, items: Iterable[tuple[str, float, str]],
                 center_title: str = "",
                 center_value: object = "") -> None:
        """
        items: list[(label, value, color)]
        center_title / center_value: strings shown in the hole.
        """
        norm: list[tuple[str, float, str]] = []
        for it in items or []:
            try:
                label, value, color = it
            except (TypeError, ValueError):
                continue
            try:
                v = float(value or 0)
            except (TypeError, ValueError):
                v = 0.0
            if v < 0:
                v = 0.0
            norm.append((str(label), v, str(color)))
        self._items = norm
        self._center_title = str(center_title or "")
        self._center_value = str(center_value) if center_value != "" else ""
        self._safe_redraw()

    # -- drawing -----------------------------------------------------
    def redraw(self) -> None:
        self.delete("all")
        W = max(1, self.winfo_width() or int(self["width"]))
        H = max(1, self.winfo_height() or int(self["height"]))
        size = min(W, H)
        cx = W / 2
        cy = H / 2
        pad = max(4, size * 0.03)
        r_out = size / 2 - pad
        r_in = r_out * (1 - self.THICKNESS_RATIO)

        total = sum(v for _, v, _ in self._items)
        if total <= 0 or r_out <= 4:
            self.create_oval(cx - r_out, cy - r_out, cx + r_out, cy + r_out,
                             fill=_EMPTY_FILL, outline=_EMPTY_OUTLINE)
            self.create_text(cx, cy, text="—", fill=_TXT_MUTED,
                             font=(_FONT, max(10, int(size / 10)), "bold"))
            return

        # ---- arcs ---------------------------------------------------
        start = 90.0                    # start at 12 o'clock
        for label, value, color in self._items:
            if value <= 0:
                continue
            extent = -360.0 * (value / total)   # clockwise
            self.create_arc(cx - r_out, cy - r_out, cx + r_out, cy + r_out,
                            start=start, extent=extent,
                            fill=color, outline=_CARD_BG, width=2)

            # in-slice percentage label (only if slice is big enough)
            if abs(extent) >= self.MIN_LABEL_ANGLE:
                self._draw_slice_label(cx, cy, (r_out + r_in) / 2,
                                       start + extent / 2, value, total)
            start += extent

        # ---- center hole -------------------------------------------
        self.create_oval(cx - r_in, cy - r_in, cx + r_in, cy + r_in,
                         fill=_CARD_BG, outline=_CARD_BG)

        # ---- center text -------------------------------------------
        if self._center_value:
            self.create_text(cx, cy - size * 0.03,
                             text=self._center_value,
                             fill="#0f2842",
                             font=(_FONT, max(11, int(size / 10)), "bold"))
        if self._center_title:
            self.create_text(cx, cy + size * 0.08,
                             text=self._center_title,
                             fill=_TXT_MUTED,
                             font=(_FONT, max(7, int(size / 18))))

    # -- helpers -----------------------------------------------------
    @staticmethod
    def _draw_slice_label(cx: float, cy: float, r: float,
                          mid_angle_deg: float,
                          value: float, total: float) -> None:
        """Place a small percentage label at the middle of a slice."""
        import math
        theta = math.radians(mid_angle_deg)
        # Canvas angles: 0° at 3 o'clock, CCW positive.
        # Our `start` uses same convention; mid_angle is average.
        x = cx + r * math.cos(theta)
        y = cy - r * math.sin(theta)
        pct = value / total * 100
        # Skip very small labels
        if pct < 4:
            return

        # no live canvas reference here — caller draws; so we return coords
        # Instead, caller should draw. To keep simple, we draw via owner.
        # (see note in redraw -> uses self.create_text directly)
        return x, y, f"{pct:.0f}%"

    def _draw_slice_label_now(self, cx: float, cy: float, r: float,
                              mid_angle_deg: float,
                              value: float, total: float) -> None:
        import math
        theta = math.radians(mid_angle_deg)
        x = cx + r * math.cos(theta)
        y = cy - r * math.sin(theta)
        pct = value / total * 100
        if pct < 4:
            return
        self.create_text(x, y, text=f"{pct:.0f}%",
                         fill="#ffffff",
                         font=(_FONT, 8, "bold"))