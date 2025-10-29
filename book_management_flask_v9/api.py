
import time
import json
import hashlib
import os
import jwt
import requests
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, abort, current_app, make_response, render_template, redirect
from urllib.parse import urlencode
from sqlalchemy.exc import IntegrityError
from . import db
from .models import BookTitle, BookCopy, User, Borrowing

api = Blueprint("api", __name__, url_prefix="/api")

SECRET_KEY = os.getenv("SECRET_KEY", "nmhung_secret")

# ==========================================
# SIMPLE IN-MEMORY CACHE
# ==========================================
CACHE = {}
CACHE_TTL = 60  # 1 minute

def cache_get(key):
    entry = CACHE.get(key)
    if not entry:
        return None
    if time.time() - entry["time"] > entry["ttl"]:
        del CACHE[key]
        return None
    return entry["data"]

def cache_set(key, value, ttl=CACHE_TTL):
    CACHE[key] = {"data": value, "time": time.time(), "ttl": ttl}

def cache_delete_prefix(prefix):
    for key in list(CACHE.keys()):
        if key.startswith(prefix):
            del CACHE[key]

def make_cache_key(path, params=None):
    params = json.dumps(params or {}, sort_keys=True)
    return hashlib.sha1(f"{path}|{params}".encode()).hexdigest()

# ==========================================
# JWT MODE and OAUTH2 INTROSPECTION MODE
# ==========================================
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allow unauthenticated access to documentation and OpenAPI YAML
        if request.path.startswith("/swagger") or request.path.startswith("/apidocs") or request.path.startswith("/flasgger_static") or request.path == "/openapi.yaml":
            return f(None, *args, **kwargs)

        token = None
        if "Authorization" in request.headers:
            parts = request.headers["Authorization"].split(" ")
            if len(parts) == 2 and parts[0] == "Bearer":
                token = parts[1]

        if not token:
            return jsonify({"message": "Missing token"}), 401

        auth_mode = current_app.config.get('AUTH_MODE', 'jwt')

        # JWT mode: decode locally using SECRET_KEY
        if auth_mode == 'jwt':
            try:
                data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                current_user = User.query.get(data["id"])
                if not current_user:
                    abort(401, "Invalid user")
            except Exception as e:
                abort(401, f"Invalid token: {str(e)}")

            return f(current_user, *args, **kwargs)

        # OAuth2 introspection mode: call introspection endpoint
        elif auth_mode == 'oauth2':
            introspect_url = current_app.config.get('OAUTH2_INTROSPECTION_URL')
            if not introspect_url:
                abort(500, "OAuth2 introspection URL not configured")

            client_id = current_app.config.get('OAUTH2_INTROSPECTION_CLIENT_ID')
            client_secret = current_app.config.get('OAUTH2_INTROSPECTION_CLIENT_SECRET')
            try:
                auth = None
                headers = {'Accept': 'application/json'}
                data = {'token': token}
                # Use HTTP Basic auth if client credentials provided
                if client_id and client_secret:
                    auth = (client_id, client_secret)

                resp = requests.post(introspect_url, data=data, headers=headers, auth=auth, timeout=5)
                if resp.status_code != 200:
                    abort(401, 'Token introspection failed')
                info = resp.json()
                # RFC7662: active boolean
                if not info.get('active'):
                    abort(401, 'Token inactive')
                # Extract user id from configured field (default 'sub')
                user_field = current_app.config.get('OAUTH2_USER_ID_FIELD', 'sub')
                user_id = info.get(user_field)
                if not user_id:
                    abort(401, 'User id not present in introspection response')
                current_user = User.query.get(user_id)
                if not current_user:
                    abort(401, 'User not found')
            except requests.RequestException as e:
                abort(502, f'Introspection request failed: {str(e)}')
            except ValueError:
                abort(502, 'Invalid JSON from introspection endpoint')

            return f(current_user, *args, **kwargs)

        else:
            abort(500, f'Unknown AUTH_MODE: {auth_mode}')
    return decorated

# ==========================================
# PAGINATION HELPER
# ==========================================
def paginate(query):
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, {
        "page": page,
        "size": size,
        "total_items": total,
        "total_pages": (total + size - 1) // size,
    }

# ==========================================
# AUTH API
# ==========================================
@api.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    if "name" not in data or "email" not in data:
        abort(400, "Missing name or email")
    if User.query.filter_by(email=data["email"]).first():
        abort(400, "Email already exists")
    u = User(name=data["name"], email=data["email"])
    db.session.add(u)
    db.session.commit()
    return jsonify({"message": "User created", "id": u.id}), 201

@api.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=data.get("email")).first()
    if not user:
        abort(401, "Invalid email")
    token = jwt.encode(
        {"id": user.id, "exp": datetime.utcnow() + timedelta(hours=2)},
        SECRET_KEY,
        algorithm="HS256",
    )
    return jsonify({"token": token}), 200


