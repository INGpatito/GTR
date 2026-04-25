const jwt = require("jsonwebtoken");

const ADMIN_API_KEY = process.env.ADMIN_API_KEY || "";
const JWT_SECRET = process.env.JWT_SECRET || "fallback_dev_secret_change_me";

function requireAdminKey(req, res, next) {
  if (!ADMIN_API_KEY) {
    return next();
  }

  const provided = req.headers["x-api-key"];
  if (!provided || provided !== ADMIN_API_KEY) {
    return res.status(401).json({
      success: false,
      errors: ["Unauthorized. A valid X-API-Key header is required."],
    });
  }
  next();
}

function requireAuth(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({ success: false, errors: ["Authentication required."] });
  }

  const token = authHeader.split(" ")[1];
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.authUser = decoded;

    const paramId = parseInt(req.params.id, 10);
    if (!isNaN(paramId) && decoded.id !== paramId) {
      return res.status(403).json({ success: false, errors: ["Access denied. You can only access your own data."] });
    }

    next();
  } catch (err) {
    if (err.name === "TokenExpiredError") {
      return res.status(401).json({ success: false, errors: ["Session expired. Please log in again."] });
    }
    return res.status(401).json({ success: false, errors: ["Invalid token."] });
  }
}

module.exports = {
  requireAdminKey,
  requireAuth
};
