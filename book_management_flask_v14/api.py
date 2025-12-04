
import time
import json
import hashlib
import os
import jwt
import requests
import sys
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, abort, current_app, make_response, render_template, redirect
from urllib.parse import urlencode
from sqlalchemy.exc import IntegrityError
from . import db
from .models import BookTitle, BookCopy, User, Borrowing
from .logging_config import get_logger, log_request, log_db_operation, log_cache_operation
from .metrics import (
    record_cache_hit, record_cache_miss, record_cache_set, record_cache_delete,
    update_cache_size, record_book_borrowed, record_book_returned,
    update_active_borrowings, record_user_registration, record_auth_attempt
)
from .webhook import send_webhook_notification, EVENT_BOOK_BORROWED, EVENT_BOOK_RETURNED, EVENT_USER_REGISTERED, EVENT_ERROR

api = Blueprint("api", __name__, url_prefix="/api")

SECRET_KEY = os.getenv("SECRET_KEY", "nmhung_secret")

# Get logger instance
logger = get_logger()

# ==========================================
# SIMPLE IN-MEMORY CACHE
# ==========================================
CACHE = {}
CACHE_TTL = 60  # 1 minute

def cache_get(key):
    entry = CACHE.get(key)
    if not entry:
        record_cache_miss()
        log_cache_operation(logger, 'GET', key, hit=False)
        return None
    if time.time() - entry["time"] > entry["ttl"]:
        del CACHE[key]
        record_cache_miss()
        log_cache_operation(logger, 'GET', key, hit=False)
        return None
    record_cache_hit()
    log_cache_operation(logger, 'GET', key, hit=True)
    return entry["data"]

def cache_set(key, value, ttl=CACHE_TTL):
    CACHE[key] = {"data": value, "time": time.time(), "ttl": ttl}
    record_cache_set()
    log_cache_operation(logger, 'SET', key)
    # Update cache size metrics
    cache_size_bytes = sys.getsizeof(CACHE)
    update_cache_size(cache_size_bytes, len(CACHE))

def cache_delete_prefix(prefix):
    deleted_count = 0
    for key in list(CACHE.keys()):
        if key.startswith(prefix):
            del CACHE[key]
            deleted_count += 1
    if deleted_count > 0:
        record_cache_delete()
        log_cache_operation(logger, 'DELETE', f"{prefix}*")
        # Update cache size metrics
        cache_size_bytes = sys.getsizeof(CACHE)
        update_cache_size(cache_size_bytes, len(CACHE))

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
        # First try to get token from HTTP-only cookie
        token = request.cookies.get('auth_token')
        
        # Fallback to Authorization header (for backward compatibility)
        if not token and "Authorization" in request.headers:
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
        logger.warning("Registration attempt with missing fields", extra={'data': data})
        abort(400, "Missing name or email")
    if User.query.filter_by(email=data["email"]).first():
        logger.warning(f"Registration attempt with existing email: {data['email']}")
        abort(400, "Email already exists")
    
    try:
        u = User(name=data["name"], email=data["email"])
        db.session.add(u)
        db.session.commit()
        
        record_user_registration()
        log_db_operation(logger, 'CREATE', 'user', u.id, success=True)
        logger.info(f"New user registered: {u.email}", extra={'user_id': u.id})
        
        # Send webhook notification
        send_webhook_notification(EVENT_USER_REGISTERED, {
            'user_id': u.id,
            'user_name': u.name,
            'user_email': u.email
        })
        
        return jsonify({"message": "User created", "id": u.id}), 201
    except Exception as e:
        db.session.rollback()
        log_db_operation(logger, 'CREATE', 'user', None, success=False, error=str(e))
        logger.error(f"Failed to register user: {str(e)}", exc_info=True)
        abort(500, "Failed to create user")

