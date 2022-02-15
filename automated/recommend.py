import pandas as pd
import os
import re
import collections
import sklearn
import sklearn.manifold
import logging
import tensorflow.compat.v1 as tf
import numpy as np
import json
import sys
tf.disable_v2_behavior()

import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)
logger.setLevel("ERROR")
#Base directory
BASE_DIR = os.getcwd()
BASE_DIR = re.sub(r"\\","/",BASE_DIR)+"/"

#marking the genres of each movie
def mark_genres(movies, genres):
  def get_random_genre(gs):
    active = [genre for genre, g in zip(genres, gs) if g==1]
    if len(active) == 0:
      return 'Other'
    return np.random.choice(active)
  def get_all_genres(gs):
    active = [genre for genre, g in zip(genres, gs) if g==1]
    if len(active) == 0:
      return 'Other'
    return '-'.join(active)
  movies['genre'] = [
      get_random_genre(gs) for gs in zip(*[movies[genre] for genre in genres])]
  movies['all_genres'] = [
      get_all_genres(gs) for gs in zip(*[movies[genre] for genre in genres])]

#helper methods
def split_dataframe(df, holdout_fraction=0.1):
  test = df.sample(frac=holdout_fraction, replace=False)
  train = df[~df.index.isin(test.index)]
  return train, test

def build_rating_sparse_tensor(ratings_df):
  indices = ratings_df[['user_id', 'movie_id']].values
  values = ratings_df['rating'].values
  return tf.SparseTensor(
      indices=indices,
      values=values,
      dense_shape=[users.shape[0], movies.shape[0]])

def sparse_mean_square_error(sparse_ratings, user_embeddings, movie_embeddings):
  predictions = tf.gather_nd(
      tf.matmul(user_embeddings, movie_embeddings, transpose_b=True),
      sparse_ratings.indices)
  loss = tf.losses.mean_squared_error(sparse_ratings.values, predictions)
  return loss

#collaborative filtering model
class CFModel(object):
  def __init__(self, embedding_vars, loss, metrics=None):
    self._embedding_vars = embedding_vars
    self._loss = loss
    self._metrics = metrics
    self._embeddings = {k: None for k in embedding_vars}
    self._session = None

  @property
  def embeddings(self):
    return self._embeddings

  def train(self, num_iterations=100, learning_rate=1.0,optimizer=tf.train.GradientDescentOptimizer):
    with self._loss.graph.as_default():
      opt = optimizer(learning_rate)
      train_op = opt.minimize(self._loss)
      local_init_op = tf.group(
          tf.variables_initializer(opt.variables()),
          tf.local_variables_initializer())
      if self._session is None:
        self._session = tf.Session()
        with self._session.as_default():
          self._session.run(tf.global_variables_initializer())
          self._session.run(tf.tables_initializer())
          tf.train.start_queue_runners()

    with self._session.as_default():
      local_init_op.run()
      iterations = []
      metrics = self._metrics or ({},)
      metrics_vals = [collections.defaultdict(list) for _ in self._metrics]

      # Train and append results.
      for i in range(num_iterations + 1):
        _, results = self._session.run((train_op, metrics))
        if (i % 10 == 0) or i == num_iterations:
          iterations.append(i)
          for metric_val, result in zip(metrics_vals, results):
            for k, v in result.items():
              metric_val[k].append(v)

      for k, v in self._embedding_vars.items():
        self._embeddings[k] = v.eval()

      return results

#function to build the model
def build_model(ratings, embedding_dim=3, init_stddev=1.):
  # Split the ratings DataFrame into train and test.
  train_ratings, test_ratings = split_dataframe(ratings)

  # SparseTensor representation of the train and test datasets.
  A_train = build_rating_sparse_tensor(train_ratings)
  A_test = build_rating_sparse_tensor(test_ratings)

  # Initialize the embeddings using a normal distribution.
  U = tf.Variable(tf.random_normal(
      [A_train.dense_shape[0], embedding_dim], stddev=init_stddev))
  V = tf.Variable(tf.random_normal(
      [A_train.dense_shape[1], embedding_dim], stddev=init_stddev))
  train_loss = sparse_mean_square_error(A_train, U, V)
  test_loss = sparse_mean_square_error(A_test, U, V)
  metrics = {
      'train_error': train_loss,
      'test_error': test_loss
  }
  embeddings = {
      "user_id": U,
      "movie_id": V
  }
  return CFModel(embeddings, train_loss, [metrics])


#helper method to compute score
DOT = 'dot'
COSINE = 'cosine'
def compute_scores(query_embedding, item_embeddings, measure=DOT):
  u = query_embedding
  V = item_embeddings
  if measure == COSINE:
    V = V / np.linalg.norm(V, axis=1, keepdims=True)
    u = u / np.linalg.norm(u)
  scores = u.dot(V.T)
  return scores

