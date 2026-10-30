# Settled genre ratings

Flask app deployed on Railway. It serves `templates/index.html` and `static/`, and computes genre ratings from the team Postgres database. `DATABASE_URL` is read on the server from the Railway service variables. Locally, if that variable is unset, `app.py` reads it from `.env`. Do not commit `.env`.

`preview_frontend.py` is a sample-data preview only. Railway must start `app.py`, not the preview server.

## Railway

Files the platform uses:

- `app.py` — home page and `GET /api/genre-ratings`
- `requirements.txt` — Flask, gunicorn, psycopg2-binary
- `Procfile` — `web: gunicorn app:app --bind 0.0.0.0:$PORT`

Set `DATABASE_URL` on the Railway service (the Postgres plugin supplies it). The public site URL is the submission URL; localhost is only for checking.

Local check against the same database: `python app.py`, then visit http://127.0.0.1:5000.

## API

`GET /api/genre-ratings`, with optional `?genre=Comedy`.

```json
{"mode":"database","genres":["Comedy","Drama"],"items":[{"genre":"Comedy","average_rating":3.5,"rating_count":2},{"genre":"Drama","average_rating":null,"rating_count":0}]}
```

`genres`: full alphabetically sorted list, even when filtering. `items`: all genres, or only the exact selected genre. Each item includes `genre` (string), `average_rating` (number or null), and `rating_count` (nonnegative integer). Zero ratings means a null average. An unknown filter returns an empty `items` array and the full `genres` list. Database failure returns non-2xx JSON and does not invent sample scores. `mode: sample` is reserved for `preview_frontend.py`. The page rounds averages to two decimals.

The frontend uses same-origin URLs and needs no npm build, external font, CDN, or API key.

## Rating definition

Mean of individual rating records for movies in the genre, not an unweighted average of movie-level averages. Each movie contributes to every genre it belongs to. Counts across genres overlap and must not be added to obtain overall totals. Unrated genres stay in the result through LEFT JOIN.

```sql
SELECT g.name AS genre,
       AVG(r.rating) AS average_rating,
       COUNT(r.rating) AS rating_count
FROM genres g
LEFT JOIN movie_genres mg ON mg.genre_id = g.genre_id
LEFT JOIN ratings r ON r.movie_id = mg.movie_id
-- For a selected genre only: WHERE g.name = %s
GROUP BY g.genre_id, g.name
ORDER BY g.name;
```

The genre filter is a bound parameter. Postgres `AVG` returns a Decimal; the API converts it to a JSON number.

## Before submission

- Check all genres, one filtered genre, an unrated genre, and the failure/retry state.
- Open the Railway URL in a browser that is not the machine that deployed it.

Design: warm charcoal #1F1B1D, muted plum #8E6C88, soft ivory #F2ECE9; responsive three/two/one-column grid, keyboard focus states, reduced-motion support, text-only data rendering.