@api.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    
    user = User.query.filter_by(email=email).first()
    if not user:
        record_auth_attempt(success=False)
        logger.warning(f"Failed login attempt for email: {email}")
        abort(401, "Invalid email")
    
    token = jwt.encode(
        {"id": user.id, "exp": datetime.utcnow() + timedelta(hours=2)},
        SECRET_KEY,
        algorithm="HS256",
    )
    
    record_auth_attempt(success=True)
    logger.info(f"User logged in: {user.email}", extra={'user_id': user.id})
    
    # Set token in HTTP-only cookie
    response = make_response(jsonify({
        "message": "Login successful",
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "token": token
    }), 200)
    
    # Set HTTP-only cookie with security flags
    response.set_cookie(
        'auth_token',
        token,
        httponly=True,      # Prevents JavaScript access (XSS protection)
        secure=False,       # Set to True in production with HTTPS
        samesite='Lax',     # CSRF protection
        max_age=7200        # 2 hours (same as token expiration)
    )
    
    return response

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
    
    # Create response with template
    response = make_response(render_template('google_callback.html', token=token))
    
    # Set HTTP-only cookie
    response.set_cookie(
        'auth_token',
        token,
        httponly=True,
        secure=False,       # Set to True in production with HTTPS
        samesite='Lax',
        max_age=7200        # 2 hours
    )
    
    return response


# ==========================================
# LOGOUT endpoint
# ==========================================
@api.route("/auth/logout", methods=["POST"])
def logout():
    response = make_response(jsonify({"message": "Logged out successfully"}), 200)
    # Clear the auth_token cookie
    response.set_cookie('auth_token', '', expires=0, httponly=True, samesite='Lax')
    return response


# ==========================================
# User info endpoint
# ==========================================
@api.route("/auth/me", methods=["GET"])
@token_required
def get_current_user(current_user):
    return jsonify({
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }), 200

# ==========================================
# BOOK TITLE APIs - HEADER VERSIONING
# ==========================================
# Strategy: Version specified via Accept or X-API-Version header
# Default (no header): v1 (legacy format)
# Accept: application/vnd.library.v1+json OR X-API-Version: 1 -> v1
# Accept: application/vnd.library.v2+json OR X-API-Version: 2 -> v2
# Migration guide: See API_VERSIONING.md

def get_book_title_version():
    """Get API version from Accept header or X-API-Version header (default: 1)"""
    # Check X-API-Version header first (simpler)
    version_header = request.headers.get('X-API-Version')
    if version_header:
        try:
            return int(version_header)
        except (ValueError, TypeError):
            pass
    
    # Check Accept header for vendor media type
    accept = request.headers.get('Accept', '')
    if 'application/vnd.library.v2+json' in accept:
        return 2
    elif 'application/vnd.library.v1+json' in accept:
        return 1
    
    # Default to v1
    return 1

def serialize_book_title_v1(b):
    """Serialize book title in v1 format (legacy)"""
    return {
        "id": b.id,
        "title": b.title,
        "author": b.author,
        "publisher": b.publisher,
        "year": b.year,
        "category": b.category,
        "copies_count": len(b.copies),
    }

def serialize_book_title_v2(b):
    """Serialize book title in v2 format (enhanced with statistics)"""
    copies = b.copies
    available_count = sum(1 for c in copies if c.available)
    borrowed_count = len(copies) - available_count
    
    # Count by condition
    condition_stats = {"Good": 0, "Damaged": 0, "Lost": 0}
    for c in copies:
        condition_stats[c.condition] = condition_stats.get(c.condition, 0) + 1
    
    return {
        "id": b.id,
        "title": b.title,
        "author": b.author,
        "publisher": b.publisher,
        "year": b.year,
        "category": b.category,
        "statistics": {
            "totalCopies": len(copies),
            "availableCopies": available_count,
            "borrowedCopies": borrowed_count,
            "conditionBreakdown": condition_stats
        },
        "metadata": {
            "hasAvailableCopies": available_count > 0,
            "allCopiesBorrowed": borrowed_count == len(copies) and len(copies) > 0
        }
    }

