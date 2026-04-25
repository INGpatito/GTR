const rateLimit = require("express-rate-limit");

const createLimiter = rateLimit({
  windowMs: 60 * 1000,           
  max: 15,                        
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    success: false,
    errors: ["Too many requests. Please wait a moment before trying again."],
  },
});

module.exports = {
  createLimiter
};
