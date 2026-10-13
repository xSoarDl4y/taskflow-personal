import html
import os
from datetime import date, timedelta

import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_cookies_manager import EncryptedCookieManager

load_dotenv()

API = os.getenv(
    "API_BASE_URL",
    "https://taskflow-personal.onrender.com"
).rstrip("/")

COOKIE_PASSWORD = os.getenv("COOKIE_PASSWORD", "")

if not COOKIE_PASSWORD:
    try:
        COOKIE_PASSWORD = st.secrets["COOKIE_PASSWORD"]
    except Exception:
        COOKIE_PASSWORD = ""

if not COOKIE_PASSWORD:
    st.error("Thiếu COOKIE_PASSWORD. Hãy cấu hình trong .env hoặc Streamlit Secrets.")
    st.stop()

cookies = EncryptedCookieManager(
    prefix="taskflow/",
    password=COOKIE_PASSWORD,
)

if not cookies.ready():
    st.stop()

st.set_page_config(
    page_title="TaskFlow Personal",
    page_icon="✦",
    layout="wide",
)

load_dotenv()
API = os.getenv("API_BASE_URL", "https://taskflow-personal.onrender.com").rstrip("/")

st.set_page_config(page_title="TaskFlow Personal", page_icon="✦", layout="wide")

# ──────────────────────────────────────────────────────────────
# Giao diện (CSS)
# ──────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');

