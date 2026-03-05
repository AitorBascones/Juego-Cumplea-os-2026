# 🎮 Gymkana Multijugador

App de gymkana en tiempo real para jugar en grupo. El host controla el ritmo desde un panel de administración.

---

## 🚀 Despliegue en Streamlit Cloud (gratis)

1. **Sube este proyecto a GitHub** (repositorio público o privado)
2. Ve a [share.streamlit.io](https://share.streamlit.io) → *New app*
3. Conecta tu repo → archivo principal: `app.py`
4. Deploy 🎉

---

## 👥 Flujo de la partida

### Para jugadores:
- Acceden a la **URL principal** de la app (o escanean QR)
- Escriben su nombre y entran al lobby
- Esperan instrucciones del host

### Para el host (admin):
- Acceden a `TU_URL/admin`
- Contraseña: `gymkana2024` *(cámbiala en `pages/admin.py`)*
- Desde ahí controlan todo: abrir apuestas, iniciar juegos, mostrar resultados

---

## 🎮 Juegos incluidos

| # | Juego | Mecánica | Puntos |
|---|-------|----------|--------|
| 1 | ⏳ Orden Histórico | Ordena 6 hechos del más antiguo al más reciente | 0–500 pts |
| 2 | 🔢 Adivina el Número | ¿Quién más se acerca? | 50–500 pts |
| 3 | 🗳️ ¿Qué Prefieres? | Los que votan la mayoría ganan | 0 / 300 pts |

### 💰 Sistema de apuestas
Antes de cada juego, los jugadores apuestan puntos a si van a ganar o no.
- **Aciertan la apuesta** → ganan los puntos apostados extra
- **Fallan la apuesta** → pierden los puntos apostados

---

## 🗂️ Estructura del proyecto

```
gymkana/
├── app.py                  # Vista del jugador (página principal)
├── pages/
│   └── admin.py            # Panel del host (contraseña requerida)
├── utils/
│   ├── database.py         # SQLite: estado compartido entre jugadores
│   └── games.py            # Contenido y lógica de puntuación
├── .streamlit/
│   └── config.toml         # Tema visual
└── requirements.txt
```

---

## ✏️ Personalización

### Cambiar preguntas
Edita `utils/games.py`:
- `GAME1_EVENTS` → los 6 hechos históricos
- `GAME4_QUESTIONS` → preguntas de "adivina el número"
- `GAME3_QUESTIONS` → preguntas de "¿qué prefieres?"

### Cambiar contraseña del admin
En `pages/admin.py`, línea:
```python
ADMIN_PASSWORD = "gymkana2024"
```

### Añadir más juegos
1. Crea la lógica en `utils/games.py`
2. Añade la vista del jugador en `app.py` → función `show_gameX()`
3. Añade el scoring en `pages/admin.py`

---

## ⚠️ Nota sobre Streamlit Cloud

Streamlit Cloud **reinicia el servidor** si no hay actividad. La base de datos SQLite se borrará en ese caso.
Para una versión más robusta, sustituye SQLite por:
- **Supabase** (PostgreSQL gratuito)
- **PlanetScale** (MySQL gratuito)
- **Redis** (con `upstash.com`)

Para una gymkana de una tarde, SQLite funciona perfectamente. 🎉
