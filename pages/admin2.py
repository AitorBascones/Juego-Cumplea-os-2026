"""
🎛️ PANEL DE HOST — controla el flujo ronda a ronda
Fases por ronda: betting → playing → round_results → (next round o game_results)
"""
import streamlit as st
import time
from utils.db_postgre import (
    init_db, get_all_state, set_state, get_players,
    get_answers, get_bets, get_player_bet, update_points,
    set_answer_score, reset_all
)

from utils.games_2 import (
    get_game1_correct_ids, score_game1,
    get_game2_round, score_game2,
    get_game3_round, score_game3,
    GAMES_CONFIG,
)

ADMIN_PASSWORD = "gymkana2024"

st.set_page_config(page_title="🎛️ Admin Gymkana", page_icon="🎛️", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&family=Nunito:wght@400;600;700;800&display=swap');
:root{--primary:#FF6B35;--yellow:#FFD23F;--green:#06D6A0;--dark:#0d0d1a;--card:#1a1a2e;}
html,body,[class*="css"]{background:var(--dark)!important;color:#eaeaea!important;font-family:'Nunito',sans-serif!important;}
h1,h2,h3{font-family:'Bangers',cursive!important;letter-spacing:2px;}
.stButton>button{background:linear-gradient(135deg,var(--primary),#ff8c42)!important;color:white!important;border:none!important;border-radius:10px!important;font-weight:800!important;transition:transform .15s!important;}
.stButton>button:hover{transform:translateY(-2px)!important;}
.card{background:var(--card);border-radius:14px;padding:18px 22px;margin:10px 0;border:1px solid rgba(255,255,255,.07);}
.stat{background:rgba(255,255,255,.07);border-radius:12px;padding:14px;text-align:center;}
.stat-n{font-family:'Bangers',cursive;font-size:38px;color:var(--primary);}
.ok{color:#06D6A0;font-weight:700;}
.wait{color:#aaa;}
.badge{background:linear-gradient(135deg,var(--yellow),#ffb347);color:#1a1a2e;border-radius:20px;padding:4px 14px;font-weight:800;}
</style>
""", unsafe_allow_html=True)

init_db()

# ── Auth ───────────────────────────────────────────────────────────────────────
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

# ── Scoring helpers ────────────────────────────────────────────────────────────
def apply_bets(game_id, round_num, winner_names: list):
    for bet in get_bets(game_id, round_num):
        won_game  = bet["player_name"] in winner_names
        bet_on_win = bool(bet["bet_win"])
        amount    = bet["bet_amount"]
        if won_game == bet_on_win:
            update_points(bet["player_name"], amount)   # acertó la apuesta → bonus
        else:
            update_points(bet["player_name"], -amount)  # falló la apuesta → penalización

def score_and_apply_game1(game_id, round_num):
    answers = get_answers(game_id, round_num)
    winners = []
    for a in answers:
        order = a["answer"].split(",")
        pts   = score_game1(order, round_num)
        update_points(a["player_name"], pts)
        set_answer_score(a["player_name"], game_id, round_num, pts)
        if pts > 0:
            winners.append(a["player_name"])
    apply_bets(game_id, round_num, winners)
    return answers

def score_and_apply_game2(game_id, round_num):
    q       = get_game2_round(round_num)
    answers = get_answers(game_id, round_num)
    results = score_game2(answers, q["answer"])
    winners = []
    for r in results:
        update_points(r["player_name"], r["points"])
        set_answer_score(r["player_name"], game_id, round_num, r["points"])
        if r["points"] > 50:
            winners.append(r["player_name"])
    apply_bets(game_id, round_num, winners)
    return results, q

def score_and_apply_game3(game_id, round_num):
    q       = get_game3_round(round_num)
    answers = get_answers(game_id, round_num)
    count_a = sum(1 for a in answers if a["answer"] == q["option_a"])
    count_b = sum(1 for a in answers if a["answer"] == q["option_b"])
    winning = q["option_a"] if count_a >= count_b else q["option_b"]
    results = score_game3(answers, winning)
    winners = []
    for r in results:
        update_points(r["player_name"], r["points"])
        if r["points"] > 0:
            winners.append(r["player_name"])
    apply_bets(game_id, round_num, winners)
    return results, winning, count_a, count_b, q

# ── Transition helpers ─────────────────────────────────────────────────────────
def open_betting_for(game_id, round_num):
    set_state("current_game",  str(game_id))
    set_state("current_round", str(round_num))
    set_state("phase",         "betting")
    set_state("betting_open",  "true")
    set_state("answers_open",  "false")

def open_playing():
    set_state("phase",        "playing")
    set_state("betting_open", "false")
    set_state("answers_open", "true")
    set_state("game_started_at", str(time.time()))

def open_round_results(rounds_played):
    set_state("phase",         "round_results")
    set_state("rounds_played", str(rounds_played))
    set_state("answers_open",  "false")

def open_game_results():
    set_state("phase", "game_results")

# ══════════════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<h1>🎛️ PANEL DE HOST — GYMKANA</h1>", unsafe_allow_html=True)

state     = get_all_state()
phase     = state.get("phase", "lobby")
game_id   = int(state.get("current_game",  0))
round_num = int(state.get("current_round", 0))
rounds_played = int(state.get("rounds_played", 0))
players   = get_players()
answers   = get_answers(game_id, round_num) if game_id else []
bets      = get_bets(game_id, round_num) if game_id else []
cfg       = GAMES_CONFIG.get(game_id, {})
total_rounds = cfg.get("total_rounds", 1)

# Stats row
c1,c2,c3,c4,c5 = st.columns(5)
with c1: st.markdown(f"<div class='stat'><div class='stat-n'>{len(players)}</div>Jugadores</div>", unsafe_allow_html=True)
with c2: st.markdown(f"<div class='stat'><div class='stat-n'>{phase.upper().replace('_',' ')}</div>Fase</div>", unsafe_allow_html=True)
with c3: st.markdown(f"<div class='stat'><div class='stat-n'>{game_id or '–'}</div>Juego</div>", unsafe_allow_html=True)
with c4: st.markdown(f"<div class='stat'><div class='stat-n'>{round_num+1 if game_id else '–'}</div>Ronda</div>", unsafe_allow_html=True)
with c5: st.markdown(f"<div class='stat'><div class='stat-n'>{len(answers)}/{len(players)}</div>Respuestas</div>", unsafe_allow_html=True)

st.markdown("---")

# ── LOBBY ──────────────────────────────────────────────────────────────────────
if phase == "lobby":
    st.markdown("### 🟢 Lobby")
    if players:
        for p in players:
            st.markdown(f"🟢 **{p['name']}** — {p['points']} pts")
    else:
        st.info("Ningún jugador conectado aún.")
    st.markdown("---")
    st.markdown("#### ¿Qué juego empezamos?")
    cols = st.columns(len(GAMES_CONFIG))
    for i, (gid, gcfg) in enumerate(GAMES_CONFIG.items()):
        with cols[i]:
            if st.button(f"{gcfg['name']}\n({gcfg['total_rounds']} rondas)", use_container_width=True):
                open_betting_for(gid, 0)
                set_state("rounds_played", "0")
                st.success(f"¡Apuestas abiertas para {gcfg['name']}!")
                st.rerun()
    st.markdown("---")
    with st.expander("⚠️ Reset total"):
        if st.button("🗑️ Borrar todo y empezar de cero", use_container_width=True):
            reset_all(); st.rerun()

# ── BETTING ────────────────────────────────────────────────────────────────────
elif phase == "betting":
    st.markdown(f"### 💰 Apuestas — {cfg.get('name','')} · Ronda {round_num+1}/{total_rounds}")
    st.markdown(f"**Apuestas recibidas:** {len(bets)} / {len(players)}")
    for p in players:
        bet  = get_player_bet(p["name"], game_id, round_num)
        icon = "✅" if bet else "⏳"
        extra = f" — **{bet['bet_amount']} pts** a {'ganar' if bet['bet_win'] else 'perder'}" if bet else ""
        st.markdown(f"{icon} **{p['name']}**{extra}")
    st.markdown("---")
    if st.button("▶️ ¡Abrir el juego ahora!", use_container_width=True):
        open_playing()
        st.success("¡Juego abierto!")
        st.rerun()

# ── PLAYING ────────────────────────────────────────────────────────────────────
elif phase == "playing":
    st.markdown(f"### ▶️ Jugando — {cfg.get('name','')} · Ronda {round_num+1}/{total_rounds}")

    # Progress bar
    pct = len(answers)/max(len(players),1)
    st.progress(pct, text=f"{len(answers)}/{len(players)} respuestas recibidas")

    for p in players:
        ans  = get_player_answer(p["name"], game_id, round_num)
        icon = "✅" if ans else "⏳"
        extra = f": `{ans['answer']}`" if ans else ""
        st.markdown(f"{icon} {p['name']}{extra}")

    st.markdown("---")

    # Game-specific info for admin
    if game_id == 2:
        q = get_game2_round(round_num)
        st.info(f"🔑 Respuesta correcta (solo tú la ves): **{q['answer']:,} {q['unit']}**")
    elif game_id == 3:
        q = get_game3_round(round_num)
        st.info(f"Opciones: **{q['option_a']}** vs **{q['option_b']}**")

    if st.button("⏹️ Cerrar respuestas y puntuar", use_container_width=True):
        # Score depending on game
        if game_id == 1:
            score_and_apply_game1(game_id, round_num)
        elif game_id == 2:
            score_and_apply_game2(game_id, round_num)
        elif game_id == 3:
            score_and_apply_game3(game_id, round_num)
        open_round_results(round_num + 1)
        st.success("✅ Puntuación aplicada. Mostrando resultados de ronda.")
        st.rerun()

# ── ROUND RESULTS ──────────────────────────────────────────────────────────────
elif phase == "round_results":
    st.markdown(f"### 📊 Resultados — {cfg.get('name','')} · Ronda {round_num+1}/{total_rounds}")

    # Show scored results
    answers_r = get_answers(game_id, round_num)
    if game_id == 2:
        q = get_game2_round(round_num)
        st.markdown(f"**✅ Respuesta correcta: {q['answer']:,} {q['unit']}**")
        results = score_game2(answers_r, q["answer"])
        for r in results:
            st.markdown(f"- **{r['player_name']}**: {r['guess']} → **+{r['points']} pts**")
    elif game_id == 3:
        q = get_game3_round(round_num)
        count_a = sum(1 for a in answers_r if a["answer"] == q["option_a"])
        count_b = sum(1 for a in answers_r if a["answer"] == q["option_b"])
        winning = q["option_a"] if count_a >= count_b else q["option_b"]
        st.markdown(f"{q['option_a']}: **{count_a}** | {q['option_b']}: **{count_b}** → Mayoría: **{winning}**")
    elif game_id == 1:
        correct = get_game1_correct_ids(round_num)
        st.markdown(f"**Orden correcto:** {' → '.join(correct)}")

    st.markdown("**Clasificación actual:**")
    for i, p in enumerate(get_players()):
        medals = ["🥇","🥈","🥉"]
        m = medals[i] if i < 3 else f"{i+1}."
        st.markdown(f"{m} **{p['name']}** — {p['points']} pts")

    st.markdown("---")
    next_round = round_num + 1

    if next_round < total_rounds:
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"⏭️ Siguiente ronda ({next_round+1}/{total_rounds})", use_container_width=True):
                open_betting_for(game_id, next_round)
                st.success(f"Apuestas abiertas para ronda {next_round+1}.")
                st.rerun()
        with col2:
            if st.button("🏁 Terminar este juego aquí", use_container_width=True):
                open_game_results()
                st.rerun()
    else:
        st.success(f"🎉 ¡Todas las rondas de {cfg['name']} completadas!")
        if st.button("🏁 Ver resultados finales del juego", use_container_width=True):
            open_game_results()
            st.rerun()

# ── GAME RESULTS ───────────────────────────────────────────────────────────────
elif phase == "game_results":
    st.markdown(f"### 🏆 Fin del juego: {cfg.get('name','')}")
    for i, p in enumerate(get_players()):
        medals = ["🥇","🥈","🥉"]
        m = medals[i] if i < 3 else f"{i+1}."
        st.markdown(f"{m} **{p['name']}** — {p['points']} pts")
    st.markdown("---")
    st.markdown("#### ¿Qué hacemos ahora?")
    other_games = {gid: gcfg for gid, gcfg in GAMES_CONFIG.items() if gid != game_id}
    cols = st.columns(len(other_games) + 1)
    for i, (gid, gcfg) in enumerate(other_games.items()):
        with cols[i]:
            if st.button(f"➡️ Jugar {gcfg['name']}", use_container_width=True):
                open_betting_for(gid, 0)
                set_state("rounds_played", "0")
                st.rerun()
    with cols[-1]:
        if st.button("🏁 Terminar gymkana", use_container_width=True):
            set_state("phase", "final")
            set_state("current_game", "0")
            st.rerun()

# ── FINAL ──────────────────────────────────────────────────────────────────────
elif phase == "final":
    st.markdown("### 🎉 ¡Gymkana terminada!")
    for i, p in enumerate(get_players()):
        medals = ["🥇","🥈","🥉"]
        m = medals[i] if i < 3 else f"{i+1}."
        st.markdown(f"{m} **{p['name']}** — {p['points']} pts")
    st.markdown("---")
    if st.button("🔄 Nueva partida completa", use_container_width=True):
        reset_all(); st.rerun()

# ── Auto-refresh ───────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("<p style='opacity:.35;font-size:12px;text-align:center;'>Autorefresh cada 5s</p>", unsafe_allow_html=True)
time.sleep(5)
st.rerun()
