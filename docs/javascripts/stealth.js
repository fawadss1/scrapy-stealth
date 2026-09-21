(function () {
  "use strict";

  var REPO = "https://github.com/fawadss1/scrapy-stealth";
  var CHECK_ICON =
    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'/%3E%3C/svg%3E\")";

  function setText(cls, value) {
    document.querySelectorAll("." + cls).forEach(function (el) {
      el.textContent = value;
    });
  }

  function fetchJson(url) {
    return fetch(url).then(function (res) {
      if (!res.ok) throw new Error(res.status);
      return res.json();
    });
  }

  function injectHeader() {
    var inner = document.querySelector(".md-header__inner");
    if (!inner || inner.querySelector(".stealth-header-extras")) return;

    var extras = document.createElement("div");
    extras.className = "stealth-header-extras";
    extras.innerHTML =
      '<div class="stealth-stat-chips">' +
      '<a href="' + REPO + '/stargazers" target="_blank" rel="noopener" class="stat-chip">' +
      '<span class="stat-chip-label"><i class="fa-regular fa-star"></i> Stars</span>' +
      '<span class="stat-chip-value stars-lbl">…</span></a>' +
      '<a href="' + REPO + '/forks" target="_blank" rel="noopener" class="stat-chip">' +
      '<span class="stat-chip-label"><i class="fa-solid fa-code-fork"></i> Forks</span>' +
      '<span class="stat-chip-value forks-lbl">…</span></a>' +
      '<a href="https://pepy.tech/project/scrapy-stealth" target="_blank" rel="noopener" class="stat-chip">' +
      '<span class="stat-chip-label"><i class="fa-solid fa-download"></i> Downloads</span>' +
      '<span class="stat-chip-value downloads-lbl">…</span></a></div>' +
      '<div class="stealth-header-actions">' +
      '<a href="https://pypi.org/project/scrapy-stealth/" target="_blank" rel="noopener" class="btn-primary">' +
      "<span>PyPI Registry</span><i class=\"fa-solid fa-arrow-up-right-from-square\"></i></a></div>";

    inner.insertBefore(
      extras,
      inner.querySelector('[data-md-component="search"]') || inner.lastElementChild
    );
  }

  function setupCopyFeedback() {
    document.body.addEventListener("click", function (e) {
      var btn = e.target.closest('[data-md-type="copy"]');
      if (!btn || btn.classList.contains("stealth-copy-success")) return;

      var title = btn.getAttribute("title") || "Copy to clipboard";
      btn.classList.add("stealth-copy-success");
      btn.setAttribute("title", "Copied");
      btn.style.setProperty("--md-code-copy-icon", CHECK_ICON);

      setTimeout(function () {
        btn.classList.remove("stealth-copy-success");
        btn.setAttribute("title", title);
        btn.style.removeProperty("--md-code-copy-icon");
      }, 1800);
    }, true);
  }

  function loadStats() {
    fetchJson("https://api.github.com/repos/fawadss1/scrapy-stealth")
      .then(function (repo) {
        setText("stars-lbl", repo.stargazers_count ?? "140+");
        setText("forks-lbl", repo.forks_count ?? "—");
      })
      .catch(function () {
        setText("stars-lbl", "140+");
        setText("forks-lbl", "—");
      });

    fetchJson("https://pypi.org/pypi/scrapy-stealth/json")
      .then(function (data) {
        setText("version-lbl", "v" + data.info.version);
      })
      .catch(function () {
        setText("version-lbl", "v0.8.2");
      });

    fetch("https://static.pepy.tech/badge/scrapy-stealth")
      .then(function (r) { return r.ok ? r.text() : Promise.reject(); })
      .then(function (svg) {
        var hits = [...svg.matchAll(/>(\d+(?:\.\d+)?[kKmM])</g)].map(function (m) {
          return m[1].toUpperCase();
        });
        setText("downloads-lbl", hits.at(-1) || "19K");
      })
      .catch(function () {
        setText("downloads-lbl", "19K");
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    injectHeader();
    setupCopyFeedback();
    loadStats();
  });
})();
