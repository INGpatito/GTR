const VALID_SERVICES = ["valet", "monthly", "event", "concierge", "fleet"];
const VALID_VEHICLES = ["sports", "suv", "sedan", "convertible", "exotic"];
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function sanitizeString(str) {
  if (typeof str !== "string") return str;
  return str
    .replace(/[<>]/g, "")           
    .replace(/javascript:/gi, "")   
    .replace(/on\w+\s*=/gi, "")     
    .trim();
}

function validateReservation(body) {
  const errors = [];
  if (!body.name || body.name.trim().length < 2)
    errors.push("Full name is required (min 2 chars).");
  if (!body.email || !EMAIL_RE.test(body.email))
    errors.push("A valid email address is required.");
  if (body.service && !VALID_SERVICES.includes(body.service))
    errors.push(`Invalid service. Must be one of: ${VALID_SERVICES.join(", ")}`);
  if (body.vehicle && !VALID_VEHICLES.includes(body.vehicle))
    errors.push(`Invalid vehicle. Must be one of: ${VALID_VEHICLES.join(", ")}`);
  if (body.date) {
    const d = new Date(body.date);
    if (isNaN(d.getTime())) errors.push("Invalid arrival date.");
  }
  if (body.time && !/^\d{2}:\d{2}(:\d{2})?$/.test(body.time))
    errors.push("Invalid arrival time format (HH:MM).");
  return errors;
}

module.exports = {
  VALID_SERVICES,
  VALID_VEHICLES,
  EMAIL_RE,
  sanitizeString,
  validateReservation
};
