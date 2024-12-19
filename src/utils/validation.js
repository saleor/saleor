const Joi = require('joi');

const validateUserRegistration = (data) => {
  const schema = Joi.object({
    email: Joi.string().email().required(),
    firstName: Joi.string().min(1).max(50).required(),
    lastName: Joi.string().min(1).max(50).required(),
    password: Joi.string().min(8).max(100).required(),
  });

  return schema.validate(data);
};

const validateUserLogin = (data) => {
  const schema = Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().min(8).max(100).required(),
  });

  return schema.validate(data);
};

const validateOrderCreation = (data) => {
  const schema = Joi.object({
    userId: Joi.string().uuid().required(),
    total: Joi.number().precision(2).required(),
    status: Joi.string().required(),
    orderItems: Joi.array().items(
      Joi.object({
        productId: Joi.string().uuid().required(),
        quantity: Joi.number().integer().min(1).required(),
        price: Joi.number().precision(2).required(),
      })
    ).required(),
  });

  return schema.validate(data);
};

const validateProduct = (data) => {
  const schema = Joi.object({
    name: Joi.string().min(1).max(100).required(),
    description: Joi.string().allow(null, ''),
    price: Joi.number().precision(2).required(),
    stock: Joi.number().integer().min(0).required(),
  });

  return schema.validate(data);
};

const validateCategory = (data) => {
  const schema = Joi.object({
    name: Joi.string().min(1).max(100).required(),
    description: Joi.string().allow(null, ''),
  });

  return schema.validate(data);
};

module.exports = {
  validateUserRegistration,
  validateUserLogin,
  validateOrderCreation,
  validateProduct,
  validateCategory,
};
