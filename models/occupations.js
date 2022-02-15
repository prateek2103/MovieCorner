const mongoose = require('mongoose')
const occupationSchema = mongoose.Schema({
    "occupations":{
        type:Array
    }
})

const occuModel = mongoose.model("Occupations",occupationSchema);
module.exports = occuModel