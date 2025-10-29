from book_management_flask_v9 import app
from flask_swagger_ui import get_swaggerui_blueprint
from flask import send_from_directory
import os

SWAGGER_URL = '/swagger'
API_URL = '/openapi.yaml'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Book Management API"
    }
)

@app.route('/openapi.yaml')
def serve_openapi_yaml():
    pkg_dir = os.path.dirname(__file__)
    return send_from_directory(pkg_dir, 'openapi.yaml')

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

if __name__ == '__main__':
    app.run(debug=True)