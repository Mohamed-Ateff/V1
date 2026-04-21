import streamlit as st
import sqlite3
import hashlib
import os
import secrets
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
DEV_BYPASS_AUTH = True
DEV_BYPASS_USER = "moham"


# ── Database setup ────────────────────────────────────────────────────────────

def _get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create users and user_favorites tables if they don't exist."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                email      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                password   TEXT    NOT NULL,
                salt       TEXT    NOT NULL,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_favorites (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL COLLATE NOCASE,
                fav_id        TEXT    NOT NULL,
                symbol        TEXT,
                pair          TEXT,
                pair_display  TEXT,
                win_rate      REAL,
                profit_factor REAL,
                expectancy    REAL,
                avg_gain      REAL,
                avg_loss      REAL,
                signals       INTEGER,
                best_regime   TEXT,
                saved_at      TEXT,
                entry_price   REAL,
                UNIQUE(username, fav_id)
            )
        """)
        # Add entry_price to existing DBs that were created before this column existed
        try:
            conn.execute("ALTER TABLE user_favorites ADD COLUMN entry_price REAL")
        except Exception:
            pass  # column already exists
        # Add stock_name to existing DBs that were created before this column existed
        try:
            conn.execute("ALTER TABLE user_favorites ADD COLUMN stock_name TEXT")
        except Exception:
            pass  # column already exists
        # Advanced save system: type + analysis settings
        for _col_ddl in [
            "ALTER TABLE user_favorites ADD COLUMN save_type TEXT DEFAULT 'strategy'",
            "ALTER TABLE user_favorites ADD COLUMN risk_val INTEGER DEFAULT 1",
            "ALTER TABLE user_favorites ADD COLUMN reward_val INTEGER DEFAULT 2",
            "ALTER TABLE user_favorites ADD COLUMN period_label TEXT DEFAULT 'Medium (63d)'",
            "ALTER TABLE user_favorites ADD COLUMN combo_indicators TEXT",
            "ALTER TABLE user_favorites ADD COLUMN signal_window INTEGER DEFAULT 1",
        ]:
            try:
                conn.execute(_col_ddl)
            except Exception:
                pass
        conn.commit()


# ── Favorites persistence ─────────────────────────────────────────────────────

def load_favorites(username: str) -> list:
    """Load all saved strategies for a user from the DB."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM user_favorites WHERE username=? ORDER BY id ASC",
            (username,)
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d['id'] = d.pop('fav_id')   # normalise key to match session_state
        result.append(d)
    return result


def upsert_favorite(username: str, fav: dict) -> None:
    """Insert or update a saved strategy for a user."""
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO user_favorites
              (username, fav_id, symbol, pair, pair_display, win_rate, profit_factor,
               expectancy, avg_gain, avg_loss, signals, best_regime, saved_at, entry_price,
                             stock_name, save_type, risk_val, reward_val, period_label, combo_indicators,
                             signal_window)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(username, fav_id) DO UPDATE SET
              symbol=excluded.symbol, pair=excluded.pair,
              pair_display=excluded.pair_display, win_rate=excluded.win_rate,
              profit_factor=excluded.profit_factor, expectancy=excluded.expectancy,
              avg_gain=excluded.avg_gain, avg_loss=excluded.avg_loss,
              signals=excluded.signals, best_regime=excluded.best_regime,
              saved_at=excluded.saved_at, entry_price=excluded.entry_price,
              stock_name=excluded.stock_name,
              save_type=excluded.save_type, risk_val=excluded.risk_val,
              reward_val=excluded.reward_val, period_label=excluded.period_label,
                            combo_indicators=excluded.combo_indicators,
                            signal_window=excluded.signal_window
        """, (
            username,
            fav.get('id', ''),
            fav.get('symbol', ''),
            fav.get('pair', ''),
            fav.get('pair_display', ''),
            fav.get('win_rate', 0),
            fav.get('profit_factor', 0),
            fav.get('expectancy', 0),
            fav.get('avg_gain', 0),
            fav.get('avg_loss', 0),
            fav.get('signals', 0),
            fav.get('best_regime', ''),
            fav.get('saved_at', ''),
            fav.get('entry_price', None),
            fav.get('stock_name', ''),
            fav.get('save_type', 'strategy'),
            fav.get('risk_val', 1),
            fav.get('reward_val', 2),
            fav.get('period_label', 'Medium (63d)'),
            fav.get('combo_indicators', ''),
            fav.get('signal_window', 1),
        ))
        conn.commit()


def delete_favorite(username: str, fav_id: str) -> None:
    """Delete a saved strategy for a user."""
    with _get_conn() as conn:
        conn.execute(
            "DELETE FROM user_favorites WHERE username=? AND fav_id=?",
            (username, fav_id)
        )
        conn.commit()


# ── Password helpers ──────────────────────────────────────────────────────────

def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


def _verify_password(password: str, salt: str, stored_hash: str) -> bool:
    return _hash_password(password, salt) == stored_hash


# ── Auth operations ───────────────────────────────────────────────────────────

def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    username = username.strip()
    email    = email.strip().lower()

    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if "@" not in email or "." not in email:
        return False, "Enter a valid email address."

    try:
        salt      = secrets.token_hex(16)
        pw_hash   = _hash_password(password, salt)
        created   = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO users (username, email, password, salt, created_at) VALUES (?,?,?,?,?)",
                (username, email, pw_hash, salt, created)
            )
            conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError as e:
        if "username" in str(e).lower():
            return False, "Username already taken."
        if "email" in str(e).lower():
            return False, "Email already registered."
        return False, "Registration failed. Try again."


def login_user(username: str, password: str) -> tuple[bool, str]:
    """Verify credentials. Returns (success, message)."""
    username = username.strip()
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,)
        ).fetchone()

    if not row:
        return False, "Username not found."
    if not _verify_password(password, row["salt"], row["password"]):
        return False, "Incorrect password."
    return True, row["username"]


def get_user_count() -> int:
    with _get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


# ── Session helpers ───────────────────────────────────────────────────────────

def is_logged_in() -> bool:
    return st.session_state.get("auth_logged_in", False)


def logout():
    st.session_state.auth_logged_in = False
    st.session_state.auth_username  = ""
    st.session_state.auth_page      = "login"


# ── UI ────────────────────────────────────────────────────────────────────────

_AUTH_CSS = """
<style>
* { box-sizing: border-box; }

