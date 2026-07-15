const grid = document.getElementById('grid');
const statusEl = document.getElementById('status');
const searchInput = document.getElementById('search-input');
const genreChips = document.getElementById('genre-chips');

let activeGenre = null;
let debounceTimer = null;

function setStatus(text) {
  statusEl.textContent = text;
}

function renderMovies(movies) {
  grid.innerHTML = '';
  if (!movies.length) {
    setStatus('Ничего не найдено.');
    return;
  }
  setStatus(Фильмов: ${movies.length});
  movies.forEach(m => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = 
      <div class="card-top">
        <h3 class="card-title">${m.title}</h3>
        <span class="card-rating">★ ${m.rating}</span>
      </div>
      <div class="card-meta">${m.genre} · ${m.year}</div>
      <div class="card-director">Режиссёр: ${m.director || '—'}</div>
      <p class="card-desc">${m.description || ''}</p>
    ;
    grid.appendChild(card);
  });
}

async function loadGenres() {
  try {
    const res = await fetch('/api/genres');
    const genres = await res.json();
    genreChips.innerHTML = '';
    const allChip = document.createElement('button');
    allChip.className = 'chip active';
    allChip.textContent = 'Все жанры';
    allChip.onclick = () => selectGenre(null, allChip);
    genreChips.appendChild(allChip);

    genres.forEach(g => {
      const chip = document.createElement('button');
      chip.className = 'chip';
      chip.textContent = g;
      chip.onclick = () => selectGenre(g, chip);
      genreChips.appendChild(chip);
    });
  } catch (e) {
    console.error('Failed to load genres', e);
  }
}

function selectGenre(genre, chipEl) {
  activeGenre = genre;
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  chipEl.classList.add('active');
  loadMovies();
}

async function loadMovies() {
  setStatus('Загрузка…');
  try {
    const query = searchInput.value.trim();
    let url;
    if (query) {
      url = /api/movies/search?q=${encodeURIComponent(query)};
    } else if (activeGenre) {
      url = /api/movies?genre=${encodeURIComponent(activeGenre)};
    } else {
      url = '/api/movies';
    }
    const res = await fetch(url);
    if (!res.ok) throw new Error(HTTP ${res.status});
    const movies = await res.json();
    renderMovies(movies);
  } catch (e) {
    setStatus('Ошибка загрузки данных. Проверьте, что backend и база данных запущены.');
    console.error(e);
  }
}

searchInput.addEventListener('input', () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(loadMovies, 300);
});

loadGenres();
loadMovies();
