document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  const loader = document.getElementById("loader");
  const pageShell = document.getElementById("pageShell");
  const progressCircle = document.getElementById("progressCircle");
  const progressValue = document.getElementById("progressValue");
  const loaderStatus = document.getElementById("loaderStatus");
  const loaderCue = document.getElementById("loaderCue");
  const yearNode = document.getElementById("year");
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (yearNode) {
    yearNode.textContent = String(new Date().getFullYear());
  }

  initRevealAnimations(prefersReducedMotion);
  initParallax(prefersReducedMotion);
  initParticles(prefersReducedMotion);
  initSplitText(prefersReducedMotion);
  initScrollTextParallax(prefersReducedMotion);
  initCounterAnimations();
  initMobileNav();
  initHeaderScroll();

  runCinematicLoading({
    loader,
    pageShell,
    body,
    progressCircle,
    progressValue,
    loaderStatus,
    loaderCue,
    prefersReducedMotion
  });
});

/* ═══════════════════════════════════════════════════
   CINEMATIC MULTI-PHASE LOADING SEQUENCE
   ═══════════════════════════════════════════════════ */
function runCinematicLoading({
  loader, pageShell, body,
  progressCircle, progressValue, loaderStatus, loaderCue,
  prefersReducedMotion
}) {
  if (!loader || !pageShell) {
    body.classList.remove("loading");
    if (pageShell) pageShell.classList.add("ready");
    return;
  }

  if (prefersReducedMotion) {
    /* Instant reveal */
    loader.classList.add("fade-out");
    body.classList.remove("loading");
    pageShell.classList.add("ready");
    return;
  }

  const phases = [
    document.getElementById("loaderPhase1"),
    document.getElementById("loaderPhase2"),
    document.getElementById("loaderPhase3"),
    document.getElementById("loaderPhase4")
  ];

  const statusMessages = [
    "Initializing Elite Access",
    "Preparing Luxury Environment",
    "Configuring Concierge Systems",
    "Finalizing Premium Experience"
  ];

  const circumference = 2 * Math.PI * 54; // r=54 from SVG
  if (progressCircle) {
    progressCircle.style.strokeDasharray = circumference;
    progressCircle.style.strokeDashoffset = circumference;
  }

  function activatePhase(index) {
    phases.forEach((phase, i) => {
      if (!phase) return;
      if (i === index) {
        phase.classList.add("active");
      } else {
        phase.classList.remove("active");
      }
    });
  }

  /* Phase 1: EST. 2026 reveal (0–1000ms) */
  setTimeout(() => activatePhase(0), 100);

  /* Phase 2: Brand name (1000–2200ms) */
  setTimeout(() => activatePhase(1), 1100);

  /* Phase 3: Tagline + divider (2200–3200ms) */
  setTimeout(() => activatePhase(2), 2300);

  /* Phase 4: Progress ring (3200ms+) */
  setTimeout(() => {
    activatePhase(3);
    startProgressAnimation();
  }, 3400);

  function startProgressAnimation() {
    const totalDuration = 2600;
    const intervalMs = 32;
    const totalSteps = Math.max(1, Math.ceil(totalDuration / intervalMs));
    let step = 0;
    let statusIndex = 0;

    const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

    const timer = setInterval(() => {
      step += 1;
      const raw = Math.min(100, easeOutCubic(step / totalSteps) * 100);
      const rounded = Math.round(raw);

      if (progressValue) progressValue.textContent = rounded;
      if (progressCircle) {
        const offset = circumference - (raw / 100) * circumference;
        progressCircle.style.strokeDashoffset = offset;
      }

      /* Rotate status messages */
      const newStatusIdx = Math.min(statusMessages.length - 1, Math.floor(raw / 28));
      if (newStatusIdx !== statusIndex && loaderStatus) {
        statusIndex = newStatusIdx;
        loaderStatus.style.opacity = "0";
        setTimeout(() => {
          loaderStatus.textContent = statusMessages[statusIndex];
          loaderStatus.style.opacity = "1";
        }, 200);
      }

      if (step >= totalSteps) {
        clearInterval(timer);

        /* Show cue */
        if (loaderCue) loaderCue.classList.add("visible");

        /* Final reveal */
        setTimeout(() => {
          loader.classList.add("fade-out");
          setTimeout(() => {
            body.classList.remove("loading");
            pageShell.classList.add("ready");
          }, 900);
        }, 600);
      }
    }, intervalMs);
  }
}

