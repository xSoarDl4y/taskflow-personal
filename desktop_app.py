import os
import queue
import re
import threading
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import ttk, messagebox

import requests
from dotenv import load_dotenv

load_dotenv()
API = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

# ── Bảng màu (đồng bộ với bản web) ────────────────────────────
INK = "#0F1B33"
INK_2 = "#1B2A4A"
GOLD = "#B8893B"
GOLD_2 = "#D9B368"
GOLD_SOFT = "#F3E8CF"
IVORY = "#F6F3EC"
CARD = "#FFFFFF"
LINE = "#E7E1D3"
MUTED = "#6B7385"
OK = "#2F7D5B"
DANGER = "#B83A3A"
SIDE_TEXT = "#E9E4D6"
NAV_ACTIVE = "#26396A"
NAV_HOVER = "#17284F"
TRACK = "#EFE9DA"

SANS = "Segoe UI"
SERIF = "Georgia"

PRIORITY_LABEL = {"low": "Thấp", "medium": "Trung bình", "high": "Cao"}
PRIORITY_VALUE = {v: k for k, v in PRIORITY_LABEL.items()}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
FILTERS = ["Tất cả", "Đang làm", "Hoàn thành"]
WEEKDAYS = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
NAV = [
    ("overview", "◈   Tổng quan"),
    ("tasks", "☰   Công việc"),
    ("calendar", "▦   Lịch"),
    ("ai", "✦   Trợ lý AI"),
]


def parse_due(text):
    """Nhận yyyy-mm-dd hoặc dd/mm/yyyy, trả về ISO hoặc None. Sai định dạng -> ValueError."""
    text = text.strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Ngày cần có dạng dd/mm/yyyy hoặc yyyy-mm-dd.")


def fmt_date(iso):
    try:
        return date.fromisoformat(iso).strftime("%d/%m/%Y")
    except Exception:
        return iso or "—"


