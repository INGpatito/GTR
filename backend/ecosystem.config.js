module.exports = {
  apps: [{
    name: "gtr-backend",
    script: "./server.js",
    instances: 1, // Puedes aumentar esto si tu servidor tiene múltiples núcleos y quieres escalar
    autorestart: true,
    watch: false,
    max_memory_restart: "500M",
    env: {
      NODE_ENV: "development"
    },
    env_production: {
      NODE_ENV: "production",
      PORT: 3000
    }
  }]
};