/* ═══════════════════════════════════════════════════
   SPLIT TEXT ANIMATION (for section titles)
   ═══════════════════════════════════════════════════ */
function initSplitText(prefersReducedMotion) {
  const splitElements = document.querySelectorAll(".split-text");

  splitElements.forEach((el) => {
    const text = el.textContent.trim();
    const words = text.split(/\s+/);
    el.innerHTML = "";
    el.classList.add("is-split-ready");

    words.forEach((word, index) => {
      const wordSpan = document.createElement("span");
      wordSpan.className = "word";
      const innerSpan = document.createElement("span");
      innerSpan.className = "word-inner";
      innerSpan.textContent = word;
      innerSpan.style.transitionDelay = `${index * 0.06}s`;
      wordSpan.appendChild(innerSpan);
      el.appendChild(wordSpan);

      if (index < words.length - 1) {
        el.appendChild(document.createTextNode(" "));
      }
    });
  });

  if (prefersReducedMotion) {
    splitElements.forEach((el) => el.classList.add("is-split"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-split");
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.3, rootMargin: "0px 0px -5% 0px" }
  );

  splitElements.forEach((el) => observer.observe(el));
}

/* ═══════════════════════════════════════════════════
   SCROLL-DRIVEN TEXT PARALLAX (hero texts)
   ═══════════════════════════════════════════════════ */
function initScrollTextParallax(prefersReducedMotion) {
  if (prefersReducedMotion) return;

  const scrollTexts = document.querySelectorAll(".scroll-text");
  if (!scrollTexts.length) return;

  let ticking = false;

  function update() {
    const scrollY = window.scrollY;
    const vh = window.innerHeight;

    scrollTexts.forEach((el) => {
      const speed = parseFloat(el.getAttribute("data-scroll-speed")) || 0.1;
      const rect = el.getBoundingClientRect();
      const elementTop = rect.top + scrollY;

      /* Only animate when in viewport */
      if (scrollY + vh > elementTop && scrollY < elementTop + rect.height + vh) {
        const offset = (scrollY - elementTop) * speed;
        el.style.transform = `translateY(${offset}px)`;
      }
    });

    ticking = false;
  }

  window.addEventListener("scroll", () => {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(update);
    }
  }, { passive: true });

  update();
}

/* ═══════════════════════════════════════════════════
   COUNTER ANIMATIONS (metrics section)
   ═══════════════════════════════════════════════════ */
function initCounterAnimations() {
  const counters = document.querySelectorAll(".counter");
  if (!counters.length) return;

  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.5 }
  );

  counters.forEach((el) => observer.observe(el));
}

function animateCounter(el) {
  const target = parseInt(el.getAttribute("data-target"), 10);
  if (isNaN(target)) return;

  const duration = 2000;
  const start = performance.now();

  function tick(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(eased * target);

    if (progress < 1) {
      requestAnimationFrame(tick);
    }
  }

  requestAnimationFrame(tick);
}

/* ═══════════════════════════════════════════════════
   MOBILE NAV TOGGLE
   ═══════════════════════════════════════════════════ */
