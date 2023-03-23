import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
from sqlalchemy.exc import IntegrityError
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, get_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db = get_db()

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
#with app.app_context():
#    db_drop_and_create_all()


# https://yozdmr.us.auth0.com/authorize?audience=coffeeshop&response_type=token&client_id=ZyPe99NAIlIdm0SQeIvd1d3YWNqUkGNc&redirect_uri=http://127.0.0.1:5000/login-results

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
def drinks():
    drinks = [drink.short() for drink in Drink.query.all()]

    # Makes sure there are drinks to view
    if len(drinks) == 0:
        abort(404)

    return jsonify({
        "success": True,
        "drinks": drinks
    }), 200

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
def drinks_long(self):
    drinks = [drink.long() for drink in Drink.query.all()]

    # Makes sure there are drinks to view
    if len(drinks) == 0:
        abort(404)

    return jsonify({
        "success": True,
        "drinks": drinks
    }), 200

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drinks(self):

    data = request.get_json()

    # Catch duplicate title, return 409 error code
    try:
        new_drink = Drink(title=data.get('title'), recipe='[{"color":"'+data.get('color')+'","name":"'+data.get('name')+'","parts":"'+str(data.get('parts'))+'"}]')
        new_drink.insert()
        db.session.commit()
    except IntegrityError:
        abort(409)

    return jsonify({
        "success": True,
        "drinks": new_drink.long()
    }), 200
    

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
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drinks(self, id: int):
    
    if id is None:
        abort(404)
    
    # Gets request data
    data = request.get_json()

    # Gets the drink based on ID
    drink_to_modify = Drink.query.filter_by(id=id).first()
    
    # Checks to make sure the drink with provided ID exists
    if drink_to_modify is not None:

        # Gets the recipe data by converting the recipe into json
        recipe_data = json.loads(drink_to_modify.recipe[1:len(drink_to_modify.recipe)-1])

        # Each part of the drink is updated
        if 'title' in data and drink_to_modify.title != data.get('title'):
            drink_to_modify.title = data.get('title')

        if 'name' in data and recipe_data['name'] != data.get('name'):
            drink_to_modify.recipe = '[{"color":"'+recipe_data['color']+'","name":"'+data.get('name')+'","parts":"'+recipe_data['parts']+'"}]'

        if 'parts' in data and recipe_data['parts'] != data.get('parts'):
            drink_to_modify.recipe = '[{"color":"'+recipe_data['color']+'","name":"'+recipe_data['name']+'","parts":"'+str(data.get('parts'))+'"}]'

        if 'color' in data and recipe_data['color'] != data.get('color'):
            drink_to_modify.recipe = '[{"color":"'+data.get('color')+'","name":"'+recipe_data['name']+'","parts":"'+recipe_data['parts']+'"}]'
        
        db.session.commit()
        
    else:
        abort(404)

    return jsonify({
        "success": True,
        "drinks": [drink_to_modify.long()]
    }), 200

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
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(self, id: int):
    
    # Gets the drink using id, if it doesn't exist 404 error
    drink_to_delete = Drink.query.filter_by(id=id).first()
    if drink_to_delete is not None:
        db.session.delete(drink_to_delete)
        db.session.commit()
    else:
        abort(404)

    return jsonify({
        "success": True,
        "delete": id
    }), 200

# Error Handling
'''
Example error handling for unprocessable entity
'''


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
@app.errorhandler(409)
def request_conflict(error):
    return jsonify({
        "success": False,
        "error": 409,
        "message": "request conflict"
        }), 409

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
        }), 404

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(401)
def authentication_error(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "authentication error"
        }), 401