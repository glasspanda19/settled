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

-- ---------------------------------------------------------------------------
-- Sample rows from settled_movielens_sample.csv
-- ---------------------------------------------------------------------------

INSERT INTO users (user_id, gender, age_id, occupation_id, zip_code) VALUES
    (2747, 'F', 18, 4,  '90025'),
    (3002, 'M', 45, 11, '90028'),
    (6005, 'F', 25, 5,  '28401'),
    (2842, 'M', 35, 17, '30145'),
    (3775, 'M', 35, 12, '14619'),
    (1718, 'M', 18, 4,  '43235'),
    (1575, 'F', 50, 7,  '94949'),
    (5907, 'M', 25, 2,  '11217'),
    (4498, 'M', 50, 7,  '76054'),
    (3001, 'M', 18, 4,  '94704');

INSERT INTO movies (movie_id, title, year) VALUES
    (3175, 'Galaxy Quest', 1999),
    (145,  'Bad Boys', 1995),
    (1985, 'Halloween 4: The Return of Michael Myers', 1988),
    (893,  'Mother Night', 1996),
    (3361, 'Bull Durham', 1988),
    (3535, 'American Psycho', 2000),
    (2529, 'Planet of the Apes', 1968),
    (923,  'Citizen Kane', 1941),
    (2822, 'Medicine Man', 1992),
    (1205, 'Transformers: The Movie, The', 1986);

INSERT INTO movie_genres (movie_id, genre_id)
SELECT 3175, genre_id FROM genres WHERE name IN ('Adventure', 'Comedy', 'Sci-Fi')
UNION ALL
SELECT 145,  genre_id FROM genres WHERE name IN ('Action')
UNION ALL
SELECT 1985, genre_id FROM genres WHERE name IN ('Horror')
UNION ALL
SELECT 893,  genre_id FROM genres WHERE name IN ('Drama')
UNION ALL
SELECT 3361, genre_id FROM genres WHERE name IN ('Comedy')
UNION ALL
SELECT 3535, genre_id FROM genres WHERE name IN ('Comedy', 'Horror', 'Thriller')
UNION ALL
SELECT 2529, genre_id FROM genres WHERE name IN ('Action', 'Sci-Fi')
UNION ALL
SELECT 923,  genre_id FROM genres WHERE name IN ('Drama')
UNION ALL
SELECT 2822, genre_id FROM genres WHERE name IN ('Adventure', 'Romance')
UNION ALL
SELECT 1205, genre_id FROM genres WHERE name IN ('Action', 'Animation', 'Children''s', 'Sci-Fi', 'Thriller', 'War');

INSERT INTO ratings (user_id, movie_id, rating, rated_at) VALUES
    (2747, 3175, 5, 973211459),
    (3002, 145,  4, 976505788),
    (6005, 1985, 3, 956795161),
    (2842, 893,  4, 972548309),
    (3775, 3361, 4, 966040006),
    (1718, 3535, 2, 974705151),
    (1575, 2529, 3, 974738001),
    (5907, 923,  3, 957373664),
    (4498, 2822, 2, 964999006),
    (3001, 1205, 5, 970618280);
