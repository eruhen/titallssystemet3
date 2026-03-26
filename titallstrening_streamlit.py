import random
from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components
from decimal import Decimal, getcontext

getcontext().prec = 28
FACTORS = [Decimal(10), Decimal(100), Decimal(1000)]

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
        if sig == 1:
            digits = str(first)
        else:
            rest = "".join(str(random.randint(0, 9)) for _ in range(sig - 1))
            digits = str(first) + rest

        trailing_zeros = random.choice([0, 1, 2])
        n = Decimal(digits + ("0" * trailing_zeros))

    elif difficulty == "Desimaltall":
        first = str(random.randint(1, 9))
        if sig == 1:
            rest = ""
        else:
            rest = "".join(str(random.randint(0, 9)) for _ in range(sig - 1))

        all_digits = first + rest

        if random.random() < 0.35:
            n = Decimal(f"0.{all_digits}")
        else:
            if len(all_digits) == 1:
                n = Decimal(all_digits)
            else:
                split = random.randint(1, len(all_digits) - 1)
                n = Decimal(all_digits[:split] + "." + all_digits[split:])

    else:
        return random_number(random.choice(["Hele tall", "Desimaltall"]))

    return n

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

def queue_new_task():
    st.session_state['spawn_new_task'] = True

def reset_session():
    st.session_state.correct_count = 0
    st.session_state.tried = 0
    st.session_state.finished = False
    st.session_state.last_feedback = None
    st.session_state.focus_answer = True
    st.session_state.clear_answer = True

    mode = st.session_state.get("mode", "Antall oppgaver")
    if mode == "Antall oppgaver":
        st.session_state.remaining = st.session_state.get("qcount", 20)
        st.session_state.pop("end_time", None)
    else:
        minutes = st.session_state.get("minutes", 2)
        st.session_state.end_time = (datetime.utcnow() + timedelta(minutes=minutes)).timestamp()
        st.session_state.pop("remaining", None)

    queue_new_task()

def focus_answer_input():
    components.html(
        """
        <script>
        const tryFocus = () => {
          const appRoot = window.parent.document.querySelector('section.main');
          if (!appRoot) return;
          const inputs = appRoot.querySelectorAll('input[type="text"]');
          if (inputs.length > 0) {
            inputs[0].focus();
            inputs[0].select && inputs[0].select();
          }
        };
        setTimeout(tryFocus, 80);
        </script>
        """, height=0
    )

def submit_answer(user_input):
    try:
        u = parse_user(user_input)
    except Exception:
        st.session_state.last_feedback = "parse_error"
        return

    st.session_state.tried += 1

    if u == st.session_state.correct:
        st.session_state.correct_count += 1
        st.session_state.last_feedback = "correct"

        if st.session_state.mode == "Antall oppgaver":
            st.session_state.remaining = max(0, st.session_state.remaining - 1)
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

st.set_page_config(page_title="Titallstrening", page_icon="🧮")

st.markdown("""
<style>
/* Mindre luft øverst på siden */
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 1rem;
}

/* Litt smalere avstand mellom elementer */
div[data-testid="stVerticalBlock"] {
    gap: 0.5rem;
}

/* Gjør metrics litt mer kompakte */
div[data-testid="metric-container"] {
    padding-top: 0.2rem;
    padding-bottom: 0.2rem;
}

/* Mindre luft rundt overskrifter */
h1 {
    margin-bottom: 0.3rem;
}

h2, h3 {
    margin-top: 0.2rem;
    margin-bottom: 0.4rem;
}
</style>
""", unsafe_allow_html=True)

st.title("Titallstrening – 10, 100, 1000")

with st.sidebar:
    st.header("Innstillinger")

    st.session_state.mode = st.selectbox("Øktmodus", ["Antall oppgaver", "Tid"])

    ops = st.multiselect("Operasjon", ["Gange (·)", "Dele (:)"], default=["Gange (·)", "Dele (:)"])
    st.session_state.ops = ['*' if o.startswith("Gange") else '/' for o in ops] or ['*', '/']

    factors = st.multiselect("Faktorer", ["10", "100", "1000"], default=["10", "100", "1000"])
    st.session_state.factors = [Decimal(f) for f in factors] or FACTORS

    st.session_state.difficulty = st.selectbox("Talltype", ["Hele tall", "Desimaltall", "Blandet"])

    if st.session_state.mode == "Antall oppgaver":
        st.session_state.qcount = st.number_input("Antall oppgaver", 1, 200, 20)
        if "remaining" not in st.session_state:
            st.session_state.remaining = st.session_state.qcount
    else:
        st.session_state.minutes = st.number_input("Minutter", 1, 60, 2)
        if "end_time" not in st.session_state:
            st.session_state.end_time = (datetime.utcnow() + timedelta(minutes=st.session_state.minutes)).timestamp()

    if st.button("Start/Nullstill"):
        reset_session()
        st.rerun()

for key, default in [
    ("task_text", None),
    ("answer", ""),
    ("finished", False),
    ("correct_count", 0),
    ("tried", 0),
    ("last_feedback", None),
    ("spawn_new_task", False),
    ("clear_answer", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.spawn_new_task:
    build_new_task()
    st.session_state.spawn_new_task = False

if st.session_state.task_text is None:
    build_new_task()

st.markdown("<h1 style='font-size: 2.4rem;'>Titallstrening – 10, 100, 1000</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Riktige", st.session_state.correct_count)
with col2:
    st.metric("Forsøk", st.session_state.tried)
with col3:
    if st.session_state.mode == "Antall oppgaver":
        st.metric("Igjen", st.session_state.get("remaining", 0))
    else:
        end_ts = st.session_state.get("end_time", None)
        tl = max(0, int(end_ts - datetime.utcnow().timestamp())) if end_ts else 0
        m, s = divmod(tl, 60)
        st.metric("Tid igjen", f"{m:02d}:{s:02d}")

st.divider()

if st.session_state.mode == "Tid":
    end_ts = st.session_state.get("end_time", None)
    if end_ts is not None and datetime.utcnow().timestamp() >= end_ts:
        st.session_state.finished = True

if st.session_state.finished or (
    st.session_state.mode == "Antall oppgaver" and st.session_state.get("remaining", 0) == 0
):
    st.session_state.finished = True
    st.success("Økten er ferdig!")
else:
    if st.session_state.last_feedback == "correct":
        st.success("Riktig! ✅")
    elif st.session_state.last_feedback == "wrong":
        st.error("Feil. Prøv igjen.")
    elif st.session_state.last_feedback == "parse_error":
        st.warning("Ugyldig svar")

    st.markdown(f"## {st.session_state.task_text}")

    if st.session_state.get("clear_answer", False):
        st.session_state["answer"] = ""
        st.session_state["clear_answer"] = False

    with st.form("answer_form"):
        user_input = st.text_input("Svar:", key="answer")
        submitted = st.form_submit_button("Sjekk svar")

    if submitted:
        submit_answer(user_input)

    if st.button("Ny oppgave"):
        build_new_task()
        st.session_state.clear_answer = True
        st.rerun()

    focus_answer_input()

st.caption("Bruk komma eller punktum.")
