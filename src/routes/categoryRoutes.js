const express = require('express');
const router = express.Router();
const { createCategory, getCategory, updateCategory, deleteCategory } = require('../controllers/categoryController');
const { authMiddleware } = require('../middleware/authMiddleware');

router.post('/', authMiddleware, createCategory);
router.get('/:id', getCategory);
router.put('/:id', authMiddleware, updateCategory);
router.delete('/:id', authMiddleware, deleteCategory);

module.exports = router;
