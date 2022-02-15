const mongoose = require('mongoose')
const bcrypt = require("bcrypt")
const SALT_WORK_FACTOR = 10;
const userSchema = mongoose.Schema({
    "name":{
        type:String
    },
    "age":{
        type:Number
    },
    "email":{
        type:String
    },
    "password":{
        type:String
    },
    "occupation":{
        type:String
    },
    "gender":{
        type:String
    },
    "country":{
        type:String
    },
    "by_rating":{
        type:Array
    },
    "by_popularity":{
        type:Array
    },
    "by_recommendation":{
        type:Array
    }
})

userSchema.pre('save', function(next) {
    var user = this;
    if (!user.isModified('password')) return next();

    bcrypt.genSalt(SALT_WORK_FACTOR, function(err, salt) {
        if (err) return next(err);

        bcrypt.hash(user.password, salt, function(err, hash) {
            if (err) return next(err);
            user.password = hash;
            next();
        });
    });
});

const userModel = mongoose.model("User",userSchema);
module.exports = userModel