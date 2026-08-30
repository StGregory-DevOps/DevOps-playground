const API_BASE = "/api";
const POLL_INTERVAL_MS = 3000;

const form = document.getElementById("add-form");
const urlInput = document.getElementById("url-input");
const noteInput = document.getElementById("note-input");
const grid = document.getElementById("bookmarks");
const emptyState = document.getElementById("empty-state");
const errorBanner = document.getElementById("error-banner");

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.remove("hidden");
  setTimeout(() => errorBanner.classList.add("hidden"), 4000);
}

function statusLabel(status) {
  return { pending: "В очереди", processing: "Обрабатывается", done: "Готово", error: "Ошибка" }[status] || status;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function renderBookmarks(bookmarks) {
  grid.querySelectorAll(".card").forEach((el) => el.remove());
  emptyState.classList.toggle("hidden", bookmarks.length > 0);

  bookmarks.forEach((b) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="card-title">${escapeHtml(b.title || b.url)}</div>
      <div class="card-url">${escapeHtml(b.url)}</div>
      ${b.note ? `<div class="card-note">📝 ${escapeHtml(b.note)}</div>` : ""}
      ${b.description ? `<div class="card-desc">${escapeHtml(b.description)}</div>` : ""}
      <div class="card-footer">
        <span class="badge ${b.status}">${statusLabel(b.status)}</span>
        <button class="delete-btn" data-id="${b.id}">Удалить</button>
      </div>
    `;
    grid.appendChild(card);
  });

  grid.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", () => deleteBookmark(btn.dataset.id));
  });
}

async function loadBookmarks() {
  try {
    const res = await fetch(`${API_BASE}/bookmarks`);
    if (!res.ok) throw new Error("Не удалось загрузить список");
    renderBookmarks(await res.json());
  } catch (err) {
    showError(err.message);
  }
}

async function addBookmark(event) {
  event.preventDefault();
  try {
    const res = await fetch(`${API_BASE}/bookmarks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: urlInput.value, note: noteInput.value || null }),
    });
    if (!res.ok) throw new Error("Не удалось добавить ссылку");
    urlInput.value = "";
    noteInput.value = "";
    await loadBookmarks();
  } catch (err) {
    showError(err.message);
  }
}

async function deleteBookmark(id) {
  try {
    const res = await fetch(`${API_BASE}/bookmarks/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Не удалось удалить ссылку");
    await loadBookmarks();
  } catch (err) {
    showError(err.message);
  }
}

form.addEventListener("submit", addBookmark);
loadBookmarks();
setInterval(loadBookmarks, POLL_INTERVAL_MS);
