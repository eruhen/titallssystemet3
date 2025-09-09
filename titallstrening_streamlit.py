# Titallstrening – Streamlit (økt-slutt-logikk)
# Kjør med: streamlit run titallstrening_streamlit.py
import random
import streamlit as st
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

def new_task():
    # Ikke lag ny oppgave hvis økten er ferdig
    if st.session_state.get('finished', False):
        return
    build_new_task()
    st.session_state['answer'] = ""  # clear input

def reset_session():
    st.session_state.correct_count = 0
    st.session_state.tried = 0
    st.session_state.remaining = st.session_state.get("qcount", 20)
    st.session_state.finished = False
    new_task()

st.set_page_config(page_title="Titallstrening", page_icon="🧮")
st.title("Titallstrening – 10, 100, 1000")

with st.sidebar:
    st.header("Innstillinger")
    ops = st.multiselect("Operasjon", ["Gange (·)","Dele (:)"], default=["Gange (·)","Dele (:)"], key="ops_sel")
    st.session_state.ops = ['*' if o.startswith("Gange") else '/' for o in ops] or ['*','/']
    factors = st.multiselect("Faktorer", ["10","100","1000"], default=["10","100","1000"], key="fac_sel")
    st.session_state.factors = [Decimal(f) for f in factors] or FACTORS
    st.session_state.difficulty = st.selectbox("Talltype", ["Hele tall","Desimaltall","Blandet"], index=2, key="diff_sel")
    qcount = st.number_input("Antall oppgaver i økt", min_value=1, max_value=200, value=20, step=1, key="qcount")
    if "remaining" not in st.session_state:
        st.session_state.remaining = qcount
    if st.button("Start/Nullstill økt", key="reset_btn"):
        reset_session()

# Init first task and input key
if "task_text" not in st.session_state:
    build_new_task()
if "answer" not in st.session_state:
    st.session_state['answer'] = ""
if "finished" not in st.session_state:
    st.session_state.finished = False
if "correct_count" not in st.session_state:
    st.session_state.correct_count = 0
if "tried" not in st.session_state:
    st.session_state.tried = 0

# Header metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Riktige", st.session_state.get("correct_count", 0))
with col2:
    st.metric("Forsøkt", st.session_state.get("tried", 0))
with col3:
    st.metric("Igjen", st.session_state.get("remaining", 0))

st.divider()

# Hvis økten er ferdig: vis oppsummering og restart-knapp
if st.session_state.get("finished", False) or st.session_state.get("remaining", 0) == 0:
    st.session_state.finished = True
    tried = st.session_state.get("tried", 0)
    correct = st.session_state.get("correct_count", 0)
    pct = int(round((100*correct/tried),0)) if tried else 0
    st.success(f"🎉 Økten er ferdig! Resultat: {correct} riktige av {tried} (≈ {pct}%).")
    st.button("Start ny økt", type="primary", on_click=reset_session, use_container_width=True)
else:
    # Big task text
    st.markdown(
        f"<div style='font-size:34px; font-weight:700; margin: 10px 0 20px 0;'>{st.session_state.task_text}</div>",
        unsafe_allow_html=True
    )

    st.text_input("Svar (bruk komma eller punktum):", key="answer")

    colA, colB = st.columns([1,1])
    with colA:
        if st.button("Sjekk svar", type="primary", use_container_width=True, key="check_btn"):
            try:
                u = parse_user(st.session_state['answer'])
                st.session_state.tried = st.session_state.get("tried", 0) + 1
                if u == st.session_state.correct:
                    st.success("Riktig! ✅")
                    st.session_state.correct_count = st.session_state.get("correct_count", 0) + 1
                else:
                    st.error(f"Feil. Riktig svar: **{fmt(st.session_state.correct)}**")
                st.session_state.remaining = max(0, st.session_state.get("remaining", 0) - 1)
                if st.session_state.remaining == 0:
                    st.session_state.finished = True
            except Exception:
                st.warning("Kunne ikke tolke svaret. Bruk tall med komma eller punktum.")
    with colB:
        st.button("Ny oppgave", use_container_width=True, key="new_task_btn", on_click=new_task)

st.caption("Desimaltall vises med komma. Du kan skrive svar med komma eller punktum.")
