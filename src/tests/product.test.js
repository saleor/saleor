const request = require('supertest');
const app = require('../app');
const Product = require('../models/product');
const { sequelize } = require('../config/database');

beforeAll(async () => {
  await sequelize.sync({ force: true });
});

afterAll(async () => {
  await sequelize.close();
});

describe('Product API', () => {
  let product;

  beforeEach(async () => {
    product = await Product.create({
      name: 'Test Product',
      description: 'This is a test product',
      price: 10.99,
      stock: 100,
    });
  });

  afterEach(async () => {
    await Product.destroy({ where: {} });
  });

  it('should create a new product', async () => {
    const res = await request(app)
      .post('/api/products')
      .send({
        name: 'New Product',
        description: 'This is a new product',
        price: 19.99,
        stock: 50,
      });

    expect(res.statusCode).toEqual(201);
    expect(res.body).toHaveProperty('id');
    expect(res.body.name).toEqual('New Product');
  });

  it('should get a product by id', async () => {
    const res = await request(app).get(`/api/products/${product.id}`);

    expect(res.statusCode).toEqual(200);
    expect(res.body).toHaveProperty('id');
    expect(res.body.name).toEqual('Test Product');
  });

  it('should update a product by id', async () => {
    const res = await request(app)
      .put(`/api/products/${product.id}`)
      .send({
        name: 'Updated Product',
        description: 'This is an updated product',
        price: 15.99,
        stock: 80,
      });

    expect(res.statusCode).toEqual(200);
    expect(res.body.name).toEqual('Updated Product');
  });

  it('should delete a product by id', async () => {
    const res = await request(app).delete(`/api/products/${product.id}`);

    expect(res.statusCode).toEqual(200);
    expect(res.body.message).toEqual('Product deleted successfully.');
  });
});
