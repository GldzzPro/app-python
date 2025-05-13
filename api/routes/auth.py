from flask import Blueprint, current_app, request, jsonify

from api.dao.auth import AuthDAO

auth_routes = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_routes.route('/register', methods=['POST'])
def register():
    form_data = request.get_json()

    email = form_data['email']
    password = form_data['password']
    name = form_data['name']

    dao = AuthDAO(current_app.driver)

    user = dao.register(email, password, name)

    return jsonify(user)


@auth_routes.route('/login', methods=['POST'])
def login():
    form_data = request.get_json()

    email = form_data['email']
    password = form_data['password']

    dao = AuthDAO(current_app.driver)

    user = dao.authenticate(email, password)

    return jsonify(user)
