<div align="left">
<h1>PulsarNews</h1>
</div>
<br>

Fork from [**flask_hackernews**](https://hackernews.duarteocarmo.com/) is a minimalistic hackernews clone. 

It uses: 

- `flask` as a web framework.
- `flask-sqlalchemy` as an ORM.
- `SQLite` as a database.
- `heroku` for a simple deployment.
- Other less known libraries listed in`requirements.txt`


### Contents

- [Features](#Features)
- [Set up](#set-up-instructions)
- [Deployment](#Deployment)
- [About](#About)


### Features
- user authentication
- upvoting on comments and posts
- karma
- user profiles
- post ranking algorithms based on the ['official'](https://news.ycombinator.com/item?id=1781417) one
- comment replies, threading and more!

### Set up Instructions

*Follow these instructions if you wish to run this project locally*

- clone this repo

```bash
$ git clone https://github.com/gixita/pulsarnews
```
- for server installation 
```bash
$ 
```


- create a virtual environment with the latest python version
- install requirements

```bash
(venv) $ pip install -r requirements.txt
```

- create a `.env` file in the home directory based on the file `.env`

- Modify the variable `is_subdomain_enable = True` to `is_subdomain_enable = False` in `__init__.py` in the `app` folder, that will deactivate the management of subdomain and enable to use `localhost`.

- initiate your database

```bash
(venv) $ flask db init
(venv) $ flask db migrate -m "first init"
(venv) $ flask db upgrade
```

- 🎉Run!!🎉

```bash
(venv) $ flask run
```

- visit [`http://localhost:5000`](http://localhost:5000) to check it out.

### Deployment

*Follow these instructions to deploy your to the 🌎*

- Heroku: follow [this guide](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xviii-deployment-on-heroku).
- Docker: follow [this guide](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xix-deployment-on-docker-containers).
- Linux: follow [this guide](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xvii-deployment-on-linux).


### About