class TaskFlowDesktop:
    def __init__(self, root):
        self.root = root
        self.root.title("TaskFlow Personal")
        self.root.geometry("1180x740")
        self.root.minsize(980, 640)
        self.root.configure(bg=IVORY)
        self.token = ""
        self.email = ""
        self.tasks = []
        self.page = "overview"
        self.content = None
        self.nav_items = {}
        self.stat_labels = {}
        self.cal_date = date.today()
        self.last_plan = ""
        self.hours_var = tk.DoubleVar(value=3.0)
        self.setup_style()
        self.show_login()

    # ── Style ─────────────────────────────────────────────────
    def setup_style(self):
        s = self.style = ttk.Style()
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass

        s.configure("TFrame", background=IVORY)
        s.configure("TLabel", background=IVORY, foreground=INK, font=(SANS, 10))

        s.configure(
            "Field.TEntry", fieldbackground=CARD, foreground=INK, bordercolor=LINE,
            lightcolor=LINE, darkcolor=LINE, padding=8, relief="flat",
        )
        s.map("Field.TEntry", bordercolor=[("focus", GOLD)], lightcolor=[("focus", GOLD)], darkcolor=[("focus", GOLD)])

        s.configure(
            "Field.TCombobox", fieldbackground=CARD, background=CARD, foreground=INK,
            bordercolor=LINE, lightcolor=LINE, darkcolor=LINE, arrowcolor=GOLD, padding=7,
        )
        s.map(
            "Field.TCombobox",
            bordercolor=[("focus", GOLD)], fieldbackground=[("readonly", CARD)],
            foreground=[("readonly", INK)], selectbackground=[("readonly", CARD)],
            selectforeground=[("readonly", INK)],
        )
        self.root.option_add("*TCombobox*Listbox.font", (SANS, 10))
        self.root.option_add("*TCombobox*Listbox.selectBackground", GOLD)

        s.configure(
            "Treeview", background=CARD, fieldbackground=CARD, foreground=INK,
            rowheight=38, borderwidth=0, font=(SANS, 10),
        )
        s.configure(
            "Treeview.Heading", background=INK, foreground="#F3E8CF",
            font=(SANS, 9, "bold"), relief="flat", padding=(10, 9),
        )
        s.map("Treeview.Heading", background=[("active", INK_2)])

        # Sửa lỗi màu tag của Treeview trên một số bản Tk 8.6
        def fixed_map(option):
            return [e for e in s.map("Treeview", query_opt=option) if e[:2] != ("!disabled", "!selected")]

        s.map("Treeview", foreground=fixed_map("foreground"), background=fixed_map("background"))
        s.map("Treeview", background=[("selected", GOLD_SOFT)], foreground=[("selected", INK)])

        s.configure(
            "Vertical.TScrollbar", background=LINE, troughcolor=IVORY, bordercolor=IVORY,
            arrowcolor=MUTED, relief="flat",
        )

    # ── Widget tiện ích ───────────────────────────────────────
    def button(self, parent, text, command, kind="primary", width=None):
        palette = {
            "primary": (GOLD, "#FFFFFF", "#A27730"),
            "ghost": (CARD, INK, GOLD_SOFT),
            "danger": (CARD, DANGER, "#FBEAEA"),
            "side": (INK_2, SIDE_TEXT, NAV_ACTIVE),
        }
        bg, fg, hover = palette[kind]
        b = tk.Button(
            parent, text=text, command=command, bg=bg, fg=fg, activebackground=hover,
            activeforeground=fg, relief="flat", bd=0, cursor="hand2",
            font=(SANS, 10, "bold"), padx=16, pady=9, width=width or 0,
            highlightthickness=1 if kind in ("ghost", "danger") else 0, highlightbackground=LINE,
            disabledforeground="#C9C3B2",
        )
        b.bind("<Enter>", lambda _e: b.configure(bg=hover) if str(b["state"]) != "disabled" else None)
        b.bind("<Leave>", lambda _e: b.configure(bg=bg))
        return b

    def field_label(self, parent, text, bg=IVORY):
        return tk.Label(parent, text=text.upper(), bg=bg, fg=MUTED, font=(SANS, 8, "bold"))

    def page_head(self, eyebrow, title, subtitle):
        head = tk.Frame(self.content, bg=IVORY)
        head.grid(row=0, column=0, sticky="ew")
        tk.Label(head, text=eyebrow.upper(), bg=IVORY, fg=GOLD, font=(SANS, 8, "bold")).pack(anchor="w")
        tk.Label(head, text=title, bg=IVORY, fg=INK, font=(SERIF, 22, "bold")).pack(anchor="w")
        tk.Label(head, text=subtitle, bg=IVORY, fg=MUTED, font=(SANS, 10)).pack(anchor="w")

    def section(self, parent, text, row, pady=(0, 8)):
        f = tk.Frame(parent, bg=IVORY)
        f.grid(row=row, column=0, sticky="ew", pady=pady)
        tk.Frame(f, bg=GOLD, width=4, height=18).pack(side="left")
        label = tk.Label(f, text=text, bg=IVORY, fg=INK, font=(SERIF, 13, "bold"))
        label.pack(side="left", padx=8)
        return label

    def make_tree(self, parent, cols, height=8):
        """cols: [(id, nhãn, rộng, co giãn)]"""
        wrap = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=LINE)
        wrap.columnconfigure(0, weight=1)
        wrap.rowconfigure(0, weight=1)
        tree = ttk.Treeview(wrap, columns=[c[0] for c in cols], show="headings", selectmode="browse", height=height)
        for cid, label, width, stretch in cols:
            tree.heading(cid, text=label.upper())
            tree.column(cid, width=width, anchor="w", stretch=stretch)
        tree.tag_configure("even", background=CARD)
        tree.tag_configure("odd", background="#FBF9F4")
        tree.tag_configure("overdue", background="#FDF0F0", foreground=DANGER)
        tree.tag_configure("done", background=CARD, foreground="#98A0AF")
        scroll = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        return wrap, tree

    def row_info(self, t, i, today):
        if t["completed"]:
            tag = "done"
        elif t["due_date"] and t["due_date"] < today:
            tag = "overdue"
        else:
            tag = "odd" if i % 2 else "even"
        status = "✓ Hoàn thành" if t["completed"] else ("Quá hạn" if tag == "overdue" else "Đang làm")
        return tag, status

    def fill_tree(self, tree, tasks):
        today = date.today().isoformat()
        columns = tree["columns"]
        selected = tree.selection()
        for item in tree.get_children():
            tree.delete(item)
        for i, t in enumerate(tasks):
            tag, status = self.row_info(t, i, today)
            cells = {
                "title": t["title"],
                "due": fmt_date(t["due_date"]) if t["due_date"] else "—",
                "priority": PRIORITY_LABEL.get(t["priority"], t["priority"]),
                "status": status,
            }
            tree.insert("", "end", iid=str(t["id"]), values=[cells[c] for c in columns], tags=(tag,))
        if selected and tree.exists(selected[0]):
            tree.selection_set(selected[0])

    # ── Giao tiếp API ─────────────────────────────────────────
    def call(self, method, path, **kwargs):
        """Gọi API, không hiện hộp thoại. Trả về (dữ liệu, thông báo lỗi)."""
        headers = kwargs.pop("headers", {})
        timeout = kwargs.pop("timeout", 15)
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            r = requests.request(method, API + path, headers=headers, timeout=timeout, **kwargs)
        except requests.RequestException as exc:
            return None, f"Không kết nối được backend {API}\n{exc}"
        if r.status_code >= 400:
            try:
                msg = r.json().get("detail", r.text)
            except Exception:
                msg = r.text
            return None, str(msg)
        try:
            return (r.json() if r.content else {}), None
        except ValueError:
            return {}, None

    def request(self, method, path, **kwargs):
        data, err = self.call(method, path, **kwargs)
        if err:
            messagebox.showerror("TaskFlow", err)
            return None
        return data

    def run_async(self, work, done):
        """Chạy work() ở luồng nền, gọi done(kết_quả) trên luồng giao diện."""
        q = queue.Queue()
        threading.Thread(target=lambda: q.put(work()), daemon=True).start()

        def poll():
            try:
                res = q.get_nowait()
            except queue.Empty:
                self.root.after(100, poll)
                return
            done(res)

        self.root.after(100, poll)

    def clear(self):
        for child in self.root.winfo_children():
            child.destroy()
        self.root.unbind("<Return>")
        self.content = None

    # ── Màn hình đăng nhập ────────────────────────────────────
    def show_login(self):
        self.clear()
        self.root.columnconfigure(0, weight=5, uniform="login", minsize=0)
        self.root.columnconfigure(1, weight=6, uniform="login", minsize=0)
        self.root.rowconfigure(0, weight=1)

        hero = tk.Frame(self.root, bg=INK)
        hero.grid(row=0, column=0, sticky="nsew")
        inner = tk.Frame(hero, bg=INK)
        inner.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(inner, text="✦", bg=INK, fg=GOLD_2, font=(SANS, 30)).pack(anchor="w")
        tk.Label(inner, text="TASKFLOW PERSONAL", bg=INK, fg=GOLD_2, font=(SANS, 9, "bold")).pack(anchor="w", pady=(8, 0))
        tk.Label(
            inner, text="Làm việc tinh gọn,\nsống chủ động.", bg=INK, fg="#FFFFFF",
            font=(SERIF, 28, "bold"), justify="left",
        ).pack(anchor="w", pady=(6, 18))
        for line in (
            "Quản lý công việc theo mức độ ưu tiên",
            "Theo dõi hạn chót rõ ràng",
            "Đồng bộ đám mây giữa web và Windows",
            "Trợ lý AI chỉ đề xuất, không tự sửa dữ liệu",
        ):
            tk.Label(inner, text=f"✦   {line}", bg=INK, fg="#D9D3C0", font=(SANS, 10), justify="left").pack(anchor="w", pady=4)

        right = tk.Frame(self.root, bg=IVORY)
        right.grid(row=0, column=1, sticky="nsew")
        form = tk.Frame(right, bg=IVORY)
        form.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(form, text="CHÀO MỪNG TRỞ LẠI", bg=IVORY, fg=GOLD, font=(SANS, 9, "bold")).pack(anchor="w")
        tk.Label(form, text="Truy cập tài khoản", bg=IVORY, fg=INK, font=(SERIF, 22, "bold")).pack(anchor="w", pady=(2, 4))
        tk.Frame(form, bg=GOLD, height=2, width=56).pack(anchor="w", pady=(0, 20))

        self.field_label(form, "Email").pack(anchor="w")
        self.email_entry = ttk.Entry(form, width=36, style="Field.TEntry", font=(SANS, 11))
        self.email_entry.pack(fill="x", pady=(4, 14))
        self.field_label(form, "Mật khẩu").pack(anchor="w")
        self.password_entry = ttk.Entry(form, width=36, show="•", style="Field.TEntry", font=(SANS, 11))
        self.password_entry.pack(fill="x", pady=(4, 20))

        self.button(form, "Đăng nhập", self.login, "primary").pack(fill="x")
        self.button(form, "Tạo tài khoản", self.register, "ghost").pack(fill="x", pady=(10, 0))
        tk.Label(
            form, text="Tạo tài khoản ở đây hoặc trên web; dùng chung tài khoản.",
            bg=IVORY, fg=MUTED, font=(SANS, 9),
        ).pack(pady=(16, 0))

        self.email_entry.focus_set()
        self.root.bind("<Return>", lambda _e: self.login())

    def credentials(self):
        return {"email": self.email_entry.get().strip(), "password": self.password_entry.get()}

    def login(self):
        data = self.request("POST", "/auth/login", json=self.credentials())
        if data:
            self.token, self.email = data["access_token"], data["email"]
            self.show_main()

    def register(self):
        data = self.request("POST", "/auth/register", json=self.credentials())
        if data:
            self.token, self.email = data["access_token"], data["email"]
            self.show_main()

    # ── Khung chính: menu bên + nội dung ──────────────────────
    def show_main(self):
        self.clear()
        self.root.columnconfigure(0, weight=0, uniform="", minsize=230)
        self.root.columnconfigure(1, weight=1, uniform="", minsize=0)
        self.root.rowconfigure(0, weight=1)

        side = tk.Frame(self.root, bg=INK, width=230)
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)

        brand = tk.Frame(side, bg=INK)
        brand.pack(fill="x", padx=22, pady=(26, 18))
        tk.Label(brand, text="✦", bg=GOLD_2, fg=INK, font=(SANS, 14, "bold"), width=2).pack(side="left")
        names = tk.Frame(brand, bg=INK)
        names.pack(side="left", padx=10)
        tk.Label(names, text="TaskFlow", bg=INK, fg="#FFFFFF", font=(SERIF, 15, "bold")).pack(anchor="w")
        tk.Label(names, text="PERSONAL", bg=INK, fg=GOLD_2, font=(SANS, 7, "bold")).pack(anchor="w")

        chip = tk.Frame(side, bg=INK_2)
        chip.pack(fill="x", padx=18, pady=(0, 18))
        initial = (self.email[:1] or "?").upper()
        tk.Label(chip, text=initial, bg=GOLD_2, fg=INK, font=(SANS, 11, "bold"), width=3, pady=6).pack(side="left", padx=(10, 8), pady=10)
        info = tk.Frame(chip, bg=INK_2)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text="TÀI KHOẢN", bg=INK_2, fg="#CDBF9B", font=(SANS, 7, "bold")).pack(anchor="w")
        email_text = self.email if len(self.email) <= 20 else self.email[:19] + "…"
        tk.Label(info, text=email_text, bg=INK_2, fg=SIDE_TEXT, font=(SANS, 9)).pack(anchor="w")

        self.nav_items = {}
        for key, text in NAV:
            row = tk.Frame(side, bg=INK, cursor="hand2")
            row.pack(fill="x", padx=18, pady=2)
            bar = tk.Frame(row, bg=INK, width=3)
            bar.pack(side="left", fill="y")
            lbl = tk.Label(row, text=text, bg=INK, fg=SIDE_TEXT, font=(SANS, 10, "bold"), anchor="w", padx=14, pady=10, cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True)
            self.nav_items[key] = (row, bar, lbl)
            for w in (row, lbl):
                w.bind("<Button-1>", lambda _e, k=key: self.navigate(k))
                w.bind("<Enter>", lambda _e, k=key: self.nav_hover(k, True))
                w.bind("<Leave>", lambda _e, k=key: self.nav_hover(k, False))

        bottom = tk.Frame(side, bg=INK)
        bottom.pack(side="bottom", fill="x", padx=18, pady=22)
        self.button(bottom, "↻  Làm mới", self.refresh, "side").pack(fill="x")
        self.button(bottom, "Đăng xuất", self.logout, "side").pack(fill="x", pady=(8, 0))

        self.page = "overview"
        self.navigate("overview")

    def nav_hover(self, key, inside):
        if key == self.page or key not in self.nav_items:
            return
        row, _bar, lbl = self.nav_items[key]
        bg = NAV_HOVER if inside else INK
        row.configure(bg=bg)
        lbl.configure(bg=bg)

    def set_nav_active(self, key):
        for k, (row, bar, lbl) in self.nav_items.items():
            active = k == key
            bg = NAV_ACTIVE if active else INK
            row.configure(bg=bg)
            lbl.configure(bg=bg, fg="#FFFFFF" if active else SIDE_TEXT)
            bar.configure(bg=GOLD_2 if active else bg)

    def navigate(self, key):
        self.page = key
        if self.content is not None:
            self.content.destroy()
        self.content = tk.Frame(self.root, bg=IVORY)
        self.content.grid(row=0, column=1, sticky="nsew", padx=28, pady=22)
        self.content.columnconfigure(0, weight=1)
        self.set_nav_active(key)
        if key != "ai":
            self.load_tasks()
        {"overview": self.page_overview, "tasks": self.page_tasks,
         "calendar": self.page_calendar, "ai": self.page_ai}[key]()

    def load_tasks(self):
        data = self.request("GET", "/tasks")
        if data is None:
            return False
        self.tasks = data
        return True

    def refresh(self):
        if self.page == "ai":
            return
        if not self.load_tasks():
            return
        {"overview": self.render_overview, "tasks": self.render_tasks,
         "calendar": self.render_calendar}[self.page]()

    # ── Thẻ thống kê (dùng ở Tổng quan và Công việc) ──────────
    def build_stats(self, row):
        stats = tk.Frame(self.content, bg=IVORY)
        stats.grid(row=row, column=0, sticky="ew", pady=(16, 14))
        self.stat_labels = {}
        for i, (key, title, dark) in enumerate(
            [("total", "TỔNG CÔNG VIỆC", True), ("done", "ĐÃ HOÀN THÀNH", False),
             ("pending", "ĐANG LÀM", False), ("overdue", "QUÁ HẠN", False)]
        ):
            stats.columnconfigure(i, weight=1, uniform="stat")
            bg = INK if dark else CARD
            card = tk.Frame(stats, bg=bg, highlightthickness=1, highlightbackground=INK if dark else LINE)
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 10, 0))
            tk.Label(card, text=title, bg=bg, fg="#CDBF9B" if dark else MUTED, font=(SANS, 8, "bold")).pack(anchor="w", padx=16, pady=(12, 0))
            value = tk.Label(
                card, text="0", bg=bg, fg="#FFFFFF" if dark else (DANGER if key == "overdue" else INK),
                font=(SERIF, 24, "bold"),
            )
            value.pack(anchor="w", padx=16, pady=(0, 10))
            self.stat_labels[key] = value

    def update_stats(self):
        today = date.today().isoformat()
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t["completed"])
        overdue = sum(1 for t in self.tasks if not t["completed"] and t["due_date"] and t["due_date"] < today)
        self.stat_labels["total"].config(text=str(total))
        self.stat_labels["done"].config(text=str(done))
        self.stat_labels["pending"].config(text=str(total - done))
        self.stat_labels["overdue"].config(text=str(overdue))

    # ── Trang: Tổng quan ──────────────────────────────────────
    def page_overview(self):
        c = self.content
        c.rowconfigure(3, weight=1)
        name = self.email.split("@")[0].replace(".", " ").replace("_", " ").title()
        self.page_head("Tổng quan", f"Xin chào, {name}", f"Hôm nay là {date.today().strftime('%d/%m/%Y')} — đây là bức tranh công việc của bạn.")
        self.build_stats(1)

        prog = tk.Frame(c, bg=CARD, highlightthickness=1, highlightbackground=LINE)
        prog.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        top = tk.Frame(prog, bg=CARD)
        top.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(top, text="Tiến độ hoàn thành", bg=CARD, fg=MUTED, font=(SANS, 9)).pack(side="left")
        self.pct_label = tk.Label(top, text="0%", bg=CARD, fg=INK, font=(SANS, 10, "bold"))
        self.pct_label.pack(side="right")
        trough = tk.Frame(prog, bg=TRACK, height=10)
        trough.pack(fill="x", padx=16, pady=(0, 14))
        trough.pack_propagate(False)
        self.pct_fill = tk.Frame(trough, bg=GOLD)
        self.pct_fill.place(x=0, y=0, relheight=1, relwidth=0)

        body = tk.Frame(c, bg=IVORY)
        body.grid(row=3, column=0, sticky="nsew")
        body.columnconfigure(0, weight=3, uniform="ov")
        body.columnconfigure(1, weight=2, uniform="ov")
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=IVORY)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        self.section(left, "Việc cần ưu tiên", 0)
        wrap, self.ov_tree = self.make_tree(
            left, [("title", "Công việc", 260, True), ("due", "Hạn chót", 100, False), ("priority", "Ưu tiên", 100, False)], height=4)
        wrap.grid(row=1, column=0, sticky="nsew")

        right = tk.Frame(body, bg=IVORY)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        self.section(right, "Đến hạn hôm nay", 0)
        wrap, self.today_tree = self.make_tree(
            right, [("title", "Công việc", 200, True), ("priority", "Ưu tiên", 90, False)], height=3)
        wrap.grid(row=1, column=0, sticky="nsew")
        self.section(right, "Phân bổ ưu tiên", 2, pady=(14, 4))
        bars = tk.Frame(right, bg=IVORY)
        bars.grid(row=3, column=0, sticky="ew")
        self.bars = {}
        for key, color in (("high", DANGER), ("medium", GOLD), ("low", OK)):
            row = tk.Frame(bars, bg=IVORY)
            row.pack(fill="x", pady=4)
            line = tk.Frame(row, bg=IVORY)
            line.pack(fill="x")
            tk.Label(line, text=PRIORITY_LABEL[key], bg=IVORY, fg=MUTED, font=(SANS, 9)).pack(side="left")
            count = tk.Label(line, text="0", bg=IVORY, fg=INK, font=(SANS, 9, "bold"))
            count.pack(side="right")
            track = tk.Frame(row, bg=TRACK, height=8)
            track.pack(fill="x", pady=(3, 0))
            track.pack_propagate(False)
            fill = tk.Frame(track, bg=color)
            fill.place(x=0, y=0, relheight=1, relwidth=0)
            self.bars[key] = (count, fill)

        self.render_overview()

    def render_overview(self):
        today = date.today().isoformat()
        self.update_stats()
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t["completed"])
        pct = round(done / total * 100) if total else 0
        self.pct_label.config(text=f"{pct}%")
        self.pct_fill.place_configure(relwidth=pct / 100)

        pending = [t for t in self.tasks if not t["completed"]]
        pending.sort(key=lambda t: (t["due_date"] or "9999-12-31", PRIORITY_ORDER.get(t["priority"], 1)))
        self.fill_tree(self.ov_tree, pending[:8])
        self.fill_tree(self.today_tree, [t for t in pending if t["due_date"] == today])
        for key, (count, fill) in self.bars.items():
            n = sum(1 for t in pending if t["priority"] == key)
            count.config(text=str(n))
            fill.place_configure(relwidth=(n / len(pending)) if pending else 0)

    # ── Trang: Công việc ──────────────────────────────────────
    def page_tasks(self):
        c = self.content
        c.rowconfigure(3, weight=1)
        self.page_head("Quản lý", "Công việc của bạn", "Thêm, theo dõi và hoàn thành nhiệm vụ.")
        self.build_stats(1)

        form = tk.Frame(c, bg=CARD, highlightthickness=1, highlightbackground=LINE)
        form.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        pad = tk.Frame(form, bg=CARD)
        pad.pack(fill="x", padx=16, pady=14)
        pad.columnconfigure(0, weight=1)

        self.field_label(pad, "Tên công việc", CARD).grid(row=0, column=0, sticky="w")
        self.field_label(pad, "Hạn (dd/mm/yyyy)", CARD).grid(row=0, column=1, sticky="w", padx=(12, 0))
        self.field_label(pad, "Ưu tiên", CARD).grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.title_entry = ttk.Entry(pad, style="Field.TEntry", font=(SANS, 10))
        self.title_entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.due_entry = ttk.Entry(pad, width=14, style="Field.TEntry", font=(SANS, 10))
        self.due_entry.grid(row=1, column=1, padx=(12, 0), pady=(4, 0))
        self.priority = tk.StringVar(value=PRIORITY_LABEL["medium"])
        ttk.Combobox(
            pad, textvariable=self.priority, values=list(PRIORITY_LABEL.values()),
            state="readonly", width=12, style="Field.TCombobox", font=(SANS, 10),
        ).grid(row=1, column=2, padx=(12, 0), pady=(4, 0))
        self.button(pad, "＋  Thêm", self.add_task, "primary").grid(row=1, column=3, padx=(12, 0), pady=(4, 0))
        self.title_entry.bind("<Return>", lambda _e: self.add_task())
        self.due_entry.bind("<Return>", lambda _e: self.add_task())

        box = tk.Frame(c, bg=IVORY)
        box.grid(row=3, column=0, sticky="nsew")
        box.columnconfigure(0, weight=1)
        box.rowconfigure(1, weight=1)

        bar = tk.Frame(box, bg=IVORY)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.filter_var = tk.StringVar(value=FILTERS[0])
        filt = ttk.Combobox(bar, textvariable=self.filter_var, values=FILTERS, state="readonly", width=14, style="Field.TCombobox", font=(SANS, 10))
        filt.pack(side="left")
        filt.bind("<<ComboboxSelected>>", lambda _e: self.render_tasks())
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_tasks())
        ttk.Entry(bar, textvariable=self.search_var, width=30, style="Field.TEntry", font=(SANS, 10)).pack(side="left", padx=10)
        tk.Label(bar, text="🔍 Tìm theo tên", bg=IVORY, fg=MUTED, font=(SANS, 9)).pack(side="left")
        self.count_label = tk.Label(bar, text="", bg=IVORY, fg=MUTED, font=(SANS, 9))
        self.count_label.pack(side="right")

        wrap, self.tree = self.make_tree(
            box, [("title", "Công việc", 440, True), ("due", "Hạn chót", 120, False),
                  ("priority", "Ưu tiên", 110, False), ("status", "Trạng thái", 120, False)], height=5)
        wrap.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", lambda _e: self.toggle())

        actions = tk.Frame(c, bg=IVORY)
        actions.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        self.button(actions, "✓  Hoàn thành / mở lại", self.toggle, "primary").pack(side="left")
        self.button(actions, "Xóa công việc", self.delete, "danger").pack(side="left", padx=10)
        tk.Label(actions, text="Mẹo: nhấp đúp vào dòng để đổi trạng thái", bg=IVORY, fg=MUTED, font=(SANS, 9)).pack(side="right")

        self.render_tasks()

    def render_tasks(self):
        self.update_stats()
        mode = self.filter_var.get()
        query = self.search_var.get().strip().lower()
        shown = []
        for t in self.tasks:
            if mode == "Đang làm" and t["completed"]:
                continue
            if mode == "Hoàn thành" and not t["completed"]:
                continue
            if query and query not in t["title"].lower():
                continue
            shown.append(t)
        self.fill_tree(self.tree, shown)
        self.count_label.config(text=f"{len(shown)} công việc")

    def add_task(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Thiếu tên", "Nhập tên công việc trước.")
            return
        try:
            due = parse_due(self.due_entry.get())
        except ValueError as exc:
            messagebox.showwarning("Hạn chót không hợp lệ", str(exc))
            return
        payload = {
            "title": title, "description": "", "due_date": due,
            "priority": PRIORITY_VALUE.get(self.priority.get(), "medium"), "completed": False,
        }
        result = self.request("POST", "/tasks", json=payload)
        if result:
            self.title_entry.delete(0, "end")
            self.due_entry.delete(0, "end")
            self.refresh()

    def selected_task(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Chọn công việc", "Hãy chọn một công việc trong danh sách.")
            return None
        return int(selection[0])

    def toggle(self):
        task_id = self.selected_task()
        if task_id is None:
            return
        tasks = self.request("GET", "/tasks")
        task = next((x for x in (tasks or []) if x["id"] == task_id), None)
        if not task:
            return
        payload = {k: task[k] for k in ["title", "description", "due_date", "priority"]}
        payload["completed"] = not task["completed"]
        if self.request("PATCH", f"/tasks/{task_id}", json=payload):
            self.refresh()

    def delete(self):
        task_id = self.selected_task()
        if task_id is None:
            return
        if messagebox.askyesno("Xác nhận", "Xóa công việc đã chọn?"):
            if self.request("DELETE", f"/tasks/{task_id}"):
                self.refresh()

    # ── Trang: Lịch ───────────────────────────────────────────
    def page_calendar(self):
        c = self.content
        c.rowconfigure(4, weight=1)
        c.rowconfigure(6, weight=1)
        self.page_head("Lịch trình", "Lịch công việc", "Xem nhanh các nhiệm vụ theo ngày và tuần.")

        ctrl = tk.Frame(c, bg=IVORY)
        ctrl.grid(row=1, column=0, sticky="w", pady=(14, 10))
        self.cal_var = tk.StringVar()
        self.button(ctrl, "‹", lambda: self.shift_day(-1), "ghost").pack(side="left")
        entry = ttk.Entry(ctrl, textvariable=self.cal_var, width=12, style="Field.TEntry", font=(SANS, 11), justify="center")
        entry.pack(side="left", padx=8)
        entry.bind("<Return>", lambda _e: self.apply_cal_entry())
        entry.bind("<FocusOut>", lambda _e: self.apply_cal_entry(silent=True))
        self.button(ctrl, "›", lambda: self.shift_day(1), "ghost").pack(side="left")
        self.button(ctrl, "Hôm nay", lambda: self.set_cal_date(date.today()), "primary").pack(side="left", padx=(12, 0))

        self.week_strip = tk.Frame(c, bg=IVORY)
        self.week_strip.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        for i in range(7):
            self.week_strip.columnconfigure(i, weight=1, uniform="wk")

        self.day_title = self.section(c, "", 3)
        wrap, self.day_tree = self.make_tree(
            c, [("title", "Công việc", 440, True), ("priority", "Ưu tiên", 110, False), ("status", "Trạng thái", 120, False)], height=3)
        wrap.grid(row=4, column=0, sticky="nsew")

        self.section(c, "7 ngày tới", 5, pady=(14, 8))
        wrap, self.week_tree = self.make_tree(
            c, [("due", "Ngày", 110, False), ("title", "Công việc", 380, True),
                ("priority", "Ưu tiên", 110, False), ("status", "Trạng thái", 120, False)], height=3)
        wrap.grid(row=6, column=0, sticky="nsew")

        self.render_calendar()

    def set_cal_date(self, d):
        self.cal_date = d
        self.render_calendar()

    def shift_day(self, n):
        self.set_cal_date(self.cal_date + timedelta(days=n))

    def apply_cal_entry(self, silent=False):
        try:
            d = parse_due(self.cal_var.get())
        except ValueError as exc:
            if not silent:
                messagebox.showwarning("Ngày không hợp lệ", str(exc))
            self.cal_var.set(self.cal_date.strftime("%d/%m/%Y"))
            return
        if d and d != self.cal_date.isoformat():
            self.set_cal_date(date.fromisoformat(d))

    def render_calendar(self):
        today_iso = date.today().isoformat()
        chosen = self.cal_date
        self.cal_var.set(chosen.strftime("%d/%m/%Y"))
        by_day = {}
        for t in self.tasks:
            if t["due_date"]:
                by_day.setdefault(t["due_date"], []).append(t)

        for w in self.week_strip.winfo_children():
            w.destroy()
        week_start = chosen - timedelta(days=chosen.weekday())
        for i in range(7):
            d = week_start + timedelta(days=i)
            n = len(by_day.get(d.isoformat(), []))
            sel = d == chosen
            bg = INK if sel else CARD
            cell = tk.Frame(self.week_strip, bg=bg, highlightthickness=1, highlightbackground=INK if sel else LINE, cursor="hand2")
            cell.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
            tk.Label(cell, text=WEEKDAYS[i], bg=bg, fg="#CDBF9B" if sel else MUTED, font=(SANS, 8, "bold"), cursor="hand2").pack(pady=(8, 0))
            num_fg = "#FFFFFF" if sel else (GOLD if d.isoformat() == today_iso else INK)
            tk.Label(cell, text=str(d.day), bg=bg, fg=num_fg, font=(SERIF, 18, "bold"), cursor="hand2").pack()
            cnt_fg = "#CDBF9B" if sel else (GOLD if n else MUTED)
            tk.Label(cell, text=f"{n} việc", bg=bg, fg=cnt_fg, font=(SANS, 8, "bold" if n else "normal"), cursor="hand2").pack(pady=(0, 8))
            for w in (cell, *cell.winfo_children()):
                w.bind("<Button-1>", lambda _e, dd=d: self.set_cal_date(dd))

        self.day_title.config(text=f"Công việc ngày {chosen.strftime('%d/%m/%Y')}")
        self.fill_tree(self.day_tree, by_day.get(chosen.isoformat(), []))
        end = (chosen + timedelta(days=6)).isoformat()
        upcoming = [t for t in self.tasks if t["due_date"] and chosen.isoformat() <= t["due_date"] <= end]
        upcoming.sort(key=lambda t: t["due_date"])
        self.fill_tree(self.week_tree, upcoming)

    # ── Trang: Trợ lý AI ──────────────────────────────────────
    def page_ai(self):
        c = self.content
        c.rowconfigure(1, weight=1)
        self.page_head("Trợ lý thông minh", "Lập kế hoạch với AI", "AI tham khảo các task chưa hoàn thành để đề xuất thứ tự ưu tiên. AI không tự sửa dữ liệu của bạn.")

        body = tk.Frame(c, bg=IVORY)
        body.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
        body.columnconfigure(0, weight=2, uniform="ai")
        body.columnconfigure(1, weight=3, uniform="ai")
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=IVORY)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left.columnconfigure(0, weight=1)
        self.field_label(left, "Bạn muốn đạt được gì?").grid(row=0, column=0, sticky="w")
        self.goal_text = tk.Text(
            left, height=8, wrap="word", bg=CARD, fg=INK, relief="flat", font=(SANS, 10),
            padx=12, pady=10, highlightthickness=1, highlightbackground=LINE, highlightcolor=GOLD,
            insertbackground=INK,
        )
        self.goal_text.grid(row=1, column=0, sticky="ew", pady=(4, 4))
        tk.Label(
            left, text="Ví dụ: hoàn thành báo cáo, học Python và dọn dẹp email trong hôm nay.",
            bg=IVORY, fg=MUTED, font=(SANS, 9), wraplength=330, justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(0, 16))

        hrow = tk.Frame(left, bg=IVORY)
        hrow.grid(row=3, column=0, sticky="ew")
        self.field_label(hrow, "Thời gian bạn có").pack(side="left")
        self.hours_label = tk.Label(hrow, text="", bg=IVORY, fg=INK, font=(SANS, 10, "bold"))
        self.hours_label.pack(side="right")
        scale = tk.Scale(
            left, from_=0.5, to=16, resolution=0.5, orient="horizontal", variable=self.hours_var,
            showvalue=False, bg=IVORY, troughcolor=LINE, highlightthickness=0, bd=0,
            activebackground=GOLD, sliderrelief="flat", command=lambda _v: self.update_hours_label(),
        )
        scale.grid(row=4, column=0, sticky="ew", pady=(4, 16))
        self.update_hours_label()

        self.ai_btn = self.button(left, "✦  Tạo kế hoạch", self.generate_plan, "primary")
        self.ai_btn.grid(row=5, column=0, sticky="ew")
        self.ai_status = tk.Label(left, text="", bg=IVORY, fg=MUTED, font=(SANS, 9))
        self.ai_status.grid(row=6, column=0, sticky="w", pady=(10, 0))

        right = tk.Frame(body, bg=IVORY)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        self.section(right, "Kế hoạch đề xuất", 0)
        card = tk.Frame(right, bg=CARD, highlightthickness=1, highlightbackground=LINE)
        card.grid(row=1, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)
        self.ai_text = tk.Text(
            card, wrap="word", bg=CARD, fg=INK, relief="flat", font=(SANS, 10), padx=18, pady=14,
            highlightthickness=0, cursor="arrow", spacing1=2, spacing3=2,
        )
        scroll = ttk.Scrollbar(card, orient="vertical", command=self.ai_text.yview)
        self.ai_text.configure(yscrollcommand=scroll.set)
        self.ai_text.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        if self.last_plan:
            self.render_markdown(self.ai_text, self.last_plan)
        else:
            self.set_placeholder(self.ai_text, "Kế hoạch sẽ xuất hiện ở đây.")

    def update_hours_label(self):
        h = self.hours_var.get()
        self.hours_label.config(text=f"{h:g} giờ")

    def set_placeholder(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.tag_configure("ph", foreground=MUTED)
        widget.insert("end", text, "ph")
        widget.config(state="disabled")

    def render_markdown(self, widget, md):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.tag_configure("bold", font=(SANS, 10, "bold"))
        widget.tag_configure("h1", font=(SERIF, 16, "bold"), spacing1=10, spacing3=4)
        widget.tag_configure("h2", font=(SERIF, 14, "bold"), spacing1=10, spacing3=4)
        widget.tag_configure("h3", font=(SERIF, 12, "bold"), spacing1=8, spacing3=2)
        widget.tag_configure("bullet", lmargin1=12, lmargin2=28)
        for raw in md.splitlines():
            line = raw.rstrip()
            stripped = line.lstrip()
            tags = ()
            m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if m:
                tags = (f"h{min(len(m.group(1)), 3)}",)
                line = m.group(2)
            elif re.match(r"^[-*•]\s+", stripped):
                tags = ("bullet",)
                line = "•  " + re.sub(r"^[-*•]\s+", "", stripped)
            for part in re.split(r"(\*\*[^*]+\*\*)", line):
                if len(part) > 4 and part.startswith("**") and part.endswith("**"):
                    widget.insert("end", part[2:-2], tags + ("bold",))
                else:
                    widget.insert("end", part, tags)
            widget.insert("end", "\n")
        widget.config(state="disabled")

    def generate_plan(self):
        goal = self.goal_text.get("1.0", "end").strip()
        if len(goal) < 3:
            messagebox.showwarning("Thiếu mục tiêu", "Hãy mô tả mục tiêu rõ hơn.")
            return
        hours = float(self.hours_var.get())
        self.ai_btn.config(state="disabled")
        self.ai_status.config(text="Đang lập kế hoạch…")

        def work():
            return self.call("POST", "/ai/plan", json={"goal": goal, "available_hours": hours}, timeout=90)

        def done(res):
            data, err = res
            if not self.token:
                return
            if not err and data:
                self.last_plan = data.get("plan", "")
            if self.page != "ai" or not self.ai_btn.winfo_exists():
                return
            self.ai_btn.config(state="normal")
            self.ai_status.config(text="")
            if err:
                messagebox.showerror("TaskFlow", err)
                return
            self.render_markdown(self.ai_text, self.last_plan)

        self.run_async(work, done)

    # ── Đăng xuất ─────────────────────────────────────────────
    def logout(self):
        self.token = ""
        self.email = ""
        self.tasks = []
        self.last_plan = ""
        self.show_login()


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskFlowDesktop(root)
    root.mainloop()