// static/js/directory_search.js
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        const container = document.getElementById('directory-browser-container');
        const searchInput = document.getElementById('directory-search-input');
        const resultsBox = document.getElementById('directory-search-results');

        if (!container || !searchInput || !resultsBox) {
            console.warn('[directory-search] элементы не найдены на странице');
            return;
        }

        const searchUrl = container.dataset.searchUrl;
        let debounceTimer;
        let currentIndex = -1;

        searchInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            const q = this.value.trim();

            if (q.length < 2) {
                resultsBox.style.display = 'none';
                resultsBox.innerHTML = '';
                return;
            }

            debounceTimer = setTimeout(() => {
                fetch(`${searchUrl}?q=${encodeURIComponent(q)}`)
                    .then(r => r.json())
                    .then(data => renderResults(data.results, q))
                    .catch(err => {
                        console.error('[directory-search] ошибка запроса', err);
                        resultsBox.innerHTML = '<div class="search-no-results">Ошибка поиска</div>';
                        resultsBox.style.display = 'block';
                    });
            }, 300);
        });

        function escapeHtml(str) {
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        }

        function renderResults(results, query) {
            currentIndex = -1;
            if (!results.length) {
                resultsBox.innerHTML = '<div class="search-no-results">Ничего не найдено</div>';
                resultsBox.style.display = 'block';
                return;
            }

            // Регулярка для поиска без учета регистра
            const regex = new RegExp(`(${query})`, 'gi');

            resultsBox.innerHTML = results.map((r, i) => {
                // Сначала экранируем HTML, чтобы ничего не сломать
                let safeLabel = escapeHtml(r.label);
                // Затем оборачиваем совпадение в тег <mark>
                let highlightedLabel = safeLabel.replace(regex, '<mark class="search-highlight">$1</mark>');

                return `<a href="${r.url}" class="search-result-item" data-index="${i}">${highlightedLabel}</a>`;
            }).join('');

            resultsBox.style.display = 'block';
        }

        searchInput.addEventListener('keydown', function (e) {
            const items = resultsBox.querySelectorAll('.search-result-item');
            if (!items.length) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                currentIndex = Math.min(currentIndex + 1, items.length - 1);
                updateActive(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                currentIndex = Math.max(currentIndex - 1, 0);
                updateActive(items);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                const target = currentIndex >= 0 ? items[currentIndex] : items[0];
                if (target) window.location.href = target.href;
            } else if (e.key === 'Escape') {
                resultsBox.style.display = 'none';
                searchInput.blur();
            }
        });

        function updateActive(items) {
            items.forEach((item, i) => item.classList.toggle('active', i === currentIndex));
            if (currentIndex >= 0) items[currentIndex].scrollIntoView({ block: 'nearest' });
        }

      document.addEventListener('click', function (e) {
            if (e.key === '/' && document.activeElement !== searchInput) {
                e.preventDefault();
                searchInput.focus();
            }
            if (!e.target.closest('.directory-search-wrapper')) {
                resultsBox.style.display = 'none';
            }
        });

        console.log('[directory-search] инициализирован');
    });
})();
