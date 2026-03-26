import random
from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components
from decimal import Decimal, getcontext

getcontext().prec = 28
FACTORS = [Decimal(10), Decimal(100), Decimal(1000)]

# --- SIDEOPPSETT ---
st.set_page_config(
    page_title="Titallstrening",
    page_icon="🧮",
    initial_sidebar_state="collapsed"
)

# --- CSS (KOMPRIMERING + STØRRE INPUT) ---
st.markdown("""
<style>

/* Mindre luft øverst */
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 1rem;
}

/* Tettere elementer */
div[data-testid="stVerticalBlock"] {
    gap: 0.5rem;
}

/* Kompakte metrikker */
div[data-testid="metric-container"] {
    padding-top: 0.2rem;
    padding-bottom: 0.2rem;
}

/* Mindre margin overskrifter */
h1 {
    margin-bottom: 0.3rem;
}

/* STØRRE INPUTTEKST */
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
        s = format(n, 'f').rstrip('0').rstrip('.')
    return s.replace('.', ',') if s else '0'

def parse_user(s: str) -> Decimal:
    s = s.strip().replace(' ', '').replace(',', '.')
    return Decimal(s)

def random_number(difficulty: str) -> Decimal:
    sig = random.choice([1, 2, 3])

    if difficulty == "Hele tall":
        first = random.randint(1, 9)
        rest = "".join(str(random.randint(0, 9)) for _ in range(sig - 1))
        digits = str(first) + rest
        trailing_zeros = random.choice([0, 1, 2])
        return Decimal(digits + ("0" * trailing_zeros))

    elif difficulty == "Desimaltall":
        first = str(random.randint(1, 9))
        rest = "".join(str(random.randint(0, 9)) for _ in range(sig - 1))
        digits = first + rest

        if random.random() < 0.35:
            return Decimal(f"0.{digits}")
        else:
            if len(digits) == 1:
                return Decimal(digits)
            split = random.randint(1, len(digits) - 1)
            return Decimal(digits[:split] + "." + digits[split:])

    else:
        return random_number(random.choice(["Hele tall", "Desimaltall"]))

def build_new_task():
    a = random_number(st.session_state.difficulty)
    op = random.choice(st.session_state.ops)
    f = random.choice(st.session_state.factors)

    if op == '*':
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
        st.session_state.remaining = st.session_state.qcount
    else:
        st.session_state.end_time = (datetime.utcnow() + timedelta(minutes=st.session_state.minutes)).timestamp()

    build_new_task()

def submit_answer(user_input):
    try:
        u = parse_user(user_input)
    except:
        st.session_state.last_feedback = "parse_error"
        return

    st.session_state.tried += 1

    if u == st.session_state.correct:
        st.session_state.correct_count += 1
        st.session_state.last_feedback = "correct"

        if st.session_state.mode == "Antall oppgaver":
            st.session_state.remaining -= 1
            if st.session_state.remaining == 0:
                st.session_state.finished = True
            else:
                build_new_task()
        else:
            build_new_task()

        st.session_state.clear_answer = True
        st.rerun()

    else:
        st.session_state.last_feedback = "wrong"

# --- SIDEBAR ---

with st.sidebar:
    st.header("Innstillinger")

    st.session_state.mode = st.selectbox("Øktmodus", ["Antall oppgaver", "Tid"])

    ops = st.multiselect("Operasjon", ["Gange (·)", "Dele (:)"], default=["Gange (·)", "Dele (:)"])
    st.session_state.ops = ['*' if o.startswith("Gange") else '/' for o in ops]

    factors = st.multiselect("Faktorer", ["10", "100", "1000"], default=["10", "100", "1000"])
    st.session_state.factors = [Decimal(f) for f in factors]

    st.session_state.difficulty = st.selectbox("Talltype", ["Hele tall", "Desimaltall", "Blandet"])

    if st.session_state.mode == "Antall oppgaver":
        st.session_state.qcount = st.number_input("Antall oppgaver", 1, 200, 20)
        if "remaining" not in st.session_state:
            st.session_state.remaining = st.session_state.qcount
    else:
        st.session_state.minutes = st.number_input("Minutter", 1, 60, 2)

    if st.button("Start på nytt"):
        reset_session()
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
]:
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.task_text is None:
    build_new_task()

# --- HEADER ---
st.markdown("<h1 style='font-size:2.3rem;'>Titallstrening</h1>", unsafe_allow_html=True)

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

# --- OPPGAVE ---
if st.session_state.finished:
    st.success("Økten er ferdig!")
else:

    if st.session_state.last_feedback == "correct":
        st.success("Riktig! ✅")
    elif st.session_state.last_feedback == "wrong":
        st.error("Feil. Prøv igjen.")
    elif st.session_state.last_feedback == "parse_error":
        st.warning("Ugyldig svar")

    st.markdown(
        f"<div style='font-size:2.2rem; font-weight:700; margin-bottom:0.8rem;'>{st.session_state.task_text}</div>",
        unsafe_allow_html=True
    )

    # Tøm input
    if st.session_state.clear_answer:
        st.session_state.answer = ""
        st.session_state.clear_answer = False

    # FORM
    with st.form("answer_form"):
        user_input = st.text_input("Svar:", key="answer")
        submitted = st.form_submit_button("Sjekk svar")

    if submitted:
        submit_answer(user_input)

    if st.button("Ny oppgave"):
        build_new_task()
        st.session_state.clear_answer = True
        st.rerun()

st.caption("Bruk komma eller punktum.")
