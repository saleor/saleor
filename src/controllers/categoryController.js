const Category = require('../models/category');
const { validateCategory } = require('../utils/validation');

const createCategory = async (req, res) => {
  const { error } = validateCategory(req.body);
  if (error) return res.status(400).send(error.details[0].message);

  const { name, description } = req.body;

  try {
    const category = await Category.create({
      name,
      description,
    });

    res.status(201).send(category);
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

const getCategory = async (req, res) => {
  try {
    const category = await Category.findByPk(req.params.id);
    if (!category) return res.status(404).send('Category not found.');

    res.send(category);
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

const updateCategory = async (req, res) => {
  const { error } = validateCategory(req.body);
  if (error) return res.status(400).send(error.details[0].message);

  const { name, description } = req.body;

  try {
    const category = await Category.findByPk(req.params.id);
    if (!category) return res.status(404).send('Category not found.');

    category.name = name;
    category.description = description;
    await category.save();

    res.send(category);
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

const deleteCategory = async (req, res) => {
  try {
    const category = await Category.findByPk(req.params.id);
    if (!category) return res.status(404).send('Category not found.');

    await category.destroy();

    res.status(204).send();
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

module.exports = {
  createCategory,
  getCategory,
  updateCategory,
  deleteCategory,
};
