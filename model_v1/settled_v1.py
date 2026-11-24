"""Reproduce the Settled v1 scatterplot, validation metrics, decision and value table."""
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FEATURES = ["user_mean", "movie_mean", "user_primary_genre_mean"]
SEED = 42
PRIOR_COUNT = 5  # fixed smoothing strength for sparse histories


def load_data(path):
    pairs, ratings = [], []
    titles, genres, genre_index = {}, {}, {}
    earliest, latest = float("inf"), 0
    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            u, m = int(row["UserID"]), int(row["MovieID"])
            pairs.append((u, m))
            ratings.append(float(row["Rating"]))
            titles[m] = row["Title"]
            genres[m] = genre_index.setdefault(row["Primary_Genre"], len(genre_index))
            stamp = int(row["Timestamp"])
            earliest, latest = min(earliest, stamp), max(latest, stamp)
    u, m = np.asarray(pairs, dtype=np.int64).T
    y = np.array(ratings)
    if len(np.unique(u * (m.max()+1) + m)) != len(y):
        raise ValueError("Expected one row per user/movie pair")
    if not np.all((1 <= y) & (y <= 5)):
        raise ValueError("Ratings must be between 1 and 5")
    period = [datetime.fromtimestamp(s, timezone.utc).date().isoformat() for s in (earliest, latest)]
    return u, m, y, titles, genres, len(genre_index), period


class RatingModel:
    def __init__(self, users, movies, y, genres, genre_count):
        self.genres = genres
        self.genre_count = genre_count
        self.total = y.sum()
        self.n = len(y)
        self.stats = [(np.bincount(k), np.bincount(k, weights=y))
                      for k in self.keys(users, movies)]
        # Every training row's own rating is removed from all three aggregates
        # and from its global smoothing prior before fitting the coefficients.
        design = self.design(users, movies, exclude=y)
        self.beta = np.linalg.lstsq(design, y, rcond=None)[0]
        self.adjusted_r2 = 1 - (np.sum((y-design@self.beta)**2)/(len(y)-len(self.beta))) / y.var(ddof=1)

    def keys(self, u, m):
        genre = np.fromiter((self.genres[int(v)] for v in m), dtype=int, count=len(m))
        return u, m, u * self.genre_count + genre

    def design(self, u, m, exclude=None):
        prior = self.total/self.n if exclude is None else (self.total-exclude)/(self.n-1)
        columns = [np.ones(len(u))]
        for key, (counts, sums) in zip(self.keys(u,m), self.stats):
            valid = (key >= 0) & (key < len(counts))
            count, total = np.zeros(len(u)), np.zeros(len(u))
            count[valid], total[valid] = counts[key[valid]], sums[key[valid]]
            if exclude is not None:
                count -= 1
                total -= exclude
            columns.append((total + PRIOR_COUNT * prior)/(count + PRIOR_COUNT))
        return np.column_stack(columns)

    def predict(self, u, m):
        return np.clip(self.design(u,m) @ self.beta, 1, 5)


def plot_ratings(actual, predicted, out):
    fig, ax = plt.subplots(figsize=(8, 7))
    rng = np.random.default_rng(271)
    ax.scatter(actual + rng.uniform(-.08, .08, len(actual)), predicted,
               s=1, alpha=.035, color="#146bab", linewidths=0)
    ax.plot([1, 5], [1, 5], "k--", lw=1.3, label="Perfect prediction (y = x)")
    ax.legend(loc="upper left")
    ax.set(xlim=(.8, 5.2), ylim=(.9, 5.1), xticks=range(1, 6), yticks=range(1, 6),
           xlabel="Actual rating (stars)", ylabel="Predicted rating (stars)")
    ax.set_title(f"Actual vs. predicted movie ratings\n{len(actual):,} held-out ratings")
    fig.tight_layout()
    fig.savefig(out / "rating_scatter_test.png", dpi=180)
    plt.close(fig)


