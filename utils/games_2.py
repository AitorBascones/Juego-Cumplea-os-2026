"""
Gymkana — contenido y lógica de puntuación.
Cada juego tiene múltiples rondas. Las apuestas se hacen antes de cada ronda.
"""

# ══════════════════════════════════════════════════════════════════════════════
# JUEGO 1 — Orden Histórico
# Cada ronda = un set distinto de 6 hechos históricos
# ══════════════════════════════════════════════════════════════════════════════

GAME1_ROUNDS = [
    # Ronda 0
    [
        {"id": "a", "text": "🏛️ Caída del Imperio Romano de Occidente", "year": 476},
        {"id": "b", "text": "🌍 Cristóbal Colón llega a América",        "year": 1492},
        {"id": "c", "text": "✊ Revolución Francesa",                     "year": 1789},
        {"id": "d", "text": "💡 Invención de la bombilla (Edison)",       "year": 1879},
        {"id": "e", "text": "🌕 El hombre llega a la Luna",              "year": 1969},
        {"id": "f", "text": "🧬 Secuenciación del genoma humano",         "year": 2003},
    ],
    # Ronda 1
    [
        {"id": "a", "text": "🔥 Erupción del Vesubio, destruye Pompeya", "year": 79},
        {"id": "b", "text": "📜 Magna Carta firmada en Inglaterra",       "year": 1215},
        {"id": "c", "text": "🖨️ Gutenberg inventa la imprenta",          "year": 1440},
        {"id": "d", "text": "🚂 Primera locomotora de vapor (Trevithick)","year": 1804},
        {"id": "e", "text": "✈️ Primer vuelo de los hermanos Wright",    "year": 1903},
        {"id": "f", "text": "🌐 Tim Berners-Lee inventa la WWW",          "year": 1989},
    ],
    # Ronda 2
    [
        {"id": "a", "text": "🏺 Construcción de la Gran Pirámide de Giza","year": -2560},
        {"id": "b", "text": "⚔️ Batalla de Maratón",                      "year": -490},
        {"id": "c", "text": "🗡️ Asesinato de Julio César",               "year": -44},
        {"id": "d", "text": "🕌 Fundación del Islam (Hégira)",            "year": 622},
        {"id": "e", "text": "🧭 Marco Polo llega a China",               "year": 1275},
        {"id": "f", "text": "🎨 Miguel Ángel pinta la Capilla Sixtina",  "year": 1512},
    ],
]

def get_game1_round(round_num: int) -> list:
    return GAME1_ROUNDS[round_num % len(GAME1_ROUNDS)]

def get_game1_correct_ids(round_num: int) -> list:
    events = get_game1_round(round_num)
    return [e["id"] for e in sorted(events, key=lambda x: x["year"])]

def score_game1(player_order: list, round_num: int) -> int:
    correct_ids = get_game1_correct_ids(round_num)
    hits = sum(1 for i, pid in enumerate(player_order) if i < len(correct_ids) and pid == correct_ids[i])
    return (hits * 500) // len(correct_ids)


# ══════════════════════════════════════════════════════════════════════════════
# JUEGO 2 — Adivina el Número
# Cada ronda = una pregunta nueva
# ══════════════════════════════════════════════════════════════════════════════

