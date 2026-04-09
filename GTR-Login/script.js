/* ── INLINE SCRIPT FOR SELF-CONTAINED PAGE ─────────── */
    (function () {
      "use strict";

      /*  Translations */
      const T = {
        en: {
          tagline: "Luxury Parking Experience",
          "nav.home": "Home", "nav.experience": "Experience", "nav.services": "Services", "nav.contact": "Contact",
          "contact.kicker": "Private Access",
          "page.subtitle": "Every journey begins with a single reservation",
          "exp.kicker": "Signature Standards", "exp.title": "A Curated Arrival Ritual",
          "card1.title": "White-Glove Valet",
          "card1.desc": "Trained attendants welcome every vehicle with precision handling, secure key management, and immaculate presentation.",
          "card2.title": "Vault-Level Security",
          "card2.desc": "Surveillance intelligence, controlled access zones, and premium insurance protection keep your car fully safeguarded.",
          "card3.title": "Seamless Priority Exit",
          "card3.desc": "On-demand retrieval with concierge timing ensures your vehicle is prepared the moment you are ready to depart.",
          "login.kicker": "Private Access", "login.title": "Access Your Dashboard", "login.submit": "Enter Vault",
          "tab.login": "Sign In", "tab.register": "Register", 
          "register.title": "Create an Account", "register.submit": "Complete Registration",
          "form.kicker": "Reserve Your Space", "form.title": "Get In Touch", "form.heading": "Make a Reservation",
          "info.kicker": "Contact Information", "info.title": "Let Us Elevate Your Arrival",
          "info.desc": "Our concierge team is available around the clock to assist with reservations, memberships, and any special requirements for your vehicle.",
          "info.phoneLabel": "Phone", "info.emailLabel": "Email", "info.addressLabel": "Location",
          "info.address": "Elite District, Premium Avenue, Suite 1",
          "info.hoursLabel": "Hours", "info.hours": "24 / 7 — 365 days",
          "form.name": "Full Name", "form.email": "Email Address", "form.phone": "Phone",
          "form.password": "Password", "form.newpassword": "Create Password",
          "form.service": "Subscription Tier", "form.selectTier": "Select a tier…",
          "form.opt.valet": "Standard Valet (Pay per Use)", "form.opt.monthly": "Monthly Membership",
          "form.opt.event": "Event VIP Pass", "form.opt.concierge": "Concierge Priority (Annual)", "form.opt.fleet": "Corporate Fleet",
          "form.vehicle": "Vehicle Classification",
          "form.veh.sports": "🏎 Sports", "form.veh.suv": "🚙 Luxury SUV", "form.veh.sedan": "🚗 Premium Sedan",
          "form.veh.convertible": "🚘 Convertible", "form.veh.exotic": "✨ Exotic/Hypercar",
          "form.date": "Arrival Date", "form.time": "Arrival Time", "form.message": "Special Requests",
          "form.submit": "Send Reservation Request",
          "form.success": "Your membership application is under review. Please wait for our concierge to contact you.",
          "back": "Home"
        },
        es: {
          tagline: "Experiencia de Estacionamiento de Lujo",
          "nav.home": "Inicio", "nav.experience": "Experiencia", "nav.services": "Servicios", "nav.contact": "Contacto",
          "contact.kicker": "Acceso Privado",
          "page.subtitle": "Todo viaje comienza con una sola reserva",
          "exp.kicker": "Estándares de Firma", "exp.title": "Un Ritual de Llegada Curado",
          "card1.title": "Valet de Guante Blanco",
          "card1.desc": "Asistentes capacitados reciben cada vehículo con manejo de precisión, gestión segura de llaves y presentación impecable.",
          "card2.title": "Seguridad de Nivel Bóveda",
          "card2.desc": "Inteligencia de vigilancia, zonas de acceso controlado y protección de seguro premium mantienen su auto completamente resguardado.",
          "card3.title": "Salida Prioritaria Perfecta",
          "card3.desc": "Recuperación bajo demanda con tiempos de conserje garantiza que su vehículo esté listo en el momento en que desee partir.",
          "login.kicker": "Acceso Privado", "login.title": "Accede a tu Panel", "login.submit": "Entrar a Bóveda",
          "tab.login": "Iniciar Sesión", "tab.register": "Registro",
          "register.title": "Crear una Cuenta", "register.submit": "Completar Registro",
          "form.kicker": "Reserve Su Espacio", "form.title": "Contáctenos", "form.heading": "Hacer una Reserva",
          "info.kicker": "Información de Contacto", "info.title": "Permítanos Elevar Su Llegada",
          "info.desc": "Nuestro equipo de conserje está disponible las 24 horas para asistirle con reservas, membresías y cualquier requisito especial para su vehículo.",
          "info.phoneLabel": "Teléfono", "info.emailLabel": "Correo", "info.addressLabel": "Ubicación",
          "info.address": "Distrito Elite, Avenida Premium, Suite 1",
          "info.hoursLabel": "Horario", "info.hours": "24 / 7 — 365 días",
          "form.name": "Nombre Completo", "form.email": "Correo Electrónico", "form.phone": "Teléfono",
          "form.password": "Contraseña", "form.newpassword": "Crear Contraseña",
          "form.service": "Nivel de Suscripción", "form.selectTier": "Seleccione un nivel…",
          "form.opt.valet": "Valet Estándar (Pago por Uso)", "form.opt.monthly": "Membresía Mensual",
          "form.opt.event": "Pase VIP para Eventos", "form.opt.concierge": "Prioridad Conserje (Anual)", "form.opt.fleet": "Flota / Corporativo",
          "form.vehicle": "Clasificación de Vehículo",
          "form.veh.sports": "🏎 Deportivo", "form.veh.suv": "🚙 SUV de Lujo", "form.veh.sedan": "🚗 Sedán Premium",
          "form.veh.convertible": "🚘 Convertible", "form.veh.exotic": "✨ Exótico / Hipercoche",
          "form.date": "Fecha de Llegada", "form.time": "Hora de Llegada", "form.message": "Solicitudes Especiales",
          "form.submit": "Enviar Solicitud de Reserva",
          "form.success": "Su solicitud de membresía está bajo revisión. Por favor, espere a que nuestro conserje lo contacte.",
          "back": "Inicio"
        }
      };

      /* ── Year ── */
      const yearEl = document.getElementById("year");
      if (yearEl) yearEl.textContent = new Date().getFullYear();

      /* ── i18n ── */
      const btnEN = document.getElementById("langEN");
      const btnES = document.getElementById("langES");

      function applyLang(lang) {
        const dict = T[lang]; if (!dict) return;
        document.documentElement.lang = lang;
        document.querySelectorAll("[data-i18n]").forEach(el => {
          const k = el.getAttribute("data-i18n");
          if (dict[k] !== undefined) el.textContent = dict[k];
        });
        btnEN.classList.toggle("lang-btn--active", lang === "en");
        btnES.classList.toggle("lang-btn--active", lang === "es");
        btnEN.setAttribute("aria-pressed", String(lang === "en"));
        btnES.setAttribute("aria-pressed", String(lang === "es"));
        try { localStorage.setItem("gtrLang", lang); } catch (_) { }
      }

      btnEN.addEventListener("click", () => applyLang("en"));
      btnES.addEventListener("click", () => applyLang("es"));

      let saved = "";
      try { saved = localStorage.getItem("gtrLang") || ""; } catch (_) { }
      if (!saved) saved = navigator.language && navigator.language.toLowerCase().startsWith("es") ? "es" : "en";
      applyLang(saved);

      /* ── Header scroll ── */
      const header = document.getElementById("siteHeader");
      window.addEventListener("scroll", () => {
        header.classList.toggle("scrolled", window.scrollY > 60);
      }, { passive: true });

      /* ── Mobile nav ── */
      const toggle = document.getElementById("navToggle");
      const nav = document.getElementById("navLinks");
      toggle.addEventListener("click", () => {
        const open = toggle.classList.toggle("open");
        nav.classList.toggle("open");
        toggle.setAttribute("aria-expanded", String(open));
      });
      nav.querySelectorAll("a").forEach(a => a.addEventListener("click", () => {
        toggle.classList.remove("open"); nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }));

      /* ── Scroll reveal ── */
      const reveals = Array.from(document.querySelectorAll(".reveal"));
      const revObs = new IntersectionObserver((entries, obs) => {
        entries.forEach(e => {
          if (e.isIntersecting) { e.target.classList.add("is-visible"); obs.unobserve(e.target); }
        });
      }, { threshold: 0.15, rootMargin: "0px 0px -6% 0px" });
      reveals.forEach(el => revObs.observe(el));

      /* ── Tabs JS ── */
      const btnTabLogin = document.getElementById("tab-login");
      const btnTabRegister = document.getElementById("tab-register");
      const panelLogin = document.getElementById("panel-login");
      const panelRegister = document.getElementById("panel-register");

      btnTabLogin.addEventListener("click", () => {
        btnTabLogin.classList.add("active");
        btnTabRegister.classList.remove("active");
        panelLogin.classList.add("active");
        panelRegister.classList.remove("active");
      });

      btnTabRegister.addEventListener("click", () => {
        btnTabRegister.classList.add("active");
        btnTabLogin.classList.remove("active");
        panelRegister.classList.add("active");
        panelLogin.classList.remove("active");
      });

      /* ── API config ── */
      const API_URL = "/api/reservations";
      const LOGIN_URL = "/api/login";

      /* ── Login Form ── */
      const loginForm = document.getElementById("loginForm");
      loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const btn = document.getElementById("btnLoginSubmit");
        const email = loginForm.querySelector("#loginEmail").value.trim();
        const password = loginForm.querySelector("#loginPass").value;
        const lang = document.documentElement.lang || "en";
        
        if (!email || !password) return;
        
        btn.disabled = true;
        const origText = btn.querySelector("span").textContent;
        btn.querySelector("span").textContent = lang === "es" ? "Verificando…" : "Verifying…";
        btn.style.opacity = "0.7";
        
        try {
          const res = await fetch(LOGIN_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
          });
          const data = await res.json();
          if (res.ok && data.success) {
            if (data.status !== "completed") {
              alert(lang === "es" ? "Pronto abriremos tu Portal de Cliente. Por favor espera a que aprobemos tu membresía." : "Client Portal coming soon. Please wait for membership approval.");
              btn.disabled = false;
              btn.style.opacity = "1";
              btn.querySelector("span").textContent = origText;
              return;
            }
            sessionStorage.setItem("gtr_user_id", data.id);
            sessionStorage.setItem("gtr_token", data.token);
            window.location.href = "../GTR-Profile/index.html";
          } else {
            alert(data.errors?.join(". ") || (lang === "es" ? "Credenciales inválidas." : "Invalid credentials."));
            btn.disabled = false;
            btn.style.opacity = "1";
            btn.querySelector("span").textContent = origText;
          }
        } catch (err) {
          alert(lang === "es" ? "Error de conexión." : "Connection error.");
          btn.disabled = false;
          btn.style.opacity = "1";
          btn.querySelector("span").textContent = origText;
        }
      });

      /* ── Form submit ── */
      const form = document.getElementById("contactForm");
      const toast = document.getElementById("formToast");

      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const btn = document.getElementById("btnSubmit");

        // Gather values
        const name = form.querySelector("#inputName").value.trim();
        const email = form.querySelector("#inputEmail").value.trim();
        const phone = form.querySelector("#inputPhone").value.trim();
        const service = form.querySelector("#inputService").value;
        const vehicle = form.querySelector("input[name='vehicle']:checked")?.value || "sports";
        const date = form.querySelector("#inputDate").value;
        const time = form.querySelector("#inputTime").value;
        const message = form.querySelector("#inputMsg").value.trim();
        const password = form.querySelector("#inputRegisterPass").value;
        const lang = document.documentElement.lang || "en";

        // Client-side validation
        let valid = true;
        [form.querySelector("#inputName"), form.querySelector("#inputEmail")].forEach(el => {
          el.style.borderColor = "";
        });
        if (!name || name.length < 2) {
          form.querySelector("#inputName").style.borderColor = "#e74c3c";
          valid = false;
        }
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
          form.querySelector("#inputEmail").style.borderColor = "#e74c3c";
          valid = false;
        }
        if (!valid) return;

        // Loading state
        btn.disabled = true;
        const origText = btn.querySelector("span").textContent;
        btn.querySelector("span").textContent = lang === "es" ? "Enviando…" : "Sending…";
        btn.style.opacity = "0.7";

        try {
          const res = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, phone, service, vehicle, date, time, message, lang, password }),
          });

          const data = await res.json();

          if (res.ok && data.success) {
            if (data.reservation.status !== "completed") {
               alert(lang === "es" ? "Solicitud recibida correctamente. Por favor, espera a que nuestros administradores validen tu perfil mediante el Panel de Seguridad." : "Application received successfully. Please wait for an administrator to authorise your profile.");
               btn.disabled = false;
               btn.style.opacity = "1";
               btn.querySelector("span").textContent = origText;
               form.reset();
               return;
            }
            // Guardamos el ID en la sesión y redirigimos si por casualidad ya estaba completado
            sessionStorage.setItem("gtr_user_id", data.reservation.id);
            if (data.token) sessionStorage.setItem("gtr_token", data.token);
            window.location.href = "../GTR-Profile/index.html";
            return;
          } else {
            toast.classList.add("error", "visible");
            const errSpan = toast.querySelector("[data-i18n='form.success']");
            errSpan.textContent = data.errors?.join(". ") || (lang === "es" ? "Error al enviar. Intente de nuevo." : "Error sending. Please try again.");
          }

          toast.scrollIntoView({ behavior: "smooth", block: "nearest" });

        } catch (err) {
          toast.classList.add("error", "visible");
          const errSpan = toast.querySelector("[data-i18n='form.success']");
          errSpan.textContent = lang === "es"
            ? "No se pudo conectar al servidor. Intente más tarde."
            : "Could not connect to server. Please try later.";
          toast.scrollIntoView({ behavior: "smooth", block: "nearest" });
        } finally {
          btn.disabled = false;
          btn.style.opacity = "1";
          btn.querySelector("span").textContent = origText;
        }
      });

      /* ── Custom cursor ── */
      const dot = document.getElementById("cursorDot");
      const ring = document.getElementById("cursorRing");
      const hasFine = window.matchMedia("(pointer: fine)").matches;
      if (hasFine && dot && ring) {
        let mx = -200, my = -200, rx = -200, ry = -200, raf;
        const tick = () => {
          rx += (mx - rx) * 0.12; ry += (my - ry) * 0.12;
          dot.style.left = mx + "px"; dot.style.top = my + "px";
          ring.style.left = Math.round(rx) + "px"; ring.style.top = Math.round(ry) + "px";
          raf = requestAnimationFrame(tick);
        };
        tick();
        document.addEventListener("mousemove", e => { mx = e.clientX; my = e.clientY; document.body.classList.remove("c-out"); });
        document.addEventListener("mouseleave", () => document.body.classList.add("c-out"));
        document.addEventListener("mouseenter", () => document.body.classList.remove("c-out"));
        const iSel = "a,button,[role='button'],input,select,textarea,.feature-card,.lang-btn";
        document.addEventListener("mouseover", e => { if (e.target.closest(iSel)) document.body.classList.add("c-hover"); });
        document.addEventListener("mouseout", e => { if (e.target.closest(iSel)) document.body.classList.remove("c-hover"); });
        document.addEventListener("mousedown", () => document.body.classList.add("c-click"));
        document.addEventListener("mouseup", () => document.body.classList.remove("c-click"));
        document.addEventListener("visibilitychange", () => { if (document.hidden) cancelAnimationFrame(raf); else tick(); });
      }

      /* ── Particles ── */
      const canvas = document.getElementById("luxuryParticles");
      if (canvas && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        const ctx = canvas.getContext("2d");
        const dpr = window.devicePixelRatio || 1;
        let W = 0, H = 0, pts = [], animId;
        class Pt {
          constructor() { this.reset(); this.x = Math.random() * W; this.y = Math.random() * H; }
          reset() { this.r = 0.4 + Math.random() * 1.6; this.a = 0.07 + Math.random() * 0.32; this.vx = (Math.random() - .5) * .26; this.vy = (Math.random() - .5) * .26; }
          update() {
            this.x += this.vx; this.y += this.vy;
            if (this.x < -5) this.x = W + 5; if (this.x > W + 5) this.x = -5;
            if (this.y < -5) this.y = H + 5; if (this.y > H + 5) this.y = -5;
          }
          draw(c) { c.beginPath(); c.arc(this.x, this.y, this.r, 0, Math.PI * 2); c.fillStyle = `rgba(212,175,55,${this.a})`; c.fill(); }
        }
        function resize() {
          W = window.innerWidth; H = window.innerHeight;
          canvas.width = Math.floor(W * dpr); canvas.height = Math.floor(H * dpr);
          canvas.style.width = W + "px"; canvas.style.height = H + "px";
          ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
          pts = Array.from({ length: Math.min(80, Math.max(32, Math.floor(W / 22))) }, () => new Pt());
        }
        function frame() {
          ctx.clearRect(0, 0, W, H);
          pts.forEach(p => { p.update(); p.draw(ctx); });
          for (let i = 0; i < pts.length; i++) for (let j = i + 1; j < pts.length; j++) {
            const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y, d = Math.sqrt(dx * dx + dy * dy);
            if (d < 85) { ctx.strokeStyle = `rgba(212,175,55,${(1 - d / 85) * .09})`; ctx.lineWidth = .5; ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y); ctx.stroke(); }
          }
          animId = requestAnimationFrame(frame);
        }
        resize(); frame();
        window.addEventListener("resize", resize);
        document.addEventListener("visibilitychange", () => { if (document.hidden) cancelAnimationFrame(animId); else frame(); });
      }

    })();