RECOMMEND_AT = 4.0
GOOD_MATCH_CENTS = 10
BAD_MATCH_CENTS = -50
SHOWN_VOLUME = 100_000


def decide(model, user_id, movie_id):
    score = model.predict(np.array([user_id]), np.array([movie_id])).item()
    return score, "Recommend" if score >= RECOMMEND_AT else "Skip"


def summarize(actual):
    shown = len(actual)
    good = int(np.count_nonzero(actual >= 4))
    bad = int(np.count_nonzero(actual <= 2))
    net_cents = GOOD_MATCH_CENTS * good + BAD_MATCH_CENTS * bad
    projected_dollars = net_cents * SHOWN_VOLUME / (100 * shown)
    return good, bad, projected_dollars


def money(value):
    sign = "-" if value < 0 else "+"
    return f"{sign}${abs(value):,.2f}"


def main():
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=repo / "movielens_clean.csv")
    data = parser.parse_args().data
    users, movies, ratings, titles, genres, count, _ = load_data(data)
    train, test = np.split(np.random.default_rng(SEED).permutation(len(ratings)), [int(.7 * len(ratings))])
    model = RatingModel(users[train], movies[train], ratings[train], genres, count)

    user = 788
    rated = set(movies[users == user])
    # Pick before scoring: the lowest catalog ID the user never rated in the full CSV.
    movie = min(set(movies[train]) - rated)
    score, action = decide(model, user, movie)
    print(f"Example: User {user}, {titles[movie]} (movie ID {movie})")
    print("Inputs (user mean, movie mean, user-genre mean):",
          *(f"{v:.4f}" for v in model.design(np.array([user]), np.array([movie]))[0, 1:]))
    print(f"Prediction: {score:.4f} stars | Threshold: {RECOMMEND_AT:.1f} | Decision: {action}")

    actual = ratings[test]
    predicted = model.predict(users[test], movies[test])
    baseline = ratings[train].mean()
    print(f"Train/test: {len(train):,}/{len(test):,}; users: {len(set(users)):,}; films: {len(titles):,}")
    print("Coefficients (intercept, user, movie, user-genre):", model.beta)
    print(f"Training adjusted R2: {model.adjusted_r2:.6f}; baseline mean: {baseline:.6f}")
    for name, estimates in [("Baseline", baseline), ("V1", predicted)]:
        mse = np.mean((actual - estimates) ** 2)
        print(f"{name} test R2: {1 - mse / actual.var():.9f}; RMSE: {np.sqrt(mse):.9f}")
    plot_ratings(actual, predicted, Path(__file__).resolve().parent)
    selected = actual[predicted >= RECOMMEND_AT]
    n, k = len(actual), len(selected)
    good0, bad0, profit0 = summarize(actual)
    good1, bad1, profit1 = summarize(selected)
    print("\nAssumptions: +10 cents per 4-5 star match, -50 cents per 1-2 star match,")
    print("zero for 3 stars. Each policy delivers 100,000 shown recommendations.")
    print("The projection assumes the test-set mix of ratings continues.")
    print(f"{'Metric':<33}{'Unfiltered baseline':>21}{'V1':>17}{'Change':>17}")
    for name, base, v1 in [
        ("Share of test pairs shown", 1, k/n),
        ("Good among shown (4-5 stars)", good0/n, good1/k),
        ("Bad among shown (1-2 stars)", bad0/n, bad1/k),
    ]:
        change = f"{100*(v1-base):+.1f} pp"
        print(f"{name:<33}{base:>21.1%}{v1:>17.1%}{change:>17}")
    print(f"{'Net per 100,000 shown':<33}{money(profit0):>21}{money(profit1):>17}{money(profit1-profit0):>17}")
    print(f"Baseline: {n:,} shown, {good0:,} good, {bad0:,} bad.")
    print(f"V1: {k:,} shown, {good1:,} good, {bad1:,} bad.")


if __name__ == "__main__":
    main()

