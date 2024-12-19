const express = require('express');
const router = express.Router();
const { createOrder, getOrder, updateOrder, deleteOrder } = require('../controllers/orderController');
const { authMiddleware } = require('../middleware/authMiddleware');

router.post('/', authMiddleware, createOrder);
router.get('/:id', authMiddleware, getOrder);
router.put('/:id', authMiddleware, updateOrder);
router.delete('/:id', authMiddleware, deleteOrder);

module.exports = router;