@api.route("/book_titles", methods=["GET"])
@token_required
def list_book_titles(current_user):
    """
    Get list of book titles with version support via header
    
    Headers:
    - X-API-Version: 1 or 2 (simple version header)
    - Accept: application/vnd.library.v1+json or application/vnd.library.v2+json (vendor media type)
    
    Query Parameters:
    - page: Page number (default: 1)
    - size: Items per page (default: 10)
    - category: Filter by category (v2 only)
    - search: Search in title or author (v2 only)
    
    Version 1 (default):
    - Legacy format with snake_case
    - Basic information with simple copies_count
    - Response: {items: [...], page: {...}}
    
    Version 2 (X-API-Version: 2 or Accept: application/vnd.library.v2+json):
    - Enhanced format with camelCase
    - Detailed statistics (available, borrowed, condition breakdown)
    - Better metadata about availability
    - Advanced filtering support
    - Response: {data: [...], pagination: {...}, meta: {...}}
    
    Examples:
    - GET /api/book_titles (uses v1)
    - GET /api/book_titles with header "X-API-Version: 2" (uses v2)
    - GET /api/book_titles with header "Accept: application/vnd.library.v2+json" (uses v2)
    - GET /api/book_titles?category=Fiction with header "X-API-Version: 2" (v2 with filter)
    """
    version = get_book_title_version()
    
    key = make_cache_key(request.path + f"_v{version}", request.args)
    cached = cache_get(key)
    if cached:
        response = jsonify(cached)
        response.headers['X-API-Version'] = str(version)
        return response

    query = BookTitle.query
    
    # v2 specific filters
    if version >= 2:
        # Filter by category
        category_filter = request.args.get('category')
        if category_filter:
            query = query.filter_by(category=category_filter)
        
        # Search in title or author
        search = request.args.get('search')
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    BookTitle.title.like(search_pattern),
                    BookTitle.author.like(search_pattern)
                )
            )
    
    items, page_info = paginate(query)
    
    # Version 1: Legacy format
    if version == 1:
        data = [serialize_book_title_v1(b) for b in items]
        result = {"items": data, "page": page_info}
        cache_set(key, result)
        response = jsonify(result)
        response.headers['X-API-Version'] = '1'
        response.headers['X-Available-Versions'] = '1, 2'
        return response
    
    # Version 2: Enhanced format
    elif version >= 2:
        data = [serialize_book_title_v2(b) for b in items]
        result = {
            "data": data,
            "pagination": page_info,
            "meta": {
                "version": "2.0",
                "features": [
                    "detailed_statistics",
                    "condition_breakdown",
                    "availability_metadata",
                    "advanced_filtering"
                ]
            }
        }
        cache_set(key, result)
        response = jsonify(result)
        response.headers['X-API-Version'] = '2'
        response.headers['Content-Type'] = 'application/vnd.library.v2+json'
        return response

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
# BOOK COPY APIs - VERSION 1 (DEPRECATED)
# ==========================================
# DEPRECATION NOTICE:
# These v1 endpoints are deprecated and will be removed in version 13.0.0 (June 2026)
# Please migrate to v2 endpoints (/api/v2/book-copies) which offer:
# - Enhanced response format with embedded book title information
# - Better error messages and validation
# - Improved filtering and search capabilities
# - RESTful kebab-case naming convention
# Migration guide: See API_VERSIONING.md

def add_deprecation_headers(response, sunset_date="2026-06-01", new_version="/api/v2/book-copies"):
    """Add deprecation headers to response according to RFC 8594"""
    response.headers['Deprecation'] = 'true'
    response.headers['Sunset'] = sunset_date
    response.headers['Link'] = f'<{new_version}>; rel="successor-version"'
    response.headers['Warning'] = '299 - "This API version is deprecated. Please migrate to v2"'
    return response

@api.route("/book_copies", methods=["GET"])
@token_required
def list_book_copies_v1(current_user):
    """
    [DEPRECATED] List all book copies (v1)
    
    Deprecation Info:
    - Deprecated since: 2025-11-13
    - Sunset date: 2026-06-01
    - Replacement: GET /api/v2/book-copies
    - Migration: v2 includes embedded book title info and better filtering
    """
    key = make_cache_key(request.path, request.args)
    cached = cache_get(key)
    if cached:
        response = jsonify(cached)
        return add_deprecation_headers(response)
        
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
    result = {"items": data, "page": page_info}
    cache_set(key, result)
    response = jsonify(result)
    return add_deprecation_headers(response)

