(function () {
  "use strict";

  // Check auth
  const userId = sessionStorage.getItem("gtr_user_id");
  if (!userId) {
    window.location.href = "../GTR-Login/index.html";
    return;
  }

  /* ── ELEMENTS ── */
  const form = document.getElementById("profileForm");
  const inputName = document.getElementById("inputName");
  const inputEmail = document.getElementById("inputEmail");
  const inputPhone = document.getElementById("inputPhone");
  const inputService = document.getElementById("inputService");
  const inputVehicle = document.getElementById("inputVehicle");
  
  const cardName = document.getElementById("cardName");
  const cardVehicle = document.getElementById("cardVehicle");
  const cardTier = document.getElementById("cardTier");
  const cardNum = document.getElementById("cardNum");
  
  const btnLogout = document.getElementById("btnLogout");
  const toast = document.getElementById("profileToast");
  const toastMsg = document.getElementById("toastMsg");

  /* ── 3D CARD HOVER EFFECT ── */
  const cardWrapper = document.getElementById("vipCard");
  const card = cardWrapper.querySelector(".vip-card");
  
  cardWrapper.addEventListener("mousemove", (e) => {
    const rect = cardWrapper.getBoundingClientRect();
    const x = e.clientX - rect.left; 
    const y = e.clientY - rect.top;
    
    // Calculate rotation (-15deg to 15deg)
    const xPct = x / rect.width;
    const yPct = y / rect.height;
    const rotateY = (xPct - 0.5) * 30; 
    const rotateX = (0.5 - yPct) * 30; 
    
    cardWrapper.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    
    // Move glow
    card.style.setProperty("--gx", `${xPct * 100}%`);
    card.style.setProperty("--gy", `${yPct * 100}%`);
  });
  
  cardWrapper.addEventListener("mouseleave", () => {
    cardWrapper.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg)`;
  });

  /* ── LOAD DATA ── */
  async function loadProfile() {
    try {
      const res = await fetch(`/api/user/${userId}`);
      const data = await res.json();
      if (res.ok && data.success) {
        const u = data.user;
        
        // Populate form
        inputName.value = u.full_name || "";
        inputEmail.value = u.email || "";
        inputPhone.value = u.phone || "";
        inputService.value = u.service || "valet";
        inputVehicle.value = u.vehicle || "exotic";
        
        updateCard(u);
      } else {
        alert("Session expired or invalid.");
        logout();
      }
    } catch (err) {
      console.error(err);
      alert("Failed to load profile details.");
    }
  }

  function updateCard(u) {
    cardName.textContent = u.full_name || "MEMBER";
    
    const vMap = {
      "sports": "SPORTS",
      "suv": "LUXURY SUV",
      "sedan": "PREMIUM SEDAN",
      "convertible": "CONVERTIBLE",
      "exotic": "HYPERCAR"
    };
    cardVehicle.textContent = vMap[u.vehicle] || "VEHICLE";
    
    const tMap = {
      "monthly": "MONTHLY",
      "concierge": "CONCIERGE",
      "fleet": "FLEET",
      "event": "VIP PASS",
      "valet": "VALET"
    };
    cardTier.textContent = tMap[u.service] || "MEMBER";
    
    // Fake card number based on ID
    const paddedId = String(u.id).padStart(4, "0");
    cardNum.textContent = `4920 8100 2344 ${paddedId}`;
  }

  /* ── UPDATE DATA ── */
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("btnUpdateProfile");
    const origText = btn.querySelector("span").textContent;
    btn.disabled = true;
    btn.style.opacity = "0.7";
    btn.querySelector("span").textContent = "Saving...";
    
    const payload = {
      name: inputName.value.trim(),
      phone: inputPhone.value.trim(),
      service: inputService.value,
      vehicle: inputVehicle.value,
      date: "",
      time: "",
      message: ""
    };
    
    try {
      const res = await fetch(`/api/user/${userId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      
      if (res.ok && data.success) {
        toast.className = "form-toast visible";
        toastMsg.textContent = "Profile updated securely in Vault.";
        updateCard(data.user);
        setTimeout(() => toast.classList.remove("visible"), 5000);
      } else {
        toast.className = "form-toast error visible";
        toastMsg.textContent = data.errors?.join(". ") || "Error updating profile.";
      }
    } catch (err) {
      toast.className = "form-toast error visible";
      toastMsg.textContent = "Network error while saving.";
    } finally {
      btn.disabled = false;
      btn.style.opacity = "1";
      btn.querySelector("span").textContent = origText;
    }
  });

  /* ── LOGOUT ── */
  function logout() {
    sessionStorage.removeItem("gtr_user_id");
    window.location.href = "../GTR-Login/index.html";
  }
  btnLogout.addEventListener("click", logout);

  /* ── INIT ── */
  loadProfile();

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  initCustomCursor(prefersReducedMotion);
  initParticles(prefersReducedMotion);

  /* ═══════════════════════════════════════════════════
     CUSTOM CURSOR
     ═══════════════════════════════════════════════════ */
  function initCustomCursor(prefersReducedMotion) {
    const hasFinePinter = window.matchMedia("(pointer: fine)").matches;
    if (!hasFinePinter || prefersReducedMotion) return;

    const dot  = document.getElementById("cursorDot");
    const ring = document.getElementById("cursorRing");
    if (!dot || !ring) return;

    let mouseX = -200, mouseY = -200;
    let ringX  = -200, ringY  = -200;
    let rafId;

    function tick() {
      ringX += (mouseX - ringX) * 0.12;
      ringY += (mouseY - ringY) * 0.12;
      dot.style.left  = mouseX + "px";
      dot.style.top   = mouseY + "px";
      ring.style.left = Math.round(ringX) + "px";
      ring.style.top  = Math.round(ringY) + "px";
      rafId = requestAnimationFrame(tick);
    }
    tick();

    document.addEventListener("mousemove", (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      document.body.classList.remove("cursor-out");
    });

    document.addEventListener("mouseleave", () => document.body.classList.add("cursor-out"));
    document.addEventListener("mouseenter", () => document.body.classList.remove("cursor-out"));

    const interactiveSelector = "a, button, [role='button'], input, select, textarea, .vip-card-wrapper, .btn";

    document.addEventListener("mouseover", (e) => {
      if (e.target.closest(interactiveSelector)) document.body.classList.add("cursor-hover");
    });
    document.addEventListener("mouseout", (e) => {
      if (e.target.closest(interactiveSelector)) document.body.classList.remove("cursor-hover");
    });

    document.addEventListener("mousedown", () => document.body.classList.add("cursor-click"));
    document.addEventListener("mouseup",   () => document.body.classList.remove("cursor-click"));
  }

  /* ═══════════════════════════════════════════════════
     LUXURY PARTICLES
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

    const isMobile = window.innerWidth < 768;

    function resize() {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);

      const count = isMobile
        ? Math.min(15, Math.max(8, Math.floor(width / 30)))
        : Math.min(95, Math.max(38, Math.floor(width / 20)));
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
      if (!isMobile) drawConnections();
      animationId = requestAnimationFrame(animate);
    }

    resize();
    animate();
    window.addEventListener("resize", resize);

    document.addEventListener("visibilitychange", () => {
      if (document.hidden) cancelAnimationFrame(animationId);
      else animate();
    });
  }

})();
