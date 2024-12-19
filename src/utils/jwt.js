const jwt = require('jsonwebtoken');

const generateToken = (payload, expiresIn = '1h') => {
  return jwt.sign(payload, process.env.JWT_SECRET, { expiresIn });
};

const verifyToken = (token) => {
  try {
    return jwt.verify(token, process.env.JWT_SECRET);
  } catch (err) {
    return null;
  }
};

const refreshToken = (token) => {
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET, { ignoreExpiration: true });
    return generateToken({ id: payload.id });
  } catch (err) {
    return null;
  }
};

module.exports = {
  generateToken,
  verifyToken,
  refreshToken,
};
