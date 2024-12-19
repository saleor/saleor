const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');
const Product = require('./product');

const Category = sequelize.define('Category', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  name: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  description: {
    type: DataTypes.TEXT,
    allowNull: true,
  },
  createdAt: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW,
  },
  updatedAt: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW,
  },
});

Category.associate = (models) => {
  Category.belongsToMany(models.Product, {
    through: 'ProductCategory',
    foreignKey: 'categoryId',
    as: 'products',
  });
};

module.exports = Category;
