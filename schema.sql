-- MovieLens schema derived from settled_movielens_sample.csv
-- Source columns: UserID, Gender, Age, Occupation, Zip-code,
--                 MovieID, Title, Genres, Rating, Timestamp
--
-- The CSV is denormalized (one row per rating, with user and movie
-- fields repeated). This schema splits that into users, movies, and
-- ratings, plus lookup/junction tables for coded fields and genres.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Lookup tables (empty in the CSV; values are MovieLens 1M codes)
-- ---------------------------------------------------------------------------

CREATE TABLE occupations (
    occupation_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE age_groups (
    age_id INTEGER PRIMARY KEY,
    description TEXT NOT NULL UNIQUE
);

CREATE TABLE genres (
    genre_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- ---------------------------------------------------------------------------
-- Core tables (populated from the CSV)
-- ---------------------------------------------------------------------------

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    gender TEXT NOT NULL CHECK (gender IN ('M', 'F')),
    age_id INTEGER NOT NULL REFERENCES age_groups (age_id),
    occupation_id INTEGER NOT NULL REFERENCES occupations (occupation_id),
    zip_code TEXT NOT NULL
);

-- Title is stored without the trailing "(YYYY)"; year is extracted.
CREATE TABLE movies (
    movie_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    year INTEGER NOT NULL CHECK (year BETWEEN 1870 AND 2100)
);

CREATE TABLE movie_genres (
    movie_id INTEGER NOT NULL REFERENCES movies (movie_id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres (genre_id),
    PRIMARY KEY (movie_id, genre_id)
);

-- One rating per (user, movie) pair, matching MovieLens 1M.
CREATE TABLE ratings (
    user_id INTEGER NOT NULL REFERENCES users (user_id),
    movie_id INTEGER NOT NULL REFERENCES movies (movie_id),
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    rated_at INTEGER NOT NULL, -- Unix timestamp from the CSV Timestamp column
    PRIMARY KEY (user_id, movie_id)
);

CREATE INDEX idx_users_occupation ON users (occupation_id);
CREATE INDEX idx_users_age ON users (age_id);
CREATE INDEX idx_movies_year ON movies (year);
CREATE INDEX idx_movie_genres_genre ON movie_genres (genre_id);
CREATE INDEX idx_ratings_movie ON ratings (movie_id);
CREATE INDEX idx_ratings_rated_at ON ratings (rated_at);

-- ---------------------------------------------------------------------------
-- MovieLens 1M reference data
-- ---------------------------------------------------------------------------

INSERT INTO occupations (occupation_id, name) VALUES
    (0,  '"other" or not specified'),
    (1,  'academic/educator'),
    (2,  'artist'),
    (3,  'clerical/admin'),
    (4,  'college/grad student'),
    (5,  'customer service'),
    (6,  'doctor/health care'),
    (7,  'executive/managerial'),
    (8,  'farmer'),
    (9,  'homemaker'),
    (10, 'K-12 student'),
    (11, 'lawyer'),
    (12, 'programmer'),
    (13, 'retired'),
    (14, 'sales/marketing'),
    (15, 'scientist'),
    (16, 'self-employed'),
    (17, 'technician/engineer'),
    (18, 'tradesman/craftsman'),
    (19, 'unemployed'),
    (20, 'writer');

INSERT INTO age_groups (age_id, description) VALUES
    (1,  'Under 18'),
    (18, '18-24'),
    (25, '25-34'),
    (35, '35-44'),
    (45, '45-49'),
    (50, '50-55'),
    (56, '56+');

INSERT INTO genres (name) VALUES
    ('Action'),
    ('Adventure'),
    ('Animation'),
    ('Children''s'),
    ('Comedy'),
    ('Crime'),
    ('Documentary'),
    ('Drama'),
    ('Fantasy'),
    ('Film-Noir'),
    ('Horror'),
    ('Musical'),
    ('Mystery'),
    ('Romance'),
    ('Sci-Fi'),
    ('Thriller'),
    ('War'),
    ('Western');
