import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

# ─────────────────────────────────────────────────────────────
# DATABASE CONFIG
# ─────────────────────────────────────────────────────────────

DB_HOST = os.getenv("DB_HOST", "192.168.1.135")
DB_NAME = os.getenv("DB_NAME", "concurso_cumple")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        cursor_factory=RealDictCursor
    )


# ─────────────────────────────────────────────────────────────
# INIT DATABASE
# ─────────────────────────────────────────────────────────────

def init_db():

    conn = get_conn()
    cur = conn.cursor()

#Crea la tabla de estados del juego
    cur.execute("""
    CREATE TABLE IF NOT EXISTS game_state (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
#Crea la tabla de jugadores
    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        points INTEGER DEFAULT 1000,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
#Crea la tabla de apuestas con un campo round_num para identificar las rondas dentro de cada juego
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bets (
        id SERIAL PRIMARY KEY,
        player_name TEXT,
        game_id INTEGER,
        round_num INTEGER DEFAULT 0,
        bet_amount INTEGER,
        bet_win INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(player_name, game_id, round_num)
    )
    """)
#Crea la tabla de respuestas
    cur.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        id SERIAL PRIMARY KEY,
        player_name TEXT,
        game_id INTEGER,
        round_num INTEGER DEFAULT 0,
        answer TEXT,
        score INTEGER DEFAULT 0,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(player_name, game_id, round_num)
    )
    """)

    # Estado inicial del juego
    defaults = {
        "phase": "lobby",
        "current_game": "0",
        "current_round": "0",
        "rounds_played": "0",
        "game_started_at": "",
        "betting_open": "false",
        "answers_open": "false",
    }

    for k, v in defaults.items():
        cur.execute(
            "INSERT INTO game_state (key, value) VALUES (%s,%s) ON CONFLICT (key) DO NOTHING",
            (k, v)
        )

    conn.commit()
    cur.close()
    conn.close()


# ─────────────────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────────────────

#Devuelve el valor del estado del juego dando su clave
def get_state(key: str):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT value FROM game_state WHERE key=%s",
        (key,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row["value"] if row else ""

#Inserta o actualiza el valor del estado del juego dado su clave
def set_state(key: str, value: str):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO game_state (key,value,updated_at)
        VALUES (%s,%s,CURRENT_TIMESTAMP)
        ON CONFLICT (key)
        DO UPDATE SET value=%s, updated_at=CURRENT_TIMESTAMP
    """, (key, value, value))

    conn.commit()
    cur.close()
    conn.close()

#Pbtiene todos los estados del juego como un diccionario
def get_all_state():

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT key,value FROM game_state")

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return {r["key"]: r["value"] for r in rows}


# ─────────────────────────────────────────────────────────────
# PLAYERS
# ─────────────────────────────────────────────────────────────

#Registra el nombre de un jugador en la base de datos
def register_player(name: str):

    try:

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO players (name) VALUES (%s)",
            (name,)
        )

        conn.commit()

        cur.close()
        conn.close()

        return True

    except psycopg2.Error:

        return False

#Devuelve la lista de jugadores ordenada por puntos
def get_players():

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM players ORDER BY points DESC")

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows

#Obttiene la información de un jugador dado su nombre
def get_player(name: str):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM players WHERE name=%s",
        (name,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row

#Actualiza los puntos de un jugador sumando el delta (puede ser positivo o negativo) como mínimo deja al jugador con 0 puntos
def update_points(name: str, delta: int):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET points = GREATEST(0, points + %s)
        WHERE name=%s
    """, (delta, name))

    conn.commit()

    cur.close()
    conn.close()

#Actualiza todos los estados del juego a sus valores iniciales
def reset_all():

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM players")
    cur.execute("DELETE FROM bets")
    cur.execute("DELETE FROM answers")

    defaults = {
        "phase": "lobby",
        "current_game": "0",
        "current_round": "0",
        "rounds_played": "0",
        "game_started_at": "",
        "betting_open": "false",
        "answers_open": "false",
    }

    for k, v in defaults.items():
        cur.execute(
            "UPDATE game_state SET value=%s WHERE key=%s",
            (v, k)
        )

    conn.commit()

    cur.close()
    conn.close()


# ─────────────────────────────────────────────────────────────
# BETS
# ─────────────────────────────────────────────────────────────

#Inserta o actualiza la apuesta de un jugador para una ronda de un juego dado el monto apostado y a quién apuesta (bet_win)
def place_bet(player_name: str, game_id: int, round_num: int, amount: int, bet_win: int):

    try:

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO bets (player_name,game_id,round_num,bet_amount,bet_win)
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT (player_name,game_id,round_num)
        DO UPDATE SET bet_amount=%s, bet_win=%s
        """, (player_name, game_id, round_num, amount, bet_win, amount, bet_win))

        conn.commit()

        cur.close()
        conn.close()

        return True

    except psycopg2.Error:

        return False

#Obtiene todas las apuestas de un juego dado su id y número de ronda
def get_bets(game_id: int, round_num: int):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM bets WHERE game_id=%s AND round_num=%s",
        (game_id, round_num)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows

#Obtiene la apuesta de un jugador para una ronda de un juego dado su nombre, id del juego y número de ronda
def get_player_bet(player_name: str, game_id: int, round_num: int):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM bets
        WHERE player_name=%s
        AND game_id=%s
        AND round_num=%s
    """, (player_name, game_id, round_num))

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row


# ─────────────────────────────────────────────────────────────
# ANSWERS
# ─────────────────────────────────────────────────────────────

#Inserta o actualiza la respuesta de un jugador para una ronda de un juego
def submit_answer(player_name: str, game_id: int, round_num: int, answer: str):

    try:

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO answers (player_name,game_id,round_num,answer)
        VALUES (%s,%s,%s,%s)
        ON CONFLICT (player_name,game_id,round_num)
        DO UPDATE SET answer=%s
        """, (player_name, game_id, round_num, answer, answer))

        conn.commit()

        cur.close()
        conn.close()

        return True

    except psycopg2.Error:

        return False

#Obtiene todas las respuestas de un juego dado su id y número de ronda
def get_answers(game_id: int, round_num: int):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM answers WHERE game_id=%s AND round_num=%s",
        (game_id, round_num)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows

#Obtiene la respuesta de un jugador para una ronda de un juego dado su nombre, id del juego y número de ronda
def get_player_answer(player_name: str, game_id: int, round_num: int):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM answers
        WHERE player_name=%s
        AND game_id=%s
        AND round_num=%s
    """, (player_name, game_id, round_num))

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row

#Actualiza la puntuación de la respuesta de un jugador para una ronda de un juego dado su nombre, id del juego, número de ronda y nueva puntuación
def set_answer_score(player_name: str, game_id: int, round_num: int, score: int):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE answers
        SET score=%s
        WHERE player_name=%s
        AND game_id=%s
        AND round_num=%s
    """, (score, player_name, game_id, round_num))

    conn.commit()

    cur.close()
    conn.close()