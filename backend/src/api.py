import os
from flask import Flask, request, jsonify, abort
import json
from flask_cors import CORS
from marshmallow import ValidationError
import sys

from .database.models import (db_drop_and_create_all,
                              setup_db,
                              Drink,
                              DrinkSchema)
from .auth.auth import (AuthError,
                        check_permissions,
                        requires_auth)

app = Flask(__name__)
setup_db(app)
CORS(app)

AUTH0_DOMAIN = 'idelmac.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee-shop'

db_drop_and_create_all()


def format_drinks_short(drinks):
    formated_drinks = []
    for drink in drinks:
        formated_drinks.append(drink.short())
    return formated_drinks


def format_drinks_long(drinks):
    formated_drinks = []
    for drink in drinks:
        formated_drinks.append(drink.long())
    return formated_drinks


# ROUTES
@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.order_by(Drink.id).all()
    formated_drinks = []

    if len(drinks) == 0:
        abort(404)

    formated_drinks = format_drinks_short(drinks)

    return jsonify({
        "success": True,
        "status": 200,
        "drinks": formated_drinks
    })


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    drinks = Drink.query.order_by(Drink.id).all()
    formated_drinks = []

    if len(drinks) == 0:
        abort(404)

    formated_drinks = format_drinks_long(drinks)

    return jsonify({
        "success": True,
        "status": 200,
        "drinks": formated_drinks
    })


@app.route("/drinks", methods=["POST"])
@requires_auth('post:drinks')
def create_drink(payload):
    body = request.get_json()
    try:
        schema = DrinkSchema()
        result = schema.load(body)
    except ValidationError as err:
        print(err.messages)
        return jsonify(err.messages), 400

    title = body.get("title", None)
    recipe = body.get("recipe", None)
    print(recipe)
    sameDrink = Drink.query.filter(
        Drink.title.ilike(f'%{title}%')
        ).order_by(Drink.id).all()

    if len(sameDrink) > 0:
        abort(409, "duplicated drink")

    try:
        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()

        new_drink = Drink.query.filter(
            Drink.title == title
            ).order_by(Drink.id).all()

        formated_drink = format_drinks_long(new_drink)

        return jsonify({
            "sucess": True,
            "status": 200,
            "drink": formated_drink
        })
    except Exception:
        print(sys.exc_info())
        abort(422)


@app.route("/drinks/<int:drink_id>", methods=["PATCH"])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    drink = Drink.query.filter(
            Drink.id == drink_id
            ).one_or_none()

    if drink is None:
        abort(404)

    body = request.get_json()
    try:
        schema = DrinkSchema()
        result = schema.load(body)
    except ValidationError as err:
        return jsonify(err.messages), 400

    title = body.get("title", None)
    recipe = body.get("recipe", None)

    try:
        drink.title = title
        drink.recipe = json.dumps(recipe)
        drink.update()

        updated_drink = Drink.query.filter(
            Drink.id == drink_id
            ).all()

        formated_drink = format_drinks_long(updated_drink)

        return jsonify({
            "sucess": True,
            "status": 200,
            "drinks": formated_drink
        })
    except Exception:
        print(sys.exc_info())
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_question(payload, drink_id):
    drink = Drink.query.filter(
        Drink.id == drink_id
        ).one_or_none()

    if drink is None:
        abort(404)

    try:
        drink.delete()
        return jsonify({
            "success": True,
            "status": 200,
            "deleted": drink_id
        })
    except Exception:
        print(sys.exc_info())
        abort(422)


# Error Handling
@app.errorhandler(400)
def bad_request(error):
    return (jsonify({
                    "success": False,
                    "error": 400,
                    "message": "bad request"}),
            400)


@app.errorhandler(404)
def not_found(error, message="resource not found"):
    return (jsonify({
                    "success": False,
                    "error": 404,
                    "message": message}),
            404)


@app.errorhandler(409)
def resource_conflict(error, message="resources conflict"):
    return (jsonify({
                    "success": False,
                    "error": 409,
                    "message": message}),
            409)


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(AuthError)
def auth_error(auth_error):
    exception = jsonify(auth_error.error)
    exception.status_code = auth_error.status_code
    return exception