# ==========================================
# GOOGLE OAUTH2 (OpenID Connect) endpoints
# ==========================================
@api.route('/auth/google', methods=['GET'])
def google_auth_start():
    #Đoạn này là để khởi tạo URL đăng nhập Google OAuth2
    #Sau khi gọi xong, lấy auth_url để chuyển đến popup đăng nhập bằng Google
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    redirect_uri = current_app.config.get('GOOGLE_OAUTH_REDIRECT_URI')
    scopes = current_app.config.get('GOOGLE_OAUTH_SCOPES', 'openid email profile')
    if not client_id or not redirect_uri:
        abort(500, 'Google OAuth not configured')
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': scopes,
        'access_type': 'offline',
        'prompt': 'consent'
    }
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
    return jsonify({'auth_url': url})

#Chỗ này xử lý callback từ Google sau khi đăng nhập thành công
@api.route('/auth/google/callback', methods=['GET'])
def google_auth_callback():
    code = request.args.get('code')
    error = request.args.get('error')
    if error:
        abort(400, f'Google auth error: {error}')
    if not code:
        abort(400, 'Missing code')
    #Đoạn này là sau khi gọi api http://localhost:5000/api/auth/google ở trên, chọn TK Google đăng nhập
    #Gọi API để lấy token
    token_url = 'https://oauth2.googleapis.com/token'
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
    redirect_uri = current_app.config.get('GOOGLE_OAUTH_REDIRECT_URI')
    if not client_id or not client_secret or not redirect_uri:
        abort(500, 'Google OAuth not configured')

    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    try:
        r = requests.post(token_url, data=data, timeout=5)
        r.raise_for_status()
        tok = r.json()
    except requests.RequestException as e:
        abort(502, f'Failed to exchange code: {str(e)}')

    access_token = tok.get('access_token')
    if not access_token:
        abort(502, 'No access_token returned')
    try:
        hu = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers={
            'Authorization': f'Bearer {access_token}'
        }, timeout=5)
        hu.raise_for_status()
        info = hu.json()
    except requests.RequestException as e:
        abort(502, f'Failed to fetch userinfo: {str(e)}')

    google_sub = info.get('sub')
    email = info.get('email')
    name = info.get('name') or info.get('email')
    if not google_sub or not email:
        abort(400, 'Invalid userinfo from Google')


    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(name=name, email=email)
        db.session.add(user)
        db.session.commit()

    token = jwt.encode(
        {"id": user.id, "exp": datetime.utcnow() + timedelta(hours=2)},
        SECRET_KEY,
        algorithm="HS256",
    )
    
    # Return HTML page that saves token to localStorage
    return render_template('google_callback.html', token=token)

# ==========================================
# BOOK TITLE APIs
# ==========================================
@api.route("/book_titles", methods=["GET"])
@token_required
def list_book_titles(current_user):
    key = make_cache_key(request.path, request.args)
    cached = cache_get(key)
    if cached:
        return jsonify(cached)

    query = BookTitle.query
    items, page_info = paginate(query)
    data = [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "publisher": b.publisher,
            "year": b.year,
            "category": b.category,
            "copies_count": len(b.copies),
        }
        for b in items
    ]
    response = {"items": data, "page": page_info}
    cache_set(key, response)
    return jsonify(response)

@api.route("/book_titles", methods=["POST"])
@token_required
def create_book_title(current_user):
    data = request.get_json() or {}
    if "title" not in data or "author" not in data:
        abort(400, "Missing title or author")
    # whitelist allowed fields
    allowed = {"title", "author", "publisher", "year", "category"}
    clean = {k: data[k] for k in data if k in allowed}
    t = BookTitle(**clean)
    db.session.add(t)
    db.session.commit()
    cache_delete_prefix("/api/book_titles")
    return jsonify({"message": "BookTitle created", "id": t.id}), 201

@api.route("/book_titles/<int:id>", methods=["GET"])
@token_required
def get_book_title(current_user, id):
    t = BookTitle.query.get_or_404(id)
    data = {
        "id": t.id,
        "title": t.title,
        "author": t.author,
        "publisher": t.publisher,
        "year": t.year,
        "category": t.category,
        "copies": [
            {
                "id": c.id,
                "barcode": c.barcode,
                "available": c.available,
                "condition": c.condition,
            }
            for c in t.copies
        ],
    }
    return jsonify(data)

@api.route("/book_titles/<int:id>", methods=["PUT"])
@token_required
def update_book_title(current_user, id):
    t = BookTitle.query.get_or_404(id)
    data = request.get_json() or {}
    for field in ("title", "author", "publisher", "year", "category"):
        if field in data:
            setattr(t, field, data[field])
    db.session.commit()
    cache_delete_prefix("/api/book_titles")
    return jsonify({"message": "BookTitle updated"})

