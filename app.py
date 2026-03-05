"""
🎮 GYMKANA — app principal
Punto de entrada para jugadores. El host accede a /admin (contraseña).
"""

import streamlit as st
import time
from utils.database import (
    init_db, register_player, get_player, get_all_state,
    get_players, place_bet, get_player_bet, submit_answer,
    get_player_answer, get_answers
)
from utils.games import (
    GAME1_EVENTS, GAME1_CORRECT_IDS, score_game1,
    GAME4_ACTIVE, score_game4,
    GAME3_QUESTIONS, score_game3,
    GAMES_CONFIG, BET_OPTIONS, INITIAL_POINTS
)

# ─── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🎮 Gymkana",
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&family=Nunito:wght@400;600;700;800&display=swap');

:root {
  --primary: #FF6B35;
  --secondary: #FFD23F;
  --accent: #06D6A0;
  --dark: #1a1a2e;
  --card: #16213e;
  --text: #eaeaea;
}

html, body, [class*="css"] {
  background-color: var(--dark) !important;
  color: var(--text) !important;
  font-family: 'Nunito', sans-serif !important;
}

h1, h2, h3 { font-family: 'Bangers', cursive !important; letter-spacing: 2px; }

.stButton > button {
  background: linear-gradient(135deg, var(--primary), #ff8c42) !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  font-family: 'Nunito', sans-serif !important;
  font-weight: 800 !important;
  font-size: 16px !important;
  padding: 10px 24px !important;
  transition: transform .15s, box-shadow .15s !important;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px rgba(255,107,53,.5) !important;
}

.card {
  background: var(--card);
  border-radius: 16px;
  padding: 20px 24px;
  margin: 12px 0;
  border: 1px solid rgba(255,255,255,.07);
}

.points-badge {
  background: linear-gradient(135deg, var(--secondary), #ffb347);
  color: #1a1a2e;
  border-radius: 24px;
  padding: 6px 18px;
  font-weight: 800;
  font-size: 18px;
  display: inline-block;
}

.phase-banner {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #1a1a2e;
  border-radius: 12px;
  padding: 14px 20px;
  font-weight: 800;
  font-size: 20px;
  text-align: center;
  margin-bottom: 16px;
}

.player-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: rgba(255,255,255,.05);
  border-radius: 10px;
  margin: 4px 0;
}

.medal-1 { color: #FFD700; font-size: 22px; }
.medal-2 { color: #C0C0C0; font-size: 22px; }
.medal-3 { color: #CD7F32; font-size: 22px; }

.waiting {
  text-align: center;
  padding: 40px 20px;
  opacity: .7;
  font-size: 17px;
}

.drag-item {
  cursor: grab;
}

.stRadio > div { gap: 10px !important; }
.stRadio label { 
  background: rgba(255,255,255,.07) !important;
  border-radius: 10px !important;
  padding: 10px 16px !important;
  border: 1px solid rgba(255,255,255,.1) !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Init ────────────────────────────────────────────────────────────────────────
init_db()

if "player_name" not in st.session_state:
    st.session_state.player_name = None

# ─── Helper: auto-refresh ────────────────────────────────────────────────────────
def auto_refresh(seconds=3):
    time.sleep(seconds)
    st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
# REGISTRO
# ════════════════════════════════════════════════════════════════════════════════
def show_register():
    st.markdown("<h1 style='text-align:center;font-size:52px;color:#FF6B35;'>🎮 GYMKANA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;font-size:18px;opacity:.8;'>¡Únete a la partida!</p>", unsafe_allow_html=True)
    st.markdown("---")

    with st.form("register_form"):
        name = st.text_input("Tu nombre", placeholder="¿Cómo te llamas?", max_chars=20)
        submitted = st.form_submit_button("🚀 Entrar al juego", use_container_width=True)
    
    if submitted:
        name = name.strip()
        if not name:
            st.error("Escribe tu nombre para entrar.")
        elif len(name) < 2:
            st.error("El nombre debe tener al menos 2 caracteres.")
        else:
            state = get_all_state()
            if state.get("phase") not in ("lobby", "betting"):
                # Allow re-join if already registered
                player = get_player(name)
                if player:
                    st.session_state.player_name = name
                    st.rerun()
                else:
                    st.warning("La partida ya ha comenzado. Pregunta al host si puedes unirte.")
            else:
                ok = register_player(name)
                if ok:
                    st.session_state.player_name = name
                    st.success(f"¡Bienvenido/a, {name}! 🎉")
                    st.rerun()
                else:
                    # Already registered = re-join
                    player = get_player(name)
                    if player:
                        st.session_state.player_name = name
                        st.rerun()
                    else:
                        st.error("Ese nombre ya está en uso. Elige otro.")

# ════════════════════════════════════════════════════════════════════════════════
# LOBBY
# ════════════════════════════════════════════════════════════════════════════════
def show_lobby(player: dict):
    st.markdown("<h1 style='text-align:center;color:#FF6B35;'>🎮 GYMKANA</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='phase-banner'>⏳ Esperando que el host inicie la partida…</div>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='card'><b>👤 Jugando como:</b> {player['name']}<br>"
                f"<b>💰 Puntos iniciales:</b> <span class='points-badge'>{player['points']}</span></div>",
                unsafe_allow_html=True)

    players = get_players()
    st.markdown(f"### 👥 Jugadores conectados ({len(players)})")
    for p in players:
        st.markdown(f"<div class='player-row'><span>🟢 {p['name']}</span><span class='points-badge'>{p['points']} pts</span></div>",
                    unsafe_allow_html=True)
    
    st.markdown("<div class='waiting'>El juego comenzará cuando el host lo indique…</div>", unsafe_allow_html=True)
    auto_refresh(4)

# ════════════════════════════════════════════════════════════════════════════════
# APUESTAS
# ════════════════════════════════════════════════════════════════════════════════
def show_betting(player: dict, state: dict):
    game_id = int(state.get("current_game", 1))
    game    = GAMES_CONFIG.get(game_id, {})
    
    st.markdown(f"<h2 style='color:#FFD23F;text-align:center;'>💰 FASE DE APUESTAS</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='phase-banner'>Próximo juego: {game.get('name','?')}</div>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='card'>📖 <b>{game.get('description','')}</b><br><br>"
                f"⏱️ Tiempo límite: <b>{game.get('time_limit',60)}s</b> &nbsp;|&nbsp; "
                f"🏆 Puntos máximos: <b>{game.get('max_points',500)}</b></div>",
                unsafe_allow_html=True)

    existing_bet = get_player_bet(player["name"], game_id)
    if existing_bet:
        msg = "ganar 🎯" if existing_bet["bet_win"] else "perder 💀"
        st.success(f"✅ Apuesta registrada: **{existing_bet['bet_amount']} puntos** a {msg}")
        st.markdown("<div class='waiting'>Esperando que abra el juego…</div>", unsafe_allow_html=True)
        auto_refresh(3)
        return

    st.markdown(f"### 🪙 Tus puntos: {player['points']}")
    
    with st.form("bet_form"):
        bet_win = st.radio(
            "¿Crees que lo harás bien?",
            options=["🎯 Sí, voy a ganar puntos", "💀 No, me va a costar"],
            index=0
        )
        bet_amount = st.select_slider(
            "¿Cuántos puntos apuestas?",
            options=BET_OPTIONS,
            value=50
        )
        submitted = st.form_submit_button("🎲 Confirmar apuesta", use_container_width=True)
    
    if submitted:
        max_pts = player["points"]
        if bet_amount > max_pts:
            st.error("No tienes suficientes puntos para esa apuesta.")
        else:
            win_flag = 1 if "ganar" in bet_win else 0
            place_bet(player["name"], game_id, bet_amount, win_flag)
            st.success("¡Apuesta registrada! 🎲")
            st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
# JUEGO 1: Orden histórico
# ════════════════════════════════════════════════════════════════════════════════
def show_game1(player: dict, state: dict):
    game_id = 1
    st.markdown("<h2 style='color:#06D6A0;'>⏳ ORDEN HISTÓRICO</h2>", unsafe_allow_html=True)
    st.markdown("Arrastra y ordena estos hechos **del más antiguo al más reciente**.")

    existing = get_player_answer(player["name"], game_id)
    if existing:
        st.success("✅ Respuesta enviada. ¡Espera los resultados!")
        _show_waiting_bar()
        auto_refresh(3)
        return

    # Use checkboxes to let user rank items (simpler than drag in Streamlit)
    st.markdown("<div class='card'>Numera del 1 (más antiguo) al 6 (más reciente):</div>", unsafe_allow_html=True)

    order_map = {}
    used_positions = []
    valid = True

    with st.form("game1_form"):
        for ev in GAME1_EVENTS:
            pos = st.selectbox(
                f"{ev['text']}",
                options=[1, 2, 3, 4, 5, 6],
                key=f"g1_{ev['id']}"
            )
            order_map[ev["id"]] = pos
        submitted = st.form_submit_button("📤 Enviar respuesta", use_container_width=True)
    
    if submitted:
        # Check no duplicates
        positions = list(order_map.values())
        if len(set(positions)) != len(positions):
            st.error("⚠️ Cada evento debe tener una posición única (sin repetir números).")
        else:
            sorted_ids = [k for k, v in sorted(order_map.items(), key=lambda x: x[1])]
            answer_str = ",".join(sorted_ids)
            submit_answer(player["name"], game_id, answer_str)
            st.success("✅ ¡Enviado!")
            st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
# JUEGO 4: Adivina el número
# ════════════════════════════════════════════════════════════════════════════════
def show_game4(player: dict, state: dict):
    game_id = 2  # DB game_id
    st.markdown("<h2 style='color:#FFD23F;'>🔢 ADIVINA EL NÚMERO</h2>", unsafe_allow_html=True)

    q = GAME4_ACTIVE
    st.markdown(f"<div class='phase-banner' style='font-size:22px;'>{q['question']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card' style='text-align:center;'>Unidad: <b>{q['unit']}</b></div>", unsafe_allow_html=True)

    existing = get_player_answer(player["name"], game_id)
    if existing:
        st.success(f"✅ Tu respuesta: **{existing['answer']}** {q['unit']}. ¡Espera los resultados!")
        _show_waiting_bar()
        auto_refresh(3)
        return

    with st.form("game4_form"):
        guess = st.number_input("Tu estimación:", min_value=0, max_value=9_999_999, step=1, value=0)
        submitted = st.form_submit_button("📤 Enviar respuesta", use_container_width=True)
    
    if submitted:
        submit_answer(player["name"], game_id, str(int(guess)))
        st.success("✅ ¡Enviado!")
        st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
# JUEGO 3: ¿Qué prefieres? (voting)
# ════════════════════════════════════════════════════════════════════════════════
def show_game3(player: dict, state: dict):
    game_id = 3
    round_num = int(state.get("current_round", 0))
    q = GAME3_QUESTIONS[min(round_num, len(GAME3_QUESTIONS)-1)]

    st.markdown("<h2 style='color:#FF6B35;'>🗳️ ¿QUÉ PREFIERES?</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='phase-banner'>{q['question']}</div>", unsafe_allow_html=True)

    existing = get_player_answer(player["name"], game_id, round_num)
    if existing:
        st.success(f"✅ Votaste: **{existing['answer']}**. ¡Esperando resultados!")
        _show_waiting_bar()
        auto_refresh(3)
        return

    col1, col2 = st.columns(2)
    with col1:
        if st.button(q["option_a"], use_container_width=True):
            submit_answer(player["name"], game_id, q["option_a"], round_num)
            st.rerun()
    with col2:
        if st.button(q["option_b"], use_container_width=True):
            submit_answer(player["name"], game_id, q["option_b"], round_num)
            st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
# RESULTADOS
# ════════════════════════════════════════════════════════════════════════════════
def show_results(player: dict, state: dict):
    game_id = int(state.get("current_game", 1))
    st.markdown("<h2 style='text-align:center;color:#FFD23F;'>🏆 RESULTADOS</h2>", unsafe_allow_html=True)

    players = get_players()
    medals = ["🥇", "🥈", "🥉"]
    
    for i, p in enumerate(players):
        medal = medals[i] if i < 3 else f"{i+1}."
        highlight = "background: rgba(255,210,63,.15); border:1px solid #FFD23F;" if p["name"] == player["name"] else ""
        st.markdown(
            f"<div class='player-row' style='{highlight}'>"
            f"<span>{medal} {p['name']}</span>"
            f"<span class='points-badge'>{p['points']} pts</span></div>",
            unsafe_allow_html=True
        )

    st.markdown("<div class='waiting'>El host iniciará el siguiente juego…</div>", unsafe_allow_html=True)
    auto_refresh(4)

# ════════════════════════════════════════════════════════════════════════════════
# FINAL
# ════════════════════════════════════════════════════════════════════════════════
def show_final(player: dict):
    st.markdown("<h1 style='text-align:center;color:#FFD23F;font-size:56px;'>🏆 FIN DE LA GYMKANA</h1>", unsafe_allow_html=True)
    players = get_players()
    medals  = ["🥇", "🥈", "🥉"]
    
    winner = players[0] if players else None
    if winner:
        st.markdown(f"<h2 style='text-align:center;color:#FF6B35;'>¡Ganador: {winner['name']}! 🎉</h2>",
                    unsafe_allow_html=True)

    st.markdown("### Clasificación final")
    for i, p in enumerate(players):
        medal = medals[i] if i < 3 else f"{i+1}."
        highlight = "background: rgba(255,210,63,.15); border:1px solid #FFD23F;" if p["name"] == player["name"] else ""
        st.markdown(
            f"<div class='player-row' style='{highlight}'>"
            f"<span style='font-size:20px;'>{medal} {p['name']}</span>"
            f"<span class='points-badge' style='font-size:20px;'>{p['points']} pts</span></div>",
            unsafe_allow_html=True
        )

def _show_waiting_bar():
    st.markdown("<div class='waiting'>⏳ Esperando al resto de jugadores…</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# ROUTER PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════════
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

    # Minimal top bar
    st.markdown(
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"background:rgba(255,255,255,.05);border-radius:12px;padding:10px 16px;margin-bottom:12px;'>"
        f"<span>👤 <b>{player['name']}</b></span>"
        f"<span class='points-badge'>💰 {player['points']} pts</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    if phase == "lobby":
        show_lobby(player)
    elif phase == "betting":
        show_betting(player, state)
    elif phase == "playing":
        if game_id == 1:
            show_game1(player, state)
        elif game_id == 2:
            show_game4(player, state)
        elif game_id == 3:
            show_game3(player, state)
        else:
            st.info("Juego en preparación…")
            auto_refresh(3)
    elif phase == "results":
        show_results(player, state)
    elif phase == "final":
        show_final(player)
    else:
        auto_refresh(3)

if __name__ == "__main__":
    main()