@api.route("/book_copies", methods=["POST"])
@token_required
def create_book_copy_v1(current_user):
    """
    [DEPRECATED] Create a new book copy (v1)
    
    Deprecation Info:
    - Deprecated since: 2025-11-13
    - Sunset date: 2026-06-01
    - Replacement: POST /api/v2/book-copies
    - Migration: v2 returns full resource representation instead of just ID
    """
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
    cache_delete_prefix("/api/v2/book-copies")
    response = jsonify({"message": "BookCopy created", "id": copy.id})
    return add_deprecation_headers(response), 201

@api.route("/book_copies/<int:id>", methods=["PUT"])
@token_required
def update_book_copy_v1(current_user, id):
    """
    [DEPRECATED] Update a book copy (v1)
    
    Deprecation Info:
    - Deprecated since: 2025-11-13
    - Sunset date: 2026-06-01
    - Replacement: PUT /api/v2/book-copies/{id}
    - Migration: v2 supports PATCH method and returns updated resource
    """
    c = BookCopy.query.get_or_404(id)
    data = request.get_json() or {}
    for field in ("available", "condition"):
        if field in data:
            setattr(c, field, data[field])
    db.session.commit()
    cache_delete_prefix("/api/book_copies")
    cache_delete_prefix("/api/v2/book-copies")
    response = jsonify({"message": "BookCopy updated"})
    return add_deprecation_headers(response)

@api.route("/book_copies/<int:id>", methods=["DELETE"])
@token_required
def delete_book_copy_v1(current_user, id):
    """
    [DEPRECATED] Delete a book copy (v1)
    
    Deprecation Info:
    - Deprecated since: 2025-11-13
    - Sunset date: 2026-06-01
    - Replacement: DELETE /api/v2/book-copies/{id}
    - Migration: v2 provides better error messages
    """
    c = BookCopy.query.get_or_404(id)
    if Borrowing.query.filter_by(book_copy_id=c.id, return_date=None).first():
        abort(400, "Book copy currently borrowed")
    db.session.delete(c)
    db.session.commit()
    cache_delete_prefix("/api/book_copies")
    cache_delete_prefix("/api/v2/book-copies")
    response = jsonify({"message": "BookCopy deleted"})
    return add_deprecation_headers(response)

# ==========================================
# BOOK COPY APIs - VERSION 2 (CURRENT)
# ==========================================

def serialize_book_copy_v2(copy, include_book_info=True):
    """Serialize book copy with enhanced v2 format"""
    result = {
        "id": copy.id,
        "bookTitleId": copy.book_title_id,
        "barcode": copy.barcode,
        "available": copy.available,
        "condition": copy.condition,
        "metadata": {
            "createdAt": None,  # Would need to add timestamp fields to model
            "updatedAt": None
        }
    }
    
    # Include embedded book title information
    if include_book_info and copy.book_title:
        result["bookTitle"] = {
            "id": copy.book_title.id,
            "title": copy.book_title.title,
            "author": copy.book_title.author,
            "publisher": copy.book_title.publisher,
            "year": copy.book_title.year
        }
    
    # Include borrowing status
    active_borrowing = Borrowing.query.filter_by(
        book_copy_id=copy.id, 
        return_date=None
    ).first()
    
    result["borrowingStatus"] = {
        "isBorrowed": not copy.available,
        "currentBorrowingId": active_borrowing.id if active_borrowing else None,
        "dueDate": active_borrowing.due_date.isoformat() if active_borrowing and active_borrowing.due_date else None
    }
    
    return result

@api.route("/v2/book-copies", methods=["GET"])
@token_required
def list_book_copies_v2(current_user):
    """
    Get list of book copies with enhanced information (v2)
    
    Query Parameters:
    - page: Page number (default: 1)
    - size: Items per page (default: 10)
    - available: Filter by availability (true/false)
    - condition: Filter by condition (Good/Damaged/Lost)
    - bookTitleId: Filter by book title ID
    - search: Search in barcode
    
    Returns:
    - Enhanced format with embedded book title info
    - Borrowing status for each copy
    """
    key = make_cache_key(request.path, request.args)
    cached = cache_get(key)
    if cached:
        return jsonify(cached)
    
    query = BookCopy.query
    
    # Apply filters
    available = request.args.get("available")
    if available is not None:
        available_bool = available.lower() in ('true', '1', 'yes')
        query = query.filter_by(available=available_bool)
    
    condition = request.args.get("condition")
    if condition:
        query = query.filter_by(condition=condition)
    
    book_title_id = request.args.get("bookTitleId")
    if book_title_id:
        query = query.filter_by(book_title_id=int(book_title_id))
    
    search = request.args.get("search")
    if search:
        query = query.filter(BookCopy.barcode.like(f"%{search}%"))
    
    items, page_info = paginate(query)
    data = [serialize_book_copy_v2(c) for c in items]
    
    result = {
        "data": data,
        "pagination": page_info,
        "meta": {
            "version": "2.0",
            "deprecated": False
        }
    }
    cache_set(key, result)
    return jsonify(result)

