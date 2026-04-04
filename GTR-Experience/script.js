(function(){
    "use strict";
    const T={
      en:{
        tagline:"Luxury Parking Experience",back:"Home",
        "nav.home":"Home","nav.experience":"Experience","nav.services":"Services","nav.contact":"Contact",
        "exp.hero.kicker":"Signature Standards",
        "exp.hero.sub":"Where every arrival becomes a masterpiece of precision and care",
        "exp.kicker":"Signature Standards","exp.title":"A Curated Arrival Ritual",
        "card1.title":"White-Glove Valet","card1.desc":"Trained attendants welcome every vehicle with precision handling, secure key management, and immaculate presentation.",
        "card2.title":"Vault-Level Security","card2.desc":"Surveillance intelligence, controlled access zones, and premium insurance protection keep your car fully safeguarded.",
        "card3.title":"Seamless Priority Exit","card3.desc":"On-demand retrieval with concierge timing ensures your vehicle is prepared the moment you are ready to depart.",
        "tl.kicker":"Step by Step","tl.title":"Your Arrival, Perfected",
        "tl.s1.tag":"Arrival","tl.s1.title":"Grand Welcome","tl.s1.desc":"You pull up at our signature entrance — no tickets, no confusion. Our uniformed attendant greets you by name, handles your door, and confirms your reservation in seconds.",
        "tl.s2.tag":"Vehicle Intake","tl.s2.title":"Precision Handoff","tl.s2.desc":"A certified attendant performs a 30-point exterior inspection, photographs the vehicle, and places it under secure key custody. Every detail is logged in our concierge system.",
        "tl.s3.tag":"Secure Storage","tl.s3.title":"Vault Placement","tl.s3.desc":"Your vehicle is parked in a designated bay within our climate-controlled facility, monitored by 360° CCTV, motion sensors, and overnight security personnel.",
        "tl.s4.tag":"On-Demand Retrieval","tl.s4.title":"Instant Request","tl.s4.desc":"Text, call, or tap the GTR app. We receive your request and immediately dispatch a technician. Average retrieval time: under 4 minutes from request to engine start.",
        "tl.s5.tag":"Departure","tl.s5.title":"Flawless Exit","tl.s5.desc":"Your car awaits at the priority exit lane — engine running at the ideal temperature, exterior wiped, and seat adjusted to your profile. Leave as you arrived: in total luxury.",
        "amen.kicker":"Exclusive Inclusions","amen.title":"Every Detail Considered",
        "a1.title":"Climate Control","a1.desc":"Temperature-regulated bays protect paint and interiors year-round",
        "a2.title":"EV Fast Charging","a2.desc":"Level 2 & DC rapid chargers in premium designated bays",
        "a3.title":"Exterior Detail","a3.desc":"Complimentary quick-detail wipe on every retrieval",
        "a4.title":"GTR App","a4.desc":"Request, track, and schedule your vehicle from anywhere",
        "a5.title":"Full Insurance","a5.desc":"Comprehensive coverage while your vehicle is in our custody",
        "a6.title":"Live Monitoring","a6.desc":"360° CCTV with 30-day encrypted cloud recording",
        "a7.title":"Reserved Bay","a7.desc":"Your personal bay, always ready — never shared, never occupied",
        "a8.title":"Personal Concierge","a8.desc":"A dedicated agent manages your account preferences and requests",
        "test.kicker":"Client Voices","test.title":"Words From Our Members",
        "t1.text":"\"GTR transformed how I think about parking. It's not a chore anymore — it's the best part of arriving anywhere.\"","t1.role":"CEO, Meridian Capital",
        "t2.text":"\"The 4-minute retrieval promise is real. I've tested it dozens of times and they've never missed. Absolutely world-class.\"","t2.role":"Supercar Collector",
        "t3.text":"\"My Lamborghini has never looked better maintained. The attention to detail from every single attendant is extraordinary.\"","t3.role":"Platinum Member",
        "cta.kicker":"Ready to Elevate?","cta.title":"Begin Your GTR Experience Today",
        "cta.desc":"Join over 300 discerning members who have already elevated their daily arrival into an unforgettable luxury ritual.",
        "cta.btn":"Reserve Your Space"
      },
      es:{
        tagline:"Experiencia de Estacionamiento de Lujo",back:"Inicio",
        "nav.home":"Inicio","nav.experience":"Experiencia","nav.services":"Servicios","nav.contact":"Contacto",
        "exp.hero.kicker":"Estándares de Firma",
        "exp.hero.sub":"Donde cada llegada se convierte en una obra maestra de precisión y cuidado",
        "exp.kicker":"Estándares de Firma","exp.title":"Un Ritual de Llegada Curado",
        "card1.title":"Valet de Guante Blanco","card1.desc":"Asistentes capacitados reciben cada vehículo con manejo de precisión, gestión segura de llaves y presentación impecable.",
        "card2.title":"Seguridad de Nivel Bóveda","card2.desc":"Inteligencia de vigilancia, zonas de acceso controlado y protección de seguro premium mantienen su auto completamente resguardado.",
        "card3.title":"Salida Prioritaria Perfecta","card3.desc":"Recuperación bajo demanda garantiza que su vehículo esté listo en el momento en que desee partir.",
        "tl.kicker":"Paso a Paso","tl.title":"Su Llegada, Perfeccionada",
        "tl.s1.tag":"Llegada","tl.s1.title":"Bienvenida de Gala","tl.s1.desc":"Llega a nuestra entrada insignia — sin boletos, sin confusión. Nuestro asistente uniformado lo saluda por su nombre, abre su puerta y confirma su reserva en segundos.",
        "tl.s2.tag":"Recepción del Vehículo","tl.s2.title":"Entrega de Precisión","tl.s2.desc":"Un asistente certificado realiza una inspección exterior de 30 puntos, fotografía el vehículo y lo coloca bajo custodia segura de llaves. Cada detalle queda registrado.",
        "tl.s3.tag":"Almacenamiento Seguro","tl.s3.title":"Ubicación en Bóveda","tl.s3.desc":"Su vehículo se estaciona en una bahía designada dentro de nuestra instalación climatizada, vigilada por CCTV 360°, sensores de movimiento y personal de seguridad nocturno.",
        "tl.s4.tag":"Recuperación Bajo Demanda","tl.s4.title":"Solicitud Instantánea","tl.s4.desc":"Mensaje, llamada o toque en la app GTR. Recibimos su solicitud y despachamos un técnico de inmediato. Tiempo promedio de recuperación: menos de 4 minutos.",
        "tl.s5.tag":"Partida","tl.s5.title":"Salida Impecable","tl.s5.desc":"Su auto le espera en el carril de salida prioritaria — motor en temperatura ideal, exterior limpiado y asiento ajustado a su perfil. Parta como llegó: en total lujo.",
        "amen.kicker":"Inclusiones Exclusivas","amen.title":"Cada Detalle Considerado",
        "a1.title":"Control de Clima","a1.desc":"Bahías con temperatura regulada protegen pintura e interiores todo el año",
        "a2.title":"Carga EV Rápida","a2.desc":"Cargadores Nivel 2 y DC rápidos en bahías premium designadas",
        "a3.title":"Detallado Exterior","a3.desc":"Limpieza rápida de cortesía en cada recuperación del vehículo",
        "a4.title":"App GTR","a4.desc":"Solicite, rastree y programe su vehículo desde cualquier lugar",
        "a5.title":"Seguro Completo","a5.desc":"Cobertura integral mientras su vehículo está bajo nuestra custodia",
        "a6.title":"Monitoreo en Vivo","a6.desc":"CCTV 360° con grabación cifrada en nube por 30 días",
        "a7.title":"Bahía Reservada","a7.desc":"Su bahía personal, siempre lista — nunca compartida, nunca ocupada",
        "a8.title":"Conserje Personal","a8.desc":"Un agente dedicado gestiona sus preferencias y solicitudes de cuenta",
        "test.kicker":"Voces de Clientes","test.title":"Palabras de Nuestros Miembros",
        "t1.text":"\"GTR transformó mi perspectiva del estacionamiento. Ya no es una molestia — es la mejor parte de llegar a cualquier lugar.\"","t1.role":"CEO, Meridian Capital",
        "t2.text":"\"La promesa de recuperación en 4 minutos es real. La he probado docenas de veces y nunca han fallado. Absolutamente de clase mundial.\"","t2.role":"Coleccionista de Superautos",
        "t3.text":"\"Mi Lamborghini nunca ha lucido mejor mantenido. La atención al detalle de cada asistente es extraordinaria.\"","t3.role":"Miembro Platinum",
        "cta.kicker":"¿Listo para Elevarse?","cta.title":"Comienza Tu Experiencia GTR Hoy",
        "cta.desc":"Únete a más de 300 miembros exigentes que ya han elevado su llegada diaria a un ritual de lujo inolvidable.",
        "cta.btn":"Reservar Su Espacio"
      }
    };

    const yr=document.getElementById("year");
    if(yr) yr.textContent=new Date().getFullYear();

    const btnEN=document.getElementById("langEN"),btnES=document.getElementById("langES");
    function applyLang(lang){
      const d=T[lang];if(!d)return;
      document.documentElement.lang=lang;
      document.querySelectorAll("[data-i18n]").forEach(el=>{const k=el.getAttribute("data-i18n");if(d[k]!==undefined)el.textContent=d[k];});
      btnEN.classList.toggle("lang-btn--active",lang==="en");btnES.classList.toggle("lang-btn--active",lang==="es");
      btnEN.setAttribute("aria-pressed",String(lang==="en"));btnES.setAttribute("aria-pressed",String(lang==="es"));
      try{localStorage.setItem("gtrLang",lang);}catch(_){}
    }
    btnEN.addEventListener("click",()=>applyLang("en"));
    btnES.addEventListener("click",()=>applyLang("es"));
    let saved="";try{saved=localStorage.getItem("gtrLang")||"";}catch(_){}
    if(!saved)saved=navigator.language&&navigator.language.toLowerCase().startsWith("es")?"es":"en";
    applyLang(saved);

    const hdr=document.getElementById("siteHeader");
    window.addEventListener("scroll",()=>hdr.classList.toggle("scrolled",window.scrollY>60),{passive:true});

    const tog=document.getElementById("navToggle"),nav=document.getElementById("navLinks");
    tog.addEventListener("click",()=>{const o=tog.classList.toggle("open");nav.classList.toggle("open");tog.setAttribute("aria-expanded",String(o));});
    nav.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>{tog.classList.remove("open");nav.classList.remove("open");tog.setAttribute("aria-expanded","false");}));

    const obs=new IntersectionObserver((entries,o)=>{entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add("is-visible");o.unobserve(e.target);}});},{threshold:.14,rootMargin:"0px 0px -6% 0px"});
    document.querySelectorAll(".reveal").forEach(el=>obs.observe(el));

    /* Cursor */
    const dot=document.getElementById("cursorDot"),ring=document.getElementById("cursorRing");
    if(window.matchMedia("(pointer:fine)").matches&&dot&&ring){
      let mx=-200,my=-200,rx=-200,ry=-200,raf;
      const tick=()=>{rx+=(mx-rx)*.12;ry+=(my-ry)*.12;dot.style.left=mx+"px";dot.style.top=my+"px";ring.style.left=Math.round(rx)+"px";ring.style.top=Math.round(ry)+"px";raf=requestAnimationFrame(tick);};
      tick();
      document.addEventListener("mousemove",e=>{mx=e.clientX;my=e.clientY;document.body.classList.remove("c-out");});
      document.addEventListener("mouseleave",()=>document.body.classList.add("c-out"));
      document.addEventListener("mouseenter",()=>document.body.classList.remove("c-out"));
      const iSel="a,button,[role='button'],.feature-card,.amenity,.testimonial,.lang-btn";
      document.addEventListener("mouseover",e=>{if(e.target.closest(iSel))document.body.classList.add("c-hover");});
      document.addEventListener("mouseout",e=>{if(e.target.closest(iSel))document.body.classList.remove("c-hover");});
      document.addEventListener("mousedown",()=>document.body.classList.add("c-click"));
      document.addEventListener("mouseup",()=>document.body.classList.remove("c-click"));
      document.addEventListener("visibilitychange",()=>{if(document.hidden)cancelAnimationFrame(raf);else tick();});
    }

    /* Particles */
    const canvas=document.getElementById("luxuryParticles");
    if(canvas&&!window.matchMedia("(prefers-reduced-motion:reduce)").matches){
      const ctx=canvas.getContext("2d"),dpr=window.devicePixelRatio||1;
      let W=0,H=0,pts=[],aid;
      class P{constructor(){this.reset();this.x=Math.random()*W;this.y=Math.random()*H;}reset(){this.r=.4+Math.random()*1.6;this.a=.07+Math.random()*.32;this.vx=(Math.random()-.5)*.26;this.vy=(Math.random()-.5)*.26;}update(){this.x+=this.vx;this.y+=this.vy;if(this.x<-5)this.x=W+5;if(this.x>W+5)this.x=-5;if(this.y<-5)this.y=H+5;if(this.y>H+5)this.y=-5;}draw(c){c.beginPath();c.arc(this.x,this.y,this.r,0,Math.PI*2);c.fillStyle=`rgba(212,175,55,${this.a})`;c.fill();}}
      function resize(){W=window.innerWidth;H=window.innerHeight;canvas.width=Math.floor(W*dpr);canvas.height=Math.floor(H*dpr);canvas.style.width=W+"px";canvas.style.height=H+"px";ctx.setTransform(dpr,0,0,dpr,0,0);pts=Array.from({length:Math.min(80,Math.max(30,Math.floor(W/22)))},()=>new P());}
      function frame(){ctx.clearRect(0,0,W,H);pts.forEach(p=>{p.update();p.draw(ctx);});for(let i=0;i<pts.length;i++)for(let j=i+1;j<pts.length;j++){const dx=pts[i].x-pts[j].x,dy=pts[i].y-pts[j].y,d=Math.sqrt(dx*dx+dy*dy);if(d<85){ctx.strokeStyle=`rgba(212,175,55,${(1-d/85)*.09})`;ctx.lineWidth=.5;ctx.beginPath();ctx.moveTo(pts[i].x,pts[i].y);ctx.lineTo(pts[j].x,pts[j].y);ctx.stroke();}}aid=requestAnimationFrame(frame);}
      resize();frame();window.addEventListener("resize",resize);document.addEventListener("visibilitychange",()=>{if(document.hidden)cancelAnimationFrame(aid);else frame();});
    }
  })();