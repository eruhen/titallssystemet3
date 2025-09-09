
# Titallstrening – Streamlit (stabil Enter uten form/JS: on_change + auto-ny oppgave ved riktig)
# Kjør: streamlit run titallstrening_streamlit.py
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
    if difficulty == 'Hele tall':
        choices = [random.randint(1, 9999), random.choice([10,20,30,40,50,60,70,80,90,100,200,500,1000])]
        n = Decimal(random.choice(choices))
    elif difficulty == 'Desimaltall':
        whole = random.randint(0, 999)
        frac_places = random.choice([1,2,3])
        frac = random.randint(1, 9*(10**(frac_places-1)))
        n = Decimal(f"{whole}.{str(frac).zfill(frac_places)}")
    else:
        return random_number(random.choice(['Hele tall','Desimaltall']))
    if random.random() < 0.2:
        frac_places = random.choice([1,2,3])
        frac = random.randint(1, 9*(10**(frac_places-1)))
        n = Decimal(f"0.{str(frac).zfill(frac_places)}")
    return n

def build_new_task():
    a = random_number(st.session_state.difficulty)
    op = random.choice(st.session_state.ops)  # '*' or '/'
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
        setTimeout(tryFocus, 50);
        </script>
        """, height=0
    )

def submit_answer():
    # Kalles automatisk når innholdet i tekstfeltet endres og elev trykker Enter.
    s = st.session_state.get('answer', '')
    try:
        u = parse_user(s)
    except Exception:
        st.session_state.last_feedback = "parse_error"
        st.session_state.focus_answer = True
        return

    st.session_state.tried += 1
    if u == st.session_state.correct:
        st.session_state.correct_count += 1
        st.session_state.last_feedback = "correct"
        if st.session_state.get("mode","Antall oppgaver") == "Antall oppgaver":
            st.session_state.remaining = max(0, st.session_state.get("remaining", 0) - 1)
            if st.session_state.remaining == 0:
                st.session_state.finished = True
        # Auto: kø ny oppgave ved riktig svar
        queue_new_task()
    else:
        st.session_state.last_feedback = "wrong"
        st.session_state.focus_answer = True

st.set_page_config(page_title="Titallstrening", page_icon="🧮")
st.title("Titallstrening – 10, 100, 1000")

with st.sidebar:
    st.header("Innstillinger")
    st.session_state.mode = st.selectbox("Øktmodus", ["Antall oppgaver", "Tid"], index=0)
    ops = st.multiselect("Operasjon", ["Gange (·)","Dele (:)"], default=["Gange (·)","Dele (:)"], key="ops_sel")
    st.session_state.ops = ['*' if o.startswith("Gange") else '/' for o in ops] or ['*','/']
    factors = st.multiselect("Faktorer", ["10","100","1000"], default=["10","100","1000"], key="fac_sel")
    st.session_state.factors = [Decimal(f) for f in factors] or FACTORS
    st.session_state.difficulty = st.selectbox("Talltype", ["Hele tall","Desimaltall","Blandet"], index=2, key="diff_sel")

    if st.session_state.mode == "Antall oppgaver":
        qcount = st.number_input("Antall oppgaver i økt", min_value=1, max_value=200, value=20, step=1, key="qcount")
        if "remaining" not in st.session_state:
            st.session_state.remaining = qcount
    else:
        minutes = st.number_input("Varighet (minutter)", min_value=1, max_value=60, value=2, step=1, key="minutes")
        if "end_time" not in st.session_state:
            st.session_state.end_time = (datetime.utcnow() + timedelta(minutes=minutes)).timestamp()

    if st.button("Start/Nullstill økt", key="reset_btn"):
        reset_session()

# Init defaults
for key, default in [
    ("task_text", None), ("answer", ""), ("finished", False),
    ("correct_count", 0), ("tried", 0), ("last_feedback", None),
    ("focus_answer", False), ("spawn_new_task", False)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Prosesser ny oppgave før UI
if st.session_state.spawn_new_task:
    build_new_task()
    st.session_state.answer = ""
    st.session_state.spawn_new_task = False
    st.session_state.focus_answer = True

if st.session_state.task_text is None:
    build_new_task()

# Header metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Riktige", st.session_state.get("correct_count", 0))
with col2:
    st.metric("Forsøkt", st.session_state.get("tried", 0))
with col3:
    if st.session_state.mode == "Antall oppgaver":
        st.metric("Igjen", st.session_state.get("remaining", 0))
    else:
        end_ts = st.session_state.get("end_time", None)
        tl = max(0, int(end_ts - datetime.utcnow().timestamp())) if end_ts else 0
        m, s = divmod(tl, 60)
        st.metric("Tid igjen", f"{m:02d}:{s:02d}")

st.divider()

# Avslutt ved tid/antall
if st.session_state.mode == "Tid":
    end_ts = st.session_state.get("end_time", None)
    if end_ts is not None and datetime.utcnow().timestamp() >= end_ts:
        st.session_state.finished = True

if st.session_state.get("finished", False) or (
    st.session_state.mode == "Antall oppgaver" and st.session_state.get("remaining", 0) == 0
):
    st.session_state.finished = True
    tried = st.session_state.get("tried", 0)
    correct = st.session_state.get("correct_count", 0)
    pct = int(round((100*correct/tried),0)) if tried else 0
    if tried > 0 and correct == tried:
        st.balloons()
        st.success(f"🎉 Perfekt økt! {correct} av {tried} (100%).")
    else:
        st.success(f"Økten er ferdig. Resultat: {correct} riktige av {tried} (≈ {pct}%).")
    st.button("Start ny økt", type="primary", on_click=reset_session, use_container_width=True)

else:
    # Sist tilbakemelding
    if st.session_state.last_feedback == "correct":
        st.success("Riktig! ✅")
    elif st.session_state.last_feedback == "wrong":
        st.error("Feil. Prøv igjen.")
    elif st.session_state.last_feedback == "parse_error":
        st.warning("Kunne ikke tolke svaret. Bruk tall med komma eller punktum.")

    # Oppgavetekst
    st.markdown(
        f"<div style='font-size:34px; font-weight:700; margin: 10px 0 20px 0;'>{st.session_state.task_text}</div>",
        unsafe_allow_html=True
    )

    # Svarfelt: Enter (on_change) = sjekk svar. Ved riktig -> auto ny oppgave.
    st.text_input("Svar (bruk komma eller punktum):", key="answer", on_change=submit_answer)

    # Knapper (mus-støtte)
    colA, colB = st.columns([1,1])
    with colA:
        if st.button("Sjekk svar", type="primary", use_container_width=True, key="check_btn"):
            submit_answer()
    with colB:
        if st.button("Ny oppgave", use_container_width=True, key="new_task_btn"):
            queue_new_task()

# Fokus
if st.session_state.get("focus_answer", False):
    focus_answer_input()
    st.session_state["focus_answer"] = False

st.caption("Desimaltall vises med komma. Du kan skrive svar med komma eller punktum.")
