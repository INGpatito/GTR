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

})();
