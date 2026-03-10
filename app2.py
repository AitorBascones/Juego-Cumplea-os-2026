"""
🎮 GYMKANA — Vista del jugador
Flujo por ronda: betting → playing → round_results → (siguiente ronda) → game_results → final
"""
import streamlit as st
import time
from utils.db_postgre import (
    init_db, register_player, get_player, get_all_state,
    get_players, place_bet, get_player_bet, submit_answer,
    get_player_answer, get_answers, update_points
)
from utils.games_2 import (
    get_game1_round, get_game1_correct_ids, score_game1,
    get_game2_round, score_game2,
    get_game3_round, score_game3,
    GAMES_CONFIG, BET_OPTIONS,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="🎮 Gymkana", page_icon="🎮",
                   layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&family=Nunito:wght@400;600;700;800&display=swap');
:root{--primary:#FF6B35;--yellow:#FFD23F;--green:#06D6A0;--dark:#1a1a2e;--card:#16213e;--text:#eaeaea;}
html,body,[class*="css"]{background:var(--dark)!important;color:var(--text)!important;font-family:'Nunito',sans-serif!important;}
h1,h2,h3{font-family:'Bangers',cursive!important;letter-spacing:2px;}
.stButton>button{background:linear-gradient(135deg,var(--primary),#ff8c42)!important;color:white!important;border:none!important;border-radius:12px!important;font-family:'Nunito',sans-serif!important;font-weight:800!important;font-size:16px!important;padding:10px 24px!important;transition:transform .15s,box-shadow .15s!important;}
.stButton>button:hover{transform:translateY(-2px)!important;box-shadow:0 6px 20px rgba(255,107,53,.5)!important;}
.card{background:var(--card);border-radius:16px;padding:20px 24px;margin:12px 0;border:1px solid rgba(255,255,255,.07);}
.badge{background:linear-gradient(135deg,var(--yellow),#ffb347);color:#1a1a2e;border-radius:24px;padding:5px 16px;font-weight:800;font-size:17px;display:inline-block;}
.banner{background:linear-gradient(135deg,var(--primary),var(--yellow));color:#1a1a2e;border-radius:12px;padding:13px 20px;font-weight:800;font-size:19px;text-align:center;margin-bottom:14px;}
.prow{display:flex;justify-content:space-between;align-items:center;padding:9px 15px;background:rgba(255,255,255,.05);border-radius:10px;margin:4px 0;}
.waiting{text-align:center;padding:36px 20px;opacity:.65;font-size:17px;}
.round-pill{background:rgba(255,255,255,.1);border-radius:20px;padding:4px 14px;font-size:14px;display:inline-block;margin-left:8px;}
.result-row{display:flex;justify-content:space-between;align-items:center;padding:10px 16px;border-radius:10px;margin:5px 0;}
</style>
""", unsafe_allow_html=True)

init_db()
if "player_name" not in st.session_state:
    st.session_state.player_name = None

# ── Helpers ────────────────────────────────────────────────────────────────────
def auto_refresh(s=3):
    time.sleep(s)
    st.rerun()

def top_bar(player):
    st.markdown(
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"background:rgba(255,255,255,.05);border-radius:12px;padding:10px 16px;margin-bottom:12px;'>"
        f"<span>👤 <b>{player['name']}</b></span>"
        f"<span class='badge'>💰 {player['points']} pts</span></div>",
        unsafe_allow_html=True
    )

def round_header(game_id, round_num, total_rounds):
    cfg = GAMES_CONFIG[game_id]
    st.markdown(
        f"<h2 style='margin-bottom:4px;'>{cfg['name']}"
        f"<span class='round-pill'>Ronda {round_num+1} / {total_rounds}</span></h2>",
        unsafe_allow_html=True
    )

def waiting_msg(msg="⏳ Esperando al resto de jugadores…"):
    st.markdown(f"<div class='waiting'>{msg}</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# REGISTRO
# ══════════════════════════════════════════════════════════════════════════════
def show_register():
    st.markdown("<h1 style='text-align:center;font-size:52px;color:#FF6B35;'>🎮 GYMKANA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;font-size:18px;opacity:.8;'>¡Únete a la partida!</p>", unsafe_allow_html=True)
    st.markdown("---")
    with st.form("reg"):
        name = st.text_input("Tu nombre", placeholder="¿Cómo te llamas?", max_chars=20)
        if st.form_submit_button("🚀 Entrar al juego", use_container_width=True):
            name = name.strip()
            if len(name) < 2:
                st.error("El nombre debe tener al menos 2 caracteres.")
            else:
                state = get_all_state()
                ok = register_player(name)
                if ok or get_player(name):
                    st.session_state.player_name = name
                    st.rerun()
                else:
                    st.error("Ese nombre ya está en uso. Elige otro.")

# ══════════════════════════════════════════════════════════════════════════════
# LOBBY
# ══════════════════════════════════════════════════════════════════════════════
def show_lobby(player):
    st.markdown("<h1 style='text-align:center;color:#FF6B35;'>🎮 GYMKANA</h1>", unsafe_allow_html=True)
    st.markdown("<div class='banner'>⏳ Esperando que el host inicie la partida…</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card'>👤 <b>{player['name']}</b> &nbsp;|&nbsp; 💰 <span class='badge'>{player['points']} pts</span></div>", unsafe_allow_html=True)
    players = get_players()
    st.markdown(f"### 👥 Jugadores conectados ({len(players)})")
    for p in players:
        st.markdown(f"<div class='prow'><span>🟢 {p['name']}</span><span class='badge'>{p['points']}</span></div>", unsafe_allow_html=True)
    waiting_msg("El juego comenzará cuando el host lo indique…")
    auto_refresh(4)

# ══════════════════════════════════════════════════════════════════════════════
# APUESTAS (antes de cada ronda)
# ══════════════════════════════════════════════════════════════════════════════
def show_betting(player, state):
    game_id   = int(state["current_game"])
    round_num = int(state["current_round"])
    cfg       = GAMES_CONFIG[game_id]

    round_header(game_id, round_num, cfg["total_rounds"])
    st.markdown(f"<div class='banner'>💰 ¡FASE DE APUESTAS!</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card'>📖 {cfg['description']}<br>⏱️ {cfg['time_limit']}s &nbsp;|&nbsp; 🏆 hasta {cfg['max_points']} pts</div>", unsafe_allow_html=True)

    existing = get_player_bet(player["name"], game_id, round_num)
    if existing:
        verb = "ganar 🎯" if existing["bet_win"] else "perder 💀"
        st.success(f"✅ Apuesta confirmada: **{existing['bet_amount']} pts** a {verb}")
        waiting_msg("Esperando que el host abra el juego…")
        auto_refresh(3)
        return

    st.markdown(f"### 🪙 Tus puntos actuales: **{player['points']}**")
    with st.form("bet"):
        bet_win = st.radio("¿Crees que lo harás bien esta ronda?",
                           ["🎯 Sí, voy a sumar puntos", "💀 No, me va a costar"], index=0)
        bet_amount = st.select_slider("¿Cuántos puntos apuestas?", options=BET_OPTIONS, value=50)
        if st.form_submit_button("🎲 Confirmar apuesta", use_container_width=True):
            if bet_amount > player["points"]:
                st.error("No tienes suficientes puntos.")
            else:
                win_flag = 1 if "ganar" in bet_win else 0
                place_bet(player["name"], game_id, round_num, bet_amount, win_flag)
                st.success("¡Apuesta registrada! 🎲")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# JUEGO 1 — Orden histórico
# ══════════════════════════════════════════════════════════════════════════════
def show_game1(player, state):
    game_id   = 1
    round_num = int(state["current_round"])
    cfg       = GAMES_CONFIG[game_id]
    events    = get_game1_round(round_num)

    round_header(game_id, round_num, cfg["total_rounds"])
    st.markdown("Numera del **1 (más antiguo)** al **6 (más reciente)**. Sin repetir posiciones.")

    existing = get_player_answer(player["name"], game_id, round_num)
    if existing:
        st.success("✅ Respuesta enviada. ¡Espera los resultados!")
        waiting_msg()
        auto_refresh(3)
        return

    with st.form("g1"):
        order_map = {}
        for ev in events:
            pos = st.selectbox(ev["text"], options=[1,2,3,4,5,6], key=f"g1_{ev['id']}")
            order_map[ev["id"]] = pos
        if st.form_submit_button("📤 Enviar respuesta", use_container_width=True):
            if len(set(order_map.values())) != len(order_map):
                st.error("⚠️ Cada evento debe tener una posición única.")
            else:
                sorted_ids = ",".join(k for k,v in sorted(order_map.items(), key=lambda x: x[1]))
                submit_answer(player["name"], game_id, round_num, sorted_ids)
                st.success("✅ ¡Enviado!")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# JUEGO 2 — Adivina el número
# ══════════════════════════════════════════════════════════════════════════════
def show_game2(player, state):
    game_id   = 2
    round_num = int(state["current_round"])
    cfg       = GAMES_CONFIG[game_id]
    q         = get_game2_round(round_num)

    round_header(game_id, round_num, cfg["total_rounds"])
    st.markdown(f"<div class='banner' style='font-size:20px;'>{q['question']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card' style='text-align:center;'>Unidad de respuesta: <b>{q['unit']}</b></div>", unsafe_allow_html=True)

    existing = get_player_answer(player["name"], game_id, round_num)
    if existing:
        st.success(f"✅ Tu respuesta: **{existing['answer']}** {q['unit']}. ¡Espera resultados!")
        waiting_msg()
        auto_refresh(3)
        return

    with st.form("g2"):
        guess = st.number_input("Tu estimación:", min_value=0, max_value=99_999_999, step=1, value=0)
        if st.form_submit_button("📤 Enviar respuesta", use_container_width=True):
            submit_answer(player["name"], game_id, round_num, str(int(guess)))
            st.success("✅ ¡Enviado!")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# JUEGO 3 — ¿Qué prefieres?
# ══════════════════════════════════════════════════════════════════════════════
def show_game3(player, state):
    game_id   = 3
    round_num = int(state["current_round"])
    cfg       = GAMES_CONFIG[game_id]
    q         = get_game3_round(round_num)

    round_header(game_id, round_num, cfg["total_rounds"])
    st.markdown(f"<div class='banner'>{q['question']}</div>", unsafe_allow_html=True)

    existing = get_player_answer(player["name"], game_id, round_num)
    if existing:
        st.success(f"✅ Votaste: **{existing['answer']}**. ¡Espera resultados!")
        waiting_msg()
        auto_refresh(3)
        return

    col1, col2 = st.columns(2)
    with col1:
        if st.button(q["option_a"], use_container_width=True):
            submit_answer(player["name"], game_id, round_num, q["option_a"])
            st.rerun()
    with col2:
        if st.button(q["option_b"], use_container_width=True):
            submit_answer(player["name"], game_id, round_num, q["option_b"])
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RESULTADOS DE RONDA
# ══════════════════════════════════════════════════════════════════════════════
def show_round_results(player, state):
    game_id   = int(state["current_game"])
    round_num = int(state["current_round"])
    cfg       = GAMES_CONFIG[game_id]
    answers   = get_answers(game_id, round_num)

    st.markdown(f"<h2>📊 Resultados — Ronda {round_num+1}</h2>", unsafe_allow_html=True)

    # Show round-specific results
    if game_id == 2:
        q = get_game2_round(round_num)
        st.markdown(f"<div class='card' style='text-align:center;'>✅ Respuesta correcta: <b>{q['answer']:,} {q['unit']}</b><br><small>{q['fun_fact']}</small></div>", unsafe_allow_html=True)
        results = score_game2(answers, q["answer"])
        for r in results:
            diff_txt = f"(diferencia: {abs(int(r['guess']) - q['answer']):,})" if r["guess"] != "–" else ""
            highlight = "background:rgba(6,214,160,.15);border:1px solid #06D6A0;" if r["player_name"] == player["name"] else "background:rgba(255,255,255,.05);"
            st.markdown(f"<div class='result-row' style='{highlight}'><span>👤 {r['player_name']} — {r['guess']} {diff_txt}</span><span class='badge'>+{r['points']}</span></div>", unsafe_allow_html=True)

    elif game_id == 1:
        correct = get_game1_correct_ids(round_num)
        st.markdown(f"<div class='card'>✅ Orden correcto: {' → '.join(correct)}</div>", unsafe_allow_html=True)
        for a in answers:
            pts_earned = a.get("score", 0)
            highlight = "background:rgba(6,214,160,.15);border:1px solid #06D6A0;" if a["player_name"] == player["name"] else "background:rgba(255,255,255,.05);"
            st.markdown(f"<div class='result-row' style='{highlight}'><span>👤 {a['player_name']}</span><span class='badge'>+{pts_earned}</span></div>", unsafe_allow_html=True)

    elif game_id == 3:
        q = get_game3_round(round_num)
        count_a = sum(1 for a in answers if a["answer"] == q["option_a"])
        count_b = sum(1 for a in answers if a["answer"] == q["option_b"])
        winner  = q["option_a"] if count_a >= count_b else q["option_b"]
        st.markdown(f"<div class='card' style='text-align:center;'>{q['option_a']}: <b>{count_a}</b> votos &nbsp;|&nbsp; {q['option_b']}: <b>{count_b}</b> votos<br>🏆 Mayoría: <b>{winner}</b></div>", unsafe_allow_html=True)
        for a in answers:
            won = "✅" if a["answer"] == winner else "❌"
            highlight = "background:rgba(6,214,160,.15);border:1px solid #06D6A0;" if a["player_name"] == player["name"] else "background:rgba(255,255,255,.05);"
            st.markdown(f"<div class='result-row' style='{highlight}'><span>{won} {a['player_name']} — {a['answer']}</span><span class='badge'>+{300 if a['answer']==winner else 0}</span></div>", unsafe_allow_html=True)

    # Ranking global
    st.markdown("### 🏆 Clasificación general")
    players = get_players()
    medals = ["🥇","🥈","🥉"]
    for i, p in enumerate(players):
        m = medals[i] if i < 3 else f"{i+1}."
        hl = "background:rgba(255,210,63,.15);border:1px solid #FFD23F;" if p["name"] == player["name"] else ""
        st.markdown(f"<div class='prow' style='{hl}'><span>{m} {p['name']}</span><span class='badge'>{p['points']}</span></div>", unsafe_allow_html=True)

    rounds_played = int(state.get("rounds_played", 0))
    total = cfg["total_rounds"]
    if rounds_played < total:
        waiting_msg(f"Ronda {rounds_played} de {total} completada. El host abrirá la siguiente…")
    else:
        waiting_msg("¡Juego completado! El host pasará al siguiente…")
    auto_refresh(4)

# ══════════════════════════════════════════════════════════════════════════════
# RESULTADOS FINALES DE JUEGO
# ══════════════════════════════════════════════════════════════════════════════
def show_game_results(player, state):
    game_id = int(state["current_game"])
    cfg     = GAMES_CONFIG[game_id]
    st.markdown(f"<h2 style='color:#FFD23F;text-align:center;'>🎯 Fin del juego {game_id}: {cfg['name']}</h2>", unsafe_allow_html=True)
    players = get_players()
    medals = ["🥇","🥈","🥉"]
    for i, p in enumerate(players):
        m = medals[i] if i < 3 else f"{i+1}."
        hl = "background:rgba(255,210,63,.15);border:1px solid #FFD23F;" if p["name"] == player["name"] else ""
        st.markdown(f"<div class='prow' style='{hl}'><span style='font-size:18px;'>{m} {p['name']}</span><span class='badge' style='font-size:18px;'>{p['points']}</span></div>", unsafe_allow_html=True)
    waiting_msg("El host iniciará el siguiente juego…")
    auto_refresh(4)

# ══════════════════════════════════════════════════════════════════════════════
# FINAL
# ══════════════════════════════════════════════════════════════════════════════
def show_final(player):
    st.markdown("<h1 style='text-align:center;color:#FFD23F;font-size:52px;'>🏆 FIN DE LA GYMKANA</h1>", unsafe_allow_html=True)
    players = get_players()
    if players:
        st.markdown(f"<h2 style='text-align:center;color:#FF6B35;'>¡Ganador/a: {players[0]['name']}! 🎉</h2>", unsafe_allow_html=True)
    medals = ["🥇","🥈","🥉"]
    for i, p in enumerate(players):
        m = medals[i] if i < 3 else f"{i+1}."
        hl = "background:rgba(255,210,63,.15);border:1px solid #FFD23F;" if p["name"] == player["name"] else ""
        st.markdown(f"<div class='prow' style='{hl}'><span style='font-size:20px;'>{m} {p['name']}</span><span class='badge' style='font-size:20px;'>{p['points']}</span></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if st.session_state.player_name is None:
        show_register()
        return

    player = get_player(st.session_state.player_name)
    if not player:
        st.session_state.player_name = None
        st.rerun()
        return

    state   = get_all_state()
    phase   = state.get("phase", "lobby")
    game_id = int(state.get("current_game", 0))

    top_bar(player)

    if   phase == "lobby":         show_lobby(player)
    elif phase == "betting":       show_betting(player, state)
    elif phase == "playing":
        if   game_id == 1: show_game1(player, state)
        elif game_id == 2: show_game2(player, state)
        elif game_id == 3: show_game3(player, state)
        else:
            st.info("Juego en preparación…"); auto_refresh(3)
    elif phase == "round_results": show_round_results(player, state)
    elif phase == "game_results":  show_game_results(player, state)
    elif phase == "final":         show_final(player)
    else:
        auto_refresh(3)

if __name__ == "__main__":
    main()
