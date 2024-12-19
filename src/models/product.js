const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');
const OrderItem = require('./orderItem');
const Category = require('./category');

const Product = sequelize.define('Product', {
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
  price: {
    type: DataTypes.DECIMAL(10, 2),
    allowNull: false,
  },
  stock: {
    type: DataTypes.INTEGER,
    allowNull: false,
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

Product.associate = (models) => {
  Product.hasMany(models.OrderItem, {
    foreignKey: 'productId',
    as: 'orderItems',
  });
  Product.belongsToMany(models.Category, {
    through: 'ProductCategory',
    foreignKey: 'productId',
    as: 'categories',
  });
};

module.exports = Product;