@api.route("/v2/book-copies/<int:id>", methods=["GET"])
@token_required
def get_book_copy_v2(current_user, id):
    """Get single book copy by ID with full details (v2)"""
    copy = BookCopy.query.get_or_404(id)
    return jsonify({
        "data": serialize_book_copy_v2(copy),
        "meta": {"version": "2.0"}
    })

@api.route("/v2/book-copies", methods=["POST"])
@token_required
def create_book_copy_v2(current_user):
    """
    Create a new book copy (v2)
    
    Request Body:
    {
        "bookTitleId": integer (required),
        "barcode": string (required, unique),
        "condition": string (optional, default: "Good")
    }
    
    Returns:
    - Full resource representation with embedded book info
    - Location header with new resource URI
    """
    data = request.get_json() or {}
    
    # Validate required fields
    if "bookTitleId" not in data or "barcode" not in data:
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Missing required fields",
                "details": {
                    "bookTitleId": "required" if "bookTitleId" not in data else None,
                    "barcode": "required" if "barcode" not in data else None
                }
            }
        }), 400
    
    # Verify book title exists
    title = BookTitle.query.get(data.get("bookTitleId"))
    if not title:
        return jsonify({
            "error": {
                "code": "INVALID_BOOK_TITLE",
                "message": f"Book title with ID {data.get('bookTitleId')} not found"
            }
        }), 404
    
    # Create book copy
    copy = BookCopy(
        book_title_id=data["bookTitleId"],
        barcode=data["barcode"],
        available=data.get("available", True),
        condition=data.get("condition", "Good")
    )
    
    db.session.add(copy)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": {
                "code": "DUPLICATE_BARCODE",
                "message": f"Barcode '{data['barcode']}' already exists"
            }
        }), 409
    
    cache_delete_prefix("/api/book_copies")
    cache_delete_prefix("/api/v2/book-copies")
    
    response = jsonify({
        "data": serialize_book_copy_v2(copy),
        "meta": {"version": "2.0"}
    })
    response.status_code = 201
    response.headers['Location'] = f'/api/v2/book-copies/{copy.id}'
    return response

@api.route("/v2/book-copies/<int:id>", methods=["PUT", "PATCH"])
@token_required
def update_book_copy_v2(current_user, id):
    """
    Update a book copy (v2)
    
    Supports both PUT (full update) and PATCH (partial update)
    
    Request Body:
    {
        "available": boolean (optional),
        "condition": string (optional)
    }
    
    Returns:
    - Full updated resource representation
    """
    copy = BookCopy.query.get_or_404(id)
    data = request.get_json() or {}
    
    # Validate condition values
    if "condition" in data:
        valid_conditions = ["Good", "Damaged", "Lost"]
        if data["condition"] not in valid_conditions:
            return jsonify({
                "error": {
                    "code": "INVALID_CONDITION",
                    "message": f"Condition must be one of: {', '.join(valid_conditions)}"
                }
            }), 400
    
    # Update fields
    for field in ("available", "condition"):
        if field in data:
            setattr(copy, field, data[field])
    
    db.session.commit()
    cache_delete_prefix("/api/book_copies")
    cache_delete_prefix("/api/v2/book-copies")
    
    return jsonify({
        "data": serialize_book_copy_v2(copy),
        "meta": {"version": "2.0"}
    })

