const form = document.getElementById('upload-form');
const fileInput = document.getElementById('file-input');
const uploadStatus = document.getElementById('upload-status');
const imageList = document.getElementById('image-list');
const refreshBtn = document.getElementById('refresh-btn');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const file = fileInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('image', file);

  uploadStatus.textContent = 'Загрузка...';

  try {
    const res = await fetch('/api/images', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    uploadStatus.textContent = 'Загружено. Обработка начнётся в фоне.';
    fileInput.value = '';
    loadImages();
  } catch (err) {
    uploadStatus.textContent = `Ошибка: ${err.message}`;
  }
});

refreshBtn.addEventListener('click', loadImages);

async function loadImages() {
  const res = await fetch('/api/images');
  const images = await res.json();

  imageList.innerHTML = '';

  for (const img of images) {
    const li = document.createElement('li');

    const statusEl = document.createElement('div');
    statusEl.className = `status status-${img.status}`;
    statusEl.textContent = `#${img.id} ${img.original_filename} — ${img.status}`;
    li.appendChild(statusEl);

    if (img.status === 'done') {
      const thumbs = document.createElement('div');
      thumbs.className = 'thumbs';
      thumbs.innerHTML = `
        <a href="/processed/${img.thumbnail_filename}" target="_blank">превью</a>
        <a href="/processed/${img.grayscale_filename}" target="_blank">ч/б</a>
        <a href="/uploads/${img.stored_filename}" target="_blank">оригинал</a>
      `;
      li.appendChild(thumbs);
    }

    if (img.status === 'failed' && img.error_message) {
      const err = document.createElement('div');
      err.textContent = `Ошибка: ${img.error_message}`;
      li.appendChild(err);
    }

    imageList.appendChild(li);
  }
}

loadImages();
