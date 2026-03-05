"""
Game definitions and scoring logic for the Gymkana.
Add / edit content here without touching UI code.
"""

# ── GAME 1: Orden histórico ────────────────────────────────────────────────────

GAME1_EVENTS = [
    {"id": "a", "text": "🏛️ Caída del Imperio Romano de Occidente", "year": 476},
    {"id": "b", "text": "🌍 Cristóbal Colón llega a América",        "year": 1492},
    {"id": "c", "text": "✊ Revolución Francesa",                      "year": 1789},
    {"id": "d", "text": "💡 Invención de la bombilla (Edison)",        "year": 1879},
    {"id": "e", "text": "🌕 El hombre llega a la Luna",               "year": 1969},
    {"id": "f", "text": "🧬 Secuenciación del genoma humano",          "year": 2003},
]

GAME1_CORRECT_ORDER = sorted(GAME1_EVENTS, key=lambda x: x["year"])
GAME1_CORRECT_IDS   = [e["id"] for e in GAME1_CORRECT_ORDER]

def score_game1(player_order: list[str]) -> int:
    """Score based on how many events are in the right relative position."""
    correct = 0
    for i in range(len(player_order)):
        if i < len(GAME1_CORRECT_IDS) and player_order[i] == GAME1_CORRECT_IDS[i]:
            correct += 1
    # 0 = 0pts, all correct = 500pts, graded
    return (correct * 500) // len(GAME1_CORRECT_IDS)


# ── GAME 4: Adivina el número ──────────────────────────────────────────────────

GAME4_QUESTIONS = [
    {
        "question": "🍺 ¿Cuántas cervezas seguidas es el record Guinness?",
        "answer": 173,
        "unit": "cervezas",
        "fun_fact": "El alemán André Ortolf bebió 173 cervezas de 0.1L en 1 hora en 2012."
    },
    {
        "question": "🦷 ¿Cuántos dientes tiene un caracol?",
        "answer": 14175,
        "unit": "dientes",
        "fun_fact": "Los caracoles tienen miles de dientes microscópicos en su lengua (rádula)."
    },
    {
        "question": "🎂 ¿Cuántas velas había en el pastel de cumpleaños más grande del mundo?",
        "answer": 72585,
        "unit": "velas",
        "fun_fact": "El récord fue establecido en India en 2014."
    },
]

GAME4_ACTIVE = GAME4_QUESTIONS[0]  # Host can rotate this

def score_game4(answers: list[dict], correct: int) -> list[dict]:
    """
    Returns list of {player_name, guess, diff, points} sorted by closeness.
    Top 3 get 500/300/150. Everyone who guesses gets 50.
    """
    results = []
    for a in answers:
        try:
            guess = int(a["answer"])
            diff  = abs(guess - correct)
            results.append({"player_name": a["player_name"], "guess": guess, "diff": diff, "points": 50})
        except Exception:
            results.append({"player_name": a["player_name"], "guess": None, "diff": 999999, "points": 0})
    
    results.sort(key=lambda x: x["diff"])
    prizes = [500, 300, 150]
    for i, prize in enumerate(prizes):
        if i < len(results) and results[i]["guess"] is not None:
            results[i]["points"] = prize
    return results


# ── GAME 3: ¿Qué prefieres? (voting) ─────────────────────────────────────────

GAME3_QUESTIONS = [
    {
        "question": "¿Qué prefieres?",
        "option_a": "🦸 Poder volar",
        "option_b": "🦸 Ser invisible",
    },
    {
        "question": "¿Qué prefieres?",
        "option_a": "🏖️ Playa infinita",
        "option_b": "🏔️ Montaña eterna",
    },
    {
        "question": "¿Qué prefieres?",
        "option_a": "🍕 Comer pizza todos los días",
        "option_b": "🌮 Comer tacos todos los días",
    },
]

def score_game3(answers: list[dict], winning_option: str) -> list[dict]:
    """Players who voted for the majority option get points."""
    results = []
    for a in answers:
        pts = 300 if a["answer"] == winning_option else 0
        results.append({"player_name": a["player_name"], "answer": a["answer"], "points": pts})
    return results


# ── General config ─────────────────────────────────────────────────────────────

GAMES_CONFIG = {
    1: {"name": "⏳ Orden Histórico",       "max_points": 500, "time_limit": 90,  "description": "Ordena los hechos históricos del más antiguo al más reciente"},
    2: {"name": "🔢 Adivina el Número",     "max_points": 500, "time_limit": 60,  "description": "¿Quién se aproxima más a la respuesta correcta?"},
    3: {"name": "🗳️ ¿Qué Prefieres?",       "max_points": 300, "time_limit": 30,  "description": "La opción más votada gana puntos para todos los que la eligieron"},
}

INITIAL_POINTS = 1000
BET_OPTIONS    = [0, 50, 100, 200]  # Points players can bet