@api.route("/v2/book-copies/<int:id>", methods=["DELETE"])
@token_required
def delete_book_copy_v2(current_user, id):
    """
    Delete a book copy (v2)
    
    Returns:
    - 204 No Content on success
    - Detailed error message if copy is currently borrowed
    """
    copy = BookCopy.query.get_or_404(id)
    
    # Check if currently borrowed
    active_borrowing = Borrowing.query.filter_by(
        book_copy_id=copy.id, 
        return_date=None
    ).first()
    
    if active_borrowing:
        return jsonify({
            "error": {
                "code": "COPY_CURRENTLY_BORROWED",
                "message": "Cannot delete book copy that is currently borrowed",
                "details": {
                    "borrowingId": active_borrowing.id,
                    "userId": active_borrowing.user_id,
                    "dueDate": active_borrowing.due_date.isoformat() if active_borrowing.due_date else None
                }
            }
        }), 409
    
    db.session.delete(copy)
    db.session.commit()
    cache_delete_prefix("/api/book_copies")
    cache_delete_prefix("/api/v2/book-copies")
    
    return '', 204

# ==========================================
# BORROWING APIs - QUERY PARAMETER VERSIONING
# ==========================================
# Strategy: Version specified via ?version=2 query parameter
# Default (no version param or version=1): Legacy format
# version=2: Enhanced format with embedded data
# Migration guide: See API_VERSIONING.md

def get_api_version():
    """Get API version from query parameter (default: 1)"""
    version = request.args.get('version', '1')
    try:
        return int(version)
    except (ValueError, TypeError):
        return 1

def serialize_borrowing_v1(b):
    """Serialize borrowing in v1 format (legacy)"""
    overdue = (
        b.due_date and not b.return_date and datetime.utcnow() > b.due_date
    )
    days_overdue = (
        (datetime.utcnow().date() - b.due_date.date()).days
        if overdue
        else 0
    )
    return {
        "id": b.id,
        "book_copy_id": b.book_copy_id,
        "user_id": b.user_id,
        "borrow_date": b.borrow_date.isoformat(),
        "due_date": b.due_date.isoformat() if b.due_date else None,
        "return_date": b.return_date.isoformat() if b.return_date else None,
        "fine": b.fine,
        "overdue": overdue,
        "days_overdue": days_overdue,
    }

def serialize_borrowing_v2(b):
    """Serialize borrowing in v2 format (enhanced with embedded data)"""
    overdue = (
        b.due_date and not b.return_date and datetime.utcnow() > b.due_date
    )
    days_overdue = (
        (datetime.utcnow().date() - b.due_date.date()).days
        if overdue
        else 0
    )
    
    result = {
        "id": b.id,
        "borrowDate": b.borrow_date.isoformat(),
        "dueDate": b.due_date.isoformat() if b.due_date else None,
        "returnDate": b.return_date.isoformat() if b.return_date else None,
        "fine": b.fine,
        "status": {
            "isOverdue": overdue,
            "daysOverdue": days_overdue,
            "isReturned": b.return_date is not None
        }
    }
    
    # Embed book copy information
    if b.book_copy:
        result["bookCopy"] = {
            "id": b.book_copy.id,
            "barcode": b.book_copy.barcode,
            "condition": b.book_copy.condition
        }
        
        # Embed book title information
        if b.book_copy.book_title:
            result["bookCopy"]["bookTitle"] = {
                "id": b.book_copy.book_title.id,
                "title": b.book_copy.book_title.title,
                "author": b.book_copy.book_title.author,
                "publisher": b.book_copy.book_title.publisher,
                "year": b.book_copy.book_title.year
            }
    
    # Embed user information
    if b.user:
        result["user"] = {
            "id": b.user.id,
            "name": b.user.name,
            "email": b.user.email
        }
    
    return result

