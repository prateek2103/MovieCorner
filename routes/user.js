const express = require("express");
const Router = express.Router();
const OccupationModel = require("../models/occupations");
const UserModel = require("../models/user");
const bcrypt = require("bcrypt");
const auth = require("../auth/auth");
const { spawnSync } = require("child_process");
const json = require("body-parser/lib/types/json");
// const db = require("../db")
const movieModel = require("../models/movie");
const ratingModel = require("../models/rating");
const mongoose = require("mongoose");
const fs = require("fs");
var csvWriter = require("csv-write-stream");

//signin page (get)
Router.get("/signin", (req, res) => {
  res.render("pages/user/login", {
    flashMessage: req.flash("message"),
    successMessage: req.flash("successMessage"),
  });
});

//signin page (post)
Router.post("/signin", (req, res) => {
  UserModel.findOne({ email: req.body.username }, (err, user) => {
    if (err) {
      console.error(err);
      req.flash("message", "Internal server error. Try again after sometime");
      res.redirect("signin");
    }

    //if no user is found
    if (user == null) {
      req.flash("message", "Username or password is incorrect");
      res.redirect("signin");
    }

    //if user is found
    else {
      bcrypt.compare(req.body.password, user.password, function (err, isMatch) {
        if (err) {
          console.error(err);
          req.flash(
            "message",
            "Internal server error. Try again after sometime"
          );
          res.redirect("signin");
        }
        //if the password matches
        else if (isMatch) {
          //get the recommendations for the user

          //step1 get user ratings
          ratingModel.find({ user_id: user["_id"] }, (err, data) => {
            if (err) {
              console.error(err);
              req.flash(
                "message",
                "Internal server error. Try again after sometime"
              );
              res.redirect("signin");
            } else {
              //if user has rated no movies
              if (data.length === 0) {
                req.session.user_data = user;
                req.session.by_recommendation = [];
                res.redirect("/user/home");
              } else {
                //get the user recommendations according to previous ratings
                let dataString = "";
                let final_data = null;
                argu_data = JSON.stringify({ data: data });

                // passing the json obj to the python code
                let data_1 = "'" + argu_data + "'";
                // console.log(data_1);
                const py = spawnSync(
                  "echo",
                  [data_1, "| python automated/recommend.py"],
                  { shell: true }
                );

                //storing the data in datastring
                dataString = py.stdout.toString();
                errorString = py.stderr.toString();

                // console.log("errorString:",errorString)
                dataString = dataString.substring(
                  dataString.indexOf("{"),
                  dataString.lastIndexOf("}") + 1
                );
                console.log("datastring:", dataString);

                try {
                  final_data = JSON.parse(dataString);
                  req.session.user_data = user;
                  req.session.by_recommendation = final_data["movie_list"];
                  res.redirect("/user/home");
                } catch (e) {
                  console.log(e);
                  console.log(errorString);
                }
              }
            }
          });
        }
        //if password does not matches
        else {
          req.flash("message", "Username or password is incorrect");
          res.redirect("signin");
        }
      });
    }
  });
});

//signup a user (get)
Router.get("/signup", (req, res) => {
  OccupationModel.find({}, (err, data) => {
    if (err) {
      console.error(err);
      res.sendStatus(500);
    } else {
      let occu = data[0];
      console.log(occu);
      res.render("pages/user/signup", {
        occupations: occu["occupations"],
        flashMessage: req.flash("message"),
      });
    }
  });
});

