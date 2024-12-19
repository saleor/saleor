const request = require('supertest');
const app = require('../app');
const User = require('../models/user');
const { sequelize } = require('../config/database');

beforeAll(async () => {
  await sequelize.sync({ force: true });
});

afterAll(async () => {
  await sequelize.close();
});

describe('User Registration', () => {
  it('should register a new user', async () => {
    const res = await request(app)
      .post('/api/users/register')
      .send({
        email: 'test@example.com',
        firstName: 'John',
        lastName: 'Doe',
        password: 'password123',
      });

    expect(res.statusCode).toEqual(201);
    expect(res.body).toHaveProperty('token');
  });

  it('should not register a user with an existing email', async () => {
    await User.create({
      email: 'test@example.com',
      firstName: 'John',
      lastName: 'Doe',
      password: 'password123',
    });

    const res = await request(app)
      .post('/api/users/register')
      .send({
        email: 'test@example.com',
        firstName: 'Jane',
        lastName: 'Doe',
        password: 'password123',
      });

    expect(res.statusCode).toEqual(400);
    expect(res.text).toBe('User already registered.');
  });
});

describe('User Login', () => {
  it('should login an existing user', async () => {
    await User.create({
      email: 'login@example.com',
      firstName: 'John',
      lastName: 'Doe',
      password: await bcrypt.hash('password123', 10),
    });

    const res = await request(app)
      .post('/api/users/login')
      .send({
        email: 'login@example.com',
        password: 'password123',
      });

    expect(res.statusCode).toEqual(200);
    expect(res.body).toHaveProperty('token');
  });

  it('should not login with invalid email', async () => {
    const res = await request(app)
      .post('/api/users/login')
      .send({
        email: 'invalid@example.com',
        password: 'password123',
      });

    expect(res.statusCode).toEqual(400);
    expect(res.text).toBe('Invalid email or password.');
  });

  it('should not login with invalid password', async () => {
    await User.create({
      email: 'password@example.com',
      firstName: 'John',
      lastName: 'Doe',
      password: await bcrypt.hash('password123', 10),
    });

    const res = await request(app)
      .post('/api/users/login')
      .send({
        email: 'password@example.com',
        password: 'wrongpassword',
      });

    expect(res.statusCode).toEqual(400);
    expect(res.text).toBe('Invalid email or password.');
  });
});

describe('User Profile', () => {
  it('should get user profile', async () => {
    const user = await User.create({
      email: 'profile@example.com',
      firstName: 'John',
      lastName: 'Doe',
      password: await bcrypt.hash('password123', 10),
    });

    const token = jwt.sign({ id: user.id }, process.env.JWT_SECRET, {
      expiresIn: '1h',
    });

    const res = await request(app)
      .get('/api/users/profile')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toEqual(200);
    expect(res.body).toHaveProperty('email', 'profile@example.com');
  });

  it('should not get profile without token', async () => {
    const res = await request(app).get('/api/users/profile');

    expect(res.statusCode).toEqual(401);
    expect(res.text).toBe('Access denied. No token provided.');
  });

  it('should not get profile with invalid token', async () => {
    const res = await request(app)
      .get('/api/users/profile')
      .set('Authorization', 'Bearer invalidtoken');

    expect(res.statusCode).toEqual(400);
    expect(res.text).toBe('Invalid token.');
  });
});
