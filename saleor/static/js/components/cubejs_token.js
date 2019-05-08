const jwt = require('jsonwebtoken');

const CUBEJS_API_SECRET = 'd242612162ecbe8c2436d47d74b83ecc1640f690ef73aef1ccfd26cf6b887bc2';

export function generate_token(){
  const cubejsToken = jwt.sign({}, CUBEJS_API_SECRET, { expiresIn: '1d' });
  return cubejsToken;
};
