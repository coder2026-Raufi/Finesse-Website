/* =====================================================================
   FINESSE — PROJECTS PAGE (behaviour)
   Load AFTER i18n.js and main-script.js.

   Part A: the 3D carousel
   1. Keeps a number "cur" = which slide is in front.
   2. render() gives every slide its distance from the front (--off / --abs).
      The CSS turns those two numbers into the 3D position, angle and size.
   3. go / next / prev change "cur" and call render() again.
   4. Autoplay, swipe, keyboard, mouse tilt, dots and RTL are small add-ons.

   Part B: the project cards
   - filter buttons show / hide cards by category
   - on phones (no hover) a tap opens and closes a card's details
   All text is translated by i18n.js (keys start with pc. and pj.).
   ===================================================================== */
(function () {
  "use strict";

  function isRTL() {
    return document.documentElement.dir === "rtl";
  }
  /* translated text from i18n.js (it returns null for English, so we use the fallback) */
  function t(key, fallback) {
    return (window.FinesseI18n && window.FinesseI18n.t(key)) || fallback;
  }

  function Carousel(root) {
    var slides = [].slice.call(root.querySelectorAll(".pc-slide"));
    var n = slides.length;
    if (!n) return;
    var track = root.querySelector(".pc-track");
    var stage = root.querySelector(".pc-stage");
    var dotsBox = root.querySelector(".pc-dots");
    var bar = root.querySelector(".pc-progress i");
    var count = root.querySelector(".pc-count b");
    var toggle = root.querySelector(".pc-toggle");
    var bgs = root.querySelectorAll(".pc-bg i");
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var TIME = 6000; /* milliseconds each slide stays in front */
    var cur = 0;
    var userPaused = false;
    var hovering = false;
    var visible = true;
    var dragged = false;
    var startX = null;
    var bgFlip = 0;

    root.style.setProperty("--pc-time", TIME + "ms");

    /* dots */
    slides.forEach(function (s, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "pc-dot";
      b.addEventListener("click", function () {
        go(i);
      });
      dotsBox.appendChild(b);
    });
    var dots = [].slice.call(dotsBox.children);

    function pad(v) {
      return (v < 10 ? "0" : "") + v;
    }

    /* put every slide in the right place */
    function render() {
      var half = Math.floor(n / 2);
      var goEl = root.querySelector("[data-pc-go]");
      var goText = goEl ? goEl.textContent : "Go to project";
      track.style.setProperty("--sign", isRTL() ? -1 : 1);
      slides.forEach(function (s, i) {
        var off = ((i - cur + n + half) % n) - half; /* shortest way around the circle */
        var abs = Math.abs(off);
        var active = off === 0;
        s.style.setProperty("--off", off);
        s.style.setProperty("--abs", abs);
        s.classList.toggle("is-active", active);
        s.classList.toggle("is-far", abs > 2);
        s.setAttribute("role", "group");
        s.setAttribute("aria-roledescription", "slide");
        s.setAttribute("aria-label", i + 1 + " / " + n);
        s.setAttribute("aria-hidden", active ? "false" : "true");
        var link = s.querySelector("a");
        if (link) link.tabIndex = active ? 0 : -1;
      });
      dots.forEach(function (d, i) {
        d.classList.toggle("on", i === cur);
        d.setAttribute("aria-label", goText + " " + (i + 1));
        if (i === cur) d.setAttribute("aria-current", "true");
        else d.removeAttribute("aria-current");
      });
      count.textContent = pad(cur + 1);
      track.setAttribute("aria-live", reduce || userPaused ? "polite" : "off");
    }

    /* blurred photo behind the section changes with the slide */
    function updateBackground() {
      var img = slides[cur].querySelector("img");
      if (!img || bgs.length < 2) return;
      bgFlip = 1 - bgFlip;
      bgs[bgFlip].style.backgroundImage = 'url("' + (img.currentSrc || img.src) + '")';
      bgs[bgFlip].classList.add("on");
      bgs[1 - bgFlip].classList.remove("on");
    }

    function restartBar() {
      bar.style.animation = "none";
      void bar.offsetWidth; /* forces the browser to forget the old animation */
      bar.style.animation = "";
    }

    function go(i) {
      cur = (i + n) % n;
      render();
      updateBackground();
      restartBar();
    }
    function next() {
      go(cur + 1);
    }
    function prev() {
      go(cur - 1);
    }

    /* autoplay state */
    function sync() {
      root.classList.toggle("is-playing", !reduce && !userPaused);
      root.classList.toggle("is-paused", hovering || !visible || document.hidden);
      var icon = toggle.querySelector("i");
      icon.className = userPaused ? "fa-solid fa-play" : "fa-solid fa-pause";
      toggle.setAttribute("aria-pressed", userPaused ? "true" : "false");
      toggle.setAttribute("aria-label", t(userPaused ? "pc.play" : "pc.pause", userPaused ? "Play slideshow" : "Pause slideshow"));
      track.setAttribute("aria-live", reduce || userPaused ? "polite" : "off");
    }
    bar.addEventListener("animationend", function () {
      if (root.classList.contains("is-playing")) next();
    });
    toggle.addEventListener("click", function () {
      userPaused = !userPaused;
      sync();
      if (!userPaused) restartBar();
    });
    stage.addEventListener("pointerenter", function (e) {
      if (e.pointerType === "mouse") {
        hovering = true;
        sync();
      }
    });
    stage.addEventListener("pointerleave", function () {
      hovering = false;
      sync();
      resetTilt();
    });
    root.addEventListener("focusin", function () {
      hovering = true;
      sync();
    });
    root.addEventListener("focusout", function () {
      hovering = false;
      sync();
    });
    document.addEventListener("visibilitychange", sync);
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(
        function (entries) {
          visible = entries[0].isIntersecting;
          sync();
        },
        { threshold: 0.25 },
      ).observe(root);
    }

    /* buttons */
    root.querySelector(".pc-prev").addEventListener("click", prev);
    root.querySelector(".pc-next").addEventListener("click", next);

    /* click a side slide to bring it to the front */
    track.addEventListener("click", function (e) {
      var s = e.target.closest(".pc-slide");
      if (!s) return;
      if (dragged) {
        dragged = false;
        e.preventDefault();
        return;
      }
      var i = slides.indexOf(s);
      if (i !== cur) {
        e.preventDefault();
        go(i);
      }
    });

    /* swipe / drag */
    stage.addEventListener("pointerdown", function (e) {
      startX = e.clientX;
      dragged = false;
    });
    stage.addEventListener("pointerup", function (e) {
      if (startX === null) return;
      var dx = e.clientX - startX;
      startX = null;
      if (Math.abs(dx) > 50) {
        dragged = true;
        dx * (isRTL() ? -1 : 1) < 0 ? next() : prev();
      }
    });
    stage.addEventListener("pointercancel", function () {
      startX = null;
    });

    /* keyboard */
    stage.addEventListener("keydown", function (e) {
      var fwd = isRTL() ? "ArrowLeft" : "ArrowRight";
      var back = isRTL() ? "ArrowRight" : "ArrowLeft";
      if (e.key === fwd) {
        e.preventDefault();
        next();
      } else if (e.key === back) {
        e.preventDefault();
        prev();
      } else if (e.key === "Home") {
        e.preventDefault();
        go(0);
      } else if (e.key === "End") {
        e.preventDefault();
        go(n - 1);
      }
    });

    /* 3D tilt of the front card that follows the mouse */
    var tiltCard = null;
    function resetTilt() {
      if (!tiltCard) return;
      tiltCard.classList.remove("is-tilting");
      tiltCard.style.setProperty("--rx", "0deg");
      tiltCard.style.setProperty("--ry", "0deg");
      tiltCard = null;
    }
    if (!reduce) {
      track.addEventListener("pointermove", function (e) {
        if (e.pointerType !== "mouse") return;
        var s = e.target.closest(".pc-slide");
        if (!s || !s.classList.contains("is-active")) return resetTilt();
        var card = s.querySelector(".pc-card");
        var r = card.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width;
        var y = (e.clientY - r.top) / r.height;
        tiltCard = card;
        card.classList.add("is-tilting");
        card.style.setProperty("--ry", (x - 0.5) * 14 + "deg");
        card.style.setProperty("--rx", (0.5 - y) * 10 + "deg");
        card.style.setProperty("--mx", x * 100 + "%");
        card.style.setProperty("--my", y * 100 + "%");
      });
    }

    /* when the visitor changes language */
    document.addEventListener("finesse:lang", function () {
      render();
      sync();
    });

    render();
    updateBackground();
    sync();
  }

  /* ---------- Part B: project cards ---------- */
  function initGrid() {
    var grid = document.querySelector(".pj-grid");
    if (!grid) return;
    var cards = [].slice.call(grid.querySelectorAll(".pj-card"));
    var chips = [].slice.call(document.querySelectorAll(".pj-chip"));
    var canHover = window.matchMedia("(hover: hover)").matches;

    function filter(cat) {
      chips.forEach(function (c) {
        var on = c.getAttribute("data-filter") === cat;
        c.classList.toggle("is-on", on);
        c.setAttribute("aria-pressed", on ? "true" : "false");
      });
      cards.forEach(function (card) {
        var show = cat === "all" || card.getAttribute("data-cat") === cat;
        card.hidden = !show;
        card.classList.remove("is-open");
        if (show) {
          card.style.setProperty("--d", "0s"); /* no stagger delay when filtering */
          card.classList.add("in"); /* hidden cards never got the scroll-reveal class */
          card.classList.remove("pj-pop");
          void card.offsetWidth; /* restart the pop-in animation */
          card.classList.add("pj-pop");
        }
      });
    }
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        filter(chip.getAttribute("data-filter"));
      });
    });

    /* the carousel buttons link to a card: make sure that card is not filtered out */
    document.addEventListener("click", function (e) {
      var a = e.target.closest('a[href^="#pj-"]');
      if (a) filter("all");
    });

    /* phones: first tap opens the details, tapping again (or another card) closes */
    if (!canHover) {
      grid.addEventListener("click", function (e) {
        var card = e.target.closest(".pj-card");
        if (!card) return;
        var open = card.classList.contains("is-open");
        if (!open) {
          e.preventDefault();
          cards.forEach(function (c) {
            c.classList.remove("is-open");
          });
          card.classList.add("is-open");
        } else if (!e.target.closest("a")) {
          card.classList.remove("is-open");
        }
      });
    }
  }

  /* ---------- Part C: load the projects from the backend ----------
     The Finesse dashboard stores the projects. This asks the API for them and builds the
     carousel slides and the cards. If the server cannot be reached, the hand-written
     cards that are already in the HTML stay (so the page never breaks). */
  var CAT_KEY = { research: "pc.s1.cat", monitoring: "pc.s2.cat", capacity: "pc.s3.cat", consulting: "pc.s4.cat", strategy: "pc.s5.cat" };
  var CAT_EN = { research: "Research", monitoring: "Monitoring & Evaluation", capacity: "Capacity Development", consulting: "Management Consulting", strategy: "Strategy" };
  var CLIENT_KEY = { dev: "pj.c.dev", ngo: "pj.c.ngo", gov: "pj.c.gov", biz: "pj.c.biz" };
  var CLIENT_EN = { dev: "Development partner", ngo: "NGO", gov: "Government", biz: "Private sector" };
  var FALLBACK_IMG = "../IMAGES/web/build.jpg";
  var dyn = []; /* [{el, fn}] text that must change when the language changes */

  function lang() {
    return (window.FinesseI18n && window.FinesseI18n.lang) || "en";
  }
  function digits(str, l) {
    var set = l === "ar" ? "٠١٢٣٤٥٦٧٨٩" : l === "fa" || l === "ps" ? "۰۱۲۳۴۵۶۷۸۹" : null;
    return set ? String(str).replace(/\d/g, function (d) { return set[d]; }) : String(str);
  }
  function monthsText(n, l) {
    var w;
    if (l === "fa") w = "ماه";
    else if (l === "ps") w = "میاشتې";
    else if (l === "ar") w = n === 1 ? "شهر" : n === 2 ? "شهران" : n <= 10 ? "أشهر" : "شهرًا";
    else return n + (n === 1 ? " month" : " months");
    return digits(n, l) + " " + w;
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }
  function icon(cls) {
    var i = el("i", cls);
    i.setAttribute("aria-hidden", "true");
    return i;
  }
  /* an element whose text depends on the language */
  function dynEl(tag, cls, fn) {
    var e = el(tag, cls, fn(lang()));
    dyn.push({ el: e, fn: fn });
    return e;
  }
  function catText(p) {
    return function (l) {
      return l === "en" ? CAT_EN[p.category] : t(CAT_KEY[p.category], CAT_EN[p.category]);
    };
  }
  function pick(map) {
    return function (l) { return map[l] || map.en || ""; };
  }
  function labeled(iconCls, key, enLabel, valueNode) {
    var li = el("li");
    li.appendChild(icon(iconCls));
    var sm = el("small", "", enLabel);
    sm.setAttribute("data-i18n", key);
    li.appendChild(sm);
    li.appendChild(valueNode);
    return li;
  }
  function two(n) {
    return n < 10 ? "0" + n : String(n);
  }
  function viewLink(cls, id) {
    var a = el("a", cls);
    a.href = "#pj-" + id;
    var sp = el("span", "", "View project");
    sp.setAttribute("data-i18n", "pc.view");
    a.appendChild(sp);
    a.appendChild(icon("fa-solid fa-arrow-right-long"));
    return a;
  }

  function buildSlide(p, i) {
    var li = el("li", "pc-slide");
    var card = el("article", "pc-card");
    var media = el("div", "pc-media");
    var img = el("img");
    img.src = p.image || FALLBACK_IMG;
    img.alt = "";
    img.loading = "lazy";
    img.draggable = false;
    media.appendChild(img);
    var idx = el("span", "pc-index", two(i + 1));
    idx.setAttribute("aria-hidden", "true");
    var info = el("div", "pc-info");
    info.appendChild(dynEl("span", "pc-cat", catText(p)));
    info.appendChild(dynEl("h2", "pc-name", pick(p.title)));
    info.appendChild(dynEl("p", "pc-text", pick(p.description)));
    info.appendChild(viewLink("pc-btn", p.id));
    card.appendChild(media);
    card.appendChild(idx);
    card.appendChild(info);
    li.appendChild(card);
    return li;
  }

  function buildCard(p, i) {
    var card = el("article", "pj-card reveal in");
    card.id = "pj-" + p.id;
    card.setAttribute("data-cat", p.category);
    var media = el("div", "pj-media");
    var img = el("img");
    img.src = p.image || FALLBACK_IMG;
    img.alt = "";
    img.loading = "lazy";
    img.draggable = false;
    media.appendChild(img);
    var no = el("span", "pj-no", two(i + 1));
    no.setAttribute("aria-hidden", "true");
    var info = el("div", "pj-info");
    info.appendChild(dynEl("span", "pj-cat", catText(p)));
    info.appendChild(dynEl("h3", "pj-name", pick(p.title)));
    var more = el("div", "pj-more");
    var inner = el("div");
    inner.appendChild(dynEl("p", "pj-desc", pick(p.description)));
    var meta = el("ul", "pj-meta");
    meta.appendChild(labeled("fa-regular fa-calendar", "pj.year", "Year", dynEl("b", "", function (l) { return digits(p.year, l); })));
    if (p.duration_months)
      meta.appendChild(labeled("fa-regular fa-clock", "pj.duration", "Duration", dynEl("b", "", function (l) { return monthsText(p.duration_months, l); })));
    if (p.client && CLIENT_KEY[p.client])
      meta.appendChild(labeled("fa-regular fa-building", "pj.client", "Client", dynEl("b", "", function (l) { return l === "en" ? CLIENT_EN[p.client] : t(CLIENT_KEY[p.client], CLIENT_EN[p.client]); })));
    inner.appendChild(meta);
    inner.appendChild(viewLink("pj-go", p.id));
    more.appendChild(inner);
    info.appendChild(more);
    card.appendChild(media);
    card.appendChild(no);
    card.appendChild(info);
    return card;
  }

  function retext() {
    var l = lang();
    dyn.forEach(function (d) { d.el.textContent = d.fn(l); });
  }
  document.addEventListener("finesse:lang", retext);

  function render(projects) {
    /* build everything first; touch the page only when nothing failed */
    var slides = projects.map(buildSlide);
    var cards = projects.map(buildCard);
    var track = document.querySelector(".pc-track");
    var grid = document.querySelector(".pj-grid");
    var carousel = document.querySelector(".pc");
    var empty = null;
    if (!projects.length) {
      empty = el("p", "pj-lead", "New projects will be published here soon.");
      empty.setAttribute("data-i18n", "pj.empty");
    }
    if (track) { track.textContent = ""; slides.forEach(function (s) { track.appendChild(s); }); }
    if (grid) { grid.textContent = ""; cards.forEach(function (c) { grid.appendChild(c); }); if (empty) grid.appendChild(empty); }
    if (carousel && !projects.length) carousel.style.display = "none";
    /* the "01 / 05" counter: the total was written by hand in the HTML */
    var cnt = document.querySelector(".pc-count");
    if (cnt && cnt.lastChild && cnt.lastChild.nodeType === 3) cnt.lastChild.textContent = " / " + two(projects.length);
    /* hide filter buttons for categories that have no project */
    var have = {};
    projects.forEach(function (p) { have[p.category] = true; });
    document.querySelectorAll(".pj-chip").forEach(function (c) {
      var f = c.getAttribute("data-filter");
      c.hidden = f !== "all" && !have[f];
    });
  }

  function start() {
    document.querySelectorAll(".pc").forEach(Carousel);
    initGrid();
    document.documentElement.classList.remove("pj-wait");
  }

  var API_URL = (window.FINESSE_API_BASE || "").replace(/\/$/, "") + "/api/projects/";
  var ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
  var timer = setTimeout(function () { if (ctrl) ctrl.abort(); }, 5000);
  fetch(API_URL, ctrl ? { signal: ctrl.signal } : {})
    .then(function (r) {
      if (!r.ok) throw new Error("bad status");
      return r.json();
    })
    .then(function (data) {
      clearTimeout(timer);
      if (!data || !Array.isArray(data.projects)) throw new Error("bad data");
      render(data.projects);
      /* translate the fixed labels (Year, Duration, View project ...) in the new elements */
      if (window.FinesseI18n) window.FinesseI18n.setLang(window.FinesseI18n.lang);
      start();
    })
    .catch(function () {
      clearTimeout(timer);
      start(); /* server unreachable: keep the static cards */
    });
})();