@api.route("/borrowings", methods=["GET"])
@token_required
def list_borrowings(current_user):
    """
    Get list of borrowings with version support via query parameter
    
    Query Parameters:
    - version: API version (1 or 2, default: 1)
    - page: Page number (default: 1)
    - size: Items per page (default: 10)
    - status: Filter by status (v2 only: active/returned/overdue)
    - userId: Filter by user ID (v2 only)
    
    Version 1 (default):
    - Legacy format with snake_case
    - Basic information only
    - Response: {items: [...], page: {...}}
    
    Version 2 (?version=2):
    - Enhanced format with camelCase
    - Embedded book copy and user information
    - Better status information
    - Response: {data: [...], pagination: {...}, meta: {...}}
    
    Examples:
    - GET /api/borrowings (uses v1)
    - GET /api/borrowings?version=1 (explicit v1)
    - GET /api/borrowings?version=2 (uses v2)
    - GET /api/borrowings?version=2&status=overdue (v2 with filter)
    """
    version = get_api_version()
    
    query = Borrowing.query
    
    # v2 specific filters
    if version >= 2:
        # Filter by status
        status_filter = request.args.get('status')
        if status_filter == 'active':
            query = query.filter_by(return_date=None)
        elif status_filter == 'returned':
            query = query.filter(Borrowing.return_date.isnot(None))
        elif status_filter == 'overdue':
            query = query.filter(
                Borrowing.return_date.is_(None),
                Borrowing.due_date < datetime.utcnow()
            )
        
        # Filter by user ID
        user_id_filter = request.args.get('userId')
        if user_id_filter:
            query = query.filter_by(user_id=int(user_id_filter))
    
    items, page_info = paginate(query)
    
    # Version 1: Legacy format
    if version == 1:
        data = [serialize_borrowing_v1(b) for b in items]
        response = jsonify({"items": data, "page": page_info})
        # Add hint header for v2
        response.headers['X-API-Version'] = '1'
        response.headers['X-Available-Versions'] = '1, 2'
        response.headers['Link'] = '</api/borrowings?version=2>; rel="alternate"; title="Version 2"'
        return response
    
    # Version 2: Enhanced format
    elif version >= 2:
        data = [serialize_borrowing_v2(b) for b in items]
        return jsonify({
            "data": data,
            "pagination": page_info,
            "meta": {
                "version": "2.0",
                "features": [
                    "embedded_book_copy",
                    "embedded_user",
                    "enhanced_status",
                    "advanced_filtering"
                ]
            }
        })

@api.route("/borrowings", methods=["POST"])
@token_required
def borrow_book(current_user):
    """
    Create a new borrowing record
    
    Supports both v1 and v2 input formats based on query parameter
    
    Version 1 (default):
    Request: {"book_copy_id": int, "due_date": string}
    Response: {"message": string, "id": int}
    
    Version 2 (?version=2):
    Request: {"bookCopyId": int, "dueDate": string}
    Response: {"data": {...}, "meta": {...}}
    """
    if not current_user:
        abort(401, "Authentication required")
    
    version = get_api_version()
    data = request.get_json() or {}
    
    # Handle different field names based on version
    if version >= 2:
        book_copy_id = data.get("bookCopyId")
        due_date = data.get("dueDate")
        
        # Validate v2
        if not book_copy_id:
            return jsonify({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Missing required field: bookCopyId"
                }
            }), 400
    else:
        book_copy_id = data.get("book_copy_id")
        due_date = data.get("due_date")
        
        # Validate v1
        if not book_copy_id:
            abort(400, "Missing book_copy_id")
    
    copy = BookCopy.query.get_or_404(book_copy_id)
    
    if not copy.available:
        logger.warning(f"Attempt to borrow unavailable book copy", 
                      extra={'user_id': current_user.id, 'book_copy_id': book_copy_id})
        if version >= 2:
            return jsonify({
                "error": {
                    "code": "BOOK_NOT_AVAILABLE",
                    "message": "Book copy is not available for borrowing",
                    "details": {
                        "bookCopyId": book_copy_id,
                        "barcode": copy.barcode
                    }
                }
            }), 400
        else:
            abort(400, "Book not available")
    
    try:
        due_dt = datetime.fromisoformat(due_date) if due_date else None
        borrow = Borrowing(book_copy_id=copy.id, user_id=current_user.id, due_date=due_dt)
        copy.available = False
        db.session.add(borrow)
        db.session.commit()
        
        # Record metrics and log
        record_book_borrowed()
        active_count = Borrowing.query.filter_by(return_date=None).count()
        update_active_borrowings(active_count)
        log_db_operation(logger, 'CREATE', 'borrowing', borrow.id, success=True)
        logger.info(f"Book borrowed by user", 
                   extra={'user_id': current_user.id, 'borrowing_id': borrow.id, 
                         'book_copy_id': copy.id, 'due_date': due_date})
        
        # Send webhook notification
        send_webhook_notification(EVENT_BOOK_BORROWED, {
            'borrowing_id': borrow.id,
            'user_id': current_user.id,
            'user_name': current_user.name,
            'user_email': current_user.email,
            'book_copy_id': copy.id,
            'book_title': copy.book_title.title,
            'book_author': copy.book_title.author,
            'borrow_date': borrow.borrow_date.isoformat(),
            'due_date': borrow.due_date.isoformat() if borrow.due_date else None
        })
    except Exception as e:
        db.session.rollback()
        log_db_operation(logger, 'CREATE', 'borrowing', None, success=False, error=str(e))
        logger.error(f"Failed to create borrowing: {str(e)}", 
                    extra={'user_id': current_user.id, 'book_copy_id': book_copy_id}, exc_info=True)
        abort(500, "Failed to borrow book")
    
    # v1 response
    if version == 1:
        return jsonify({"message": "Book borrowed", "id": borrow.id}), 201
    
    # v2 response
    else:
        response = jsonify({
            "data": serialize_borrowing_v2(borrow),
            "meta": {"version": "2.0"}
        })
        response.status_code = 201
        response.headers['Location'] = f'/api/borrowings/{borrow.id}'
        return response

