require('dotenv').config();
const jwt = require('jsonwebtoken');
const CUBEJS_API_SECRET=process.env.CUBEJS_API_SECRET;

export function generate_token(){
  const cubejsToken = jwt.sign({}, CUBE_API_SECRET, { expiresIn: '1d' });
  return cubejsToken;
};
