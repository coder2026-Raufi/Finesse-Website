/* =====================================================================
   FINESSE — MAIN SCRIPT
   1. Navbar (close on click, shadow on scroll)   5. 3D tilt for every card
   2. Tooltips (Bootstrap + jQuery)               6. Hero 3D scene
   3. Dark / light theme                          7. Language menu
   4. Reveal on scroll + progress + back-to-top   8. Contact form
   ===================================================================== */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var canHover = window.matchMedia("(hover: hover)").matches;

  /* ---------- 1. NAVBAR ---------- */
  $(".navbar .nav-link").on("click", function () {
    $("#mynavbar").collapse("hide");
  });
  var nav = document.getElementById("siteNav");

  /* ---------- 2. TOOLTIPS ---------- */
  $(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();
  });

  /* ---------- 3. THEME ---------- */
  var themeSwitch = document.getElementById("themeSwitch");
  function applyTheme(theme) {
    document.body.setAttribute("data-theme", theme);
    if (themeSwitch) themeSwitch.checked = theme === "dark";
    try {
      localStorage.setItem("websiteTheme", theme);
    } catch (e) {}
  }
  var savedTheme = "light";
  try {
    savedTheme = localStorage.getItem("websiteTheme") || "light";
  } catch (e) {}
  applyTheme(savedTheme);
  if (themeSwitch) {
    themeSwitch.addEventListener("change", function () {
      applyTheme(themeSwitch.checked ? "dark" : "light");
    });
  }

  /* ---------- 4. REVEAL + PROGRESS + BACK TO TOP ---------- */
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    /* give siblings a small stagger so cards appear one after another */
    revealEls.forEach(function (el) {
      var siblings = el.parentElement ? el.parentElement.querySelectorAll(":scope > .reveal") : [];
      var i = Array.prototype.indexOf.call(siblings, el);
      if (i > 0) el.style.setProperty("--d", Math.min(i, 6) * 0.09 + "s");
    });
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach(function (el) {
      io.observe(el);
    });
  } else {
    revealEls.forEach(function (el) {
      el.classList.add("in");
    });
  }

  var bar = document.getElementById("scrollProgress");
  var toTop = document.getElementById("toTop");
  function onScroll() {
    var y = window.scrollY || document.documentElement.scrollTop;
    var max = document.documentElement.scrollHeight - window.innerHeight;
    if (bar) bar.style.setProperty("--p", max > 0 ? (y / max).toFixed(4) : 0);
    if (nav) nav.classList.toggle("scrolled", y > 20);
    if (toTop) toTop.classList.toggle("show", y > 500);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  if (toTop) {
    toTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
    });
  }

  /* ---------- 5. 3D TILT (every element with data-tilt) ----------
     The pointer position inside the card is turned into two angles.
     CSS reads --rx / --ry and rotates the card; --mx / --my move the light. */
  function initTilt() {
    if (reduceMotion) return;
    document.querySelectorAll("[data-tilt]").forEach(function (el) {
      var max = parseFloat(el.getAttribute("data-tilt-max")) || 9;
      var frame = null;

      function update(e) {
        var r = el.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width;
        var py = (e.clientY - r.top) / r.height;
        px = Math.max(0, Math.min(1, px));
        py = Math.max(0, Math.min(1, py));
        if (frame) cancelAnimationFrame(frame);
        frame = requestAnimationFrame(function () {
          el.style.setProperty("--ry", ((px - 0.5) * 2 * max).toFixed(2) + "deg");
          el.style.setProperty("--rx", (-(py - 0.5) * 2 * max).toFixed(2) + "deg");
          el.style.setProperty("--mx", (px * 100).toFixed(1) + "%");
          el.style.setProperty("--my", (py * 100).toFixed(1) + "%");
        });
      }
      function reset() {
        if (frame) cancelAnimationFrame(frame);
        el.classList.remove("is-tilting");
        el.style.setProperty("--rx", "0deg");
        el.style.setProperty("--ry", "0deg");
      }
      el.addEventListener("pointerenter", function (e) {
        el.classList.add("is-tilting");
        update(e);
      });
      el.addEventListener("pointermove", update);
      el.addEventListener("pointerleave", reset);
      el.addEventListener("pointercancel", reset);
    });
  }
  initTilt();

  /* ---------- 6. HERO 3D SCENE ---------- */
  var scene = document.querySelector(".stage-scene");
  var hero = document.querySelector(".banner-style");
  if (scene && hero && !reduceMotion) {
    var pointerIn = false;
    var tx = 0,
      ty = 0,
      cx = 0,
      cy = 0;
    hero.addEventListener("pointermove", function (e) {
      var r = hero.getBoundingClientRect();
      tx = ((e.clientX - r.left) / r.width - 0.5) * 2;
      ty = ((e.clientY - r.top) / r.height - 0.5) * 2;
      pointerIn = true;
    });
    hero.addEventListener("pointerleave", function () {
      pointerIn = false;
    });
    var t0 = performance.now();
    (function loop(now) {
      if (!pointerIn) {
        var t = (now - t0) / 1000;
        tx = Math.sin(t * 0.6) * 0.7; /* gentle idle sway */
        ty = Math.cos(t * 0.45) * 0.5;
      }
      cx += (tx - cx) * 0.06;
      cy += (ty - cy) * 0.06;
      scene.style.setProperty("--ry", (cx * 16).toFixed(2) + "deg");
      scene.style.setProperty("--rx", (-cy * 10).toFixed(2) + "deg");
      requestAnimationFrame(loop);
    })(t0);
  }

  /* ---------- 7. LANGUAGE MENU ---------- */
  var sw = document.getElementById("langSwitch");
  var btn = document.getElementById("langBtn");
  if (sw && btn) {
    function closeMenu() {
      sw.classList.remove("open");
      btn.setAttribute("aria-expanded", "false");
    }
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = sw.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    sw.querySelectorAll(".lang-option").forEach(function (opt) {
      opt.addEventListener("click", function () {
        window.FinesseI18n.setLang(opt.getAttribute("data-lang"));
        closeMenu();
        btn.focus();
      });
    });
    document.addEventListener("click", function (e) {
      if (!sw.contains(e.target)) closeMenu();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeMenu();
    });
  }

  /* ---------- 8. CONTACT FORM ----------
     Sends the message to the Finesse backend (POST /api/contact/).
     The server validates again, saves the message and emails the team.
     Where the API lives is set in JS/config.js. */
  function tx(key, fallback) {
    return (window.FinesseI18n && window.FinesseI18n.t(key)) || fallback;
  }

  var form = document.getElementById("contactForm");
  if (form) {
    var statusBox = document.getElementById("formStatus");
    var sendBtn = form.querySelector(".send-btn");
    var sendLabel = sendBtn.querySelector("span");
    var API_URL = (window.FINESSE_API_BASE || "").replace(/\/$/, "") + "/api/contact/";
    /* server field name -> input id on this page */
    var FIELD_IDS = { name: "username", email: "useremail", subject: "subject", message: "message" };

    function showStatus(kind, text) {
      statusBox.hidden = false;
      statusBox.className = "form-status " + kind;
      statusBox.textContent = text; /* textContent (never innerHTML): safe */
    }

    function setSending(on) {
      sendBtn.disabled = on;
      sendLabel.removeAttribute("data-i18n");
      sendLabel.textContent = on ? tx("form.sending", "Sending…") : tx("form.send", "Send Message");
      if (!on) sendLabel.setAttribute("data-i18n", "form.send");
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      statusBox.hidden = true;
      form.classList.add("was-validated");
      if (!form.checkValidity()) return;

      var payload = {
        name: form.elements["username"].value.trim(),
        email: form.elements["useremail"].value.trim(),
        subject: form.elements["subject"].value,
        message: form.elements["message"].value.trim(),
        website: form.elements["website"].value /* honeypot, must stay empty */,
        language: (window.FinesseI18n && window.FinesseI18n.lang) || "en",
      };

      setSending(true);
      fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then(function (res) {
          return res
            .json()
            .catch(function () {
              return {};
            })
            .then(function (data) {
              return { status: res.status, data: data };
            });
        })
        .then(function (r) {
          if (r.status === 201 && r.data.ok) {
            form.reset();
            form.classList.remove("was-validated");
            showStatus("ok", tx("form.ok", "Thank you! Your message was sent. Our team will get back to you soon."));
          } else if (r.status === 429) {
            showStatus("err", tx("form.err.rate", "You have sent several messages already. Please try again later."));
          } else if (r.status === 400 && r.data.fields) {
            Object.keys(r.data.fields).forEach(function (f) {
              var el = document.getElementById(FIELD_IDS[f]);
              if (el) el.classList.add("is-invalid");
            });
            showStatus("err", tx("form.invalid", "Please fill in this field."));
          } else {
            showStatus("err", tx("form.err.generic", "Your message could not be sent. Please try again."));
          }
        })
        .catch(function () {
          /* server unreachable: tell the visitor the direct email address */
          showStatus(
            "err",
            tx("form.err.net", "We could not reach the server. Please email us directly at finesse.researchmc@gmail.com.")
          );
        })
        .then(function () {
          setSending(false);
        });
    });
  }

  /* ---------- footer year ---------- */
  var yr = document.getElementById("year");
  if (yr) yr.textContent = new Date().getFullYear();
})();
