import random
from datetime import datetime, timedelta
import streamlit as st
from decimal import Decimal, getcontext

getcontext().prec = 28
FACTORS = [Decimal(10), Decimal(100), Decimal(1000)]

# --- SIDEOPPSETT ---
st.set_page_config(
    page_title="Titallstrening",
    page_icon="🧮",
    initial_sidebar_state="collapsed"
)

# --- CSS ---
st.markdown("""
<style>

/* Litt mer luft øverst (viktig!) */
.block-container {
    padding-top: 2rem;
    padding-bottom: 1rem;
}

/* Kompakt spacing ellers */
div[data-testid="stVerticalBlock"] {
    gap: 0.45rem;
}

/* Kompakte metrikker */
div[data-testid="metric-container"] {
    padding-top: 0.15rem;
    padding-bottom: 0.15rem;
}

/* FIKS: sørg for at tittelen ikke blir kuttet */
h1 {
    margin-top: 0 !important;
    margin-bottom: 0.5rem !important;
    line-height: 1.3 !important;
    padding-top: 0.2rem !important;
}

/* Større inputfelt */
input[type="text"] {
    font-size: 1.8rem !important;
    text-align: center;
    padding: 0.6rem !important;
}

input::placeholder {
    font-size: 1.2rem;
}

</style>
""", unsafe_allow_html=True)

# --- HJELPEFUNKSJONER ---

def fmt(n: Decimal) -> str:
    if n == n.to_integral():
        s = str(int(n))
    else:
        s = format(n, "f").rstrip("0").rstrip(".")
    return s.replace(".", ",") if s else "0"

def parse_user(s: str) -> Decimal:
    s = s.strip().replace(" ", "").replace(",", ".")
    return Decimal(s)

def random_number(difficulty: str) -> Decimal:
    sig = random.choice([1, 2, 3])

    if difficulty == "Hele tall":
        first = random.randint(1, 9)
        rest = "".join(str(random.randint(0, 9)) for _ in range(sig - 1))
        digits = str(first) + rest
        trailing_zeros = random.choice([0, 1, 2])
        return Decimal(digits + ("0" * trailing_zeros))

    if difficulty == "Desimaltall":
        first = str(random.randint(1, 9))
        rest = "".join(str(random.randint(0, 9)) for _ in range(sig - 1))
        digits = first + rest

        if random.random() < 0.35:
            return Decimal(f"0.{digits}")
        if len(digits) == 1:
            return Decimal(digits)
        split = random.randint(1, len(digits) - 1)
        return Decimal(digits[:split] + "." + digits[split:])

    return random_number(random.choice(["Hele tall", "Desimaltall"]))

def build_new_task():
    a = random_number(st.session_state.difficulty)
    op = random.choice(st.session_state.ops)
    f = random.choice(st.session_state.factors)

    if op == "*":
        correct = a * f
        text = f"{fmt(a)} · {fmt(f)} = ?"
    else:
        correct = a / f
        text = f"{fmt(a)} : {fmt(f)} = ?"

    st.session_state.task_text = text
    st.session_state.correct = correct

def reset_session():
    st.session_state.correct_count = 0
    st.session_state.tried = 0
    st.session_state.finished = False
    st.session_state.last_feedback = None
    st.session_state.clear_answer = True

    if st.session_state.mode == "Antall oppgaver":
        st.session_state.remaining = int(st.session_state.qcount)
        st.session_state.pop("end_time", None)
    else:
        st.session_state.end_time = (
            datetime.utcnow() + timedelta(minutes=int(st.session_state.minutes))
        ).timestamp()
        st.session_state.pop("remaining", None)

    build_new_task()

def submit_answer(user_input: str):
    try:
        u = parse_user(user_input)
    except Exception:
        st.session_state.last_feedback = "parse_error"
        st.rerun()

    st.session_state.tried += 1

    if u == st.session_state.correct:
        st.session_state.correct_count += 1
        st.session_state.last_feedback = "correct"

        if st.session_state.mode == "Antall oppgaver":
            st.session_state.remaining -= 1
            if st.session_state.remaining <= 0:
                st.session_state.remaining = 0
                st.session_state.finished = True
            else:
                build_new_task()
        else:
            build_new_task()

        st.session_state.clear_answer = True
        st.rerun()

    st.session_state.last_feedback = "wrong"
    st.session_state.clear_answer = False
    st.rerun()