@api.route("/borrowings/<int:id>/return", methods=["POST"])
@token_required
def return_book(current_user, id):
    """
    Return a borrowed book
    
    Supports both v1 and v2 response formats based on query parameter
    
    Version 1 (default):
    Response: {"message": string, "fine": int}
    
    Version 2 (?version=2):
    Response: {"data": {...}, "meta": {...}}
    """
    version = get_api_version()
    
    b = Borrowing.query.get_or_404(id)
    
    if b.return_date:
        logger.warning(f"Attempt to return already returned book", 
                      extra={'user_id': current_user.id, 'borrowing_id': id})
        if version >= 2:
            return jsonify({
                "error": {
                    "code": "ALREADY_RETURNED",
                    "message": "This book has already been returned",
                    "details": {
                        "borrowingId": id,
                        "returnDate": b.return_date.isoformat()
                    }
                }
            }), 400
        else:
            abort(400, "Already returned")
    
    try:
        b.return_date = datetime.utcnow()
        fine_per_day = current_app.config.get("LIBRARY_FINE_PER_DAY", 5000)
        if b.due_date and b.return_date > b.due_date:
            days = (b.return_date.date() - b.due_date.date()).days
            b.fine = days * fine_per_day
        
        copy = BookCopy.query.get(b.book_copy_id)
        copy.available = True
        db.session.commit()
        
        # Record metrics and log
        record_book_returned()
        active_count = Borrowing.query.filter_by(return_date=None).count()
        update_active_borrowings(active_count)
        log_db_operation(logger, 'UPDATE', 'borrowing', id, success=True)
        logger.info(f"Book returned by user", 
                   extra={'user_id': current_user.id, 'borrowing_id': id, 
                         'fine': b.fine, 'overdue_days': days if b.fine else 0})
        
        # Send webhook notification
        send_webhook_notification(EVENT_BOOK_RETURNED, {
            'borrowing_id': id,
            'user_id': current_user.id,
            'user_name': current_user.name,
            'user_email': current_user.email,
            'book_copy_id': b.book_copy_id,
            'book_title': copy.book_title.title,
            'book_author': copy.book_title.author,
            'borrow_date': b.borrow_date.isoformat(),
            'return_date': b.return_date.isoformat(),
            'due_date': b.due_date.isoformat() if b.due_date else None,
            'fine': b.fine,
            'overdue_days': days if b.fine else 0
        })
    except Exception as e:
        db.session.rollback()
        log_db_operation(logger, 'UPDATE', 'borrowing', id, success=False, error=str(e))
        logger.error(f"Failed to return book: {str(e)}", 
                    extra={'user_id': current_user.id, 'borrowing_id': id}, exc_info=True)
        abort(500, "Failed to return book")
    
    # v1 response
    if version == 1:
        return jsonify({"message": "Book returned", "fine": b.fine})
    
    # v2 response
    else:
        return jsonify({
            "data": serialize_borrowing_v2(b),
            "meta": {
                "version": "2.0",
                "action": "returned"
            }
        })
