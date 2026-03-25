from flask_caching import Cache

# cache instance — initialised in app.py via cache.init_app(app)
# to migrate to Redis: set CACHE_TYPE="RedisCache" and CACHE_REDIS_URL in app.py
cache = Cache()
