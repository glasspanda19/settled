# Settled genre ratings frontend

Scope: responsive HTML/CSS/JavaScript frontend. No Railway settings, credentials, database schema, or existing team files are changed. No production backend is implemented here.

## Local preview

Run `python preview_frontend.py`, then visit http://127.0.0.1:8765.
Python 3 standard library only. The local-only server loads `schema.sql` into a temporary in-memory SQLite database for each request and computes the results. It never writes a database file or connects to Railway. The page explicitly labels these results as repository sample data. Do not deploy this preview server as the final assignment app.

## Flask integration

Keep `templates/index.html` and `static/` in the existing Flask app root. Serve the home page with `render_template('index.html')`. The frontend uses same-origin URLs and requires no npm build, external font, CDN, or API key.

Implement `GET /api/genre-ratings` and optional `?genre=Comedy`.
Response shape (illustrative format; values must be computed from the database):

```json
{"mode":"database","genres":["Comedy","Drama"],"items":[{"genre":"Comedy","average_rating":3.5,"rating_count":2},{"genre":"Drama","average_rating":null,"rating_count":0}]}
```

`genres`: full alphabetically sorted list, even when filtering. `items`: all genres, or only the exact selected genre. Each item includes `genre` (string), `average_rating` (number or null), `rating_count` (nonnegative integer). Zero ratings means null average. Unknown filter may return an empty items array. Return non-2xx JSON on database failure, not fabricated sample results. `mode: sample` is reserved for the local preview; use `database` for the real backend. The UI rounds averages to two decimals.

## Rating definition / suggested PostgreSQL query

Mean of individual rating records for movies in the genre, not an unweighted average of movie-level averages. Each movie contributes to every genre it belongs to. Counts across genres overlap and must not be added to obtain overall totals. Preserve unrated genres with LEFT JOIN.

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

Use a bound SQL parameter, not string interpolation. Convert database Decimal averages to JSON numbers if required. Read credentials only on the server from the team's environment configuration. Confirm this query against the actual Railway schema before integrating.

## Before submission

- Connect to the real Flask endpoint and Railway database.
- Check all genres, a filtered genre, an unrated genre, and failure/retry behavior.
- Verify the public deployment from a different browser; localhost is not the submission URL.
- Nihar handles deployment. Frontend files alone do not complete the deployed-app assignment.

Design: warm charcoal #1F1B1D, muted plum #8E6C88, soft ivory #F2ECE9; responsive three/two/one-column grid, keyboard focus states, reduced-motion support, text-only data rendering.
