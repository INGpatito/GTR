(function () {
  "use strict";

  // Check auth
  const userId = sessionStorage.getItem("gtr_user_id");
  const token = sessionStorage.getItem("gtr_token");
  if (!userId || !token) {
    window.location.href = "../GTR-Login/index.html";
    return;
  }

  const API = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:3000"
    : (window.location.protocol === "file:" ? "https://papoys.me" : "");

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
  let currentMembershipTier = "none";

  const TIER_LABELS = {
    none: "MEMBER",
    silver: "SILVER",
    gold: "GOLD PRESTIGE",
    platinum: "PLATINUM ELITE"
  };

  const TIER_LIMITS = {
    none: 0,
    silver: 1,
    gold: 2,
    platinum: 3
  };

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
    const card = cardWrapper.querySelector(".vip-card-front");

    cardWrapper.addEventListener("mousemove", (e) => {
      if (cardWrapper.classList.contains("is-flipped")) return;
      const rect = cardWrapper.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const xPct = x / rect.width;
      const yPct = y / rect.height;
      const rotateY = (xPct - 0.5) * 30;
      const rotateX = (0.5 - yPct) * 30;
      cardWrapper.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
      if (card) {
        card.style.setProperty("--gx", `${xPct * 100}%`);
        card.style.setProperty("--gy", `${yPct * 100}%`);
      }
    });

    cardWrapper.addEventListener("mouseleave", () => {
      if (cardWrapper.classList.contains("is-flipped")) return;
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

        // Set membership tier
        currentMembershipTier = u.membership_tier || "none";
        updateMembershipUI(currentMembershipTier);

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

  let userCardNumber = "";

  function updateVIPCard(u) {
    const name = u.full_name || "MEMBER";
    cardName.textContent = name;
    if (welcomeName) welcomeName.textContent = `Welcome, ${name.split(" ")[0]}`;

    const svc = u.preferred_service || u.service || "valet";
    const tier = u.membership_tier || currentMembershipTier || "none";
    cardTier.textContent = tier !== "none" ? TIER_LABELS[tier] : (SERVICE_MAP[svc] || "MEMBER");

    // Use the server-generated encrypted card number
    userCardNumber = u.card_number || "0000 0000 0000 0000";
    cardNum.textContent = userCardNumber;

    const paddedId = String(u.id).padStart(4, "0");
    if (memberId) memberId.textContent = `GTR-${paddedId}`;

    // Member since
    if (u.created_at && cardSince) {
      const d = new Date(u.created_at);
      cardSince.textContent = d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
    }

    // Generate QR code with encrypted card number
    generateQR(userCardNumber);
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
    const limit = TIER_LIMITS[currentMembershipTier] || 0;
    garageCounter.textContent = `${userVehicles.length} / ${limit}`;

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
    if (userVehicles.length >= limit) {
      btnAddVehicle.classList.add("disabled");
      btnAddVehicle.querySelector("span:last-child").textContent = `Garage Full (${userVehicles.length}/${limit})`;
    } else {
      btnAddVehicle.classList.remove("disabled");
      btnAddVehicle.querySelector("span:last-child").textContent = "Add Vehicle";
    }
  }

  /* ── ADD VEHICLE ── */
  btnAddVehicle.addEventListener("click", () => {
    const limit = TIER_LIMITS[currentMembershipTier] || 0;
    if (userVehicles.length >= limit) return;
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
  window.deleteVehicle = async function (vid, name) {
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
  window.setPrimary = async function (vid) {
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
     CARD FLIP & QR GENERATION
     ══════════════════════════════════════════════════ */
  const btnFlipCard = document.getElementById("btnFlipCard");
  let qrGenerated = false;

  function generateQR(cardNum) {
    if (qrGenerated || !cardNum) return;
    const qrEl = document.getElementById("qrCode");
    if (!qrEl || typeof QRCode === "undefined") return;
    qrEl.innerHTML = "";
    new QRCode(qrEl, {
      text: cardNum.replace(/\s/g, ""),
      width: 120,
      height: 120,
      colorDark: "#111",
      colorLight: "#ffffff",
      correctLevel: QRCode.CorrectLevel.H
    });
    qrGenerated = true;
  }

  if (btnFlipCard && cardWrapper) {
    btnFlipCard.addEventListener("click", () => {
      const isFlipped = cardWrapper.classList.toggle("is-flipped");
      cardWrapper.style.transform = "";
      const labelSpan = btnFlipCard.querySelector("span:last-child");
      if (isFlipped) {
        labelSpan.textContent = currentLang === "es" ? "Volver a Tarjeta" : "Back to Card";
      } else {
        labelSpan.textContent = currentLang === "es" ? "Mostrar Pase" : "Show Access Pass";
      }
    });

    // Also flip when clicking the back of the card
    const backFace = cardWrapper.querySelector(".vip-card-back");
    if (backFace) {
      backFace.addEventListener("click", () => {
        cardWrapper.classList.remove("is-flipped");
        cardWrapper.style.transform = "";
        const labelSpan = btnFlipCard.querySelector("span:last-child");
        labelSpan.textContent = currentLang === "es" ? "Mostrar Pase" : "Show Access Pass";
      });
    }
  }

  /* ══════════════════════════════════════════════════
     PASSWORD CHANGE
     ══════════════════════════════════════════════════ */
  const btnTogglePw = document.getElementById("btnTogglePw");
  const pwFields = document.getElementById("pwFields");
  const btnChangePw = document.getElementById("btnChangePw");

  if (btnTogglePw && pwFields) {
    btnTogglePw.addEventListener("click", () => {
      const open = pwFields.style.display === "none";
      pwFields.style.display = open ? "block" : "none";
      btnTogglePw.classList.toggle("open", open);
    });
  }

  if (btnChangePw) {
    btnChangePw.addEventListener("click", async () => {
      const currentPw = document.getElementById("inputCurrentPw").value;
      const newPw = document.getElementById("inputNewPw").value;

      if (!currentPw || !newPw) {
        showToast(currentLang === "es" ? "Ambos campos son requeridos." : "Both fields are required.", true);
        return;
      }
      if (newPw.length < 6) {
        showToast(currentLang === "es" ? "Mínimo 6 caracteres." : "Minimum 6 characters.", true);
        return;
      }

      btnChangePw.disabled = true;
      btnChangePw.querySelector("span").textContent = currentLang === "es" ? "Actualizando..." : "Updating...";

      try {
        const res = await fetch(`${API}/api/user/${userId}/password`, {
          method: "PUT",
          headers: authHeaders,
          body: JSON.stringify({ currentPassword: currentPw, newPassword: newPw })
        });
        const data = await res.json();

        if (res.ok && data.success) {
          showToast(currentLang === "es" ? "Contraseña actualizada." : "Password updated successfully.");
          document.getElementById("inputCurrentPw").value = "";
          document.getElementById("inputNewPw").value = "";
          pwFields.style.display = "none";
          btnTogglePw.classList.remove("open");
        } else {
          showToast(data.errors?.join(". ") || "Error.", true);
        }
      } catch (err) {
        showToast("Network error.", true);
      } finally {
        btnChangePw.disabled = false;
        btnChangePw.querySelector("span").textContent = currentLang === "es" ? "Actualizar Contraseña" : "Update Password";
      }
    });
  }

  /* ══════════════════════════════════════════════════
     INIT — Load everything
     ══════════════════════════════════════════════════ */
  loadProfile();
  loadStats();
  loadVehicles();
  loadActivity();

  /* ══════════════════════════════════════════════════
     MEMBERSHIP TIER SELECTION
     ══════════════════════════════════════════════════ */
  function updateMembershipUI(tier) {
    const hierarchy = { none: 0, silver: 1, gold: 2, platinum: 3 };
    const currentLevel = hierarchy[tier] || 0;

    const allCards = document.querySelectorAll('.mem-card');
    allCards.forEach(card => {
      const cardTierValue = card.getAttribute('data-tier');
      const cardLevel = hierarchy[cardTierValue];
      const btn = card.querySelector('.mem-btn span');
      const btnWrapper = card.querySelector('.mem-btn');
      const activeBadge = card.querySelector('.mem-active-badge');

      // Reset displays
      if (btnWrapper) btnWrapper.style.display = 'block';
      if (activeBadge) activeBadge.style.display = 'none';
      card.classList.remove('is-active');

      if (cardTierValue === tier) {
        card.classList.add('is-active');
        if (btnWrapper) btnWrapper.style.display = 'none';
        if (activeBadge) activeBadge.style.display = 'flex';
      } else if (cardLevel > currentLevel) {
        if (btn) btn.textContent = currentLang === 'es' ? `Mejorar a ${cardTierValue.toUpperCase()}` : `Upgrade to ${cardTierValue.toUpperCase()}`;
      } else {
        if (btn) btn.textContent = currentLang === 'es' ? `Bajar a ${cardTierValue.toUpperCase()}` : `Downgrade to ${cardTierValue.toUpperCase()}`;
      }
    });

    // Update VIP Card appearance
    const vipCards = document.querySelectorAll('.vip-card');
    vipCards.forEach(card => {
      card.classList.remove('tier-silver', 'tier-gold', 'tier-platinum');
      if (tier && tier !== 'none') {
        card.classList.add(`tier-${tier}`);
      }
    });
  }

  async function selectMembership(tier) {
    if (tier === currentMembershipTier) return;

    const tierNames = { silver: 'Silver Access', gold: 'Gold Prestige', platinum: 'Platinum Elite' };
    const tierNamesES = { silver: 'Acceso Silver', gold: 'Gold Prestigio', platinum: 'Platinum Elite' };
    const name = currentLang === 'es' ? tierNamesES[tier] : tierNames[tier];

    if (!confirm(currentLang === 'es'
      ? `¿Deseas activar la membresía ${name}?`
      : `Activate ${name} membership?`)) return;

    try {
      const res = await fetch(`${API}/api/user/${userId}/membership`, {
        method: 'PATCH',
        headers: authHeaders,
        body: JSON.stringify({ tier })
      });
      const data = await res.json();
      if (handleAuthError(res)) return;

      if (res.ok && data.success) {
        currentMembershipTier = tier;
        updateMembershipUI(tier);

        // Update VIP card tier display
        if (cardTier) cardTier.textContent = TIER_LABELS[tier];

        // Removed the code that destroys the membership section.
        // The updateMembershipUI(tier) call above now elegantly handles showing 'Active Plan' and 'Upgrade' buttons.

        // Update Garage limits display
        renderGarage();

        // Add local activity record
        const dateStr = new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
        const timeStr = new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
        const newActivity = `
            <div class="activity-item">
              <div class="act-dot confirmed"></div>
              <div class="act-info">
                <div class="act-title">Membership Upgraded: ${name}</div>
                <div class="act-date">${dateStr} at ${timeStr}</div>
              </div>
              <span class="act-status confirmed">Confirmed</span>
            </div>`;
        if (activityList) {
          activityList.insertAdjacentHTML('afterbegin', newActivity);
        }

        showToast(currentLang === 'es'
          ? `Su nivel de prestigio ha mejorado a ${name}`
          : `Membership upgraded to ${name}.`);
      } else {
        showToast(data.errors?.join('. ') || 'Error updating membership.', true);
      }
    } catch (err) {
      console.error('Membership error:', err);
      showToast(currentLang === 'es' ? 'Error de red.' : 'Network error.', true);
    }
  }

  // Attach click listeners to membership buttons
  document.querySelectorAll('.mem-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tier = btn.getAttribute('data-tier');
      if (tier) selectMembership(tier);
    });
  });

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  initCustomCursor(prefersReducedMotion);
  initParticles(prefersReducedMotion);

  /* ═══════════════════════════════════════════════════
     CUSTOM CURSOR
     ═══════════════════════════════════════════════════ */
  function initCustomCursor(prefersReducedMotion) {
    const hasFinePinter = window.matchMedia("(pointer: fine)").matches;
    if (!hasFinePinter || prefersReducedMotion) return;

    const dot = document.getElementById("cursorDot");
    const ring = document.getElementById("cursorRing");
    if (!dot || !ring) return;

    let mouseX = -200, mouseY = -200;
    let ringX = -200, ringY = -200;
    let rafId;

    function tick() {
      ringX += (mouseX - ringX) * 0.12;
      ringY += (mouseY - ringY) * 0.12;
      dot.style.left = mouseX + "px";
      dot.style.top = mouseY + "px";
      ring.style.left = Math.round(ringX) + "px";
      ring.style.top = Math.round(ringY) + "px";
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

    const interactiveSelector = "a, button, [role='button'], input, select, textarea, .vip-card-wrapper, .btn, .vehicle-card, .svc-chip";

    document.addEventListener("mouseover", (e) => {
      if (e.target.closest(interactiveSelector)) document.body.classList.add("cursor-hover");
    });
    document.addEventListener("mouseout", (e) => {
      if (e.target.closest(interactiveSelector)) document.body.classList.remove("cursor-hover");
    });

    document.addEventListener("mousedown", () => document.body.classList.add("cursor-click"));
    document.addEventListener("mouseup", () => document.body.classList.remove("cursor-click"));
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

  /* ══════════════════════════════════════════════════
     TRANSLATIONS
     ══════════════════════════════════════════════════ */
  const TEXTS = {
    en: {
      langBtn: "🌐 ES",
      signOut: "Sign Out",
      reservations: "Reservations",
      vehicles: "Vehicles",
      daysMember: "Days as Member",
      accStatus: "Account Status",
      memberId: "Member ID",
      profSettings: "Profile Settings",
      profDesc: "Update your personal information and preferred service tier.",
      fName: "Full Name",
      fPhone: "Phone",
      fPrefServ: "Preferred Service",
      fSave: "Save Profile",
      garTitle: "My Garage",
      garDesc: "Register up to 3 vehicles. Set one as primary for automatic valet recognition.",
      addBtn: "Add Vehicle",
      garEmpty: "No vehicles registered yet. Add your first car below.",
      actTitle: "Recent Activity",
      actDesc: "Track your latest valet and concierge interactions.",
      actEmpty: "No activity records found.",
      flipShow: "Show Access Pass",
      flipBack: "Back to Card",
      changePw: "Change Password",
      currentPw: "Current Password",
      newPw: "New Password",
      updatePw: "Update Password",
      // Membership
      memTitle: "Membership Plans",
      memDesc: "Choose your level of prestige. Upgrade anytime to unlock premium benefits.",
      memActive: "Active Plan",
      memPopular: "Most Popular",
      memSilverName: "Silver Access",
      memSilverDesc: "Perfect for the discerning driver who visits multiple times a week.",
      memSilverBtn: "Select Silver",
      memSilverF1: "Standard valet service",
      memSilverF2: "Up to 12 visits/month",
      memSilverF3: "Covered parking bay",
      memSilverF4: "Mobile app retrieval",
      memSilverF5: "24/7 support line",
      memGoldName: "Gold Prestige",
      memGoldDesc: "The preferred choice for executives and enthusiasts who demand excellence daily.",
      memGoldBtn: "Select Gold",
      memGoldF1: "Unlimited white-glove valet",
      memGoldF2: "Dedicated reserved bay",
      memGoldF3: "Priority express exit",
      memGoldF4: "EV charging included",
      memGoldF5: "Exterior detailing (2×/mo)",
      memGoldF6: "Dedicated account manager",
      memPlatName: "Platinum Elite",
      memPlatDesc: "The ultimate GTR experience — limitless, uncompromising, bespoke.",
      memPlatBtn: "Select Platinum",
      memPlatF1: "Everything in Gold",
      memPlatF2: "Multi-vehicle coverage (up to 3)",
      memPlatF3: "Full interior & exterior detail (4×/mo)",
      memPlatF4: "VIP event parking access",
      memPlatF5: "Chauffeur coordination",
      memPlatF6: "Concierge personal assistant",
      memPlatF7: "Premium insurance coverage"
    },
    es: {
      langBtn: "🌐 EN",
      signOut: "Cerrar Sesión",
      reservations: "Reservas",
      vehicles: "Vehículos",
      daysMember: "Días como Miembro",
      accStatus: "Estado de Cuenta",
      memberId: "ID de Socio",
      profSettings: "Configuración de Perfil",
      profDesc: "Actualiza tu información personal y nivel de servicio preferido.",
      fName: "Nombre Completo",
      fPhone: "Teléfono",
      fPrefServ: "Servicio Preferido",
      fSave: "Guardar Perfil",
      garTitle: "Mi Garaje",
      garDesc: "Registra hasta 3 vehículos. Fija uno como principal para el valet.",
      addBtn: "Añadir Vehículo",
      garEmpty: "No hay vehículos. Añade tu primer auto abajo.",
      actTitle: "Actividad Reciente",
      actDesc: "Rastrea tus últimas interacciones de valet y concierge.",
      actEmpty: "No se encontraron registros de actividad.",
      flipShow: "Mostrar Pase",
      flipBack: "Volver a Tarjeta",
      changePw: "Cambiar Contraseña",
      currentPw: "Contraseña Actual",
      newPw: "Nueva Contraseña",
      updatePw: "Actualizar Contraseña",
      // Membership
      memTitle: "Planes de Membresía",
      memDesc: "Elige tu nivel de prestigio. Actualiza en cualquier momento para desbloquear beneficios premium.",
      memActive: "Plan Activo",
      memPopular: "Más Popular",
      memSilverName: "Acceso Silver",
      memSilverDesc: "Perfecto para el conductor exigente que visita varias veces por semana.",
      memSilverBtn: "Seleccionar Silver",
      memSilverF1: "Servicio valet estándar",
      memSilverF2: "Hasta 12 visitas/mes",
      memSilverF3: "Estacionamiento cubierto",
      memSilverF4: "Recuperación por app móvil",
      memSilverF5: "Línea de soporte 24/7",
      memGoldName: "Gold Prestigio",
      memGoldDesc: "La opción preferida para ejecutivos y entusiastas que exigen excelencia diaria.",
      memGoldBtn: "Seleccionar Gold",
      memGoldF1: "Valet premium ilimitado",
      memGoldF2: "Bahía reservada dedicada",
      memGoldF3: "Salida express prioritaria",
      memGoldF4: "Carga EV incluida",
      memGoldF5: "Detallado exterior (2×/mes)",
      memGoldF6: "Gerente de cuenta dedicado",
      memPlatName: "Platinum Elite",
      memPlatDesc: "La experiencia GTR definitiva — sin límites, sin compromisos, a medida.",
      memPlatBtn: "Seleccionar Platinum",
      memPlatF1: "Todo lo de Gold",
      memPlatF2: "Cobertura multi-vehículo (hasta 3)",
      memPlatF3: "Detallado interior y exterior completo (4×/mes)",
      memPlatF4: "Acceso a estacionamiento VIP en eventos",
      memPlatF5: "Coordinación de chofer",
      memPlatF6: "Asistente personal concierge",
      memPlatF7: "Cobertura de seguro premium"
    }
  };

  let currentLang = localStorage.getItem("gtr_lang") || "en";

  const langEN = document.getElementById("langEN");
  const langES = document.getElementById("langES");

  function updateLangButtons() {
    if (!langEN || !langES) return;
    if (currentLang === "en") {
      langEN.classList.add("lang-btn--active");
      langES.classList.remove("lang-btn--active");
    } else {
      langES.classList.add("lang-btn--active");
      langEN.classList.remove("lang-btn--active");
    }
  }

  if (langEN) langEN.addEventListener("click", () => { currentLang = "en"; localStorage.setItem("gtr_lang", "en"); updateLangButtons(); applyTranslations(); });
  if (langES) langES.addEventListener("click", () => { currentLang = "es"; localStorage.setItem("gtr_lang", "es"); updateLangButtons(); applyTranslations(); });

  function applyTranslations() {
    const t = TEXTS[currentLang];
    if (btnLogout) btnLogout.textContent = t.signOut;

    document.querySelector("#statsGrid .stat-box:nth-child(1) .stat-label").textContent = t.reservations;
    document.querySelector("#statsGrid .stat-box:nth-child(2) .stat-label").textContent = t.vehicles;
    document.querySelector("#statsGrid .stat-box:nth-child(3) .stat-label").textContent = t.daysMember;
    document.querySelector("#statsGrid .stat-box:nth-child(4) .stat-label").textContent = t.accStatus;

    document.querySelector(".mid-label").textContent = t.memberId;

    document.querySelector(".dash-card:nth-child(1) .dash-title").textContent = t.profSettings;
    document.querySelector(".dash-card:nth-child(1) .dash-desc").textContent = t.profDesc;

    document.querySelector('label[for="inputName"]').textContent = t.fName;
    document.querySelector('label[for="inputPhone"]').textContent = t.fPhone;
    document.querySelector('.form-group.full:nth-of-type(4) label').textContent = t.fPrefServ;
    document.querySelector('#btnUpdateProfile span').textContent = t.fSave;

    const rightCards = document.querySelectorAll('.dash-col:nth-child(2) .dash-card');
    if (rightCards[0]) {
      rightCards[0].querySelector('.dash-title').textContent = t.garTitle;
      rightCards[0].querySelector('.dash-desc').textContent = t.garDesc;
      rightCards[0].querySelector('#btnAddVehicle span:last-child').textContent = userVehicles.length >= 3 ? (currentLang === 'es' ? "Garaje Lleno" : "Garage Full") : t.addBtn;
    }
    if (rightCards[1]) {
      rightCards[1].querySelector('.dash-title').textContent = t.actTitle;
      rightCards[1].querySelector('.dash-desc').textContent = t.actDesc;
    }

    // Flip button
    const flipLabel = document.querySelector('#btnFlipCard span:last-child');
    if (flipLabel && cardWrapper) {
      flipLabel.textContent = cardWrapper.classList.contains('is-flipped') ? t.flipBack : t.flipShow;
    }

    // Password section
    const pwLabel = document.querySelector('#btnTogglePw span[data-en]');
    if (pwLabel) pwLabel.textContent = t.changePw;
    const lblCurPw = document.querySelector('label[for="inputCurrentPw"]');
    if (lblCurPw) lblCurPw.textContent = t.currentPw;
    const lblNewPw = document.querySelector('label[for="inputNewPw"]');
    if (lblNewPw) lblNewPw.textContent = t.newPw;
    const btnPwSpan = document.querySelector('#btnChangePw span');
    if (btnPwSpan) btnPwSpan.textContent = t.updatePw;

    // Membership section translations
    const memTitle = document.getElementById('membershipTitle');
    if (memTitle) memTitle.textContent = t.memTitle;
    const memDesc = document.getElementById('membershipDesc');
    if (memDesc) memDesc.textContent = t.memDesc;

    // Popular badge
    const popBadge = document.querySelector('.mem-popular-badge');
    if (popBadge) popBadge.textContent = t.memPopular;

    // Active badges
    document.querySelectorAll('.mem-active-badge [data-i18n-mem="active"]').forEach(el => {
      el.textContent = t.memActive;
    });

    // Silver
    const sN = document.querySelector('[data-i18n-mem="silver.name"]');
    if (sN) sN.textContent = t.memSilverName;
    const sD = document.querySelector('[data-i18n-mem="silver.desc"]');
    if (sD) sD.textContent = t.memSilverDesc;
    const sB = document.querySelector('[data-i18n-mem="silver.btn"]');
    if (sB) sB.textContent = t.memSilverBtn;
    const silverFeatures = ['memSilverF1', 'memSilverF2', 'memSilverF3', 'memSilverF4', 'memSilverF5'];
    silverFeatures.forEach((key, i) => {
      const el = document.querySelector(`[data-i18n-mem="silver.f${i + 1}"]`);
      if (el) el.textContent = t[key];
    });

    // Gold
    const gN = document.querySelector('[data-i18n-mem="gold.name"]');
    if (gN) gN.textContent = t.memGoldName;
    const gD = document.querySelector('[data-i18n-mem="gold.desc"]');
    if (gD) gD.textContent = t.memGoldDesc;
    const gB = document.querySelector('[data-i18n-mem="gold.btn"]');
    if (gB) gB.textContent = t.memGoldBtn;
    const goldFeatures = ['memGoldF1', 'memGoldF2', 'memGoldF3', 'memGoldF4', 'memGoldF5', 'memGoldF6'];
    goldFeatures.forEach((key, i) => {
      const el = document.querySelector(`[data-i18n-mem="gold.f${i + 1}"]`);
      if (el) el.textContent = t[key];
    });

    // Platinum
    const pN = document.querySelector('[data-i18n-mem="platinum.name"]');
    if (pN) pN.textContent = t.memPlatName;
    const pD = document.querySelector('[data-i18n-mem="platinum.desc"]');
    if (pD) pD.textContent = t.memPlatDesc;
    const pB = document.querySelector('[data-i18n-mem="platinum.btn"]');
    if (pB) pB.textContent = t.memPlatBtn;
    const platFeatures = ['memPlatF1', 'memPlatF2', 'memPlatF3', 'memPlatF4', 'memPlatF5', 'memPlatF6', 'memPlatF7'];
    platFeatures.forEach((key, i) => {
      const el = document.querySelector(`[data-i18n-mem="platinum.f${i + 1}"]`);
      if (el) el.textContent = t[key];
    });
  }

  // Initial call
  updateLangButtons();
  applyTranslations();

})();