#user recommendations(helper method)
def user_recommendations(model, measure=DOT, exclude_rated=True, k=10):
    scores = compute_scores(
        model.embeddings["user_id"][943], model.embeddings["movie_id"], measure)
    score_key = measure + ' score'
    df = pd.DataFrame({
        score_key: list(scores),
        'links':movies['IMDb_URL'],
        'movie_id': movies['movie_id'],
        'titles': movies['movie_title'],
        'genres': movies['all_genres'],
    })
    if exclude_rated:
        rated_movies = ratings[ratings.user_id == "943"]["movie_id"].values
        df = df[df.movie_id.apply(lambda movie_id: movie_id not in rated_movies)]
    return (df.sort_values([score_key], ascending=False)[['titles',"genres","links"]].head(k)) 

#helper function to clean the resultant data
def clean_data(df):
    df_dict = df.to_dict('index')
    movie_list = []

    for item in df_dict:
        movie_dict = dict()
        movie_dict['name']= df_dict[item]['titles']
        movie_dict['link'] = df_dict[item]['links']
        movie_dict['genre']=df_dict[item]['genres'].split('-')
        movie_list.append(movie_dict)
    return movie_list

#.......Process starts from here.....

#loading the data
ratings = pd.read_csv(BASE_DIR+"data/ratings_df.csv")
movies = pd.read_csv(BASE_DIR+"data/movies_df.csv")
users = pd.read_csv(BASE_DIR + "data/users_df.csv")

#setting up the columns
genre_cols = [
    "unknown", "Action", "Adventure", "Animation", "Children's", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
    "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western"
]
movies_cols = [
    'movie_id', 'title', 'release_date', "video_release_date", "imdb_url"
] + genre_cols

# Since the ids start at 1, we shift them to start at 0.
users["user_id"] = users["user_id"].apply(lambda x: str(x-1))
movies["movie_id"] = movies["movie_id"].apply(lambda x: str(x-1))
movies["year"] = movies['release_date'].apply(lambda x: str(x).split('-')[-1])
ratings["movie_id"] = ratings["movie_id"].apply(lambda x: str(x-1))
ratings["user_id"] = ratings["user_id"].apply(lambda x: str(x-1))
ratings["rating"] = ratings["rating"].apply(lambda x: float(x))

mark_genres(movies, genre_cols)

# user_data
# data = [
#     {"_id":"60bbf73b5fe6f41ef745e877",
#     "movie_id":"60bbc6e79d10a3281076bdc4",
#     "user_id":"60bbecff068e973dfc84e487",
#     "__v":0,"movie_title":"Return of the Jedi (1983)",
#     "rating":5,
#     "movie_link":"https://m.media-amazon.com/images/M/MV5BMTQ2YTE0MmItODU3MC00MTQxLTg5NzQtYmIyZTVhOGQ2NjYwXkEyXkFqcGdeQXVyNzg5OTk2OA@@._V1_.jpg"},
#     {"_id":"60bbfc935fe6f41ef745ec19","movie_id":"60bbc6e79d10a3281076bd41","user_id":"60bbecff068e973dfc84e487","__v":0,"movie_link":"https://m.media-amazon.com/images/M/MV5BNzVlY2MwMjktM2E4OS00Y2Y3LWE3ZjctYzhkZGM3YzA1ZWM2XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_.jpg","movie_title":"Star Wars (1977)","rating":2},{"_id":"60bbfc985fe6f41ef745ec23","movie_id":"60bbc6e79d10a3281076bd10","user_id":"60bbecff068e973dfc84e487","__v":0,"movie_link":"https://m.media-amazon.com/images/M/MV5BMDU2ZWJlMjktMTRhMy00ZTA5LWEzNDgtYmNmZTEwZTViZWJkXkEyXkFqcGdeQXVyNDQ2OTk4MzI@._V1_.jpg","movie_title":"Toy Story (1995)","rating":4},{"_id":"60bc96595fe6f41ef745f6bc","movie_id":"60bbc6e79d10a3281076bd16","user_id":"60bbecff068e973dfc84e487","__v":0,"movie_link":"https://m.media-amazon.com/images/M/MV5BN2Y2OWU4MWMtNmIyMy00YzMyLWI0Y2ItMTcyZDc3MTdmZDU4XkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_.jpg","movie_title":"Twelve Monkeys (1995)","rating":2}]

data = json.load(sys.stdin)['data']

#removing unwanted keys
for d in data:
    d['movie_id']=movies[movies['movie_title']==d['movie_title']].iloc[0]['movie_id']
    d['user_id']=943
    del d['__v']
    del d['_id']
    del d['movie_link']
    del d['movie_title']

#creating the dataframe for the user ratings and adding it to the ratings df
my_ratings  = pd.DataFrame(data,columns=['movie_id','user_id','rating'])
ratings = ratings.append(my_ratings, ignore_index=True)

#adding the data to the users df
if users.shape[0] == 943:
    users = users.append(users.iloc[942], ignore_index=True)
    users["user_id"][943] = "943"

ratings[ratings.user_id=="943"].merge(movies[['movie_id', 'movie_title']])

# Build the CF model and train it.
model = build_model(ratings, embedding_dim=30, init_stddev=0.5)
model.train(num_iterations=1000, learning_rate=10.)

#getting the recommended movies for user
recommended_movies = user_recommendations(model, measure=COSINE, k=10)
movie_list = clean_data(recommended_movies)
print(json.dumps({"movie_list":movie_list}))


