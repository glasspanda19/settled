'use strict';
const grid = document.querySelector('#genre-grid');
const select = document.querySelector('#genre');
const apply = document.querySelector('#apply');
const count = document.querySelector('#results-count');
const errorBox = document.querySelector('#error');
let requestNumber = 0;
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function validate(data) {
  if (!data || !Array.isArray(data.genres) || !Array.isArray(data.items)) throw new Error('Invalid response');
  if (!data.genres.every(x => typeof x === 'string')) throw new Error('Invalid genres');
  for (const item of data.items) {
    if (typeof item.genre !== 'string' || !Number.isInteger(item.rating_count) || item.rating_count < 0 ||
        !(item.average_rating === null || (Number.isFinite(item.average_rating) && item.average_rating >= 0 && item.average_rating <= 5)) ||
        (item.rating_count === 0) !== (item.average_rating === null)) throw new Error('Invalid ratings');
  }
  return data;
}
function renderCard(item) {
  const card = element('article', 'genre-card');
  const top = element('div', 'card-top');
  top.append(element('h3', '', item.genre));
  const symbol = element('span', 'genre-symbol', '✦'); symbol.setAttribute('aria-hidden', 'true'); top.append(symbol);
  const score = element('p', item.average_rating === null ? 'score unrated' : 'score', item.average_rating === null ? 'Not rated yet' : item.average_rating.toFixed(2));
  if (item.average_rating !== null) score.append(element('small', '', '/ 5'));
  const bottom = element('div', 'card-bottom');
  bottom.append(element('span', '', 'AVERAGE USER RATING'), element('span', '', `${item.rating_count.toLocaleString()} ${item.rating_count === 1 ? 'rating' : 'ratings'}`));
  card.append(top, score, bottom); return card;
}
async function loadRatings() {
  const thisRequest = ++requestNumber;
  const selected = select.value;
  errorBox.hidden = true; document.querySelector('#empty').hidden = true;
  grid.setAttribute('aria-busy', 'true'); grid.replaceChildren(...Array.from({length:3}, () => element('div', 'skeleton')));
  select.disabled = true; apply.disabled = true; count.textContent = 'Loading genres…';
  const controller = new AbortController(); const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch('/api/genre-ratings' + (selected ? `?genre=${encodeURIComponent(selected)}` : ''), {signal:controller.signal, headers:{Accept:'application/json'}});
    if (!response.ok) throw new Error('Service unavailable');
    const data = validate(await response.json());
    if (thisRequest !== requestNumber) return;
    select.replaceChildren(new Option('All genres', ''), ...data.genres.map(name => new Option(name, name)));
    select.value = selected;
    grid.replaceChildren(...data.items.map(renderCard));
    document.querySelector('#empty').hidden = data.items.length !== 0;
    count.textContent = `${data.items.length} ${data.items.length === 1 ? 'genre' : 'genres'} shown · out of ${data.genres.length}`;
    const preview = data.mode === 'sample';
    document.querySelector('#source-badge').textContent = preview ? '●  Repository sample · Preview' : '●  Connected dataset';
    document.querySelector('#data-note').textContent = preview ? 'Local preview uses the sample records in schema.sql. These scores do not represent the full MovieLens dataset.' : 'Source: MovieLens · Scores reflect the records currently stored in the connected database.';
  } catch (_) {
    if (thisRequest !== requestNumber) return;
    grid.replaceChildren(); errorBox.hidden = false; count.textContent = 'Ratings unavailable';
    document.querySelector('#source-badge').textContent = 'Data connection unavailable';
    document.querySelector('#data-note').textContent = 'No placeholder scores are displayed. Retry when the data service is available.';
  } finally {
    clearTimeout(timer);
    if (thisRequest === requestNumber) {grid.setAttribute('aria-busy', 'false');select.disabled = false; apply.disabled = false;}
  }
}
document.querySelector('#filter-form').addEventListener('submit', event => {event.preventDefault(); loadRatings();});
document.querySelector('#retry').addEventListener('click', loadRatings);
loadRatings();