function initMobileNav() {
  const toggle = document.getElementById("navToggle");
  const nav = document.getElementById("navLinks");
  if (!toggle || !nav) return;

  toggle.addEventListener("click", () => {
    const isOpen = toggle.classList.toggle("open");
    nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });

  /* Close on link click */
  nav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      toggle.classList.remove("open");
      nav.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

/* ═══════════════════════════════════════════════════
   HEADER SCROLL EFFECT
   ═══════════════════════════════════════════════════ */
function initHeaderScroll() {
  const header = document.getElementById("siteHeader");
  if (!header) return;

  let last = 0;

  window.addEventListener("scroll", () => {
    const y = window.scrollY;
    if (y > 80) {
      header.classList.add("scrolled");
    } else {
      header.classList.remove("scrolled");
    }
    last = y;
  }, { passive: true });
}

/* ═══════════════════════════════════════════════════
   SCROLL REVEAL (IntersectionObserver)
   ═══════════════════════════════════════════════════ */
function initRevealAnimations(prefersReducedMotion) {
  const revealItems = Array.from(document.querySelectorAll(".reveal"));
  if (!revealItems.length || prefersReducedMotion) {
    revealItems.forEach((item) => item.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        obs.unobserve(entry.target);
      });
    },
    { threshold: 0.15, rootMargin: "0px 0px -8% 0px" }
  );

  revealItems.forEach((item) => observer.observe(item));
}

/* ═══════════════════════════════════════════════════
   PARALLAX
   ═══════════════════════════════════════════════════ */
function initParallax(prefersReducedMotion) {
  const parallaxItems = Array.from(document.querySelectorAll(".parallax-item"));
  if (!parallaxItems.length || prefersReducedMotion) return;

  let ticking = false;

  const update = () => {
    const viewportCenter = window.scrollY + window.innerHeight / 2;

    parallaxItems.forEach((item) => {
      const speed = Number(item.getAttribute("data-parallax")) || 0.15;
      const rect = item.getBoundingClientRect();
      const itemCenter = window.scrollY + rect.top + rect.height / 2;
      const delta = viewportCenter - itemCenter;
      item.style.setProperty("--parallax-offset", `${delta * speed * 0.18}px`);
    });

    ticking = false;
  };

  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(update);
  };

  update();
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
}

/* ═══════════════════════════════════════════════════
   PARTICLES
   ═══════════════════════════════════════════════════ */
function initParticles(prefersReducedMotion) {
  const canvas = document.getElementById("luxuryParticles");
  if (!canvas || prefersReducedMotion) return;

  const context = canvas.getContext("2d");
  if (!context) return;

  const dpr = window.devicePixelRatio || 1;
  let particles = [];
  let width = 0;
  let height = 0;
  let animationId = 0;

  class Particle {
    constructor() {
      this.reset();
      this.x = Math.random() * width;
      this.y = Math.random() * height;
    }

    reset() {
      this.radius = 0.45 + Math.random() * 1.7;
      this.alpha = 0.08 + Math.random() * 0.38;
      this.vx = (Math.random() - 0.5) * 0.28;
      this.vy = (Math.random() - 0.5) * 0.28;
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;

      if (this.x < -6) this.x = width + 6;
      if (this.x > width + 6) this.x = -6;
      if (this.y < -6) this.y = height + 6;
      if (this.y > height + 6) this.y = -6;
    }

    draw(ctx) {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(212, 175, 55, ${this.alpha})`;
      ctx.fill();
    }
  }

  function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    context.setTransform(dpr, 0, 0, dpr, 0, 0);

    const count = Math.min(95, Math.max(38, Math.floor(width / 20)));
    particles = Array.from({ length: count }, () => new Particle());
  }

  function drawConnections() {
    for (let i = 0; i < particles.length; i += 1) {
      for (let j = i + 1; j < particles.length; j += 1) {
        const a = particles[i];
        const b = particles[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < 90) {
          const alpha = (1 - distance / 90) * 0.1;
          context.strokeStyle = `rgba(212, 175, 55, ${alpha})`;
          context.lineWidth = 0.5;
          context.beginPath();
          context.moveTo(a.x, a.y);
          context.lineTo(b.x, b.y);
          context.stroke();
        }
      }
    }
  }

  function animate() {
    context.clearRect(0, 0, width, height);
    particles.forEach((particle) => {
      particle.update();
      particle.draw(context);
    });
    drawConnections();
    animationId = requestAnimationFrame(animate);
  }

  resize();
  animate();
  window.addEventListener("resize", resize);

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      cancelAnimationFrame(animationId);
    } else {
      animate();
    }
  });
}
