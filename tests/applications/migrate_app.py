from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.route("/")
def index():
    users = User.query.all()
    return [x.to_dict() for x in users]


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    email = db.Column(db.String(255))
    age = db.Column(db.Integer)

    def to_dict(self):
        return {"user": self.username}
