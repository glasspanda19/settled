#!/usr/bin/env python3
"""Settled genre ratings app for Railway.

Serves the home page and GET /api/genre-ratings from the Postgres database
named by DATABASE_URL. Railway injects that variable; a local run falls
back to .env. Sample data is never substituted for a database failure.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2
from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parent

GENRES_SQL = "SELECT name FROM genres ORDER BY name"

RATINGS_SQL = """
SELECT g.name AS genre,
       AVG(r.rating) AS average_rating,
       COUNT(r.rating) AS rating_count
FROM genres g
LEFT JOIN movie_genres mg ON mg.genre_id = g.genre_id
LEFT JOIN ratings r ON r.movie_id = mg.movie_id
{where}
GROUP BY g.genre_id, g.name
ORDER BY g.name
"""

app = Flask(__name__)


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    env_path = ROOT / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() == "DATABASE_URL":
                value = value.strip().strip("'\"")
                if value:
                    return value
    raise RuntimeError("DATABASE_URL is not configured")


def genre_payload(genre: str | None) -> dict:
    where = "WHERE g.name = %s" if genre else ""
    params = (genre,) if genre else ()
    conn = psycopg2.connect(database_url())
    try:
        with conn.cursor() as cur:
            cur.execute(GENRES_SQL)
            genres = [row[0] for row in cur.fetchall()]
            cur.execute(RATINGS_SQL.format(where=where), params)
            items = []
            for name, average, count in cur.fetchall():
                count = int(count)
                items.append(
                    {
                        "genre": name,
                        "average_rating": None
                        if count == 0 or average is None
                        else float(average),
                        "rating_count": count,
                    }
                )
        return {"mode": "database", "genres": genres, "items": items}
    finally:
        conn.close()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/genre-ratings")
def genre_ratings():
    genre = request.args.get("genre", "").strip() or None
    try:
        return jsonify(genre_payload(genre))
    except Exception:
        return jsonify({"error": "Database unavailable"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
