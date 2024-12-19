const Category = require('../models/category');

const createCategory = async (name, description) => {
  const category = await Category.create({
    name,
    description,
  });

  return category;
};

const getCategory = async (categoryId) => {
  const category = await Category.findByPk(categoryId);

  return category;
};

const updateCategory = async (categoryId, name, description) => {
  const category = await Category.findByPk(categoryId);
  if (!category) return null;

  category.name = name;
  category.description = description;
  await category.save();

  return category;
};

const deleteCategory = async (categoryId) => {
  const category = await Category.findByPk(categoryId);
  if (!category) return null;

  await category.destroy();

  return category;
};

module.exports = {
  createCategory,
  getCategory,
  updateCategory,
  deleteCategory,
};
