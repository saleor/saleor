const Order = require('../models/order');
const OrderItem = require('../models/orderItem');
const { validateOrderCreation } = require('../utils/validation');

const createOrder = async (req, res) => {
  const { error } = validateOrderCreation(req.body);
  if (error) return res.status(400).send(error.details[0].message);

  const { userId, total, status, orderItems } = req.body;

  try {
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

    res.status(201).send(order);
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

const getOrder = async (req, res) => {
  try {
    const order = await Order.findByPk(req.params.id, {
      include: [
        {
          model: OrderItem,
          as: 'orderItems',
        },
      ],
    });
    if (!order) return res.status(404).send('Order not found.');

    res.send(order);
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

const updateOrder = async (req, res) => {
  const { error } = validateOrderCreation(req.body);
  if (error) return res.status(400).send(error.details[0].message);

  try {
    const order = await Order.findByPk(req.params.id);
    if (!order) return res.status(404).send('Order not found.');

    const { total, status, orderItems } = req.body;

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

    res.send(order);
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

const deleteOrder = async (req, res) => {
  try {
    const order = await Order.findByPk(req.params.id);
    if (!order) return res.status(404).send('Order not found.');

    await OrderItem.destroy({ where: { orderId: order.id } });
    await order.destroy();

    res.send('Order deleted.');
  } catch (err) {
    res.status(500).send('Internal server error.');
  }
};

module.exports = {
  createOrder,
  getOrder,
  updateOrder,
  deleteOrder,
};
