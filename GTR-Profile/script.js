(function () {
  "use strict";

  // Check auth
  const userId = sessionStorage.getItem("gtr_user_id");
  const token  = sessionStorage.getItem("gtr_token");
  if (!userId || !token) {
    window.location.href = "../GTR-Login/index.html";
    return;
  }

  const API = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:3000"
    : "";

  // Auth headers for all protected requests
  const authHeaders = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  };

  // Handle 401 globally (expired/invalid token → re-login)
  function handleAuthError(res) {
    if (res.status === 401 || res.status === 403) {
      sessionStorage.clear();
      window.location.href = "../GTR-Login/index.html";
      return true;
    }
    return false;
  }

  /* ── ELEMENTS ── */
  const form = document.getElementById("profileForm");
  const inputName = document.getElementById("inputName");
  const inputEmail = document.getElementById("inputEmail");
  const inputPhone = document.getElementById("inputPhone");
  
  const cardName = document.getElementById("cardName");
  const cardSince = document.getElementById("cardSince");
  const cardTier = document.getElementById("cardTier");
  const cardNum = document.getElementById("cardNum");
  const welcomeName = document.getElementById("welcomeName");
  const memberId = document.getElementById("memberId");
  
  const btnLogout = document.getElementById("btnLogout");
  const toast = document.getElementById("profileToast");
  const toastMsg = document.getElementById("toastMsg");

  // Stats
  const statReservations = document.getElementById("statReservations");
  const statVehicles = document.getElementById("statVehicles");
  const statDays = document.getElementById("statDays");
  const statStatus = document.getElementById("statStatus");

  // Garage
  const garageGrid = document.getElementById("garageGrid");
  const garageCounter = document.getElementById("garageCounter");
  const btnAddVehicle = document.getElementById("btnAddVehicle");
  const addVehiclePanel = document.getElementById("addVehiclePanel");
  const addVehicleForm = document.getElementById("addVehicleForm");
  const btnCancelAdd = document.getElementById("btnCancelAdd");

  // Activity & Vault
  const activityList = document.getElementById("activityList");
  const vaultValue = document.getElementById("vaultValue");

  let userVehicles = [];

  /* ── TOAST HELPER ── */
  function showToast(msg, isError = false) {
    toast.className = isError ? "form-toast error visible" : "form-toast visible";
    toastMsg.textContent = msg;
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => toast.classList.remove("visible"), 5000);
  }

  /* ── MAPS ── */
  const EMOJI = { exotic: "✨", sports: "🏎", suv: "🚙", sedan: "🚗", convertible: "🚘" };
  const TYPE_LABEL = { exotic: "Exotic", sports: "Sports", suv: "SUV", sedan: "Sedan", convertible: "Convertible" };
  const SERVICE_MAP = { valet: "VALET", monthly: "MONTHLY", concierge: "CONCIERGE", fleet: "FLEET", event: "VIP PASS" };

  /* ── 3D CARD HOVER EFFECT ── */
  const cardWrapper = document.getElementById("vipCard");
  if (cardWrapper) {
    const card = cardWrapper.querySelector(".vip-card");
    
    cardWrapper.addEventListener("mousemove", (e) => {
      const rect = cardWrapper.getBoundingClientRect();
      const x = e.clientX - rect.left; 
      const y = e.clientY - rect.top;
      const xPct = x / rect.width;
      const yPct = y / rect.height;
      const rotateY = (xPct - 0.5) * 30; 
      const rotateX = (0.5 - yPct) * 30; 
      cardWrapper.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
      card.style.setProperty("--gx", `${xPct * 100}%`);
      card.style.setProperty("--gy", `${yPct * 100}%`);
    });
    
    cardWrapper.addEventListener("mouseleave", () => {
      cardWrapper.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg)`;
    });
  }

  /* ══════════════════════════════════════════════════
     LOAD PROFILE DATA
     ══════════════════════════════════════════════════ */
  async function loadProfile() {
    try {
      const res = await fetch(`${API}/api/user/${userId}`, { headers: authHeaders });
      if (handleAuthError(res)) return;
      const data = await res.json();
      if (res.ok && data.success) {
        const u = data.user;
        inputName.value = u.full_name || "";
        inputEmail.value = u.email || "";
        inputPhone.value = u.phone || "";
        
        // Set service chip
        const svcValue = u.preferred_service || u.service || "valet";
        const svcRadio = document.querySelector(`input[name="preferred_service"][value="${svcValue}"]`);
        if (svcRadio) svcRadio.checked = true;
        
        updateVIPCard(u);
      } else {
        alert("Session expired or invalid.");
        logout();
      }
    } catch (err) {
      console.error(err);
      showToast("Failed to load profile.", true);
    }
  }

  function updateVIPCard(u) {
    const name = u.full_name || "MEMBER";
    cardName.textContent = name;
    if (welcomeName) welcomeName.textContent = `Welcome, ${name.split(" ")[0]}`;
    
    const svc = u.preferred_service || u.service || "valet";
    cardTier.textContent = SERVICE_MAP[svc] || "MEMBER";
    
    const paddedId = String(u.id).padStart(4, "0");
    cardNum.textContent = `4920 8100 2344 ${paddedId}`;
    if (memberId) memberId.textContent = `GTR-${paddedId}`;
    
    // Member since
    if (u.created_at && cardSince) {
      const d = new Date(u.created_at);
      cardSince.textContent = d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
    }
  }

  /* ══════════════════════════════════════════════════
     LOAD STATS
     ══════════════════════════════════════════════════ */
  async function loadStats() {
    try {
      const res = await fetch(`${API}/api/user/${userId}/stats`, { headers: authHeaders });
      const data = await res.json();
      if (res.ok && data.success) {
        const s = data.stats;
        animateCounter(statReservations, s.total_reservations);
        animateCounter(statVehicles, s.vehicles_registered);
        animateCounter(statDays, s.member_days);
        statStatus.textContent = (s.status || "pending").toUpperCase();
        statStatus.style.fontSize = ".85rem";
      }
    } catch (err) {
      console.error("Stats error:", err);
    }
  }

  function animateCounter(el, target) {
    if (!el) return;
    const start = performance.now();
    const dur = 1200;
    (function tick(now) {
      const p = Math.min((now - start) / dur, 1);
      el.textContent = Math.round((1 - Math.pow(1 - p, 3)) * target);
      if (p < 1) requestAnimationFrame(tick);
    })(start);
  }

  /* ══════════════════════════════════════════════════
     LOAD VEHICLES (GARAGE)
     ══════════════════════════════════════════════════ */
  async function loadVehicles() {
    try {
      const res = await fetch(`${API}/api/user/${userId}/vehicles`, { headers: authHeaders });
      const data = await res.json();
      if (res.ok && data.success) {
        userVehicles = data.vehicles;
        renderGarage();
      }
    } catch (err) {
      console.error("Vehicles error:", err);
    }
  }

  function renderGarage() {
    garageCounter.textContent = `${userVehicles.length} / 3`;

    if (userVehicles.length === 0) {
      garageGrid.innerHTML = `<div class="garage-empty">No vehicles registered yet. Add your first car below.</div>`;
    } else {
      garageGrid.innerHTML = userVehicles.map(v => {
        const emoji = EMOJI[v.vehicle] || "🚗";
        const typeLabel = TYPE_LABEL[v.vehicle] || "Vehicle";
        const meta = [v.brand, v.model, v.year].filter(Boolean).join(" · ") || typeLabel;
        const badges = [];
        if (v.is_primary) badges.push(`<span class="veh-badge primary">★ Primary</span>`);
        badges.push(`<span class="veh-badge">${typeLabel}</span>`);
        if (v.plate) badges.push(`<span class="veh-badge">${v.plate}</span>`);
        if (v.color) badges.push(`<span class="veh-badge">${v.color}</span>`);

        return `
          <div class="vehicle-card ${v.is_primary ? 'is-primary' : ''}" data-vid="${v.id}">
            <div class="veh-emoji">${emoji}</div>
            <div class="veh-info">
              <div class="veh-name">${v.nickname}</div>
              <div class="veh-meta">${meta}</div>
              <div class="veh-badges">${badges.join("")}</div>
            </div>
            <div class="veh-actions">
              ${!v.is_primary ? `<button class="veh-btn" onclick="setPrimary(${v.id})">★ Primary</button>` : ''}
              <button class="veh-btn delete" onclick="deleteVehicle(${v.id}, '${v.nickname.replace(/'/g, "\\'")}')">&times; Remove</button>
            </div>
          </div>`;
      }).join("");
    }

    // Toggle add button state
    if (userVehicles.length >= 3) {
      btnAddVehicle.classList.add("disabled");
      btnAddVehicle.querySelector("span:last-child").textContent = "Garage Full (3/3)";
    } else {
      btnAddVehicle.classList.remove("disabled");
      btnAddVehicle.querySelector("span:last-child").textContent = "Add Vehicle";
    }
  }

  /* ── ADD VEHICLE ── */
  btnAddVehicle.addEventListener("click", () => {
    if (userVehicles.length >= 3) return;
    addVehiclePanel.style.display = "block";
    btnAddVehicle.style.display = "none";
    document.getElementById("vNickname").focus();
  });

  btnCancelAdd.addEventListener("click", () => {
    addVehiclePanel.style.display = "none";
    btnAddVehicle.style.display = "flex";
    addVehicleForm.reset();
  });

  addVehicleForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const nickname = document.getElementById("vNickname").value.trim();
    if (!nickname) {
      document.getElementById("vNickname").style.borderColor = "#e74c3c";
      return;
    }

    const payload = {
      nickname,
      vehicle: document.getElementById("vType").value,
      brand: document.getElementById("vBrand").value.trim(),
      model: document.getElementById("vModel").value.trim(),
      year: document.getElementById("vYear").value,
      color: document.getElementById("vColor").value.trim(),
      plate: document.getElementById("vPlate").value.trim(),
      is_primary: document.getElementById("vPrimary").checked,
    };

    try {
      const res = await fetch(`${API}/api/user/${userId}/vehicles`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast(`${nickname} added to your garage!`);
        addVehiclePanel.style.display = "none";
        btnAddVehicle.style.display = "flex";
        addVehicleForm.reset();
        loadVehicles();
        loadStats();
      } else {
        showToast(data.errors?.join(". ") || "Error adding vehicle.", true);
      }
    } catch (err) {
      showToast("Network error.", true);
    }
  });

  /* ── DELETE VEHICLE ── */
  window.deleteVehicle = async function(vid, name) {
    if (!confirm(`Remove "${name}" from your garage?`)) return;
    try {
      const res = await fetch(`${API}/api/user/${userId}/vehicles/${vid}`, { method: "DELETE", headers: authHeaders });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast(`${name} removed from garage.`);
        loadVehicles();
        loadStats();
      } else {
        showToast(data.errors?.join(". ") || "Error removing vehicle.", true);
      }
    } catch (err) {
      showToast("Network error.", true);
    }
  };

  /* ── SET PRIMARY ── */
  window.setPrimary = async function(vid) {
    try {
      const veh = userVehicles.find(v => v.id === vid);
      const res = await fetch(`${API}/api/user/${userId}/vehicles/${vid}`, {
        method: "PUT",
        headers: authHeaders,
        body: JSON.stringify({ ...veh, is_primary: true }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast("Primary vehicle updated.");
        loadVehicles();
      }
    } catch (err) {
      showToast("Network error.", true);
    }
  };

  /* ══════════════════════════════════════════════════
     LOAD ACTIVITY HISTORY
     ══════════════════════════════════════════════════ */
  async function loadActivity() {
    try {
      const res = await fetch(`${API}/api/user/${userId}/activity`, { headers: authHeaders });
      const data = await res.json();
      if (res.ok && data.success && data.activity.length > 0) {
        const items = data.activity;
        
        activityList.innerHTML = items.map(a => {
          const date = new Date(a.created_at);
          const dateStr = date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
          const timeStr = date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
          const svc = SERVICE_MAP[a.service] || a.service || "RESERVATION";
          const status = a.status || "pending";
          
          return `
            <div class="activity-item">
              <div class="act-dot ${status}"></div>
              <div class="act-info">
                <div class="act-title">${svc} Service</div>
                <div class="act-date">${dateStr} at ${timeStr}</div>
              </div>
              <span class="act-status ${status}">${status}</span>
            </div>`;
        }).join("");

        // Update vault status based on most recent confirmed/active reservation
        const active = items.find(a => a.status === "confirmed");
        if (active) {
          vaultValue.textContent = "🟢 Vehicle currently in Vault";
          vaultValue.style.color = "#2ecc71";
        } else {
          vaultValue.textContent = "No vehicle in Vault";
        }
      }
    } catch (err) {
      console.error("Activity error:", err);
    }
  }

  /* ══════════════════════════════════════════════════
     SAVE PROFILE
     ══════════════════════════════════════════════════ */
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("btnUpdateProfile");
    const origText = btn.querySelector("span").textContent;
    btn.disabled = true;
    btn.style.opacity = "0.7";
    btn.querySelector("span").textContent = "Saving...";
    
    const selectedService = document.querySelector('input[name="preferred_service"]:checked')?.value || "valet";
    
    const payload = {
      name: inputName.value.trim(),
      phone: inputPhone.value.trim(),
      service: selectedService,
      vehicle: "sports",
      date: "",
      time: "",
      message: ""
    };
    
    try {
      const res = await fetch(`${API}/api/user/${userId}`, {
        method: "PUT",
        headers: authHeaders,
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      
      // Update preferred service
      await fetch(`${API}/api/user/${userId}/service`, {
        method: "PATCH",
        headers: authHeaders,
        body: JSON.stringify({ service: selectedService })
      });
      
      if (res.ok && data.success) {
        showToast("Profile updated securely in Vault.");
        updateVIPCard({ ...data.user, preferred_service: selectedService });
      } else {
        showToast(data.errors?.join(". ") || "Error updating profile.", true);
      }
    } catch (err) {
      showToast("Network error while saving.", true);
    } finally {
      btn.disabled = false;
      btn.style.opacity = "1";
      btn.querySelector("span").textContent = origText;
    }
  });

  /* ── LOGOUT ── */
  function logout() {
    sessionStorage.removeItem("gtr_user_id");
    sessionStorage.removeItem("gtr_token");
    window.location.href = "../GTR-Login/index.html";
  }
  btnLogout.addEventListener("click", logout);

  /* ══════════════════════════════════════════════════
     INIT — Load everything
     ══════════════════════════════════════════════════ */
  loadProfile();
  loadStats();
  loadVehicles();
  loadActivity();

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

    const interactiveSelector = "a, button, [role='button'], input, select, textarea, .vip-card-wrapper, .btn, .vehicle-card, .svc-chip, .notif-toggle";

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
