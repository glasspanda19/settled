"""Local-only preview. Reads repository sample data; does not connect to Railway."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json
import sqlite3
import argparse

ROOT = Path(__file__).resolve().parent
QUERY = """SELECT g.name AS genre, AVG(r.rating) AS average_rating,
COUNT(r.rating) AS rating_count
FROM genres g
LEFT JOIN movie_genres mg ON mg.genre_id = g.genre_id
LEFT JOIN ratings r ON r.movie_id = mg.movie_id
{where}
GROUP BY g.genre_id, g.name ORDER BY g.name"""

def sample_data(genre=None):
    with sqlite3.connect(':memory:') as conn:
        conn.row_factory = sqlite3.Row
        conn.executescript((ROOT / 'schema.sql').read_text(encoding='utf-8-sig'))
        genres = [r[0] for r in conn.execute('SELECT name FROM genres ORDER BY name')]
        rows = conn.execute(QUERY.format(where='WHERE g.name = ?' if genre else ''), (genre,) if genre else ())
        return {'mode': 'sample', 'genres': genres, 'items': [dict(row) for row in rows]}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/genre-ratings':
            try:
                data = sample_data(parse_qs(parsed.query).get('genre', [None])[0])
                self.send_body(200, json.dumps(data).encode(), 'application/json; charset=utf-8')
            except Exception:
                self.send_body(500, b'{"error":"Preview data unavailable"}', 'application/json')
            return
        files = {'/': ('templates/index.html', 'text/html; charset=utf-8'),
                 '/static/style.css': ('static/style.css', 'text/css; charset=utf-8'),
                 '/static/app.js': ('static/app.js', 'text/javascript; charset=utf-8')}
        if parsed.path not in files:
            self.send_error(404); return
        filename, mime = files[parsed.path]
        self.send_body(200, (ROOT / filename).read_bytes(), mime)

    def send_body(self, status, body, mime):
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers(); self.wfile.write(body)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    print(f'Local sample preview: http://127.0.0.1:{args.port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
