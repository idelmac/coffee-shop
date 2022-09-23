import os
from urllib import response
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from marshmallow import ValidationError
import sys

from .database.models import db_drop_and_create_all, setup_db, Drink, DrinkSchema, RecipeSchema
from .auth.auth import AuthError, check_permissions, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

AUTH0_DOMAIN = 'idelmac.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee-shop'

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

@app.route('/headers')
@requires_auth('post:drinks')
def headers(jwt):
    print(jwt)
    return 'not implemented'

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
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
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

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
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

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks", methods=["POST"])
@requires_auth('post:drinks')
def create_drink(payload):
    body = request.get_json()
    try:
        schema = DrinkSchema()
        result = schema.load(body)
    except ValidationError as err:
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

        new_drink = Drink.query.filter(Drink.title==title).order_by(Drink.id).all()
        formated_drink = format_drinks_long(new_drink)

        return jsonify({
            "sucess": True,
            "status": 200,
            "drink": formated_drink
        })
    except Exception:
        print(sys.exc_info())
        abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
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

        updated_drink = Drink.query.filter(Drink.id==drink_id).all()
        formated_drink = format_drinks_long(updated_drink)

        return jsonify({
            "sucess": True,
            "status": 200,
            "drinks": formated_drink
        })
    except Exception:
        print(sys.exc_info())
        abort(422)
    
'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
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
'''
Example error handling for unprocessable entity
'''

@app.errorhandler(400)
def bad_request(error):
    return (jsonify({"success": False,
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


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def auth_error(error):
    response = jsonify(error.error)
    response.status_code = error.status_code
    
    return response