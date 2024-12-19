const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const User = require('../models/user');
const { validateUserRegistration, validateUserLogin } = require('../utils/validation');

const registerUser = async (req, res) => {
  const { error } = validateUserRegistration(req.body);
  if (error) return res.status(400).send(error.details[0].message);

  const { email, firstName, lastName, password } = req.body;

  try {
    const existingUser = await User.findOne({ where: { email } });
    if (existingUser) return res.status(400).send('User already registered.');

    const hashedPassword = await bcrypt.hash(password, 10);

    const user = await User.create({
      email,
      firstName,
      lastName,
      password: hashedPassword,
    });

    const token = jwt.sign({ id: user.id }, process.env.JWT_SECRET, {
      expiresIn: '1h',
    });

    res.status(201).send({ token });
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

const loginUser = async (req, res) => {
  const { error } = validateUserLogin(req.body);
  if (error) return res.status(400).send(error.details[0].message);

  const { email, password } = req.body;

  try {
    const user = await User.findOne({ where: { email } });
    if (!user) return res.status(400).send('Invalid email or password.');

    const validPassword = await bcrypt.compare(password, user.password);
    if (!validPassword) return res.status(400).send('Invalid email or password.');

    const token = jwt.sign({ id: user.id }, process.env.JWT_SECRET, {
      expiresIn: '1h',
    });

    res.send({ token });
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

const getUserProfile = async (req, res) => {
  try {
    const user = await User.findByPk(req.user.id, {
      attributes: ['id', 'email', 'firstName', 'lastName', 'isStaff', 'isActive'],
    });
    if (!user) return res.status(404).send('User not found.');

    res.send(user);
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

module.exports = {
  registerUser,
  loginUser,
  getUserProfile,
};
