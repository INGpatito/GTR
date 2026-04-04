(function(){
    "use strict";
    const T={
      en:{
        tagline:"Luxury Parking Experience",
        "nav.home":"Home","nav.experience":"Experience","nav.services":"Services","nav.contact":"Contact",
        "svc.kicker":"Premium Portfolio","svc.sub":"Crafted for the elite. Designed for the exceptional.",
        "cat.kicker":"Full Spectrum","cat.title":"Everything You Need, Nothing You Don't",
        "s1.title":"White-Glove Valet","s1.desc":"Our uniformed attendants greet you at the entrance, handle your vehicle with expert care, and deliver it back spotless on demand.",
        "s2.title":"Vault-Level Security","s2.desc":"360° CCTV surveillance, biometric access control, and dedicated security personnel protect your asset around the clock.",
        "s3.title":"Priority Concierge Exit","s3.desc":"Request retrieval via app, call, or text. Your vehicle is brought to the exit lane within minutes, engine warm and ready.",
        "s4.title":"Fleet & Corporate","s4.desc":"Tailored multi-vehicle accounts for executives and enterprises. Centralized billing, dedicated bays, and a personal account manager.",
        "s5.title":"EV Charging Bays","s5.desc":"Level 2 and DC fast-charging stations available in designated premium bays — charge while you work, dine, or shop.",
        "s6.title":"Event & Special Occasion","s6.desc":"Exclusive reserved lots for galas, premieres, and private events. Coordinated logistics and live queue management included.",
        "tag.signature":"Signature Service","tag.core":"Core Benefit","tag.onDemand":"On-Demand","tag.corporate":"Corporate","tag.green":"Eco Premium","tag.exclusive":"Exclusive",
        "showcase.kicker":"Designed For Prestige","showcase.title":"Where Automotive Elegance Meets Absolute Convenience",
        "showcase.desc":"Parking GTR is crafted for owners who value discretion, speed, and premium treatment. From supercars to executive fleets, every arrival is elevated into a refined brand experience.",
        "showcase.cta":"Request Membership",
        "stat1":"Concierge Coverage","stat2":"Luxury Spots","stat3":"Client Satisfaction","stat4":"Premium Services",
        "plans.kicker":"Membership Tiers","plans.title":"Choose Your Level of Prestige",
        "plan.mo":"/mo","plan.popular":"Most Popular","plan.cta.start":"Get Started","plan.cta.choose":"Choose Gold","plan.cta.elite":"Join Platinum",
        "plan1.name":"Silver Access","plan1.desc":"Perfect for the discerning driver who visits multiple times a week.",
        "plan1.f1":"Standard valet service","plan1.f2":"Up to 12 visits/month","plan1.f3":"Covered parking bay","plan1.f4":"Mobile app retrieval","plan1.f5":"24/7 support line",
        "plan2.name":"Gold Prestige","plan2.desc":"The preferred choice for executives and enthusiasts who demand excellence daily.",
        "plan2.f1":"Unlimited white-glove valet","plan2.f2":"Dedicated reserved bay","plan2.f3":"Priority express exit","plan2.f4":"EV charging included","plan2.f5":"Exterior detailing (2×/mo)","plan2.f6":"Dedicated account manager",
        "plan3.name":"Platinum Elite","plan3.desc":"The ultimate GTR experience — limitless, uncompromising, bespoke.",
        "plan3.f1":"Everything in Gold","plan3.f2":"Multi-vehicle coverage (up to 3)","plan3.f3":"Full interior & exterior detail (4×/mo)","plan3.f4":"VIP event parking access","plan3.f5":"Chauffeur coordination","plan3.f6":"Concierge personal assistant","plan3.f7":"Premium insurance coverage",
        "metric1":"/ 7 Concierge Coverage","metric2":"+ Luxury Spots","metric3":"Client Satisfaction","metric4":"% Retention Rate",
        "back":"Home"
      },
      es:{
        tagline:"Experiencia de Estacionamiento de Lujo",
        "nav.home":"Inicio","nav.experience":"Experiencia","nav.services":"Servicios","nav.contact":"Contacto",
        "svc.kicker":"Portafolio Premium","svc.sub":"Creado para la élite. Diseñado para lo excepcional.",
        "cat.kicker":"Espectro Completo","cat.title":"Todo lo que Necesitas, Nada que No Necesitas",
        "s1.title":"Valet de Guante Blanco","s1.desc":"Nuestros asistentes uniformados lo reciben en la entrada, manejan su vehículo con cuidado experto y lo entregan impecable cuando usted lo solicite.",
        "s2.title":"Seguridad de Nivel Bóveda","s2.desc":"Vigilancia CCTV 360°, control de acceso biométrico y personal de seguridad dedicado protegen su activo las 24 horas.",
        "s3.title":"Salida Prioritaria Concierge","s3.desc":"Solicite la recuperación por app, llamada o mensaje. Su vehículo estará en la rampa de salida en minutos, con el motor encendido y listo.",
        "s4.title":"Flota y Corporativo","s4.desc":"Cuentas multivehículo personalizadas para ejecutivos y empresas. Facturación centralizada, bahías dedicadas y un administrador de cuenta personal.",
        "s5.title":"Bahías de Carga EV","s5.desc":"Estaciones de carga Nivel 2 y DC rápidas disponibles en bahías premium designadas — cargue mientras trabaja, come o compra.",
        "s6.title":"Eventos y Ocasiones Especiales","s6.desc":"Lotes reservados exclusivos para galas, estrenos y eventos privados. Logística coordinada y gestión de filas en tiempo real incluidas.",
        "tag.signature":"Servicio Firma","tag.core":"Beneficio Principal","tag.onDemand":"Bajo Demanda","tag.corporate":"Corporativo","tag.green":"Eco Premium","tag.exclusive":"Exclusivo",
        "showcase.kicker":"Diseñado Para el Prestigio","showcase.title":"Donde la Elegancia Automotriz se Une a la Conveniencia Absoluta",
        "showcase.desc":"Parking GTR está creado para propietarios que valoran la discreción, la velocidad y el trato premium. Desde superautos hasta flotas ejecutivas, cada llegada se eleva a una experiencia de marca refinada.",
        "showcase.cta":"Solicitar Membresía",
        "stat1":"Cobertura de Conserje","stat2":"Lugares de Lujo","stat3":"Satisfacción del Cliente","stat4":"Servicios Premium",
        "plans.kicker":"Niveles de Membresía","plans.title":"Elige Tu Nivel de Prestigio",
        "plan.mo":"/mes","plan.popular":"Más Popular","plan.cta.start":"Comenzar","plan.cta.choose":"Elegir Gold","plan.cta.elite":"Unirse al Platinum",
        "plan1.name":"Acceso Silver","plan1.desc":"Perfecto para el conductor exigente que visita varias veces por semana.",
        "plan1.f1":"Servicio de valet estándar","plan1.f2":"Hasta 12 visitas/mes","plan1.f3":"Bahía de estacionamiento cubierta","plan1.f4":"Recuperación por app móvil","plan1.f5":"Línea de soporte 24/7",
        "plan2.name":"Prestigio Gold","plan2.desc":"La opción preferida de ejecutivos y entusiastas que exigen excelencia a diario.",
        "plan2.f1":"Valet de guante blanco ilimitado","plan2.f2":"Bahía reservada dedicada","plan2.f3":"Salida exprés prioritaria","plan2.f4":"Carga EV incluida","plan2.f5":"Detallado exterior (2×/mes)","plan2.f6":"Administrador de cuenta dedicado",
        "plan3.name":"Élite Platinum","plan3.desc":"La experiencia GTR definitiva — ilimitada, sin compromisos, a medida.",
        "plan3.f1":"Todo lo de Gold","plan3.f2":"Cobertura multivehículo (hasta 3)","plan3.f3":"Detallado interior y exterior completo (4×/mes)","plan3.f4":"Acceso a estacionamiento VIP en eventos","plan3.f5":"Coordinación de chofer","plan3.f6":"Asistente personal conserje","plan3.f7":"Cobertura de seguro premium",
        "metric1":"/ 7 Cobertura de Conserje","metric2":"+ Lugares de Lujo","metric3":"Satisfacción del Cliente","metric4":"% Tasa de Retención",
        "back":"Inicio"
      }
    };

    /* Year */
    const yr=document.getElementById("year");
    if(yr) yr.textContent=new Date().getFullYear();

    /* i18n */
    const btnEN=document.getElementById("langEN");
    const btnES=document.getElementById("langES");
    function applyLang(lang){
      const d=T[lang]; if(!d) return;
      document.documentElement.lang=lang;
      document.querySelectorAll("[data-i18n]").forEach(el=>{
        const k=el.getAttribute("data-i18n");
        if(d[k]!==undefined) el.textContent=d[k];
      });
      btnEN.classList.toggle("lang-btn--active",lang==="en");
      btnES.classList.toggle("lang-btn--active",lang==="es");
      btnEN.setAttribute("aria-pressed",String(lang==="en"));
      btnES.setAttribute("aria-pressed",String(lang==="es"));
      try{localStorage.setItem("gtrLang",lang);}catch(_){}
    }
    btnEN.addEventListener("click",()=>applyLang("en"));
    btnES.addEventListener("click",()=>applyLang("es"));
    let saved="";
    try{saved=localStorage.getItem("gtrLang")||"";}catch(_){}
    if(!saved) saved=navigator.language&&navigator.language.toLowerCase().startsWith("es")?"es":"en";
    applyLang(saved);

    /* Header scroll */
    const hdr=document.getElementById("siteHeader");
    window.addEventListener("scroll",()=>hdr.classList.toggle("scrolled",window.scrollY>60),{passive:true});

    /* Mobile nav */
    const tog=document.getElementById("navToggle"),nav=document.getElementById("navLinks");
    tog.addEventListener("click",()=>{const o=tog.classList.toggle("open");nav.classList.toggle("open");tog.setAttribute("aria-expanded",String(o));});
    nav.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>{tog.classList.remove("open");nav.classList.remove("open");tog.setAttribute("aria-expanded","false");}));

    /* Reveal */
    const obs=new IntersectionObserver((entries,o)=>{entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add("is-visible");o.unobserve(e.target);}});},{threshold:.14,rootMargin:"0px 0px -6% 0px"});
    document.querySelectorAll(".reveal").forEach(el=>obs.observe(el));

    /* Counters */
    const cObs=new IntersectionObserver((entries,o)=>{entries.forEach(e=>{if(e.isIntersecting){animCount(e.target);o.unobserve(e.target);}});},{threshold:.5});
    document.querySelectorAll(".counter").forEach(el=>cObs.observe(el));
    function animCount(el){
      const target=parseInt(el.getAttribute("data-target"),10);
      const start=performance.now();
      const dur=1800;
      (function tick(now){
        const p=Math.min((now-start)/dur,1);
        el.textContent=Math.round((1-Math.pow(1-p,3))*target);
        if(p<1) requestAnimationFrame(tick);
      })(start);
    }

    /* Custom cursor */
    const dot=document.getElementById("cursorDot"),ring=document.getElementById("cursorRing");
    if(window.matchMedia("(pointer:fine)").matches&&dot&&ring){
      let mx=-200,my=-200,rx=-200,ry=-200,raf;
      const tick=()=>{rx+=(mx-rx)*.12;ry+=(my-ry)*.12;dot.style.left=mx+"px";dot.style.top=my+"px";ring.style.left=Math.round(rx)+"px";ring.style.top=Math.round(ry)+"px";raf=requestAnimationFrame(tick);};
      tick();
      document.addEventListener("mousemove",e=>{mx=e.clientX;my=e.clientY;document.body.classList.remove("c-out");});
      document.addEventListener("mouseleave",()=>document.body.classList.add("c-out"));
      document.addEventListener("mouseenter",()=>document.body.classList.remove("c-out"));
      const iSel="a,button,[role='button'],input,select,.service-card,.plan-card,.stat-item,.lang-btn";
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