from __future__ import annotations

import os, sys
import logging 
from flask import Flask
from flask_cors import CORS

from routes.analyze import analyze_bp
from routes.upload import upload_bp
from routes.download import download_bp

from dotenv import load_dotenv

from extensions import cache

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

load_dotenv()

def create_app() -> Flask:
    app = Flask(__name__)

    ## caching
    app.config["CACHE_TYPE"] = 'SimpleCache'
    app.config["CACHE_DEFAULT_TIMEOUT"] = 1800
    cache.init_app(app)

    ## end of caching
    CORS(
        app,
        resources={r"/*": {"origins": "http://localhost:3000"}},
        supports_credentials=False,
    )

    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
    app.config["OUTPUT_FOLDER"] = os.path.join(os.path.dirname(__file__), "outputs")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

    app.register_blueprint(upload_bp, url_prefix="/api")
    app.register_blueprint(analyze_bp, url_prefix="/api")
    app.register_blueprint(download_bp, url_prefix="/api")
    return app


app = create_app()

@app.route("/api/health")
def health():
    return {"status": "ok"}

def validate_environment():
    required_env_variables = ["ANTHROPIC_API_KEY"]

    missing = [var for var in required_env_variables if not os.getenv(var)]

    if missing:
        # logger.critical(f"Missing environment variables: {missing}")
        raise EnvironmentError(f"Missing environment variable(s): {missing}")

    required_directory = ["uploads","output", "cache"]
    for dir in required_directory:
        os.makedirs(dir, exist_ok=True)
    logger.info(f"Environment validated. Required env variable and dirs")

    
if __name__ == "__main__":
    # Development entrypoint. In production, use a WSGI server (gunicorn, etc.).
    validate_environment()
    app.run(host="0.0.0.0", port=5001, debug=True)
