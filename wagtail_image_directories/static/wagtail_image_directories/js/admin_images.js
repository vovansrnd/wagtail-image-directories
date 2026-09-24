// blog/static/js/admin_images.js (v6.2 - ИСПРАВЛЕННАЯ ВЕРСИЯ)

console.log("--- admin_images.js ЗАГРУЖЕН (v6.2) ---");

document.addEventListener('DOMContentLoaded', function() {
    // Определяем, на какой мы странице, и запускаем соответствующий код
    const imageListPage = document.getElementById('image-list-container');
    if (imageListPage) {
        console.log("--- Инициализация страницы списка изображений ---");
        initImageListPage(imageListPage);
    }

    const browserPage = document.querySelector('.directory-browser');
    if (browserPage) {
        console.log("--- Инициализация страницы навигатора ---");
        initBrowserPage(browserPage);
    }
});


// ================================================================
// ЛОГИКА ДЛЯ СТРАНИЦЫ СПИСКА ИЗОБРАЖЕНИЙ (filtered_list.html)
// ================================================================
function initImageListPage(container) {
    // 1. Элементы и данные
    const { deleteUrl, moveUrl, moveChooserUrl, uploadUrl, csrfToken } = container.dataset;
    let imageGrid = document.getElementById('image-grid'); // `let` чтобы можно было переопределить
    const toolbar = document.getElementById('actions-toolbar');
    const selectedCountSpan = document.getElementById('selected-count');
    const deleteSelectedBtn = document.getElementById('delete-selected-btn');
    const moveSelectedBtn = document.getElementById('move-selected-btn');
    const modalOverlay = document.getElementById('custom-modal-overlay');
    const modalWrapper = document.getElementById('custom-modal-wrapper');
    const modalBodyEl = document.getElementById('custom-modal-body');
    const uploadZone = document.getElementById('upload-zone');

    let selectedImages = new Set();

    // 2. Функции-помощники
    function showMessage(message, type = 'success') {
        const existingMessages = document.querySelector('.messages');
        if (existingMessages) existingMessages.remove();
        const messageDiv = document.createElement('div');
        messageDiv.className = `messages`;
        messageDiv.innerHTML = `<div class="inner"><ul class="messagelist"><li class="${type}">${message}</li></ul></div>`;
        const header = document.querySelector('header.merged');
        if (header) {
            header.insertAdjacentElement('afterend', messageDiv);
        } else {
            document.body.insertBefore(messageDiv, document.body.firstChild);
        }
        setTimeout(() => messageDiv.remove(), 5000);
    }

    // 3. Управление выделением
    function updateUI() {
        document.querySelectorAll('.image-item').forEach(item => {
            const id = item.dataset.id;
            const checkbox = item.querySelector('.image-checkbox');
            if (id && checkbox) {
                const isSelected = selectedImages.has(id);
                item.classList.toggle('selected', isSelected);
                checkbox.checked = isSelected;
            }
        });
        const count = selectedImages.size;
        if (selectedCountSpan) selectedCountSpan.textContent = count;
        if (toolbar) toolbar.classList.toggle('active', count > 0);
    }

    function toggleImageSelection(imageId) {
        if (selectedImages.has(imageId)) {
            selectedImages.delete(imageId);
        } else {
            selectedImages.add(imageId);
        }
        updateUI();
    }

    function clearSelection() {
        selectedImages.clear();
        updateUI();
    }

    // 4. Логика модального окна и AJAX
    function openMoveModal() {
        if (selectedImages.size === 0) {
            alert('Сначала выберите изображения.');
            return;
        }
        modalOverlay.classList.add('visible');
        modalWrapper.classList.add('visible');
        fetch(moveChooserUrl)
            .then(res => res.json())
            .then(data => {
                modalBodyEl.innerHTML = data.html;
                setTimeout(attachModalListeners, 0);
            })
            .catch(err => {
                modalBodyEl.innerHTML = '<p style="color: var(--w-color-text-error);">Не удалось загрузить содержимое окна.</p>';
            });
    }

    function closeModal() {
        modalOverlay.classList.remove('visible');
        modalWrapper.classList.remove('visible');
        modalBodyEl.innerHTML = '<div class="w-flex w-justify-center w-p-8"><div class="icon icon-spinner w-animate-spin" style="width: 3em; height: 3em;"></div></div>';
    }

    function attachModalListeners() {
        const submitBtn = modalBodyEl.querySelector('#submit-move-btn');
        const cancelBtn = modalBodyEl.querySelector('#cancel-move-btn');
        const yearInput = modalBodyEl.querySelector('#id_new_year');
        const slugInput = modalBodyEl.querySelector('#id_new_slug');
        const destinationSelect = modalBodyEl.querySelector('#id_destination_dir');

        if (!submitBtn || !cancelBtn) { return; }

        destinationSelect.addEventListener('change', (e) => {
            const val = e.target.value;
            if (val) {
                const [year, ...slugParts] = val.split('/');
                yearInput.value = year || '';
                slugInput.value = slugParts.join('/');
            } else {
                yearInput.value = '';
                slugInput.value = '';
            }
        });
        yearInput.addEventListener('input', () => { destinationSelect.value = ''; });
        slugInput.addEventListener('input', () => { destinationSelect.value = ''; });
        cancelBtn.addEventListener('click', closeModal);
        modalOverlay.addEventListener('click', closeModal);
        submitBtn.addEventListener('click', () => {
            const targetYear = yearInput.value;
            if (!targetYear) {
                alert('Корневая директория обязательна');
                return;
            }
            moveImages(Array.from(selectedImages), targetYear, slugInput.value);
            closeModal();
        });
    }

    function moveImages(imageIds, targetYear, targetSlug) {
        const formData = new FormData();
        imageIds.forEach(id => formData.append('ids[]', id));
        formData.append('year', targetYear);
        formData.append('slug', targetSlug);
        fetch(moveUrl, { method: 'POST', body: formData, headers: { 'X-CSRFToken': csrfToken } })
            .then(res => res.json()).then(data => {
                if (data.success) {
                    imageIds.forEach(id => document.querySelector(`.image-item[data-id="${id}"]`)?.remove());
                    clearSelection();
                    if (data.message) showMessage(data.message, 'success');
                } else { throw new Error(data.error); }
            }).catch(err => showMessage(err.message || 'Ошибка перемещения.', 'error'));
    }

    function deleteImages(imageIds) {
        const formData = new FormData();
        imageIds.forEach(id => formData.append('ids[]', id));
        fetch(deleteUrl, { method: 'POST', body: formData, headers: { 'X-CSRFToken': csrfToken } })
            .then(res => res.json()).then(data => {
                if (data.success) {
                    imageIds.forEach(id => document.querySelector(`.image-item[data-id="${id}"]`)?.remove());
                    selectedImages = new Set([...selectedImages].filter(id => !imageIds.includes(id)));
                    updateUI();
                    if (data.message) showMessage(data.message, 'success');
                } else { throw new Error(data.error); }
            }).catch(err => showMessage(err.message || 'Ошибка удаления.', 'error'));
    }

    // 5. Drag & Drop
    function handleFiles(files) {
        const year = container.dataset.year;
        const slug = container.dataset.slug;
        if (!year || typeof slug === 'undefined') {
            alert("Ошибка: не удалось определить текущую директорию для загрузки.");
            return;
        }
        const formData = new FormData();
        formData.append('year', year);
        formData.append('slug', slug);
        let imageCount = 0;
        [...files].forEach(file => {
            if (file.type.startsWith('image/')) {
                formData.append('files[]', file);
                imageCount++;
            }
        });
        if (imageCount === 0) return;
        showMessage(`Загрузка ${imageCount} изображений...`, 'info');
        fetch(uploadUrl, {
            method: 'POST',
            body: formData,
            headers: { 'X-CSRFToken': csrfToken }
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    const errorWindow = window.open('', 'errorWindow');
                    if (errorWindow) errorWindow.document.write(text);
                    throw new Error(`Ошибка сервера: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.cards) {
                // --- ИСПРАВЛЕННАЯ ЛОГИКА СОЗДАНИЯ ГРИДА ---
                if (!imageGrid || !document.body.contains(imageGrid)) {
                    const placeholder = container.querySelector('.help-block.help-info');
                    imageGrid = document.createElement('div');
                    imageGrid.id = 'image-grid';
                    imageGrid.className = 'image-grid';
                    if (placeholder) {
                        placeholder.parentNode.replaceChild(imageGrid, placeholder);
                    } else {
                        const uploadZoneAfter = document.getElementById('upload-zone');
                        if (uploadZoneAfter) {
                            uploadZoneAfter.insertAdjacentElement('afterend', imageGrid);
                        } else {
                            container.appendChild(imageGrid);
                        }
                    }
                }

                data.cards.reverse().forEach(cardHTML => {
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = cardHTML.trim();
                    const newCard = tempDiv.firstChild;
                    imageGrid.insertAdjacentElement('afterbegin', newCard);

                    // --- ИСПРАВЛЕННАЯ ЛОГИКА ПРИВЯЗКИ СОБЫТИЙ ---
                    // Привязываем событие ТОЛЬКО к новому чекбоксу
                    const newCheckbox = newCard.querySelector('.image-checkbox');
                    if (newCheckbox) {
                        newCheckbox.addEventListener('change', handleCheckboxChange);
                    }
                });
                showMessage(`Успешно загружено ${data.cards.length} изображений.`, 'success');
            } else {
                throw new Error(data.error || 'Ошибка сервера при загрузке.');
            }
        })
        .catch(error => {
            showMessage(error.message, 'error');
        });
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // --- 6. ОБРАБОТЧИК ДЛЯ ЧЕКБОКСОВ ---
    function handleCheckboxChange(e) {
        const id = e.target.dataset.id;
        if (id) {
            toggleImageSelection(id);
        }
    }

    // --- 7. ПЕРВИЧНАЯ ПРИВЯЗКА СОБЫТИЙ ---
  function attachInitialEventListeners() {

        const fileInput = document.getElementById('zone-file-input');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files.length > 0) {
                    handleFiles(e.target.files);
                    e.target.value = ''; // сброс
                }
            });
        }

        // Привязываем события к уже существующим на странице чекбоксам
        const checkboxes = document.querySelectorAll('.image-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', handleCheckboxChange);
        });

        // Привязываем события к кнопкам тулбара
        if (deleteSelectedBtn) {
            deleteSelectedBtn.addEventListener('click', () => {
                if (selectedImages.size > 0 && confirm(`Удалить ${selectedImages.size} изображений?`)) {
                    deleteImages(Array.from(selectedImages));
                }
            });
        }
        if (moveSelectedBtn) {
            moveSelectedBtn.addEventListener('click', openMoveModal);
        }

        // Привязываем события Drag & Drop ТОЛЬКО ОДИН РАЗ
        if (uploadZone) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadZone.addEventListener(eventName, preventDefaults, false);
            });
            ['dragenter', 'dragover'].forEach(eventName => {
                uploadZone.addEventListener(eventName, () => uploadZone.classList.add('dragover'), false);
            });
            ['dragleave', 'drop'].forEach(eventName => {
                uploadZone.addEventListener(eventName, () => uploadZone.classList.remove('dragover'), false);
            });
            uploadZone.addEventListener('drop', (e) => handleFiles(e.dataTransfer.files), false);
        }

        // Привязываем делегированный обработчик для кнопок удаления на карточках
        document.body.addEventListener('click', function(e) {
            const deleteBtn = e.target.closest('.delete-single');
            if (deleteBtn) {
                e.preventDefault();
                if (confirm('Удалить это изображение?')) {
                    deleteImages([deleteBtn.dataset.id]);
                }
            }
        });
    }

        // Кнопки "Переименовать/Слить" для текущей директории (если есть)
    const renameDirUrl = container.dataset.renameDirUrl;
    const mergeDirUrl = container.dataset.mergeDirUrl;
    const currentYear = container.dataset.year || '';
    const currentSlug = container.dataset.slug || '';

    function postRenameDir(srcYear, srcSlug, dstYear, dstSlug) {
        const fd = new FormData();
        fd.append('src_year', srcYear);
        fd.append('src_slug', srcSlug);
        fd.append('dst_year', dstYear);
        fd.append('dst_slug', dstSlug);
        fetch(renameDirUrl, { method: 'POST', body: fd, headers: { 'X-CSRFToken': csrfToken } })
            .then(async (r) => {
                const ct = r.headers.get('content-type') || '';
                const data = ct.includes('application/json') ? await r.json() : { success: false, error: await r.text() };
                if (!r.ok || !data.success) throw new Error(data.error || `HTTP ${r.status}`);
                window.location.href = data.redirect_url;
            })
            .catch(err => alert(err.message || 'Ошибка переименования.'));
    }

    function postMergeDir(srcYear, srcSlug, dstYear, dstSlug) {
        const fd = new FormData();
        fd.append('src_year', srcYear);
        fd.append('src_slug', srcSlug);
        fd.append('dst_year', dstYear);
        fd.append('dst_slug', dstSlug);
        fetch(mergeDirUrl, { method: 'POST', body: fd, headers: { 'X-CSRFToken': csrfToken } })
            .then(async (r) => {
                const ct = r.headers.get('content-type') || '';
                const data = ct.includes('application/json') ? await r.json() : { success: false, error: await r.text() };
                if (!r.ok || !data.success) throw new Error(data.error || `HTTP ${r.status}`);
                window.location.href = data.redirect_url;
            })
            .catch(err => alert(err.message || 'Ошибка слияния.'));
    }

    const renameCurrentBtn = document.getElementById('rename-current-dir-btn');
    if (renameCurrentBtn && renameDirUrl) {
        renameCurrentBtn.addEventListener('click', () => {
            const newYear = prompt('Новое имя корневой директории:', currentYear);
            if (newYear === null) return;
            const newSlug = prompt('Новая под-директория (можно оставить пустой):', currentSlug || '');
            if (newSlug === null) return;
            if (!newYear.trim()) { alert('Корневая директория обязательна'); return; }
            postRenameDir(currentYear, currentSlug, newYear.trim(), newSlug.trim());
        });
    }

    const mergeCurrentBtn = document.getElementById('merge-current-dir-btn');
    if (mergeCurrentBtn && mergeDirUrl) {
        mergeCurrentBtn.addEventListener('click', () => {
            const target = prompt('Целевая директория (формат: "корень[/поддиректория]"):', `${currentYear}/`);
            if (target === null) return;
            const parts = target.split('/');
            const dstYear = (parts[0] || '').trim();
            const dstSlug = (parts[1] || '').trim();
            if (!dstYear) { alert('Корневая директория обязательна'); return; }
            if (dstYear === currentYear && (dstSlug || '') === (currentSlug || '')) {
                alert('Нельзя слить директорию саму с собой.');
                return;
            }
            if (!confirm(`Слить "${currentYear}/${currentSlug || '(без-категории)'}" в "${dstYear}/${dstSlug || '(без-категории)'}"?`)) return;
            postMergeDir(currentYear, currentSlug, dstYear, dstSlug);
        });
    }

    // Первичный запуск
    attachInitialEventListeners();
}

// ================================================================
// ЛОГИКА ДЛЯ СТРАНИЦЫ НАВИГАТОРА (directory_browser.html)
// ================================================================
function initBrowserPage(container) {
    const createBtn = document.getElementById('create-dir-btn');
    if (!createBtn) return;

    const renameUrl = container.dataset.renameUrl;
    const mergeUrl = container.dataset.mergeUrl;
    const deleteUrl = container.dataset.deleteUrl;
    const createUrl = container.dataset.createUrl;
    const csrfToken = container.dataset.csrfToken;
    const modalOverlay = document.getElementById('create-dir-overlay');
    const modalWrapper = document.getElementById('create-dir-wrapper');
    const cancelCreateBtn = document.getElementById('cancel-create-btn');
    const submitCreateBtn = document.getElementById('submit-create-btn');

    function closeCreateModal() {
        if (modalOverlay) modalOverlay.style.display = 'none';
        if (modalWrapper) modalWrapper.style.display = 'none';
    }

    createBtn.addEventListener('click', () => {
        if (modalOverlay) modalOverlay.style.display = 'block';
        if (modalWrapper) modalWrapper.style.display = 'block';
    });

    if (cancelCreateBtn) cancelCreateBtn.addEventListener('click', closeCreateModal);
    if (modalOverlay) modalOverlay.addEventListener('click', closeCreateModal);

    if (submitCreateBtn) {
        submitCreateBtn.addEventListener('click', () => {
            const year = document.getElementById('id_create_year').value;
            const slug = document.getElementById('id_create_slug').value;
            const errorEl = document.getElementById('create-error-message');

            if (!year) {
                errorEl.textContent = 'Корневая директория обязательна.';
                errorEl.style.display = 'block';
                return;
            }
            errorEl.style.display = 'none';

            const formData = new FormData();
            formData.append('year', year);
            formData.append('slug', slug);

            fetch(createUrl, { method: 'POST', body: formData, headers: { 'X-CSRFToken': csrfToken } })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = data.redirect_url;
                    } else {
                        throw new Error(data.error);
                    }
                })
                .catch(err => {
                    errorEl.textContent = err.message || 'Ошибка создания директории.';
                    errorEl.style.display = 'block';
                });
        });
    }

    container.addEventListener('click', (e) => {
        const deleteBtn = e.target.closest('.delete-dir-btn');
        if (deleteBtn && !deleteBtn.disabled) {
            e.preventDefault();
            e.stopPropagation();

            const year = deleteBtn.dataset.year;
            const slug = deleteBtn.dataset.slug;

            if (confirm(`Удалить пустую директорию "${year}/${slug || '(без-категории)'}"?`)) {
                const formData = new FormData();
                formData.append('year', year);
                formData.append('slug', slug);

                fetch(deleteUrl, { method: 'POST', body: formData, headers: { 'X-CSRFToken': csrfToken } })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            deleteBtn.closest('.directory-card-wrapper').remove();
                        } else {
                            throw new Error(data.error);
                        }
                    })
                    .catch(err => alert(err.message || 'Ошибка удаления.'));
            }
        }

        const renameBtn = e.target.closest('.rename-dir-btn');
        if (renameBtn) {
            e.preventDefault(); e.stopPropagation();
            const year = renameBtn.dataset.year;
            const slug = renameBtn.dataset.slug || '';
            const newYear = prompt('Новое имя корневой директории:', year);
            if (newYear === null) return;
            const newSlug = prompt('Новая под-директория (можно оставить пустой):', slug);
            if (newSlug === null) return;
            if (!newYear.trim()) { alert('Корневая директория обязательна'); return; }

            const fd = new FormData();
            fd.append('src_year', year);
            fd.append('src_slug', slug);
            fd.append('dst_year', newYear.trim());
            fd.append('dst_slug', (newSlug || '').trim());

            fetch(renameUrl, { method: 'POST', body: fd, headers: { 'X-CSRFToken': csrfToken } })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = data.redirect_url;
                    } else {
                        throw new Error(data.error);
                    }
                })
                .catch(err => alert(err.message || 'Ошибка переименования.'));
        }

        const mergeBtn = e.target.closest('.merge-dir-btn');
        if (mergeBtn) {
            e.preventDefault(); e.stopPropagation();
            const year = mergeBtn.dataset.year;
            const slug = mergeBtn.dataset.slug || '';
            const target = prompt('Целевая директория (формат: "корень[/поддиректория]"):', `${year}/`);
            if (target === null) return;

            const parts = target.split('/');
            const dstYear = (parts[0] || '').trim();
            const dstSlug = (parts[1] || '').trim();

            if (!dstYear) { alert('Корневая директория обязательна'); return; }
            if (dstYear === year && (dstSlug || '') === (slug || '')) {
                alert('Нельзя слить директорию саму с собой.');
                return;
            }

            const fd = new FormData();
            fd.append('src_year', year);
            fd.append('src_slug', slug);
            fd.append('dst_year', dstYear);
            fd.append('dst_slug', dstSlug);

            fetch(mergeUrl, { method: 'POST', body: fd, headers: { 'X-CSRFToken': csrfToken } })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = data.redirect_url;
                    } else {
                        throw new Error(data.error);
                    }
                })
                .catch(err => alert(err.message || 'Ошибка слияния.'));
        }
    });
}
