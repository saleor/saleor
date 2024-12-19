const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');
const User = require('./user');
const Address = require('./address');
const OrderItem = require('./orderItem');

const Order = sequelize.define('Order', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  userId: {
    type: DataTypes.UUID,
    allowNull: false,
    references: {
      model: User,
      key: 'id',
    },
  },
  total: {
    type: DataTypes.DECIMAL(10, 2),
    allowNull: false,
  },
  status: {
    type: DataTypes.STRING,
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

Order.associate = (models) => {
  Order.belongsTo(models.User, {
    foreignKey: 'userId',
    as: 'user',
  });
  Order.belongsTo(models.Address, {
    foreignKey: 'addressId',
    as: 'address',
  });
  Order.hasMany(models.OrderItem, {
    foreignKey: 'orderId',
    as: 'orderItems',
  });
};

module.exports = Order;