GAME2_ROUNDS = [
    {
        "question": "🍺 ¿Cuántas cervezas seguidas es el récord Guinness?",
        "answer": 173,
        "unit": "cervezas",
        "fun_fact": "André Ortolf bebió 173 vasos de 0.1L en 1 hora en 2012.",
    },
    {
        "question": "🦷 ¿Cuántos dientes tiene un caracol?",
        "answer": 14175,
        "unit": "dientes",
        "fun_fact": "Los caracoles tienen miles de dientes microscópicos en su lengua (rádula).",
    },
    {
        "question": "🎂 ¿Cuántas velas había en el pastel de cumpleaños más grande del mundo?",
        "answer": 72585,
        "unit": "velas",
        "fun_fact": "El récord fue establecido en India en 2014.",
    },
    {
        "question": "🐘 ¿Cuántos días dura el embarazo de una elefanta?",
        "answer": 640,
        "unit": "días",
        "fun_fact": "El elefante africano tiene la gestación más larga de todos los mamíferos.",
    },
    {
        "question": "🎸 ¿Cuántas guitarras destruyó Pete Townshend (The Who) a lo largo de su carrera?",
        "answer": 35,
        "unit": "guitarras",
        "fun_fact": "Aunque destruyó muchas en directo, el número exacto documentado es alrededor de 35.",
    },
    {
        "question": "🌡️ ¿Cuántos grados Celsius alcanza el centro del Sol?",
        "answer": 15000000,
        "unit": "°C",
        "fun_fact": "La temperatura en el núcleo solar alcanza unos 15 millones de grados.",
    },
]

def get_game2_round(round_num: int) -> dict:
    return GAME2_ROUNDS[round_num % len(GAME2_ROUNDS)]

def score_game2(answers: list, correct: int) -> list:
    results = []
    for a in answers:
        try:
            guess = int(a["answer"])
            diff  = abs(guess - correct)
            results.append({"player_name": a["player_name"], "guess": guess, "diff": diff, "points": 50})
        except Exception:
            results.append({"player_name": a["player_name"], "guess": "–", "diff": 10**9, "points": 0})
    results.sort(key=lambda x: x["diff"])
    for i, prize in enumerate([500, 300, 150]):
        if i < len(results) and results[i]["guess"] != "–":
            results[i]["points"] = prize
    return results


# ══════════════════════════════════════════════════════════════════════════════
# JUEGO 3 — ¿Qué Prefieres?
# Varias rondas de votación seguidas
# ══════════════════════════════════════════════════════════════════════════════

GAME3_ROUNDS = [
    {"question": "¿Qué prefieres?", "option_a": "🦸 Poder volar",              "option_b": "👻 Ser invisible"},
    {"question": "¿Qué prefieres?", "option_a": "🏖️ Playa infinita",           "option_b": "🏔️ Montaña eterna"},
    {"question": "¿Qué prefieres?", "option_a": "🍕 Pizza todos los días",      "option_b": "🌮 Tacos todos los días"},
    {"question": "¿Qué prefieres?", "option_a": "⏪ Viajar al pasado",          "option_b": "⏩ Viajar al futuro"},
    {"question": "¿Qué prefieres?", "option_a": "🧠 Ser el más listo del mundo","option_b": "😍 Ser el más guapo/a del mundo"},
    {"question": "¿Qué prefieres?", "option_a": "🎤 Cantar mal siempre en público","option_b": "💃 Bailar mal siempre en público"},
]

def get_game3_round(round_num: int) -> dict:
    return GAME3_ROUNDS[round_num % len(GAME3_ROUNDS)]

def score_game3(answers: list, winning_option: str) -> list:
    return [
        {"player_name": a["player_name"], "answer": a["answer"],
         "points": 300 if a["answer"] == winning_option else 0}
        for a in answers
    ]


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN GLOBAL
# ══════════════════════════════════════════════════════════════════════════════

GAMES_CONFIG = {
    1: {
        "name":         "⏳ Orden Histórico",
        "max_points":   500,
        "time_limit":   90,
        "total_rounds": len(GAME1_ROUNDS),
        "description":  "Ordena 6 hechos históricos del más antiguo al más reciente",
    },
    2: {
        "name":         "🔢 Adivina el Número",
        "max_points":   500,
        "time_limit":   60,
        "total_rounds": len(GAME2_ROUNDS),
        "description":  "¿Quién se acerca más a la respuesta correcta?",
    },
    3: {
        "name":         "🗳️ ¿Qué Prefieres?",
        "max_points":   300,
        "time_limit":   25,
        "total_rounds": len(GAME3_ROUNDS),
        "description":  "Los que votan con la mayoría ganan puntos",
    },
}

INITIAL_POINTS = 1000
BET_OPTIONS    = [0, 50, 100, 200]
