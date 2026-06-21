const { Pool } = require("pg");

const { execSync } = require("child_process");

function resolveHost() {
  if (process.env.DB_HOST && process.env.DB_HOST !== "auto") {
    return process.env.DB_HOST;
  }
  const candidates = [
    "10.42.0.1",
    "192.168.100.16",
    "100.89.43.30",
    "192.168.100.61"
  ];
  
  for (const host of candidates) {
    try {
      execSync(`node -e "const net=require('net'); const s=net.createConnection(5432, '${host}'); setTimeout(()=>{process.exit(1)}, 1000); s.on('connect', ()=>{process.exit(0)}).on('error', ()=>{process.exit(1)})"`, { stdio: 'ignore' });
      console.log(`[OK] DB conectada via: ${host}`);
      return host;
    } catch (e) {
      // continua
    }
  }
  console.log("  [ERROR] Ningun host de DB disponible.");
  return "127.0.0.1";
}

const activeHost = resolveHost();

const pool = new Pool({
  host:     activeHost,
  port:     Number(process.env.DB_PORT) || 5432,
  user:     process.env.DB_USER     || "postgres",
  password: process.env.DB_PASSWORD || "",
  database: process.env.DB_NAME     || "parking_gtr",
  max:      5,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

module.exports = pool;
