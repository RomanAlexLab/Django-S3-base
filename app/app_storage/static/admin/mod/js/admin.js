// static/admin/mod/admin.js

// === Переменные ===
let currentMediaIndex = 0; // Текущий индекс медиафайла в галерее
let mediaElements = [];    // Массив элементов с медиа (изображения, видео и т.д.)

// === Функции работы с модальным окном ===

/**
 * Открывает модальное окно с медиафайлом.
 * @param {Event} e - Событие клика (опционально)
 * @param {string} url - URL медиафайла
 * @param {string} fileType - Тип файла (image, video, unknown)
 * @param {string} mimeType - MIME-тип файла
 * @param {string} fileName - Имя файла
 * @param {number} index - Индекс файла в галерее
 */
function openMediaModal(e, url, fileType, mimeType, fileName, index = 0) {
    e?.preventDefault();
    closeMediaModal(); // Закрываем предыдущее модальное окно, если оно открыто
    currentMediaIndex = index;

    const wrapper = document.createElement('div');
    wrapper.id = 'customMediaModalWrapper';
    wrapper.innerHTML = `
        <div id="FullSpceMediaModal">
            <div class="line-btn-close"><button class="btn-close">×</button></div>
            <div class="line-content">
                <div class="media-left-nav"><button id="prevMedia" class="media-nav left-nav" onclick="navigateMedia(-1)">❮</button></div>
                <div id="customMediaModal" class="custom-media-modal">
                    <div class="modal-content" id="modalContent"></div>
                </div>
                <div class="media-right-nav"><button id="nextMedia" class="media-nav right-nav" onclick="navigateMedia(1)">❯</button></div>
            </div>
        </div>
    `;
    document.body.appendChild(wrapper);

    const fullSpaceModal = document.getElementById('FullSpceMediaModal');
    const btnClose = fullSpaceModal.querySelector('.btn-close');

    // Закрытие по клику вне контента
    fullSpaceModal.addEventListener('click', (event) => {
        if (event.target === fullSpaceModal) {
            closeMediaModal();
        }
    });

    // Закрытие по кнопке
    btnClose.addEventListener('click', closeMediaModal);

    renderMediaContent(url, fileType, mimeType, fileName);
    document.addEventListener('keydown', handleKeyDown); // Обработчики клавиш
}

/**
 * Рендерит содержимое медиафайла в модальном окне.
 * @param {string} url - URL медиафайла
 * @param {string} fileType - Тип файла (image, video, unknown)
 * @param {string} mimeType - MIME-тип файла
 * @param {string} fileName - Имя файла
 */
function renderMediaContent(url, fileType, mimeType, fileName) {
    const modalContent = document.getElementById('modalContent');
    if (!modalContent) return;

    let contentHTML = '';
    switch (fileType) {
        case 'image':
            contentHTML = `<img src="${url}" alt="Файл" loading="lazy" crossorigin="anonymous">`;
            break;
        case 'video':
            contentHTML = `<video controls loading="lazy" crossorigin="anonymous"><source src="${url}" type="${mimeType}"></video>`;
            break;
        case 'unknown':
            contentHTML = `<p class="no-filetype">Неизвестный тип файла</p><a href="${url}" target="_blank" download>Скачать</a>`;
            break;
        default:
            contentHTML = `<p class="no-filetype">Неизвестный тип файла</p><a href="${url}" target="_blank" download>Скачать</a>`;
    }
    contentHTML += `<p class="modal-text-filename">${fileName}</p>`;
    modalContent.innerHTML = contentHTML;
}

/**
 * Закрывает модальное окно.
 */
function closeMediaModal() {
    const wrapper = document.getElementById('customMediaModalWrapper');
    if (wrapper) wrapper.remove();
    document.removeEventListener('keydown', handleKeyDown);
}

// === Обработчики событий ===

/**
 * Обработчик нажатий на клавиатуру.
 * @param {KeyboardEvent} e - Событие клавиатуры
 */
function handleKeyDown(e) {
    if (e.key === 'Escape') closeMediaModal();     // ESC — закрыть окно
    if (e.key === 'ArrowLeft') navigateMedia(-1);  // ← — предыдущий файл
    if (e.key === 'ArrowRight') navigateMedia(1);  // → — следующий файл
}

/**
 * Переключает медиафайл в галерее.
 * @param {number} direction - Направление (-1 — назад, 1 — вперед)
 */
function navigateMedia(direction) {
    const newIndex = currentMediaIndex + direction;
    if (newIndex >= 0 && newIndex < mediaElements.length) {
        const el = mediaElements[newIndex];
        currentMediaIndex = newIndex;
        openMediaModal(null, el.dataset.url, el.dataset.fileType, el.dataset.mimeType, el.dataset.filename, newIndex);
    }
}

// === Инициализация медиа-галереи при загрузке страницы.
document.addEventListener('DOMContentLoaded', () => {
    mediaElements = Array.from(document.querySelectorAll('[data-media="true"]'));

    mediaElements.forEach((el, index) => {
        el.addEventListener('click', function (e) {
            const url = el.dataset.url;
            const type = el.dataset.fileType;
            const mimeType = el.dataset.mimeType || 'application/octet-stream';
            const fileName = el.dataset.filename;
            openMediaModal(e, url, type, mimeType, fileName, index);
        });
    });

    // Автоматическое открытие медиа по параметру URL
    const urlParams = new URLSearchParams(window.location.search);
    const autoplay = urlParams.get('autoplay');
    if (autoplay && mediaElements.length > 0) {
        let indexToOpen = autoplay === 'last' ? mediaElements.length - 1 : 0;
        const el = mediaElements[indexToOpen];
        const url = el.dataset.url;
        const type = el.dataset.fileType;
        const mimeType = el.dataset.mimeType || 'application/octet-stream';
        const fileName = el.dataset.filename;
        openMediaModal(null, url, type, mimeType, fileName, indexToOpen);

        // Удаление параметра autoplay из URL без перезагрузки
        const urlObj = new URL(window.location.href);
        urlObj.searchParams.delete('autoplay');
        window.history.replaceState({}, '', urlObj.toString());
    }
});