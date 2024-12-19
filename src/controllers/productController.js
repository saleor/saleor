const Product = require('../models/product');
const { validateProduct } = require('../utils/validation');

const createProduct = async (req, res) => {
  const { error } = validateProduct(req.body);
  if (error) return res.status(400).send(error.details[0].message);

  const { name, description, price, stock } = req.body;

  try {
    const product = await Product.create({
      name,
      description,
      price,
      stock,
    });

    res.status(201).send(product);
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

const getProduct = async (req, res) => {
  try {
    const product = await Product.findByPk(req.params.id);
    if (!product) return res.status(404).send('Product not found.');

    res.send(product);
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

const updateProduct = async (req, res) => {
  const { error } = validateProduct(req.body);
  if (error) return res.status(400).send(error.details[0].message);

  try {
    const product = await Product.findByPk(req.params.id);
    if (!product) return res.status(404).send('Product not found.');

    const { name, description, price, stock } = req.body;

    await product.update({
      name,
      description,
      price,
      stock,
    });

    res.send(product);
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

const deleteProduct = async (req, res) => {
  try {
    const product = await Product.findByPk(req.params.id);
    if (!product) return res.status(404).send('Product not found.');

    await product.destroy();

    res.send({ message: 'Product deleted successfully.' });
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

module.exports = {
  createProduct,
  getProduct,
  updateProduct,
  deleteProduct,
};
