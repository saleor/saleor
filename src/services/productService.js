const Product = require('../models/product');

const createProduct = async (name, description, price, stock) => {
  const product = await Product.create({
    name,
    description,
    price,
    stock,
  });

  return product;
};

const getProduct = async (productId) => {
  const product = await Product.findByPk(productId);

  return product;
};

const updateProduct = async (productId, name, description, price, stock) => {
  const product = await Product.findByPk(productId);
  if (!product) return null;

  product.name = name;
  product.description = description;
  product.price = price;
  product.stock = stock;
  await product.save();

  return product;
};

const deleteProduct = async (productId) => {
  const product = await Product.findByPk(productId);
  if (!product) return null;

  await product.destroy();

  return product;
};

module.exports = {
  createProduct,
  getProduct,
  updateProduct,
  deleteProduct,
};