#MainMenu, footer, header,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], [data-testid="stSidebarNav"],
[data-testid="collapsedControl"] {
    visibility: hidden !important; display: none !important;
}

/* ===== Layout ===== */
.stApp, body {
    background: #0b0f16 !important;
}

section[data-testid="stMain"] > div.block-container,
div.block-container {
    min-height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
}

div.block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    max-width: 100% !important;
}

/* ===== Auth Card ===== */
[data-testid="stVerticalBlockBorderWrapper"] {
    width: 100% !important;
    max-width: 560px !important;
    margin-inline: auto !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div:first-child {
    background: #121823 !important;
    border: 1px solid #2a3445 !important;
    border-radius: 16px !important;
    padding: 1.45rem 1.35rem 1.25rem !important;
    box-shadow: none !important;
}

/* ===== Auth Switch Buttons ===== */
.auth-switch-wrap {
    display: flex;
    gap: 0.6rem;
    width: 100%;
    margin-bottom: 1rem;
}

/* ===== Inputs ===== */
div[data-testid="stTextInput"] { margin-bottom: 0.65rem !important; }
.stTextInput > label {
    color: #aeb9c8 !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    margin-bottom: 0.28rem !important;
    letter-spacing: 0.2px !important;
}
.stTextInput > div > div {
    background: #0f1520 !important;
    border: 1px solid #2a3445 !important;
    border-radius: 10px !important;
    transition: border-color 0.18s, box-shadow 0.18s, transform 0.1s !important;
}
.stTextInput > div > div > input {
    color: #e2e8f0 !important;
    height: 2.65rem !important;
    padding: 0 0.85rem !important;
    font-size: 0.9rem !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input::placeholder { color: #7d8a9d !important; }
.stTextInput > div > div:focus-within {
    border-color: #5a6880 !important;
    box-shadow: none !important;
    transform: none;
}

/* ===== Button ===== */
.stButton { margin-top: 0.9rem !important; }
.stButton > button {
    width: 100% !important;
    height: 2.72rem !important;
    border-radius: 10px !important;
    border: 1px solid #3b4658 !important;
    background: #1a2230 !important;
    color: #e2e8f0 !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.2px !important;
    box-shadow: none !important;
    transition: background 0.15s, border-color 0.15s !important;
}
.stButton > button:hover {
    background: #232d3e !important;
    border-color: #5a6880 !important;
}
.stButton > button:active { transform: none !important; }

/* ===== Alerts ===== */
.a-err {
    border-radius: 10px;
    background: #2a1a1d;
    border: 1px solid #5c353c;
    color: #f0b3bd;
    padding: 0.55rem 0.7rem;
    font-size: 0.8rem;
    margin-bottom: 0.9rem;
}
.a-ok {
    border-radius: 10px;
    background: #1a2a24;
    border: 1px solid #355247;
    color: #b7dbce;
    padding: 0.55rem 0.7rem;
    font-size: 0.8rem;
    margin-bottom: 0.9rem;
}
</style>
"""


def auth_wall() -> bool:
    """
    Call this at the top of your app.
    Returns True if the user is authenticated, False otherwise.
    """
    init_db()

    if DEV_BYPASS_AUTH:
        st.session_state.auth_logged_in = True
        st.session_state.auth_username = DEV_BYPASS_USER
        return True

    for k, v in [("auth_logged_in", False), ("auth_username", ""), ("auth_msg", None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    if st.session_state.auth_logged_in:
        return True

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "signin"

    st.markdown(_AUTH_CSS, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 0.92, 1])
    with col:
        with st.container(border=True):
            # ── Flash message ──
            if st.session_state.auth_msg:
                msg, kind = st.session_state.auth_msg
                cls = "a-ok" if kind == "success" else "a-err"
                st.markdown(f"<div class='{cls}'>{msg}</div>", unsafe_allow_html=True)
                st.session_state.auth_msg = None

            if st.session_state.auth_mode == "signin":
                st.markdown(
                    """
                    <style>
                    .st-key-btn_mode_signin button {
                        background: #2a3445 !important;
                        color: #f1f5f9 !important;
                        border: 1px solid #6b7b95 !important;
                        box-shadow: none !important;
                    }
                    .st-key-btn_mode_create button {
                        background: #171f2b !important;
                        color: #9aa8bc !important;
                        box-shadow: none !important;
                        border: 1px solid #364255 !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <style>
                    .st-key-btn_mode_create button {
                        background: #2a3445 !important;
                        color: #f1f5f9 !important;
                        border: 1px solid #6b7b95 !important;
                        box-shadow: none !important;
                    }
                    .st-key-btn_mode_signin button {
                        background: #171f2b !important;
                        color: #9aa8bc !important;
                        box-shadow: none !important;
                        border: 1px solid #364255 !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

            # ── Two full-width mode buttons ──
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Sign In", key="btn_mode_signin", width="stretch"):
                    st.session_state.auth_mode = "signin"
                    st.rerun()
            with b2:
                if st.button("Create Account", key="btn_mode_create", width="stretch"):
                    st.session_state.auth_mode = "create"
                    st.rerun()

            # ── SIGN IN ──
            if st.session_state.auth_mode == "signin":
                username = st.text_input("Username", key="li_user",
                                         placeholder="Enter your username")
                password = st.text_input("Password", type="password", key="li_pass",
                                         placeholder="Enter your password")

                if st.button("Sign In", key="btn_login", width="stretch"):
                    if not username or not password:
                        st.markdown("<div class='a-err'>Please fill in all fields.</div>",
                                    unsafe_allow_html=True)
                    else:
                        ok, result = login_user(username, password)
                        if ok:
                            st.session_state.auth_logged_in = True
                            st.session_state.auth_username  = result
                            st.rerun()
                        else:
                            st.markdown(f"<div class='a-err'>{result}</div>",
                                        unsafe_allow_html=True)

            # ── CREATE ACCOUNT ──
            else:
                r_user  = st.text_input("Username", key="rg_user",
                                         placeholder="Choose a username")
                r_email = st.text_input("Email", key="rg_email",
                                         placeholder="Your email address")
                r_pass  = st.text_input("Password", type="password", key="rg_pass",
                                         placeholder="At least 6 characters")
                r_conf  = st.text_input("Confirm Password", type="password", key="rg_conf",
                                         placeholder="Repeat your password")

                if st.button("Create Account", key="btn_register", width="stretch"):
                    if not r_user or not r_email or not r_pass or not r_conf:
                        st.markdown("<div class='a-err'>Please fill in all fields.</div>",
                                    unsafe_allow_html=True)
                    elif r_pass != r_conf:
                        st.markdown("<div class='a-err'>Passwords do not match.</div>",
                                    unsafe_allow_html=True)
                    else:
                        ok, msg = register_user(r_user, r_email, r_pass)
                        if ok:
                            st.session_state.auth_msg = (msg, "success")
                            st.rerun()
                        else:
                            st.markdown(f"<div class='a-err'>{msg}</div>",
                                        unsafe_allow_html=True)

    return False


def show_user_badge(location: str = "sidebar", market_status: dict = None, market_data: dict = None):
    """
    Show user badge in sidebar.
    location: "sidebar" or "header" (header now handled in app.py control panel)
    """
    if location == "header":
        # Header buttons are now in control panel in app.py
        return
        
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:0.8rem 1rem;background:#212121;border:1px solid #303030;
                    border-radius:10px;margin-bottom:1rem;'>
            <div style='font-size:0.65rem;color:#9e9e9e;text-transform:uppercase;
                        letter-spacing:0.6px;margin-bottom:0.2rem;'>Welcome</div>
            <div style='font-size:0.95rem;font-weight:700;color:#26A69A;'>
                {st.session_state.auth_username}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Logout", key="auth_logout"):
            logout()
            st.rerun()
