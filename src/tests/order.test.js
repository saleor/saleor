const request = require('supertest');
const app = require('../app');
const { sequelize, Order, OrderItem, User } = require('../models');

beforeAll(async () => {
  await sequelize.sync({ force: true });
});

afterAll(async () => {
  await sequelize.close();
});

describe('Order API', () => {
  let token;
  let userId;

  beforeAll(async () => {
    const user = await User.create({
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
      password: 'password123',
    });
    userId = user.id;

    const res = await request(app)
      .post('/api/users/login')
      .send({
        email: 'test@example.com',
        password: 'password123',
      });

    token = res.body.token;
  });

  describe('POST /api/orders', () => {
    it('should create a new order', async () => {
      const res = await request(app)
        .post('/api/orders')
        .set('Authorization', `Bearer ${token}`)
        .send({
          userId,
          total: 100.0,
          status: 'pending',
          orderItems: [
            {
              productId: 'product-id-1',
              quantity: 2,
              price: 50.0,
            },
          ],
        });

      expect(res.status).toBe(201);
      expect(res.body).toHaveProperty('id');
      expect(res.body.total).toBe(100.0);
      expect(res.body.status).toBe('pending');
    });
  });

  describe('GET /api/orders/:id', () => {
    it('should retrieve an order by ID', async () => {
      const order = await Order.create({
        userId,
        total: 100.0,
        status: 'pending',
      });

      const res = await request(app)
        .get(`/api/orders/${order.id}`)
        .set('Authorization', `Bearer ${token}`);

      expect(res.status).toBe(200);
      expect(res.body).toHaveProperty('id');
      expect(res.body.total).toBe(100.0);
      expect(res.body.status).toBe('pending');
    });
  });

  describe('PUT /api/orders/:id', () => {
    it('should update an order by ID', async () => {
      const order = await Order.create({
        userId,
        total: 100.0,
        status: 'pending',
      });

      const res = await request(app)
        .put(`/api/orders/${order.id}`)
        .set('Authorization', `Bearer ${token}`)
        .send({
          total: 150.0,
          status: 'completed',
          orderItems: [
            {
              productId: 'product-id-1',
              quantity: 3,
              price: 50.0,
            },
          ],
        });

      expect(res.status).toBe(200);
      expect(res.body).toHaveProperty('id');
      expect(res.body.total).toBe(150.0);
      expect(res.body.status).toBe('completed');
    });
  });

  describe('DELETE /api/orders/:id', () => {
    it('should delete an order by ID', async () => {
      const order = await Order.create({
        userId,
        total: 100.0,
        status: 'pending',
      });

      const res = await request(app)
        .delete(`/api/orders/${order.id}`)
        .set('Authorization', `Bearer ${token}`);

      expect(res.status).toBe(200);
      expect(res.text).toBe('Order deleted.');
    });
  });
});