//signup a user (post)
Router.post("/signup", (req, res) => {
  //checking if a user with that email is already present or not
  UserModel.findOne({ email: req.body.email }, (err, result) => {
    if (err) {
      console.error(err);
      req.flash("message", "Internal server error. Try again after sometime");
      res.redirect("signup");
    } else {
      //no user is found
      if (result == null) {
        let user_data = req.body;
        let dataString = "";
        let final_data = null;

        //passing the json obj to the python code
        let argu_data = req.body;
        console.log(
          `python automated/add_user.py ${argu_data["name"]} ${argu_data["email"]} ${argu_data["age"]} ${argu_data["gender"]} ${argu_data["occupation"]} ${argu_data["country"]}`
        );
        const py = spawnSync(
          `python automated/add_user.py ${argu_data["name"]} ${argu_data["email"]} ${argu_data["age"]} ${argu_data["gender"]} ${argu_data["occupation"]} ${argu_data["country"]}`,
          {
            shell: true,
          }
        );

        //storing the data in datastring
        dataString = py.stdout.toString();
        errorString = py.stderr.toString();

        try {
          final_data = JSON.parse(dataString);
          user_data["by_rating"] = final_data["rating"];
          user_data["by_popularity"] = final_data["popularity"];

          //saving the data in the database
          let userData = new UserModel(user_data);
          userData.save(() => {
            req.flash("successMessage", "You have been successfully signed up");
            res.redirect("signin");
          });
        } catch (err) {
          console.error("errorString:", errorString);
          console.error("error:", err);
          req.flash(
            "message",
            "Internal server error. Try again after sometime"
          );
          res.redirect("signup");
        }
      } else {
        req.flash("message", "Sorry, user with that email already exists.");
        res.redirect("signup");
      }
    }
  });
});

//after successful signin
Router.get("/home", auth, (req, res) => {
  user = req.session.user_data;
  user["by_recommendation"] = req.session.by_recommendation;
  res.render("pages/user/mainpage", {
    user: user,
    successMessage: req.flash("successMessage"),
  });
});

//signout the user
Router.get("/signout", auth, (req, res) => {
  req.session.destroy();
  res.redirect("/user/signin");
});

//helper method
Router.get("/createOccupations", (req, res) => {
  let occu = new OccupationModel({
    occupations: [
      "administrator",
      "artist",
      "doctor",
      "educator",
      "engineer",
      "entertainment",
      "executive",
      "healthcare",
      "homemaker",
      "lawyer",
      "librarian",
      "marketing",
      "none",
      "other",
      "programmer",
      "retired",
      "salesman",
      "scientist",
      "student",
      "technician",
      "writer",
    ],
  });
  occu.save();
});

//getting the description of a particular movie
Router.get("/movie_description/:movie_title", auth, (req, res) => {
  movieModel.findOne({ movie_title: req.params.movie_title }, (err, data) => {
    if (err) {
      console.error(err);
      res.sendStatus(500);
    } else {
      //filtering the genres
      filtered_genres = [];
      for (const key in data) {
        if (
          data[key] == 1 &&
          key != "movie_id" &&
          key != "$isMongooseModelPrototype" &&
          key != "$init"
        )
          filtered_genres.push(key);
      }

      //saving in a object before passing to the response
      movie_data = {};
      movie_data["movie_id"] = data["_id"];
      movie_data["release_date"] = data["release_date"];
      movie_data["movie_title"] = data["movie_title"];
      movie_data["image"] = data["IMDb_URL"];
      movie_data["filtered_genres"] = filtered_genres;

      //check if user has already rated the movie
      user_id = req.session.user_data["_id"];
      ratingModel.findOne(
        { movie_id: data["_id"], user_id: user_id },
        (err, result) => {
          if (err) res.sendStatus(500);
          else {
            //user hasn't watched the movie
            if (result == null) movie_data["rating"] = 0;
            //user has watched the movie
            else movie_data["rating"] = result["rating"];

            res.render("pages/user/movie_description", {
              user: req.session.user_data,
              movie_data: movie_data,
              successMessage: req.flash("successMessage"),
            });
          }
        }
      );
    }
  });
});

//save the user ratings
Router.post(
  "/save_user_rating/:id/:movie_title/:movie_link",
  auth,
  (req, res) => {
    let rating_proto = {
      rating: req.body["rating"],
      user_id: req.session.user_data["_id"],
      movie_id: req.params.id,
      movie_title: req.params.movie_title,
      movie_link:
        "https://m.media-amazon.com/images/M/" + req.params.movie_link,
    };

    ratingModel.findOneAndUpdate(
      { user_id: rating_proto.user_id, movie_id: rating_proto.movie_id },
      rating_proto,
      { upsert: true },
      (err, data) => {
        if (err) res.sendStatus(500);
      }
    );

    // //add the ratings in ratings_df.csv
    // user_data={
    //     "index":"",
    //     "user_id":rating_proto['user_id'],
    //     "movie_id":rating_proto['movie_id'],
    //     "rating":rating_proto['rating'],
    //     "timestamp":Date.now()
    // }

    // var writer = csvWriter({sendHeaders:false})
    // writer.pipe(fs.createWriteStream('data/ratings_df.csv',{flags: 'a'}))
    // writer.write(user_data)
    // writer.end()

    //print success message
    req.flash("successMessage", "Your rating have been submitted successfully");
    res.redirect("/user/home");
  }
);

