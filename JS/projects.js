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

  document.querySelectorAll(".pc").forEach(Carousel);
  initGrid();
})();
