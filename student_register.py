import streamlit as st
import json
import requests
import base64
from datetime import datetime

# ── Session state init ────────────────────────────────────────────────────────
if "confirmed_student" not in st.session_state:
    st.session_state.confirmed_student = None

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Student Register",
    page_icon="🎓",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Sans+3:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Source Sans 3', sans-serif; color: #1a1a1a; }
h1, h2, h3 { font-family: 'Playfair Display', serif; color: #1a1a1a; }

/* White app background so all Streamlit text is readable */
.stApp { background: #ffffff; }

/* Main content wrapper */
[data-testid="stAppViewContainer"] { background: #ffffff; }
[data-testid="block-container"] { background: #ffffff; padding-top: 2rem; }

/* Inputs */
.stTextInput label { color: #1a1a1a !important; font-weight: 600; }
.stTextInput input { color: #1a1a1a !important; background: #f9f9f9 !important; border: 1px solid #ccc !important; }

/* Subheader / markdown text */
.stMarkdown p, .stMarkdown li { color: #1a1a1a; }

.register-header {
    background: #1a1a2e;
    color: #e8d5b0;
    padding: 2rem 2.5rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    border-left: 6px solid #c9a84c;
}
.register-header h1 { margin: 0; font-size: 2rem; letter-spacing: 1px; color: #e8d5b0 !important; }
.register-header p  { margin: 0.4rem 0 0; color: #c8aa70; font-size: 0.95rem; }

.success-box {
    background: #d4edda; border: 1px solid #28a745;
    border-radius: 8px; padding: 0.75rem 1rem;
    color: #155724 !important; font-weight: 600; margin-top: 0.5rem;
}
.error-box {
    background: #f8d7da; border: 1px solid #dc3545;
    border-radius: 8px; padding: 0.75rem 1rem;
    color: #721c24 !important; font-weight: 600; margin-top: 0.5rem;
}

/* Confirmation card */
.confirm-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #c9a84c;
    border-radius: 14px;
    padding: 2rem 2.5rem;
    margin-top: 1.5rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.18);
    position: relative;
    overflow: hidden;
}
.confirm-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #c9a84c, #e8d5b0, #c9a84c);
}
.confirm-card-title {
    font-family: 'Playfair Display', serif;
    color: #e8d5b0;
    font-size: 1.2rem;
    margin: 0 0 1.5rem;
    letter-spacing: 0.5px;
}
.confirm-card-title span {
    display: inline-block;
    margin-right: 0.5rem;
}
.confirm-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0;
    border-bottom: 1px solid rgba(201,168,76,0.2);
}
.confirm-row:last-child { border-bottom: none; }
.confirm-label {
    color: #c8aa70;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}
.confirm-value {
    color: #ffffff;
    font-size: 1rem;
    font-weight: 600;
    text-align: right;
}
.confirm-matric {
    font-family: 'Courier New', monospace;
    background: rgba(201,168,76,0.15);
    border: 1px solid rgba(201,168,76,0.4);
    border-radius: 6px;
    padding: 0.25rem 0.6rem;
    color: #e8d5b0;
    letter-spacing: 2px;
    font-size: 1rem;
}
.confirm-footer {
    margin-top: 1.2rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(201,168,76,0.25);
    color: #c8aa70;
    font-size: 0.8rem;
    text-align: center;
    font-style: italic;
}

/* Dataframe text */
[data-testid="stDataFrame"] { color: #1a1a1a; }

div[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Load secrets ──────────────────────────────────────────────────────────────
try:
    GH_TOKEN  = st.secrets["github"]["token"]
    GH_REPO   = st.secrets["github"]["repo"]
    GH_BRANCH = st.secrets["github"].get("branch", "main")
except KeyError:
    st.error(
        "⚠️ GitHub secrets not configured. "
        "Add `[github]` with `token`, `repo`, and optionally `branch` to your Streamlit secrets."
    )
    st.stop()

DATA_FILE = "students.json"

# ── GitHub helpers ────────────────────────────────────────────────────────────
def load_from_github():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{DATA_FILE}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers, params={"ref": GH_BRANCH})
    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data["sha"]
    elif r.status_code == 404:
        return [], None
    else:
        st.error(f"GitHub load error {r.status_code}: {r.json().get('message')}")
        return None, None

def save_to_github(students, sha):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{DATA_FILE}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    content = base64.b64encode(json.dumps(students, indent=2).encode()).decode()
    payload = {
        "message": f"Update student register – {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "content": content,
        "branch": GH_BRANCH,
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code in (200, 201), r.json().get("message", "")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="register-header">
    <h1>🎓 Student Register</h1>
    <p>Enter student details below. Names are stored alphabetically by surname.</p>
</div>
""", unsafe_allow_html=True)

# ── Entry form ────────────────────────────────────────────────────────────────
st.subheader("Add a Student")
with st.form("entry_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        surname      = st.text_input("Surname *")
        first_name   = st.text_input("First Name *")
    with col2:
        middle_names = st.text_input("Middle Name(s)", help="Optional")
        matric_no    = st.text_input("Matric Number *", help="Exactly 11 digits, numbers only")
    submitted = st.form_submit_button("➕ Add Student", use_container_width=True)

msg_placeholder = st.empty()

if submitted:
    errors = []
    if not surname.strip():    errors.append("Surname is required.")
    if not first_name.strip(): errors.append("First name is required.")
    matric_clean = matric_no.strip()
    if not matric_clean.isdigit() or len(matric_clean) != 11:
        errors.append("Matric number must be exactly 11 digits (numbers only).")

    if errors:
        msg_placeholder.markdown(
            "<div class='error-box'>⚠️ " + "<br>".join(errors) + "</div>",
            unsafe_allow_html=True
        )
    else:
        students, sha = load_from_github()
        if students is None:
            msg_placeholder.markdown(
                "<div class='error-box'>❌ Could not reach GitHub. Check your secrets configuration.</div>",
                unsafe_allow_html=True
            )
        else:
            norm_name  = (surname.strip().lower(), first_name.strip().lower(), middle_names.strip().lower())
            dup_name   = any(
                (s["surname"].lower(), s["first_name"].lower(), s.get("middle_names","").lower()) == norm_name
                for s in students
            )
            dup_matric = any(s["matric_no"] == matric_clean for s in students)

            if dup_name:
                msg_placeholder.markdown(
                    "<div class='error-box'>⚠️ A student with this exact name already exists.</div>",
                    unsafe_allow_html=True
                )
            elif dup_matric:
                msg_placeholder.markdown(
                    "<div class='error-box'>⚠️ This matric number is already registered.</div>",
                    unsafe_allow_html=True
                )
            else:
                students.append({
                    "surname":      surname.strip().title(),
                    "first_name":   first_name.strip().title(),
                    "middle_names": middle_names.strip().title(),
                    "matric_no":    matric_clean,
                })
                students.sort(key=lambda s: (
                    s["surname"].lower(),
                    s["first_name"].lower(),
                    s.get("middle_names","").lower()
                ))
                ok, errmsg = save_to_github(students, sha)
                if ok:
                    st.session_state.confirmed_student = {
                        "surname":      surname.strip().title(),
                        "first_name":   first_name.strip().title(),
                        "middle_names": middle_names.strip().title(),
                        "matric_no":    matric_clean,
                        "registered_at": datetime.utcnow().strftime("%d %b %Y, %H:%M UTC"),
                    }
                else:
                    msg_placeholder.markdown(
                        f"<div class='error-box'>❌ GitHub save failed: {errmsg}</div>",
                        unsafe_allow_html=True
                    )

# ── Confirmation card (shown only to the student who just registered) ─────────
if st.session_state.confirmed_student:
    s = st.session_state.confirmed_student
    full_name = s["first_name"]
    if s.get("middle_names"):
        full_name += " " + s["middle_names"]

    card_style = """
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #c9a84c;
        border-radius: 14px;
        padding: 2rem 2.5rem;
        margin-top: 1rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        border-top: 4px solid #c9a84c;
    """
    title_style = "font-family: 'Playfair Display', serif; color: #e8d5b0; font-size: 1.15rem; margin: 0 0 1.5rem; letter-spacing: 0.5px;"
    row_style   = "display: flex; justify-content: space-between; align-items: center; padding: 0.65rem 0; border-bottom: 1px solid rgba(201,168,76,0.2);"
    row_last    = "display: flex; justify-content: space-between; align-items: center; padding: 0.65rem 0;"
    label_style = "color: #c8aa70; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase;"
    value_style = "color: #ffffff; font-size: 1rem; font-weight: 600; text-align: right;"
    matric_style= "font-family: 'Courier New', monospace; background: rgba(201,168,76,0.15); border: 1px solid rgba(201,168,76,0.4); border-radius: 6px; padding: 0.2rem 0.6rem; color: #e8d5b0; letter-spacing: 2px;"
    footer_style= "margin-top: 1.2rem; padding-top: 1rem; border-top: 1px solid rgba(201,168,76,0.25); color: #c8aa70; font-size: 0.8rem; text-align: center; font-style: italic;"

    st.markdown(f"""
<div style="{card_style}">
    <p style="{title_style}">✅ Registration Successful — Please verify your details</p>
    <div style="{row_style}">
        <span style="{label_style}">Surname</span>
        <span style="{value_style}">{s['surname']}</span>
    </div>
    <div style="{row_style}">
        <span style="{label_style}">Other Names</span>
        <span style="{value_style}">{full_name}</span>
    </div>
    <div style="{row_style}">
        <span style="{label_style}">Matric Number</span>
        <span style="{value_style}"><span style="{matric_style}">{s['matric_no']}</span></span>
    </div>
    <div style="{row_last}">
        <span style="{label_style}">Registered At</span>
        <span style="{value_style}">{s['registered_at']}</span>
    </div>
    <div style="{footer_style}">🔒 This card is only visible to you. Please confirm the details above are correct before leaving this page.</div>
</div>
""", unsafe_allow_html=True)

    if st.button("✔️ Confirmed — Register another student", use_container_width=True):
        st.session_state.confirmed_student = None
        st.rerun()