//has already watched
Router.get("/alreadyWatched", auth, (req, res) => {
  ratingModel.find({ user_id: req.session.user_data["_id"] }, (err, data) => {
    if (err) res.send("error" + err);
    else {
      res.render("pages/user/watched", {
        list_data: data,
        user: req.session.user_data["_id"],
      });
    }
  });
});

//top 50 trending all over
Router.get("/trending", auth, (req, res) => {
  let dataString = "";
  let final_data = null;

  //passing the json obj to the python code
  const py = spawnSync("python", ["automated/get_movies.py"]);

  //storing the data in datastring
  dataString = py.stdout.toString();
  errorString = py.stderr.toString();

  try {
    final_data = JSON.parse(dataString);
    res.render("pages/user/trending", {
      user: req.session.user_data["_id"],
      list_data: final_data["movie_list"],
    });
  } catch (err) {
    console.error(errorString);
    console.error("err", err);
    res.sendStatus(500);
  }
});

//get the search movies page
Router.get("/search", auth, (req, res) => {
  res.render("pages/user/search", { user: req.session.user_data["_id"] });
});

//return the searched movies
Router.get("/search/:movie", auth, (req, res) => {
  var regexp = new RegExp("^" + req.params.movie);
  movieModel.find(
    { movie_title: { $regex: regexp, $options: "i" } },
    (err, data) => {
      if (err) {
        console.error(err);
        res.sendStatus(500);
      } else {
        res.send(data);
      }
    }
  );
});

// //fake data
// Router.get("/insertFake",(req,res)=>{
//     user_proto={
//         "by_recommendation":[
//             {"name":"Twelve Monkeys (1995)",
//             "link":"https://m.media-amazon.com/images/M/MV5BN2Y2OWU4MWMtNmIyMy00YzMyLWI0Y2ItMTcyZDc3MTdmZDU4XkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_.jpg",
//             "genre":["Action"]
//             },
//             {"name":"Mr. Holland's Opus (1995)",
//             "link":"https://m.media-amazon.com/images/M/MV5BZDZhNDRlZjAtYzdhNy00ZjU1LWFlMDYtNjA5NjliM2Y5ZmVjL2ltYWdlXkEyXkFqcGdeQXVyNjE5MjUyOTM@._V1_.jpg",
//             "genre":["Action"]
//             },
//             {"name":"Braveheart (1995)",
//             "link":"https://m.media-amazon.com/images/M/MV5BMzkzMmU0YTYtOWM3My00YzBmLWI0YzctOGYyNTkwMWE5MTJkXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_.jpg",
//             "genre":["Action"]
//             },
//             {"name":"Bad Boys (1995)",
//             "link":"https://m.media-amazon.com/images/M/MV5BMGE1ZTQ0ZTEtZTEwZS00NWE0LTlmMDUtMTE1ZWJiZTYzZTQ2XkEyXkFqcGdeQXVyNTAyODkwOQ@@._V1_.jpg",
//             "genre":["Action"]
//             },
//             {"name":"Batman Forever (1995)",
//             "link":"https://m.media-amazon.com/images/M/MV5BNDdjYmFiYWEtYzBhZS00YTZkLWFlODgtY2I5MDE0NzZmMDljXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_.jpg",
//             "genre":["Action"]
//             },
//         ]
//     }
//     UserModel.findOneAndUpdate({email:"usernamekshitij@gmail.com"},user_proto,{upsert:true},(err,data)=>{
//         if(err)
//             res.sendStatus(500)
//     })
// })

// Router.get("/userData",(req,res)=>{
//     ratingModel.find({user_id:"60bbecff068e973dfc84e487"},(err,data)=>{
//         if(err)
//             console.log(err)
//         else
//             res.send(data)
//     })
// })
module.exports = Router;
