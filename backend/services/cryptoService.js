const crypto = require("crypto");
const JWT_SECRET = process.env.JWT_SECRET || "fallback_dev_secret_change_me";

function generateCardNumber(memberId) {
  const hmac = crypto.createHmac("sha256", JWT_SECRET);
  hmac.update(`GTR-CARD-${memberId}`);
  const hex = hmac.digest("hex"); 
  let digits = "";
  for (let i = 0; i < 48 && digits.length < 16; i += 3) {
    const num = parseInt(hex.substring(i, i + 3), 16) % 10;
    digits += num;
  }
  while (digits.length < 16) digits += "0";
  return `${digits.slice(0,4)} ${digits.slice(4,8)} ${digits.slice(8,12)} ${digits.slice(12,16)}`;
}

module.exports = {
  generateCardNumber
};
