import os
from sqlalchemy import Column, String, Integer
from flask_sqlalchemy import SQLAlchemy
import json
from marshmallow import Schema, fields, validate
from flask_migrate import Migrate

database_filename = "database.db"
project_dir = os.path.dirname(os.path.abspath(__file__))
database_path = "sqlite:///{}".format(os.path.join(
                                                project_dir,
                                                database_filename))

db = SQLAlchemy()


def setup_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['JSON_SORT_KEYS'] = False
    db.app = app
    db.init_app(app)
    migrate = Migrate(app, db)


def db_drop_and_create_all():
    db.drop_all()
    db.create_all()
    # add one demo row which is helping in POSTMAN test
    drink = Drink(
        title='water',
        recipe='[{"name": "water", "color": "blue", "parts": 1}]'
    )
    drink.insert()

# ROUTES


class RecipeSchema(Schema):
    color = fields.String(
                        required=True,
                        allow_none=False,
                        validate=validate.Length(min=1))
    name = fields.String(
                        required=True,
                        allow_none=False,
                        validate=validate.Length(min=1))
    parts = fields.Integer(
                        required=True,
                        allow_none=False,
                        validate=validate.Range(min=1))


class DrinkSchema(Schema):
    id = fields.Integer(required=False,
                        allow_none=True)
    title = fields.String(
                            required=True,
                            allow_none=False,
                            validate=validate.Length(min=1))
    recipe = fields.List(fields.Nested(RecipeSchema))


class Drink(db.Model):
    id = Column(Integer().with_variant(Integer, "sqlite"),
                primary_key=True,
                autoincrement=True)
    title = Column(String(80), unique=True)
    recipe = Column(String(180), nullable=False)

    def short(self):
        short_recipe = [{'color': r['color'], 'parts': r['parts']}
                        for r in
                        json.loads(self.recipe)]
        return {
            'id': self.id,
            'title': self.title,
            'recipe': short_recipe
        }

    def long(self):
        return {
            'id': self.id,
            'title': self.title,
            'recipe': json.loads(self.recipe)
        }

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def __repr__(self):
        return json.dumps(self.short())
