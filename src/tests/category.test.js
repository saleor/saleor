const request = require('supertest');
const app = require('../app');
const { sequelize, Category } = require('../models');

beforeAll(async () => {
  await sequelize.sync({ force: true });
});

afterAll(async () => {
  await sequelize.close();
});

describe('Category API', () => {
  let token;

  beforeAll(async () => {
    const res = await request(app)
      .post('/api/users/register')
      .send({
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        password: 'password123',
      });
    token = res.body.token;
  });

  describe('POST /api/categories', () => {
    it('should create a new category', async () => {
      const res = await request(app)
        .post('/api/categories')
        .set('Authorization', `Bearer ${token}`)
        .send({
          name: 'Electronics',
          description: 'Electronic devices and gadgets',
        });

      expect(res.statusCode).toEqual(201);
      expect(res.body).toHaveProperty('id');
      expect(res.body.name).toEqual('Electronics');
      expect(res.body.description).toEqual('Electronic devices and gadgets');
    });
  });

  describe('GET /api/categories/:id', () => {
    it('should retrieve a category by ID', async () => {
      const category = await Category.create({
        name: 'Books',
        description: 'Books and literature',
      });

      const res = await request(app).get(`/api/categories/${category.id}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body).toHaveProperty('id');
      expect(res.body.name).toEqual('Books');
      expect(res.body.description).toEqual('Books and literature');
    });
  });

  describe('PUT /api/categories/:id', () => {
    it('should update a category by ID', async () => {
      const category = await Category.create({
        name: 'Clothing',
        description: 'Apparel and accessories',
      });

      const res = await request(app)
        .put(`/api/categories/${category.id}`)
        .set('Authorization', `Bearer ${token}`)
        .send({
          name: 'Fashion',
          description: 'Fashion and style',
        });

      expect(res.statusCode).toEqual(200);
      expect(res.body).toHaveProperty('id');
      expect(res.body.name).toEqual('Fashion');
      expect(res.body.description).toEqual('Fashion and style');
    });
  });

  describe('DELETE /api/categories/:id', () => {
    it('should delete a category by ID', async () => {
      const category = await Category.create({
        name: 'Toys',
        description: 'Toys and games',
      });

      const res = await request(app)
        .delete(`/api/categories/${category.id}`)
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(204);

      const deletedCategory = await Category.findByPk(category.id);
      expect(deletedCategory).toBeNull();
    });
  });
});
