const Order = require('../models/order');
const OrderItem = require('../models/orderItem');

const createOrder = async (userId, total, status, orderItems) => {
  const order = await Order.create({
    userId,
    total,
    status,
  });

  const orderItemsData = orderItems.map((item) => ({
    orderId: order.id,
    productId: item.productId,
    quantity: item.quantity,
    price: item.price,
  }));

  await OrderItem.bulkCreate(orderItemsData);

  return order;
};

const getOrder = async (orderId) => {
  const order = await Order.findByPk(orderId, {
    include: [
      {
        model: OrderItem,
        as: 'orderItems',
      },
    ],
  });

  return order;
};

const updateOrder = async (orderId, total, status, orderItems) => {
  const order = await Order.findByPk(orderId);
  if (!order) return null;

  order.total = total;
  order.status = status;
  await order.save();

  await OrderItem.destroy({ where: { orderId: order.id } });

  const orderItemsData = orderItems.map((item) => ({
    orderId: order.id,
    productId: item.productId,
    quantity: item.quantity,
    price: item.price,
  }));

  await OrderItem.bulkCreate(orderItemsData);

  return order;
};

const deleteOrder = async (orderId) => {
  const order = await Order.findByPk(orderId);
  if (!order) return null;

  await OrderItem.destroy({ where: { orderId: order.id } });
  await order.destroy();

  return order;
};

module.exports = {
  createOrder,
  getOrder,
  updateOrder,
  deleteOrder,
};