@api.route("/book_titles/<int:id>", methods=["DELETE"])
@token_required
def delete_book_title(current_user, id):
    t = BookTitle.query.get_or_404(id)
    if t.copies:
        abort(400, "Cannot delete a title with copies")
    db.session.delete(t)
    db.session.commit()
    cache_delete_prefix("/api/book_titles")
    return jsonify({"message": "BookTitle deleted"})

# ==========================================
# BOOK COPY APIs
# ==========================================
@api.route("/book_copies", methods=["GET"])
@token_required
def list_book_copies(current_user):
    key = make_cache_key(request.path, request.args)
    cached = cache_get(key)
    if cached:
        return jsonify(cached)
    query = BookCopy.query
    items, page_info = paginate(query)
    data = [
        {
            "id": c.id,
            "book_title_id": c.book_title_id,
            "barcode": c.barcode,
            "available": c.available,
            "condition": c.condition,
        }
        for c in items
    ]
    response = {"items": data, "page": page_info}
    cache_set(key, response)
    return jsonify(response)

@api.route("/book_copies", methods=["POST"])
@token_required
def create_book_copy(current_user):
    data = request.get_json() or {}
    if "book_title_id" not in data or "barcode" not in data:
        abort(400, "Missing book_title_id or barcode")
    # verify FK exists
    title = BookTitle.query.get(data.get("book_title_id"))
    if not title:
        abort(400, "Invalid book_title_id")
    # whitelist
    allowed = {"book_title_id", "barcode", "available", "condition"}
    clean = {k: data[k] for k in data if k in allowed}
    copy = BookCopy(**clean)
    db.session.add(copy)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(400, "Duplicate barcode")
    cache_delete_prefix("/api/book_copies")
    return jsonify({"message": "BookCopy created", "id": copy.id}), 201

@api.route("/book_copies/<int:id>", methods=["PUT"])
@token_required
def update_book_copy(current_user, id):
    c = BookCopy.query.get_or_404(id)
    data = request.get_json() or {}
    for field in ("available", "condition"):
        if field in data:
            setattr(c, field, data[field])
    db.session.commit()
    cache_delete_prefix("/api/book_copies")
    return jsonify({"message": "BookCopy updated"})

@api.route("/book_copies/<int:id>", methods=["DELETE"])
@token_required
def delete_book_copy(current_user, id):
    c = BookCopy.query.get_or_404(id)
    if Borrowing.query.filter_by(book_copy_id=c.id, return_date=None).first():
        abort(400, "Book copy currently borrowed")
    db.session.delete(c)
    db.session.commit()
    cache_delete_prefix("/api/book_copies")
    return jsonify({"message": "BookCopy deleted"})

# ==========================================
# BORROWING APIs
# ==========================================
@api.route("/borrowings", methods=["GET"])
@token_required
def list_borrowings(current_user):
    query = Borrowing.query
    items, page_info = paginate(query)
    data = []
    for b in items:
        overdue = (
            b.due_date and not b.return_date and datetime.utcnow() > b.due_date
        )
        days_overdue = (
            (datetime.utcnow().date() - b.due_date.date()).days
            if overdue
            else 0
        )
        data.append(
            {
                "id": b.id,
                "book_copy_id": b.book_copy_id,
                "user_id": b.user_id,
                "borrow_date": b.borrow_date.isoformat(),
                "due_date": b.due_date.isoformat() if b.due_date else None,
                "return_date": b.return_date.isoformat()
                if b.return_date
                else None,
                "fine": b.fine,
                "overdue": overdue,
                "days_overdue": days_overdue,
            }
        )
    return jsonify({"items": data, "page": page_info})

@api.route("/borrowings", methods=["POST"])
@token_required
def borrow_book(current_user):
    if not current_user:
        abort(401, "Authentication required")
    data = request.get_json() or {}
    copy = BookCopy.query.get_or_404(data.get("book_copy_id"))
    if not copy.available:
        abort(400, "Book not available")
    due_date = data.get("due_date")
    due_dt = datetime.fromisoformat(due_date) if due_date else None
    borrow = Borrowing(book_copy_id=copy.id, user_id=current_user.id, due_date=due_dt)
    copy.available = False
    db.session.add(borrow)
    db.session.commit()
    return jsonify({"message": "Book borrowed", "id": borrow.id}), 201

@api.route("/borrowings/<int:id>/return", methods=["POST"])
@token_required
def return_book(current_user, id):
    b = Borrowing.query.get_or_404(id)
    if b.return_date:
        abort(400, "Already returned")
    b.return_date = datetime.utcnow()
    fine_per_day = current_app.config.get("LIBRARY_FINE_PER_DAY", 5000)
    if b.due_date and b.return_date > b.due_date:
        days = (b.return_date.date() - b.due_date.date()).days
        b.fine = days * fine_per_day
    copy = BookCopy.query.get(b.book_copy_id)
    copy.available = True
    db.session.commit()
    return jsonify({"message": "Book returned", "fine": b.fine})
