const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');
const User = require('./user');
const Order = require('./order');

const Address = sequelize.define('Address', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  firstName: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  lastName: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  companyName: {
    type: DataTypes.STRING,
    allowNull: true,
  },
  streetAddress1: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  streetAddress2: {
    type: DataTypes.STRING,
    allowNull: true,
  },
  city: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  cityArea: {
    type: DataTypes.STRING,
    allowNull: true,
  },
  postalCode: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  country: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  countryArea: {
    type: DataTypes.STRING,
    allowNull: true,
  },
  phone: {
    type: DataTypes.STRING,
    allowNull: true,
  },
  validationSkipped: {
    type: DataTypes.BOOLEAN,
    defaultValue: false,
  },
});

Address.associate = (models) => {
  Address.belongsTo(models.User, {
    foreignKey: 'userId',
    as: 'user',
  });
  Address.hasMany(models.Order, {
    foreignKey: 'addressId',
    as: 'orders',
  });
};

module.exports = Address;