# --- INIT ---
for key, default in [
    ("task_text", None),
    ("answer", ""),
    ("finished", False),
    ("correct_count", 0),
    ("tried", 0),
    ("last_feedback", None),
    ("clear_answer", False),
    ("mode", "Antall oppgaver"),
    ("ops", ["*", "/"]),
    ("factors", FACTORS),
    ("difficulty", "Blandet"),
    ("qcount", 20),
    ("minutes", 2),
]:
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.task_text is None:
    build_new_task()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Innstillinger")

    st.session_state.mode = st.selectbox(
        "Øktmodus",
        ["Antall oppgaver", "Tid"],
        index=0 if st.session_state.mode == "Antall oppgaver" else 1,
    )

    ops = st.multiselect(
        "Operasjon",
        ["Gange (·)", "Dele (:)"],
        default=["Gange (·)", "Dele (:)"] if set(st.session_state.ops) == {"*", "/"} else
                (["Gange (·)"] if st.session_state.ops == ["*"] else ["Dele (:)"])
    )
    st.session_state.ops = ["*" if o.startswith("Gange") else "/" for o in ops] or ["*", "/"]

    factors = st.multiselect(
        "Faktorer",
        ["10", "100", "1000"],
        default=[str(f) for f in st.session_state.factors] if st.session_state.factors else ["10", "100", "1000"]
    )
    st.session_state.factors = [Decimal(f) for f in factors] or FACTORS

    st.session_state.difficulty = st.selectbox(
        "Talltype",
        ["Hele tall", "Desimaltall", "Blandet"],
        index=["Hele tall", "Desimaltall", "Blandet"].index(st.session_state.difficulty),
    )

    if st.session_state.mode == "Antall oppgaver":
        st.session_state.qcount = st.number_input("Antall oppgaver", 1, 200, int(st.session_state.qcount))
        if "remaining" not in st.session_state:
            st.session_state.remaining = int(st.session_state.qcount)
    else:
        st.session_state.minutes = st.number_input("Minutter", 1, 60, int(st.session_state.minutes))
        if "end_time" not in st.session_state:
            st.session_state.end_time = (
                datetime.utcnow() + timedelta(minutes=int(st.session_state.minutes))
            ).timestamp()

    if st.button("Start på nytt"):
        reset_session()
        st.rerun()

# --- HEADER ---
st.markdown(
    "<h1 style='font-size:2.3rem; line-height:1.2; margin:0;'>Titallstrening</h1>",
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Riktige", st.session_state.correct_count)
with col2:
    st.metric("Forsøk", st.session_state.tried)
with col3:
    if st.session_state.mode == "Antall oppgaver":
        st.metric("Igjen", st.session_state.get("remaining", 0))
    else:
        end = st.session_state.get("end_time", datetime.utcnow().timestamp())
        t = max(0, int(end - datetime.utcnow().timestamp()))
        m, s = divmod(t, 60)
        st.metric("Tid", f"{m:02d}:{s:02d}")

st.divider()

# --- TIDSAVSLUTNING ---
if st.session_state.mode == "Tid":
    end = st.session_state.get("end_time")
    if end is not None and datetime.utcnow().timestamp() >= end:
        st.session_state.finished = True

# --- OPPGAVE / SLUTT ---
if st.session_state.finished:
    tried = st.session_state.tried
    correct = st.session_state.correct_count
    pct = int(round((100 * correct / tried), 0)) if tried else 0

    if tried > 0 and correct == tried:
        st.balloons()
        st.success(f"🎉 Perfekt økt! {correct} av {tried} (100%).")
    else:
        st.success(f"Økten er ferdig. Resultat: {correct} riktige av {tried} (≈ {pct}%).")

    if st.button("Start ny økt", type="primary", use_container_width=True):
        reset_session()
        st.rerun()

else:
    if st.session_state.last_feedback == "correct":
        st.success("Riktig! ✅")
    elif st.session_state.last_feedback == "wrong":
        st.error("Feil. Prøv igjen.")
    elif st.session_state.last_feedback == "parse_error":
        st.warning("Kunne ikke tolke svaret. Bruk tall med komma eller punktum.")

    st.markdown(
        f"<div style='font-size:2.2rem; font-weight:700; margin:0.2rem 0 0.8rem 0;'>{st.session_state.task_text}</div>",
        unsafe_allow_html=True
    )

    if st.session_state.clear_answer:
        st.session_state["answer"] = ""
        st.session_state["clear_answer"] = False

    with st.form("answer_form"):
        user_input = st.text_input("Svar:", key="answer")
        submitted = st.form_submit_button("Sjekk svar", use_container_width=True)

    if submitted:
        submit_answer(user_input)

    if st.button("Ny oppgave", use_container_width=True):
        build_new_task()
        st.session_state.clear_answer = True
        st.session_state.last_feedback = None
        st.rerun()

st.caption("Bruk komma eller punktum.")
