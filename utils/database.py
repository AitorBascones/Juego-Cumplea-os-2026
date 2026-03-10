import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "gymkana.db"

#Crea una conexión a la base de datos y asegura que las tablas necesarias existan. Esto se llama al iniciar la aplicación (app.py).

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS game_state (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            points INTEGER DEFAULT 1000,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            game_id INTEGER,
            bet_amount INTEGER,
            bet_win INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(player_name, game_id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            game_id INTEGER,
            round_num INTEGER DEFAULT 0,
            answer TEXT,
            score INTEGER DEFAULT 0,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(player_name, game_id, round_num)
        )
    """)
    
    # Initialize default game state
    defaults = {
        "phase": "lobby",           # lobby | betting | playing | results | final
        "current_game": "0",        # 0 = none, 1-5 = game number
        "game_started_at": "",
        "betting_open": "false",
        "answers_open": "false",
        "show_results": "false",
        "current_round": "0",       # For game 5 (blur game)
        "max_rounds": "5",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO game_state (key, value) VALUES (?, ?)", (k, v))
    
    conn.commit()
    conn.close()

# ── State helpers ─────────────────────────────────────────────────────────────

def get_state(key: str) -> str:
    conn = get_conn()
    row = conn.execute("SELECT value FROM game_state WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else ""

def set_state(key: str, value: str):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO game_state (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (key, value)
    )
    conn.commit()
    conn.close()

def get_all_state() -> dict:
    conn = get_conn()
    rows = conn.execute("SELECT key, value FROM game_state").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

# ── Players ───────────────────────────────────────────────────────────────────

def register_player(name: str) -> bool:
    try:
        conn = get_conn()
        conn.execute("INSERT INTO players (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_players() -> list:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM players ORDER BY points DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_player(name: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM players WHERE name=?", (name,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_points(name: str, delta: int):
    conn = get_conn()
    conn.execute("UPDATE players SET points = points + ? WHERE name=?", (delta, name))
    conn.commit()
    conn.close()

def reset_all():
    conn = get_conn()
    conn.execute("DELETE FROM players")
    conn.execute("DELETE FROM bets")
    conn.execute("DELETE FROM answers")
    defaults = {
        "phase": "lobby",
        "current_game": "0",
        "game_started_at": "",
        "betting_open": "false",
        "answers_open": "false",
        "show_results": "false",
        "current_round": "0",
    }
    for k, v in defaults.items():
        conn.execute("UPDATE game_state SET value=? WHERE key=?", (v, k))
    conn.commit()
    conn.close()

# ── Bets (hay que incorporarle el tema de las rondas dentro de cada juego) ──────────────────────────────────────────────────────────────────────

def place_bet(player_name: str, game_id: int, amount: int, bet_win: int) -> bool:
    try:
        conn = get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO bets (player_name, game_id, bet_amount, bet_win) VALUES (?,?,?,?)",
            (player_name, game_id, amount, bet_win)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_bets(game_id: int) -> list:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM bets WHERE game_id=?", (game_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_player_bet(player_name: str, game_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM bets WHERE player_name=? AND game_id=?", (player_name, game_id)).fetchone()
    conn.close()
    return dict(row) if row else None

# ── Answers ───────────────────────────────────────────────────────────────────

def submit_answer(player_name: str, game_id: int, answer: str, round_num: int = 0) -> bool:
    try:
        conn = get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO answers (player_name, game_id, round_num, answer) VALUES (?,?,?,?)",
            (player_name, game_id, round_num, answer)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_answers(game_id: int, round_num: int = 0) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM answers WHERE game_id=? AND round_num=?", (game_id, round_num)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_player_answer(player_name: str, game_id: int, round_num: int = 0) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM answers WHERE player_name=? AND game_id=? AND round_num=?",
        (player_name, game_id, round_num)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def set_answer_score(player_name: str, game_id: int, round_num: int, score: int):
    conn = get_conn()
    conn.execute(
        "UPDATE answers SET score=? WHERE player_name=? AND game_id=? AND round_num=?",
        (score, player_name, game_id, round_num)
    )
    conn.commit()
    conn.close()