:root{
  --ink:#0F1B33; --ink-2:#1B2A4A; --gold:#B8893B; --gold-2:#D9B368; --gold-soft:#F3E8CF;
  --ivory:#F6F3EC; --card:#FFFFFF; --line:#E7E1D3; --muted:#6B7385;
  --ok:#2F7D5B; --warn:#C27A12; --danger:#B83A3A;
}
html, body, [class*="css"], .stApp { font-family:'Inter',sans-serif; }
.stApp { background: radial-gradient(1200px 500px at 85% -10%, #EFE6D0 0%, transparent 60%), var(--ivory); color:var(--ink); }
header[data-testid="stHeader"] { background:transparent; }
#MainMenu, footer { visibility:hidden; }
.block-container { padding-top:2.2rem; padding-bottom:4rem; max-width:1280px; }

h1,h2,h3 { font-family:'Playfair Display',serif !important; color:var(--ink); letter-spacing:.2px; }

/* Sidebar */
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0F1B33 0%,#14244A 100%); border-right:1px solid rgba(217,179,104,.25); }
[data-testid="stSidebar"] * { color:#E9E4D6; }
[data-testid="stSidebar"] hr { border-color:rgba(217,179,104,.25); }
[data-testid="stSidebar"] .stRadio label { padding:.55rem .8rem; border-radius:10px; transition:all .15s; width:100%; }
[data-testid="stSidebar"] .stRadio label:hover { background:rgba(217,179,104,.12); }
[data-testid="stSidebar"] .stRadio label:has(input:checked) { background:linear-gradient(90deg,rgba(217,179,104,.28),rgba(217,179,104,.06)); border-left:3px solid var(--gold-2); }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child { display:none; }
[data-testid="stSidebar"] .stButton > button { background:transparent; border:1px solid rgba(217,179,104,.5); color:#F3E8CF; border-radius:10px; }
[data-testid="stSidebar"] .stButton > button:hover { background:rgba(217,179,104,.15); border-color:var(--gold-2); }

.brand { display:flex; align-items:center; gap:.7rem; margin:.2rem 0 1.2rem; }
.brand-mark { width:38px; height:38px; border-radius:11px; display:grid; place-items:center; font-size:1.15rem; color:#0F1B33;
  background:linear-gradient(135deg,#F3E2B3,#C99A4B); box-shadow:0 6px 18px rgba(201,154,75,.35); }
.brand-name { font-family:'Playfair Display',serif; font-size:1.25rem; font-weight:600; color:#fff; line-height:1.1; }
.brand-sub { font-size:.68rem; letter-spacing:.18em; text-transform:uppercase; color:var(--gold-2); }
.user-chip { display:flex; align-items:center; gap:.65rem; padding:.7rem .8rem; border-radius:12px; background:rgba(255,255,255,.06); border:1px solid rgba(217,179,104,.2); margin-bottom:1rem; }
.avatar { width:34px; height:34px; border-radius:50%; display:grid; place-items:center; font-weight:700; color:#0F1B33; background:linear-gradient(135deg,#F3E2B3,#C99A4B); }
.user-mail { font-size:.8rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

/* Header trang */
.page-head { margin-bottom:1.4rem; }
.eyebrow { font-size:.72rem; letter-spacing:.22em; text-transform:uppercase; color:var(--gold); font-weight:600; }
.page-title { font-family:'Playfair Display',serif; font-size:2.1rem; font-weight:600; margin:.15rem 0 .2rem; color:var(--ink); }
.page-sub { color:var(--muted); font-size:.95rem; }
.gold-rule { height:2px; width:64px; background:linear-gradient(90deg,var(--gold),transparent); margin:.7rem 0 0; border-radius:2px; }

/* KPI */
.kpi { background:var(--card); border:1px solid var(--line); border-radius:18px; padding:1.15rem 1.3rem; box-shadow:0 8px 24px rgba(15,27,51,.05); position:relative; overflow:hidden; }
.kpi::after { content:""; position:absolute; right:-30px; top:-30px; width:90px; height:90px; border-radius:50%; background:radial-gradient(circle,var(--gold-soft),transparent 70%); }
.kpi-label { font-size:.75rem; letter-spacing:.12em; text-transform:uppercase; color:var(--muted); font-weight:600; }
.kpi-value { font-family:'Playfair Display',serif; font-size:2.4rem; font-weight:600; line-height:1.15; margin-top:.2rem; color:var(--ink); }
.kpi-sub { font-size:.8rem; color:var(--muted); }
.kpi.dark { background:linear-gradient(135deg,#0F1B33,#1F3463); border-color:#0F1B33; }
.kpi.dark .kpi-label, .kpi.dark .kpi-sub { color:#CDBF9B; }
.kpi.dark .kpi-value { color:#fff; }
.kpi.danger .kpi-value { color:var(--danger); }

/* Panel */
.panel-title { font-family:'Playfair Display',serif; font-size:1.25rem; font-weight:600; color:var(--ink); margin:.4rem 0 .8rem; display:flex; align-items:center; gap:.5rem; }
.panel-title::before { content:""; width:4px; height:1.1em; background:var(--gold); border-radius:2px; }

/* Progress */
.progress-wrap { background:var(--card); border:1px solid var(--line); border-radius:18px; padding:1.1rem 1.3rem; box-shadow:0 8px 24px rgba(15,27,51,.05); margin:1.1rem 0 .4rem; }
.progress-top { display:flex; justify-content:space-between; font-size:.85rem; color:var(--muted); margin-bottom:.55rem; }
.progress-top b { color:var(--ink); }
.progress-bar { height:10px; background:#EFE9DA; border-radius:999px; overflow:hidden; }
.progress-fill { height:100%; border-radius:999px; background:linear-gradient(90deg,var(--gold),var(--gold-2)); }

/* Task card */
.task { display:flex; gap:.9rem; background:var(--card); border:1px solid var(--line); border-radius:14px; padding:.9rem 1.05rem; margin-bottom:.6rem; box-shadow:0 4px 14px rgba(15,27,51,.04); transition:transform .12s, box-shadow .12s; }
.task:hover { transform:translateY(-1px); box-shadow:0 10px 24px rgba(15,27,51,.08); }
.task .bar { width:4px; border-radius:4px; flex:none; }
.bar.high { background:var(--danger); } .bar.medium { background:var(--gold); } .bar.low { background:var(--ok); }
.task .body { flex:1; min-width:0; }
.task .t { font-weight:600; font-size:1rem; color:var(--ink); }
.task.done .t { text-decoration:line-through; color:#98A0AF; }
.task .d { color:var(--muted); font-size:.86rem; margin-top:.25rem; white-space:pre-wrap; }
.task .meta { display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.5rem; }
.badge { font-size:.72rem; font-weight:600; padding:.18rem .6rem; border-radius:999px; border:1px solid transparent; }
.badge.high { background:#FBEAEA; color:var(--danger); border-color:#F1CACA; }
.badge.medium { background:var(--gold-soft); color:#8A6420; border-color:#EBD8AC; }
.badge.low { background:#E6F3EC; color:var(--ok); border-color:#C4E1D1; }
.badge.danger { background:#FBEAEA; color:var(--danger); border-color:#F1CACA; }
.badge.warn { background:#FDF1DC; color:var(--warn); border-color:#F2DAA9; }
.badge.ok { background:#EEF1F7; color:#44506B; border-color:#DCE1EC; }
.badge.muted { background:#F2F0EA; color:#8A8F9C; border-color:#E5E1D6; }

.empty { text-align:center; padding:2.2rem 1rem; color:var(--muted); background:var(--card); border:1px dashed var(--line); border-radius:16px; }
.empty .ic { font-size:1.6rem; color:var(--gold); }

/* Week strip */
.week { display:grid; grid-template-columns:repeat(7,1fr); gap:.6rem; margin:.4rem 0 1.2rem; }
.day { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:.7rem .4rem; text-align:center; }
.day .dn { font-size:.68rem; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); }
.day .dd { font-family:'Playfair Display',serif; font-size:1.5rem; font-weight:600; color:var(--ink); }
.day .dc { font-size:.72rem; color:var(--muted); }
.day.sel { background:linear-gradient(135deg,#0F1B33,#1F3463); border-color:#0F1B33; }
.day.sel .dn, .day.sel .dc { color:#CDBF9B; } .day.sel .dd { color:#fff; }
.day.has .dc { color:var(--gold); font-weight:600; }

.date-head { font-family:'Playfair Display',serif; font-size:1.15rem; font-weight:600; color:var(--ink); margin:1rem 0 .5rem; padding-bottom:.3rem; border-bottom:1px solid var(--line); }

/* Hero đăng nhập */
.hero { background:linear-gradient(145deg,#0F1B33 0%,#1F3463 100%); border-radius:24px; padding:2.8rem 2.4rem; color:#F3EEE0; min-height:430px; position:relative; overflow:hidden; box-shadow:0 24px 60px rgba(15,27,51,.25); }
.hero::before { content:""; position:absolute; right:-80px; bottom:-80px; width:300px; height:300px; border-radius:50%; background:radial-gradient(circle,rgba(217,179,104,.35),transparent 70%); }
.hero h1 { color:#fff !important; font-size:2.6rem; line-height:1.15; margin:.6rem 0 1rem; }
.hero p { color:#CFC8B3; font-size:1rem; line-height:1.7; }
.hero ul { list-style:none; padding:0; margin:1.6rem 0 0; }
.hero li { padding:.45rem 0; color:#E9E3D0; font-size:.95rem; }
.hero li::before { content:"✦"; color:var(--gold-2); margin-right:.7rem; }

/* Widgets */
.stButton > button, .stFormSubmitButton > button { border-radius:12px; font-weight:600; border:1px solid var(--line); padding:.55rem 1.1rem; transition:all .15s; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background:linear-gradient(135deg,#C99A4B,#B8893B); border:none; color:#fff; box-shadow:0 8px 20px rgba(184,137,59,.35); }
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover { filter:brightness(1.07); transform:translateY(-1px); }
.stTextInput input, .stTextArea textarea, .stDateInput input, div[data-baseweb="select"] > div { border-radius:12px !important; background:#fff !important; border:1px solid var(--line) !important; }
.stTextInput input:focus, .stTextArea textarea:focus { border-color:var(--gold) !important; box-shadow:0 0 0 3px rgba(184,137,59,.18) !important; }
.stTabs [data-baseweb="tab-list"] { gap:.4rem; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { font-weight:600; color:var(--muted); }
.stTabs [aria-selected="true"] { color:var(--ink) !important; }
.stTabs [data-baseweb="tab-highlight"] { background:var(--gold) !important; }
div[data-testid="stForm"], div[data-testid="stExpander"] { background:var(--card); border:1px solid var(--line) !important; border-radius:16px; box-shadow:0 8px 24px rgba(15,27,51,.05); }
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] .ai-result) { background:var(--card); border-radius:18px; border:1px solid var(--line); }
.stSlider [role="slider"] { background:var(--gold) !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# Tiện ích
# ──────────────────────────────────────────────────────────────
PRIORITY_LABEL = {"low": "Thấp", "medium": "Trung bình", "high": "Cao"}
WEEKDAYS = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]


def esc(value):
    return html.escape(str(value)) if value is not None else ""


def fmt_date(iso):
    try:
        return date.fromisoformat(iso).strftime("%d/%m/%Y")
    except Exception:
        return iso or ""


def api(method, path, token=None, **kwargs):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = requests.request(method, f"{API}{path}", headers=headers, timeout=25, **kwargs)
        if response.status_code >= 400:
            try:
                message = response.json().get("detail", response.text)
            except Exception:
                message = response.text
            st.error(f"Lỗi {response.status_code}: {message}")
            return None
        return response.json() if response.content else {}
    except requests.RequestException as exc:
        st.error(f"Không kết nối được backend tại {API}. Hãy chạy backend trước. ({exc})")
        return None


def page_header(eyebrow, title, subtitle=""):
    st.markdown(
        f'<div class="page-head"><div class="eyebrow">{esc(eyebrow)}</div>'
        f'<div class="page-title">{esc(title)}</div>'
        f'<div class="page-sub">{esc(subtitle)}</div><div class="gold-rule"></div></div>',
        unsafe_allow_html=True,
    )


def kpi(label, value, sub="", variant=""):
    return (f'<div class="kpi {variant}"><div class="kpi-label">{esc(label)}</div>'
            f'<div class="kpi-value">{esc(value)}</div><div class="kpi-sub">{esc(sub)}</div></div>')


def due_badge(task):
    due = task.get("due_date")
    if not due:
        return '<span class="badge muted">Chưa đặt hạn</span>'
    today = date.today().isoformat()
    if task.get("completed"):
        return f'<span class="badge muted">Hạn {fmt_date(due)}</span>'
    if due < today:
        return f'<span class="badge danger">Quá hạn · {fmt_date(due)}</span>'
    if due == today:
        return '<span class="badge warn">Hôm nay</span>'
    return f'<span class="badge ok">Hạn {fmt_date(due)}</span>'


def task_html(task, show_desc=True):
    prio = task.get("priority", "medium")
    prio = prio if prio in PRIORITY_LABEL else "medium"
    done_cls = " done" if task.get("completed") else ""
    desc = f'<div class="d">{esc(task["description"])}</div>' if show_desc and task.get("description") else ""
    return (
        f'<div class="task{done_cls}"><div class="bar {prio}"></div><div class="body">'
        f'<div class="t">{esc(task["title"])}</div>{desc}'
        f'<div class="meta"><span class="badge {prio}">Ưu tiên {PRIORITY_LABEL[prio]}</span>{due_badge(task)}</div>'
        f'</div></div>'
    )


def empty_state(icon, text):
    st.markdown(f'<div class="empty"><div class="ic">{icon}</div>{esc(text)}</div>', unsafe_allow_html=True)


def set_session(result):
    token = result["access_token"]
    email = result["email"]

    st.session_state.token = token
    st.session_state.email = email

    cookies["token"] = token
    cookies["email"] = email
    cookies.save()

    st.rerun()


if "token" not in st.session_state:
    st.session_state.token = cookies.get("token", "")

if "email" not in st.session_state:
    st.session_state.email = cookies.get("email", "")

# ──────────────────────────────────────────────────────────────
# Đăng nhập / Đăng ký
# ──────────────────────────────────────────────────────────────
if not st.session_state.token:
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown(
            '<div class="hero"><div class="eyebrow" style="color:#D9B368">TaskFlow Personal</div>'
            '<h1>Làm việc tinh gọn,<br>sống chủ động.</h1>'
            '<p>Không gian quản lý công việc cá nhân với lịch trực quan và trợ lý AI giúp bạn sắp xếp ưu tiên mỗi ngày.</p>'
            '<ul><li>Quản lý công việc theo mức độ ưu tiên</li><li>Lịch theo dõi hạn chót rõ ràng</li>'
            '<li>Đồng bộ đám mây giữa web và Windows</li><li>Trợ lý AI chỉ đề xuất, không tự sửa dữ liệu</li></ul></div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown('<div style="height:1.2rem"></div>', unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">Chào mừng trở lại</div><div class="page-title">Truy cập tài khoản</div>', unsafe_allow_html=True)
        login_tab, register_tab = st.tabs(["Đăng nhập", "Tạo tài khoản"])
        with login_tab:
            with st.form("login"):
                email = st.text_input("Email", key="login_email", placeholder="ban@example.com")
                password = st.text_input("Mật khẩu", type="password", key="login_password")
                submitted = st.form_submit_button("Đăng nhập", type="primary", use_container_width=True)
            if submitted:
                result = api("POST", "/auth/login", json={"email": email, "password": password})
                if result:
                    set_session(result)
        with register_tab:
            with st.form("register"):
                email = st.text_input("Email", key="reg_email", placeholder="ban@example.com")
                password = st.text_input("Mật khẩu (ít nhất 8 ký tự)", type="password", key="reg_password")
                submitted = st.form_submit_button("Tạo tài khoản", type="primary", use_container_width=True)
            if submitted:
                result = api("POST", "/auth/register", json={"email": email, "password": password})
                if result:
                    set_session(result)
        st.caption("Tạo tài khoản một lần; dùng cùng tài khoản để đăng nhập trên app Windows.")
    st.stop()

# ──────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────
token = st.session_state.token
email = st.session_state.email
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-mark">✦</div><div><div class="brand-name">TaskFlow</div>'
        '<div class="brand-sub">Personal</div></div></div>',
        unsafe_allow_html=True,
    )
    initial = (email[:1] or "?").upper()
    st.markdown(
        f'<div class="user-chip"><div class="avatar">{esc(initial)}</div>'
        f'<div><div style="font-size:.68rem;color:#CDBF9B;letter-spacing:.1em;text-transform:uppercase">Tài khoản</div>'
        f'<div class="user-mail">{esc(email)}</div></div></div>',
        unsafe_allow_html=True,
    )
    nav = {"◈  Tổng quan": "Tổng quan", "☰  Công việc": "Công việc", "▦  Lịch": "Lịch", "✦  Trợ lý AI": "Trợ lý AI"}
    choice = st.radio("Điều hướng", list(nav.keys()), label_visibility="collapsed")
    page = nav[choice]
    st.markdown("<hr>", unsafe_allow_html=True)
    
if st.button("Đăng xuất", use_container_width=True):
    st.session_state.token = ""
    st.session_state.email = ""

    cookies["token"] = ""
    cookies["email"] = ""
    cookies.save()

    st.rerun()


today_iso = date.today().isoformat()

# ──────────────────────────────────────────────────────────────
# Tổng quan
# ──────────────────────────────────────────────────────────────
if page == "Tổng quan":
    name = email.split("@")[0].replace(".", " ").replace("_", " ").title()
    page_header("Tổng quan", f"Xin chào, {name}", f"Hôm nay là {date.today().strftime('%d/%m/%Y')} — đây là bức tranh công việc của bạn.")
    tasks = api("GET", "/tasks", token=token)
    if tasks is not None:
        total = len(tasks)
        done = sum(1 for t in tasks if t["completed"])
        pending = total - done
        overdue = sum(1 for t in tasks if not t["completed"] and t["due_date"] and t["due_date"] < today_iso)
        pct = round(done / total * 100) if total else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(kpi("Tổng công việc", total, "Tất cả nhiệm vụ", "dark"), unsafe_allow_html=True)
        c2.markdown(kpi("Đã hoàn thành", done, f"{pct}% tiến độ"), unsafe_allow_html=True)
        c3.markdown(kpi("Đang thực hiện", pending, "Chưa hoàn thành"), unsafe_allow_html=True)
        c4.markdown(kpi("Quá hạn", overdue, "Cần xử lý ngay", "danger" if overdue else ""), unsafe_allow_html=True)

        st.markdown(
            f'<div class="progress-wrap"><div class="progress-top"><span>Tiến độ hoàn thành</span><b>{pct}%</b></div>'
            f'<div class="progress-bar"><div class="progress-fill" style="width:{pct}%"></div></div></div>',
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns([1.7, 1], gap="large")
        upcoming = [t for t in tasks if not t["completed"]]
        upcoming.sort(key=lambda t: (t["due_date"] or "9999-12-31", {"high": 0, "medium": 1, "low": 2}.get(t["priority"], 1)))
        with col_a:
            st.markdown('<div class="panel-title">Việc cần ưu tiên</div>', unsafe_allow_html=True)
            if upcoming:
                for task in upcoming[:8]:
                    st.markdown(task_html(task, show_desc=False), unsafe_allow_html=True)
            else:
                empty_state("✦", "Bạn không còn công việc chưa hoàn thành.")
        with col_b:
            st.markdown('<div class="panel-title">Đến hạn hôm nay</div>', unsafe_allow_html=True)
            today_tasks = [t for t in upcoming if t["due_date"] == today_iso]
            if today_tasks:
                for task in today_tasks:
                    st.markdown(task_html(task, show_desc=False), unsafe_allow_html=True)
            else:
                empty_state("☀", "Không có việc đến hạn hôm nay.")
            st.markdown('<div class="panel-title" style="margin-top:1.2rem">Phân bổ ưu tiên</div>', unsafe_allow_html=True)
            for key, color in (("high", "#B83A3A"), ("medium", "#B8893B"), ("low", "#2F7D5B")):
                n = sum(1 for t in upcoming if t["priority"] == key)
                w = round(n / len(upcoming) * 100) if upcoming else 0
                st.markdown(
                    f'<div style="margin-bottom:.7rem"><div class="progress-top" style="margin-bottom:.3rem"><span>{PRIORITY_LABEL[key]}</span><b>{n}</b></div>'
                    f'<div class="progress-bar"><div style="height:100%;width:{w}%;background:{color};border-radius:999px"></div></div></div>',
                    unsafe_allow_html=True,
                )

# ──────────────────────────────────────────────────────────────
# Công việc
# ──────────────────────────────────────────────────────────────
elif page == "Công việc":
    page_header("Quản lý", "Công việc", "Thêm, theo dõi và hoàn thành nhiệm vụ của bạn.")

    with st.expander("＋  Thêm công việc mới", expanded=False):
        with st.form("new_task", clear_on_submit=True, border=False):
            title = st.text_input("Tên công việc *", placeholder="Ví dụ: Hoàn thiện báo cáo quý")
            description = st.text_area("Mô tả", placeholder="Ghi chú thêm (không bắt buộc)", height=90)
            col1, col2 = st.columns(2)
            with col1:
                due = st.date_input("Hạn chót", value=None)
            with col2:
                priority = st.selectbox("Ưu tiên", ["medium", "high", "low"], format_func=lambda x: PRIORITY_LABEL[x])
            add = st.form_submit_button("Thêm công việc", type="primary")
        if add:
            if not title.strip():
                st.warning("Hãy nhập tên công việc.")
            else:
                payload = {"title": title.strip(), "description": description, "due_date": due.isoformat() if due else None, "priority": priority, "completed": False}
                if api("POST", "/tasks", token=token, json=payload):
                    st.toast("Đã thêm công việc.", icon="✅")
                    st.rerun()

    f1, f2 = st.columns([1.2, 1])
    with f1:
        show = st.radio("Hiển thị", ["Tất cả", "Chưa hoàn thành", "Đã hoàn thành"], horizontal=True)
    with f2:
        query = st.text_input("Tìm kiếm", placeholder="Tìm theo tên công việc…", label_visibility="collapsed")
    status = None if show == "Tất cả" else show == "Đã hoàn thành"
    tasks = api("GET", "/tasks", token=token, params={"completed": status} if status is not None else {})
    if tasks is not None:
        if query.strip():
            q = query.strip().lower()
            tasks = [t for t in tasks if q in t["title"].lower() or q in (t["description"] or "").lower()]
        st.caption(f"{len(tasks)} công việc")
        if not tasks:
            empty_state("☰", "Chưa có công việc nào phù hợp.")
        for task in tasks:
            chk, body, act = st.columns([0.55, 7, 1], vertical_alignment="center")
            with chk:
                new_completed = st.checkbox("Hoàn thành", value=task["completed"], key=f"done_{task['id']}", label_visibility="collapsed")
            with body:
                st.markdown(task_html(task), unsafe_allow_html=True)
            with act:
                delete = st.button("Xóa", key=f"del_{task['id']}", use_container_width=True)
            if new_completed != task["completed"]:
                payload = {k: task[k] for k in ["title", "description", "due_date", "priority"]}
                payload["completed"] = new_completed
                if api("PATCH", f"/tasks/{task['id']}", token=token, json=payload):
                    st.rerun()
            if delete:
                if api("DELETE", f"/tasks/{task['id']}", token=token):
                    st.rerun()

# ──────────────────────────────────────────────────────────────
# Lịch
# ──────────────────────────────────────────────────────────────
elif page == "Lịch":
    page_header("Lịch trình", "Lịch công việc", "Xem nhanh các nhiệm vụ theo ngày và tuần.")
    chosen = st.date_input("Chọn ngày", value=date.today(), format="DD/MM/YYYY")
    all_tasks = api("GET", "/tasks", token=token)
    if all_tasks is not None:
        by_day = {}
        for t in all_tasks:
            if t["due_date"]:
                by_day.setdefault(t["due_date"], []).append(t)

        week_start = chosen - timedelta(days=chosen.weekday())
        cells = ""
        for i in range(7):
            d = week_start + timedelta(days=i)
            n = len(by_day.get(d.isoformat(), []))
            cls = "day" + (" sel" if d == chosen else "") + (" has" if n else "")
            cells += (f'<div class="{cls}"><div class="dn">{WEEKDAYS[i]}</div><div class="dd">{d.day}</div>'
                      f'<div class="dc">{n} việc</div></div>')
        st.markdown(f'<div class="week">{cells}</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="date-head">{chosen.strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)
        day_tasks = by_day.get(chosen.isoformat(), [])
        if day_tasks:
            for task in day_tasks:
                st.markdown(task_html(task), unsafe_allow_html=True)
        else:
            empty_state("☀", "Không có công việc đến hạn trong ngày này.")

        st.markdown('<div class="panel-title" style="margin-top:1.8rem">7 ngày tới</div>', unsafe_allow_html=True)
        end = (chosen + timedelta(days=6)).isoformat()
        found = sorted([t for t in all_tasks if t["due_date"] and chosen.isoformat() <= t["due_date"] <= end], key=lambda t: t["due_date"])
        if found:
            current = None
            for t in found:
                if t["due_date"] != current:
                    current = t["due_date"]
                    st.markdown(f'<div class="date-head" style="font-size:1rem">{fmt_date(current)}</div>', unsafe_allow_html=True)
                st.markdown(task_html(t, show_desc=False), unsafe_allow_html=True)
        else:
            empty_state("▦", "Chưa có nhiệm vụ trong khoảng thời gian này.")

# ──────────────────────────────────────────────────────────────
# Trợ lý AI
# ──────────────────────────────────────────────────────────────
elif page == "Trợ lý AI":
    page_header("Trợ lý thông minh", "Lập kế hoạch với AI", "AI tham khảo các task chưa hoàn thành để đề xuất thứ tự ưu tiên. AI không tự sửa dữ liệu của bạn.")
    goal = st.text_area("Bạn muốn đạt được gì?", height=130, placeholder="Ví dụ: hoàn thành báo cáo, học Python và dọn dẹp email trong hôm nay.")
    hours = st.slider("Thời gian bạn có (giờ)", 0.5, 16.0, 3.0, 0.5)
    if st.button("✦  Tạo kế hoạch", type="primary"):
        if len(goal.strip()) < 3:
            st.warning("Hãy mô tả mục tiêu rõ hơn.")
        else:
            with st.spinner("Đang lập kế hoạch..."):
                result = api("POST", "/ai/plan", token=token, json={"goal": goal, "available_hours": hours})
            if result:
                st.markdown('<div class="panel-title" style="margin-top:1.2rem">Kế hoạch đề xuất</div>', unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown('<span class="ai-result"></span>', unsafe_allow_html=True)
                    st.markdown(result["plan"])