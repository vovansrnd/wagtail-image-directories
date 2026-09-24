// vsproject/static/js/image_navigator.js (v14.2)
(function() {
  'use strict';
  console.log('image_navigator.js v14.2: script executed');

  // --- УТИЛИТЫ ---
  function onPageEdit() { return /^\/admin\/pages\/\d+\/edit\//.test(location.pathname); }

  function getArticleYear() {
    if (!onPageEdit()) return String(new Date().getFullYear());
    const dateLike = document.querySelector('#id_date, input[name="date"], input[name$="date"]');
    if (dateLike && dateLike.value) {
      const m = dateLike.value.match(/\b(20\d{2}|19\d{2})\b/);
      if (m) return m[1];
    }
    return String(new Date().getFullYear());
  }

  function slugify(str) {
    if (!str) return '';
    return String(str)
      .toLowerCase().trim()
      .replace(/[\s_]+/g, '-')
      .replace(/[.]/g, '-')
      .replace(/[^a-z0-9\-а-яё]/g, '')
      .replace(/-+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  function getArticleSlug() {
    if (!onPageEdit()) return 'misc';
    const slugField = document.querySelector('#id_slug');
    if (slugField && slugField.value) return slugField.value;
    const titleField = document.querySelector('#id_title');
    if (titleField && titleField.value) return slugify(titleField.value) || 'misc';
    return 'misc';
  }

  // Берем директорию из URL, реферера или из формы статьи
  function resolveDefaultDir() {
    // 1) Параметры текущего URL (важно для /admin/images/add?year=...&slug=...)
    try {
      const p = new URLSearchParams(location.search);
      const y = p.get('year'); const s = p.get('slug');
      if (y) return { year: y, slug: s || '' };
    } catch {}

    // 2) Если пришли с filtered-страницы — попробуем реферер
    if (document.referrer) {
      try {
        const u = new URL(document.referrer);
        if (u.pathname.includes('/admin/blog/images/filtered/')) {
          const y = u.searchParams.get('year'); const s = u.searchParams.get('slug');
          if (y) return { year: y, slug: s || '' };
        }
      } catch {}
    }

    // 3) Если редактируем страницу — год статьи + slug
    if (onPageEdit()) {
      return { year: getArticleYear(), slug: getArticleSlug() };
    }

    // 4) Фолбэк
    return { year: String(new Date().getFullYear()), slug: 'misc' };
  }

  // --- ПАТЧ ДЛЯ CHOOSER-МОДАЛКИ ---

  function patchChooserUploadFields(root) {
    const { year, slug } = resolveDefaultDir();

    const yearInput =
      (root || document).querySelector('input[name="image-chooser-upload-year"]') ||
      (root || document).querySelector('#id_image-chooser-upload-year');

    const slugInput =
      (root || document).querySelector('input[name="image-chooser-upload-slug"]') ||
      (root || document).querySelector('#id_image-chooser-upload-slug');

    if (yearInput) {
      if (yearInput.value !== year) {
        yearInput.value = year;
        yearInput.dispatchEvent(new Event('input', { bubbles: true }));
        yearInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }
    if (slugInput) {
      const val = slug || '';
      if (slugInput.value !== val) {
        slugInput.value = val;
        slugInput.dispatchEvent(new Event('input', { bubbles: true }));
        slugInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }

    if (yearInput || slugInput) {
      console.log(`[chooser] set → year=${year} slug=${slug}`);
    }
  }

  function patchFormatLeft(root) {
    const container = (root || document).querySelector('#id_image-chooser-insertion-format') || root || document;
    if (!container) return;
    const leftRadio = container.querySelector('input[type="radio"][name="image-chooser-insertion-format"][value="left"]');
    if (leftRadio && !leftRadio.checked) {
      leftRadio.click();
      console.log('[chooser] format set → left');
    }
  }

  function patchNode(node) {
    if (node.nodeType !== 1) return;

    if (
      node.matches?.('input[name="image-chooser-upload-year"], #id_image-chooser-upload-year') ||
      node.querySelector?.('input[name="image-chooser-upload-year"], #id_image-chooser-upload-year, input[name="image-chooser-upload-slug"], #id_image-chooser-upload-slug')
    ) {
      patchChooserUploadFields(node);
    }

    if (node.matches?.('#id_image-chooser-insertion-format') ||
        node.querySelector?.('#id_image-chooser-insertion-format, input[type="radio"][name="image-chooser-insertion-format"]')) {
      patchFormatLeft(node);
    }
  }

  // --- ПАТЧ ДЛЯ /admin/images/add и /admin/images/multiple ---

  function patchAddImagePage() {
    // Стандартная форма Wagtail: input[name="year"] / #id_year и input[name="slug"] / #id_slug
    const { year, slug } = resolveDefaultDir();

    const yearInput =
      document.querySelector('input[name="year"]') ||
      document.querySelector('#id_year');

    const slugInput =
      document.querySelector('input[name="slug"]') ||
      document.querySelector('#id_slug');

    if (yearInput) {
      if (yearInput.value !== year) {
        yearInput.value = year;
        yearInput.dispatchEvent(new Event('input', { bubbles: true }));
        yearInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }
    if (slugInput) {
      const val = slug || '';
      if (slugInput.value !== val) {
        slugInput.value = val;
        slugInput.dispatchEvent(new Event('input', { bubbles: true }));
        slugInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }

    if (yearInput || slugInput) {
      console.log(`[add-page] set → year=${year} slug=${slug}`);
    }
  }

  function onAddImagesPage() {
    const p = location.pathname;
    return p.startsWith('/admin/images/add') || p.includes('/admin/images/multiple');
  }

  // --- ИНИЦИАЛИЗАЦИЯ ---

  document.addEventListener('DOMContentLoaded', function() {
    console.log('image_navigator.js v14.2: DOMContentLoaded');

    // 0) Если мы на странице добавления изображений — сразу проставим поля
    if (onAddImagesPage()) {
      patchAddImagePage();
    }

    // 1) Первичный проход для уже открытых модалок (на всякий случай)
    patchChooserUploadFields(document.body);
    patchFormatLeft(document.body);

    // 2) Наблюдатель: ловим элементы модалки chooser по мере появления
    const observer = new MutationObserver(mutations => {
      for (const mutation of mutations) {
        for (const node of mutation.addedNodes) {
          patchNode(node);
        }
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    console.log('Universal observer is active.');
  });
})();