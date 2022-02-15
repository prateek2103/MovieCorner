const mongoose = require('mongoose')
const ratingSchema = mongoose.Schema({
    "user_id":{
        type:String
    },
    "movie_id":{
        type:String
    },
    "rating":{
        type:Number
    },
    "movie_title":{
        type:String,
    },
    "movie_link":{
        type:String,
    }

})

const ratingModel = mongoose.model("ratings",ratingSchema);
module.exports = ratingModel