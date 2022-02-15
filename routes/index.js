const express = require('express');
const Router = express.Router();

Router.get('/home', (req, res) => {
    res.render("pages/index/homepage");
})

module.exports = Router;