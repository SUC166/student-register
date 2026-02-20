import streamlit as st
import json
import requests
import base64
from datetime import datetime

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
                    msg_placeholder.markdown(
                        f"<div class='success-box'>✅ {surname.strip().title()}, {first_name.strip().title()} added successfully!</div>",
                        unsafe_allow_html=True
                    )
                    st.rerun()
                else:
                    msg_placeholder.markdown(
                        f"<div class='error-box'>❌ GitHub save failed: {errmsg}</div>",
                        unsafe_allow_html=True
                    )

# ── Display table ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Registered Students")

col_refresh, _ = st.columns([1, 4])
with col_refresh:
    if st.button("🔄 Refresh"):
        st.rerun()

students, _ = load_from_github()
if students is None:
    st.error("Could not load data from GitHub.")
elif not students:
    st.info("No students registered yet.")
else:
    import pandas as pd
    rows = []
    for i, s in enumerate(students, 1):
        full = s["first_name"]
        if s.get("middle_names"):
            full += " " + s["middle_names"]
        rows.append({
            "S/N":           i,
            "Surname":       s["surname"],
            "Other Names":   full,
            "Matric Number": s["matric_no"],
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"Total students: **{len(students)}**")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download as CSV",
        data=csv,
        file_name="student_register.csv",
        mime="text/csv",
        use_container_width=True,
    )
