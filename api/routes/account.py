from flask import Blueprint, current_app, request, jsonify

from api.dao.favorites import FavoriteDAO
from api.dao.ratings import RatingDAO

account_routes = Blueprint("account", __name__, url_prefix="/api/account")

@account_routes.route('/', methods=['GET'])
def get_profile():
    # Admin user profile
    admin_user = {
        "userId": "00000000-0000-0000-0000-000000000000",
        "email": "admin@neo4j.com",
        "name": "Admin User",
        "role": "admin"
    }
    return jsonify(admin_user)

@account_routes.route('/favorites', methods=['GET'])
def get_favorites():
    # Admin access - no auth required
    user_id = "00000000-0000-0000-0000-000000000000"

    # Get search parameters
    sort = request.args.get("sort", "title")
    order = request.args.get("order", "ASC")
    limit = request.args.get("limit", 6, type=int)
    skip = request.args.get("skip", 0, type=int)

    # Create the DAO
    dao = FavoriteDAO(current_app.driver)

    output = dao.all(user_id, sort, order, limit, skip)

    return jsonify(output)

@account_routes.route('/favorites/<movie_id>', methods=['POST', 'DELETE'])
def add_favorite(movie_id):
    # Admin access - no auth required
    user_id = "00000000-0000-0000-0000-000000000000"

    # Create the DAO
    dao = FavoriteDAO(current_app.driver)

    if request.method == "POST":
        # Save the favorite
        output = dao.add(user_id, movie_id)
    else:
        # Remove the favorite
        output = dao.remove(user_id, movie_id)

    # Return the output
    return jsonify(output)


@account_routes.route('/ratings/<movie_id>', methods=['POST'])
def save_rating(movie_id):
    # Admin access - no auth required
    user_id = "00000000-0000-0000-0000-000000000000"

    # Get rating from Request
    form_data = request.get_json()
    rating = int(form_data["rating"])

    # Create the DAO
    dao = RatingDAO(current_app.driver)

    # Save the rating
    output = dao.add(user_id, movie_id, rating)

    # Return the output
    return jsonify(output)

