"""
🎛️ PANEL DE ADMINISTRACIÓN — Host
Acceso: /admin  (contraseña configurada abajo)
"""

import streamlit as st
import time
from utils.database import (
    init_db, get_all_state, set_state, get_players,
    get_answers, get_bets, update_points, set_answer_score,
    reset_all, get_player_bet
)
from utils.games import (
    GAME1_CORRECT_IDS, score_game1,
    GAME4_ACTIVE, score_game4,
    GAME3_QUESTIONS, score_game3,
    GAMES_CONFIG, INITIAL_POINTS
)

ADMIN_PASSWORD = "gymkana2024"

st.set_page_config(page_title="🎛️ Admin Gymkana", page_icon="🎛️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&family=Nunito:wght@400;600;700;800&display=swap');
:root { --primary:#FF6B35; --secondary:#FFD23F; --accent:#06D6A0; --dark:#0d0d1a; --card:#1a1a2e; }
html, body, [class*="css"] { background-color: var(--dark) !important; color: #eaeaea !important; font-family: 'Nunito', sans-serif !important; }
h1,h2,h3 { font-family:'Bangers',cursive !important; letter-spacing:2px; }
.stButton>button { background:linear-gradient(135deg,var(--primary),#ff8c42)!important; color:white!important; border:none!important; border-radius:10px!important; font-weight:800!important; transition:transform .15s!important; }
.stButton>button:hover { transform:translateY(-2px)!important; }
.btn-green>button { background:linear-gradient(135deg,#06D6A0,#00b386)!important; }
.btn-yellow>button { background:linear-gradient(135deg,var(--secondary),#ffb347)!important; color:#1a1a2e!important; }
.btn-red>button { background:linear-gradient(135deg,#e63946,#c1121f)!important; }
.card { background:var(--card); border-radius:14px; padding:18px 22px; margin:10px 0; border:1px solid rgba(255,255,255,.07); }
.phase-big { font-family:'Bangers',cursive; font-size:32px; color:var(--secondary); letter-spacing:2px; }
.stat-box { background:rgba(255,255,255,.07); border-radius:12px; padding:14px; text-align:center; }
.stat-num { font-family:'Bangers',cursive; font-size:40px; color:var(--primary); }
</style>
""", unsafe_allow_html=True)

init_db()

# ─── Auth ─────────────────────────────────────────────────────────────────────
if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False

if not st.session_state.admin_auth:
    st.markdown("<h1 style='color:#FF6B35;'>🎛️ Panel de Admin</h1>", unsafe_allow_html=True)
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.admin_auth = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def apply_bet_bonuses(game_id: int, winners: list[str]):
    """
    Apply bet bonuses/penalties.
    winners = list of player names who 'won' (got any positive score).
    """
    bets = get_bets(game_id)
    for bet in bets:
        won_game = bet["player_name"] in winners
        bet_on_win = bool(bet["bet_win"])
        amount = bet["bet_amount"]
        if won_game and bet_on_win:
            update_points(bet["player_name"], amount)     # double reward: already got game pts + bet bonus
        elif not won_game and not bet_on_win:
            update_points(bet["player_name"], amount)     # bet on losing, correct
        elif won_game and not bet_on_win:
            update_points(bet["player_name"], -amount)    # bet on losing but won
        elif not won_game and bet_on_win:
            update_points(bet["player_name"], -amount)    # bet on winning but lost

# ─── Main UI ──────────────────────────────────────────────────────────────────
st.markdown("<h1>🎛️ PANEL DE HOST — GYMKANA</h1>", unsafe_allow_html=True)

state   = get_all_state()
phase   = state.get("phase", "lobby")
game_id = int(state.get("current_game", 0))
players = get_players()

# Top stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='stat-box'><div class='stat-num'>{len(players)}</div><div>Jugadores</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='stat-box'><div class='stat-num'>{phase.upper()}</div><div>Fase</div></div>", unsafe_allow_html=True)
with col3:
    game_name = GAMES_CONFIG.get(game_id, {}).get("name", "–") if game_id else "–"
    st.markdown(f"<div class='stat-box'><div class='stat-num'>{game_id or '–'}</div><div>Juego actual</div></div>", unsafe_allow_html=True)
with col4:
    answers = get_answers(game_id) if game_id else []
    st.markdown(f"<div class='stat-box'><div class='stat-num'>{len(answers)}</div><div>Respuestas</div></div>", unsafe_allow_html=True)

st.markdown("---")

# ─── LOBBY ────────────────────────────────────────────────────────────────────
if phase == "lobby":
    st.markdown("### 🟢 Lobby — Esperando jugadores")
    
    if players:
        for p in players:
            st.markdown(f"- 🟢 **{p['name']}** — {p['points']} pts")
    else:
        st.info("Ningún jugador conectado aún. Comparte el link / QR.")

    st.markdown("---")
    st.markdown("#### Iniciar Juego 1")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎲 Abrir apuestas → Juego 1", use_container_width=True):
            set_state("current_game", "1")
            set_state("phase", "betting")
            set_state("betting_open", "true")
            st.success("¡Apuestas abiertas!")
            st.rerun()
    with c2:
        with st.expander("⚠️ Reset total"):
            if st.button("🗑️ Borrar todo y empezar de cero", use_container_width=True):
                reset_all()
                st.success("Reset hecho.")
                st.rerun()

# ─── BETTING ──────────────────────────────────────────────────────────────────
elif phase == "betting":
    game_cfg = GAMES_CONFIG.get(game_id, {})
    st.markdown(f"### 💰 Fase de apuestas — {game_cfg.get('name','')}")
    
    bets = get_bets(game_id)
    st.markdown(f"**Apuestas recibidas:** {len(bets)} / {len(players)}")
    
    for p in players:
        bet = get_player_bet(p["name"], game_id)
        icon = "✅" if bet else "⏳"
        st.markdown(f"{icon} **{p['name']}**" + (f" — apostó **{bet['bet_amount']}** pts" if bet else " — sin apuesta aún"))
    
    st.markdown("---")
    if st.button("▶️ ¡Empezar el juego!", use_container_width=True):
        set_state("phase", "playing")
        set_state("answers_open", "true")
        set_state("game_started_at", str(time.time()))
        st.success("¡Juego iniciado!")
        st.rerun()

# ─── PLAYING ──────────────────────────────────────────────────────────────────
elif phase == "playing":
    game_cfg = GAMES_CONFIG.get(game_id, {})
    st.markdown(f"### ▶️ Jugando — {game_cfg.get('name','')}")

    answers = get_answers(game_id)
    st.markdown(f"**Respuestas recibidas:** {len(answers)} / {len(players)}")
    
    for p in players:
        from utils.database import get_player_answer
        ans = get_player_answer(p["name"], game_id)
        icon = "✅" if ans else "⏳"
        st.markdown(f"{icon} {p['name']}" + (f": `{ans['answer']}`" if ans else ""))

    st.markdown("---")
    st.markdown("#### Calcular puntuación y mostrar resultados")

    # ── Game 1 scoring ──
    if game_id == 1:
        if st.button("🏆 Puntuar Juego 1 y mostrar resultados", use_container_width=True):
            answers = get_answers(1)
            winners = []
            for a in answers:
                order = a["answer"].split(",")
                pts = score_game1(order)
                update_points(a["player_name"], pts)
                set_answer_score(a["player_name"], 1, 0, pts)
                if pts > 0:
                    winners.append(a["player_name"])
            apply_bet_bonuses(1, winners)
            set_state("phase", "results")
            set_state("show_results", "true")
            st.success("¡Resultados calculados!")
            st.rerun()

    # ── Game 2 (number game) scoring ──
    elif game_id == 2:
        st.markdown(f"**Respuesta correcta:** {GAME4_ACTIVE['answer']} {GAME4_ACTIVE['unit']}")
        if st.button("🏆 Puntuar Juego 2 y mostrar resultados", use_container_width=True):
            answers = get_answers(2)
            results = score_game4(answers, GAME4_ACTIVE["answer"])
            winners = []
            for r in results:
                update_points(r["player_name"], r["points"])
                if r["points"] > 50:
                    winners.append(r["player_name"])
            apply_bet_bonuses(2, winners)
            set_state("phase", "results")
            st.success("¡Resultados calculados!")
            st.rerun()

    # ── Game 3 (voting) scoring ──
    elif game_id == 3:
        round_num = int(state.get("current_round", 0))
        q = GAME3_QUESTIONS[min(round_num, len(GAME3_QUESTIONS)-1)]
        answers_r = get_answers(3, round_num)
        
        count_a = sum(1 for a in answers_r if a["answer"] == q["option_a"])
        count_b = sum(1 for a in answers_r if a["answer"] == q["option_b"])
        
        st.markdown(f"**{q['option_a']}:** {count_a} votos  |  **{q['option_b']}:** {count_b} votos")
        
        winning = q["option_a"] if count_a >= count_b else q["option_b"]
        st.markdown(f"**Ganadora (mayoría):** {winning}")
        
        if st.button("🏆 Puntuar Juego 3 y mostrar resultados", use_container_width=True):
            results = score_game3(answers_r, winning)
            winners = [r["player_name"] for r in results if r["points"] > 0]
            for r in results:
                update_points(r["player_name"], r["points"])
            apply_bet_bonuses(3, winners)
            set_state("phase", "results")
            st.success("¡Resultados calculados!")
            st.rerun()

# ─── RESULTS ──────────────────────────────────────────────────────────────────
elif phase == "results":
    st.markdown("### 🏆 Resultados en pantalla")
    
    players = get_players()
    for i, p in enumerate(players):
        medals = ["🥇","🥈","🥉"]
        m = medals[i] if i < 3 else f"{i+1}."
        st.markdown(f"{m} **{p['name']}** — {p['points']} pts")
    
    st.markdown("---")
    st.markdown("#### ¿Qué hacemos ahora?")
    
    next_game = game_id + 1
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if next_game <= 3 and st.button(f"⏭️ Siguiente juego ({GAMES_CONFIG.get(next_game,{}).get('name','?')})", use_container_width=True):
            set_state("current_game", str(next_game))
            set_state("phase", "betting")
            set_state("betting_open", "true")
            set_state("show_results", "false")
            st.success(f"¡Apuestas abiertas para juego {next_game}!")
            st.rerun()
    with col2:
        if st.button("🏁 Terminar gymkana", use_container_width=True):
            set_state("phase", "final")
            set_state("current_game", "0")
            st.success("¡Gymkana terminada!")
            st.rerun()
    with col3:
        if st.button("🔄 Repetir mismo juego", use_container_width=True):
            set_state("phase", "betting")
            set_state("betting_open", "true")
            st.rerun()

# ─── FINAL ────────────────────────────────────────────────────────────────────
elif phase == "final":
    st.markdown("### 🎉 ¡Gymkana terminada!")
    players = get_players()
    for i, p in enumerate(players):
        medals = ["🥇","🥈","🥉"]
        m = medals[i] if i < 3 else f"{i+1}."
        st.markdown(f"{m} **{p['name']}** — {p['points']} pts")
    
    if st.button("🔄 Nueva partida", use_container_width=True):
        reset_all()
        st.rerun()

# ─── Auto refresh panel ───────────────────────────────────────────────────────
st.markdown("---")
if st.button("🔄 Refrescar", use_container_width=False):
    st.rerun()

st.markdown("<p style='opacity:.4;font-size:13px;text-align:center;'>Panel se refresca automáticamente cada 5s</p>", unsafe_allow_html=True)
time.sleep(5)
st.rerun()
