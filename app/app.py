import os
import redis
import json
import psycopg2
from flask import Flask, jsonify, request
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Настройки в app.py
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "crud-db-postgresql"), # Имя сервиса из Helm
    "port": os.getenv("PG_PORT", 5432),
    "database": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "postgres")
}

# Подключение к Redis (имя сервиса из Helm)
cache = redis.Redis(host=os.getenv("REDIS_HOST", "crud-db-redis-master"), port=6379, decode_responses=True)

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# --- CRUD ---


@app.route('/status', methods=['GET'])
def status_check():
    return jsonify({"status": " АОАОАОАО"})


# CREATE
@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, surname, age, town) VALUES (%s, %s, %s, %s) RETURNING id",
        (data['name'], data['surname'], data['age'], data['town'])
    )
    new_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"id": new_id, "status": "created"}), 201

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # ПРИНУДИТЕЛЬНЫЙ ПРИНТ (появится в docker logs)
    print(f"--> Request for user {user_id}", flush=True)

    try:
        cached_user = cache.get(f"user:{user_id}")
        if cached_user:
            print(f"--> Found in REDIS", flush=True)
            return jsonify({"data": json.loads(cached_user), "source": "cache"})
    except Exception as e:
        print(f"--> REDIS ERROR: {e}", flush=True)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        try:
            cache.setex(f"user:{user_id}", 60, json.dumps(user))
            print(f"--> Saved to REDIS", flush=True)
        except Exception as e:
            print(f"--> REDIS SAVE ERROR: {e}", flush=True)
            
        return jsonify({"data": user, "source": "database"})
    
    return jsonify({"error": "Not found"}), 404

# UPDATE
@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET name=%s, town=%s WHERE id=%s",
        (data['name'], data['town'], user_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    # Инвалидируем кеш (удаляем старые данные)
    cache.delete(f"user:{user_id}")
    return jsonify({"status": "updated"})

# DELETE
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    cache.delete(f"user:{user_id}")
    return jsonify({"status": "deleted"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
