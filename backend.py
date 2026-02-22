from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid
import os
import json
import random
import base64

from database import SessionLocal, User, Server, Payment, TrafficLog, Device, ReferralBonus, VIPSupportTicket, UserServerAccess
from config import API_HOST, API_PORT, TRIAL_DAYS, BASIC_DAYS, VIP_DAYS, REFERRAL_BONUS_DAYS, REFERRALS_NEEDED_FOR_BONUS, TRIAL_TRAFFIC_LIMIT_GB, BASIC_TRAFFIC_LIMIT_GB, VIP_TRAFFIC_LIMIT_GB, ADMIN_IDS

app = Flask(__name__, static_folder="webapp")
CORS(app)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_servers():
    db = SessionLocal()
    
    if db.query(Server).count() == 0:
        servers_data = [
            {
                "name": "🇷🇺 Russia #1",
                "location": "RU",
                "country": "Россия",
                "city": "Москва",
                "host": "212.192.14.234",
                "port": 24441,
                "protocol": "shadowsocks",
                "method": "chacha20-ietf-poly1305",
                "password": "Ow8iSExQNaobZPY9bJ4EPI",
                "vip_only": False
            },
            {
                "name": "🇷🇺 Russia #2",
                "location": "RU",
                "country": "Россия",
                "city": "Санкт-Петербург",
                "host": "62.113.114.116",
                "port": 42320,
                "protocol": "shadowsocks",
                "method": "chacha20-ietf-poly1305",
                "password": "BShcek5ydlWbXEnhl2vlym",
                "vip_only": False
            },
            {
                "name": "🇷🇺 Russia #3",
                "location": "RU",
                "country": "Россия",
                "city": "Санкт-Петербург",
                "host": "spb.scroogethebest.com",
                "port": 443,
                "protocol": "vless",
                "uuid": "ccedb1b1-35f3-46d1-a85a-c699eef5f3e1",
                "flow": "xtls-rprx-vision",
                "security": "reality",
                "network": "tcp",
                "tls": "reality",
                "sni": "spb.scroogethebest.com",
                "fingerprint": "chrome",
                "public_key": "C3hc32Cknec2shasKJIH2DYVb7Fyu64RF9v71L3ipEg",
                "short_id": "9c2378562188c3cb",
                "vip_only": False
            },
            {
                "name": "🇬🇧 UK #1",
                "location": "GB",
                "country": "Великобритания",
                "city": "Лондон",
                "host": "series-a1.samanehha.co",
                "port": 443,
                "protocol": "shadowsocks",
                "method": "chacha20-ietf-poly1305",
                "password": "W74XFALLLuw6m5IA",
                "vip_only": False
            },
            {
                "name": "🇬🇧 UK #2",
                "location": "GB",
                "country": "Великобритания",
                "city": "Манчестер",
                "host": "admin.c2.havij.co",
                "port": 443,
                "protocol": "shadowsocks",
                "method": "chacha20-ietf-poly1305",
                "password": "kaQH3hGdcP80XEDI",
                "vip_only": False
            },
            {
                "name": "🇫🇷 France",
                "location": "FR",
                "country": "Франция",
                "city": "Париж",
                "host": "95.111.250.4",
                "port": 80,
                "protocol": "shadowsocks",
                "method": "aes-256-gcm",
                "password": "BbOUgNLUyT6rdrxE",
                "vip_only": False
            },
            {
                "name": "🇺🇸 USA",
                "location": "US",
                "country": "США",
                "city": "Нью-Йорк",
                "host": "154.38.176.7",
                "port": 80,
                "protocol": "shadowsocks",
                "method": "aes-256-gcm",
                "password": "nKeE2ZFWVaE4DyjR",
                "vip_only": False
            },
            {
                "name": "🇳🇱 Netherlands",
                "location": "NL",
                "country": "Нидерланды",
                "city": "Амстердам",
                "host": "82.38.31.62",
                "port": 8080,
                "protocol": "shadowsocks",
                "method": "chacha20-ietf-poly1305",
                "password": "oZloA69Q8yhcQV8ka3Pa3A",
                "vip_only": False
            },
            {
                "name": "🇸🇪 Sweden",
                "location": "SE",
                "country": "Швеция",
                "city": "Стокгольм",
                "host": "46.246.97.140",
                "port": 53908,
                "protocol": "shadowsocks",
                "method": "chacha20-ietf-poly1305",
                "password": "ZweuXavjovuhzt1AF0d6qx",
                "vip_only": False
            },
            {
                "name": "🇯🇵 Japan",
                "location": "JP",
                "country": "Япония",
                "city": "Токио",
                "host": "103.106.228.175",
                "port": 8009,
                "protocol": "shadowsocks",
                "method": "aes-256-gcm",
                "password": "XKFKI2rULjlP74",
                "vip_only": False
            },
            {
                "name": "🇮🇹 Italy VIP",
                "location": "IT",
                "country": "Италия",
                "city": "Милан",
                "host": "80.211.133.156",
                "port": 443,
                "protocol": "vless",
                "uuid": "d443fb54-207c-4fa4-b9d8-3ae2a2957532",
                "flow": "xtls-rprx-vision",
                "security": "reality",
                "network": "tcp",
                "tls": "reality",
                "sni": "gmail.com",
                "fingerprint": "chrome",
                "alpn": "h2",
                "public_key": "ckRcueERkPqqjZABwxqni_J_Nbb70Q6k5fEEUAjoImw",
                "vip_only": True
            },
            {
                "name": "🇩🇪 Germany #2 VIP",
                "location": "DE",
                "country": "Германия",
                "city": "Франкфурт",
                "host": "93.94.51.13",
                "port": 25451,
                "protocol": "vless",
                "uuid": "a90f4742-2f30-47b5-9f17-b6ab04cc98e8",
                "security": "reality",
                "network": "tcp",
                "tls": "reality",
                "sni": "yandex.ru",
                "fingerprint": "chrome",
                "public_key": "JlMOb8hVg1VOrRlMLdXpv8IADp-R4I-cIT856hz_Cg0",
                "short_id": "f686d19cd7b8b3df",
                "vip_only": True
            },
            {
                "name": "🇩🇪 Germany #3 VIP",
                "location": "DE",
                "country": "Германия",
                "city": "Франкфурт",
                "host": "deu469.unboundworld.org",
                "port": 8443,
                "protocol": "vless",
                "uuid": "cc9f7840-757a-430b-bddc-a73478bea434",
                "security": "tls",
                "network": "grpc",
                "tls": "tls",
                "sni": "deu469.unboundworld.org",
                "fingerprint": "chrome",
                "alpn": "h2",
                "allow_insecure": True,
                "grpc_mode": "gun",
                "grpc_service_name": "grpc-vless",
                "vip_only": True
            },
            {
                "name": "🇩🇪 Germany #4 VIP",
                "location": "DE",
                "country": "Германия",
                "city": "Франкфурт",
                "host": "81.19.141.190",
                "port": 51529,
                "protocol": "vless",
                "uuid": "ad2879c1-7f77-4a4c-ba50-c24dd5ceffa4",
                "security": "reality",
                "network": "tcp",
                "tls": "reality",
                "sni": "yandex.ru",
                "fingerprint": "chrome",
                "public_key": "9smFk5QZXifHGrtwDwhbROsLBh179bExNWABnvUCvSw",
                "short_id": "b77a294515ecc200",
                "vip_only": True
            }
        ]
        
        for server_data in servers_data:
            server = Server(**server_data)
            db.add(server)
        
        db.commit()
    
    db.close()

def check_subscription_access(user, server):
    if user.is_admin:
        return True
    if not user.is_active():
        return False
    if server.admin_only and not user.is_admin:
        return False
    if server.vip_only and user.subscription_type != "vip" and not user.is_admin:
        return False
    return True

@app.route("/api/user/create", methods=["POST"])
def create_user():
    db = SessionLocal()
    data = request.json
    telegram_id = data.get("id")
    username = data.get("username", "")
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")
    
    existing = db.query(User).filter(User.telegram_id == telegram_id).first()
    if existing:
        db.close()
        return jsonify({"status": "exists", "user": existing.to_dict()})
    
    is_admin = telegram_id in ADMIN_IDS
    
    referral_code = f"VPN{uuid.uuid4().hex[:8].upper()}"
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        referral_code=referral_code,
        status="NO_SUBSCRIPTION",
        is_admin=is_admin,
        vip_support_access=is_admin,
        priority_server_access=is_admin
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    
    return jsonify({"status": "ok", "user": user.to_dict()})

@app.route("/api/user/info")
def user_info():
    db = SessionLocal()
    telegram_id = request.args.get("id")
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    db.close()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict())

@app.route("/api/user/subscription/activate", methods=["POST"])
def activate_subscription():
    db = SessionLocal()
    data = request.json
    telegram_id = data.get("id")
    sub_type = data.get("type", "basic")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    if user.is_admin:
        db.close()
        return jsonify({"status": "ok", "message": "Admin account"})
    
    if sub_type == "trial" and user.trial_used:
        db.close()
        return jsonify({"error": "Trial already used"}), 400
    
    if sub_type == "trial":
        days = TRIAL_DAYS
        traffic_limit = TRIAL_TRAFFIC_LIMIT_GB * 1024
        user.trial_used = True
        user.trial_start = datetime.utcnow()
        user.subscription_type = "trial"
        user.status = "ACTIVE"
    elif sub_type == "vip":
        days = VIP_DAYS
        traffic_limit = VIP_TRAFFIC_LIMIT_GB * 1024
        user.subscription_type = "vip"
        user.status = "VIP"
        user.vip_support_access = True
        user.priority_server_access = True
    else:
        days = BASIC_DAYS
        traffic_limit = BASIC_TRAFFIC_LIMIT_GB * 1024
        user.subscription_type = "basic"
        user.status = "ACTIVE"
    
    end_date = datetime.utcnow() + timedelta(days=days)
    user.subscription_end = end_date
    user.traffic_limit = traffic_limit
    user.traffic_used = 0
    
    db.commit()
    db.close()
    
    return jsonify({"status": "ok", "expire": end_date.isoformat()})

@app.route("/api/admin/make_admin", methods=["POST"])
def make_admin():
    db = SessionLocal()
    data = request.json
    admin_id = data.get("admin_id")
    target_id = data.get("target_id")
    
    admin = db.query(User).filter(User.telegram_id == admin_id).first()
    if not admin or not admin.is_admin:
        db.close()
        return jsonify({"error": "Unauthorized"}), 403
    
    user = db.query(User).filter(User.telegram_id == target_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    user.is_admin = True
    user.vip_support_access = True
    user.priority_server_access = True
    user.status = "VIP"
    
    db.commit()
    db.close()
    
    return jsonify({"status": "ok"})

@app.route("/api/servers")
def list_servers():
    db = SessionLocal()
    telegram_id = request.args.get("user_id")
    
    user = None
    if telegram_id:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if user and user.is_admin:
        servers = db.query(Server).filter(Server.is_active == True).all()
    elif user and user.status == "VIP":
        servers = db.query(Server).filter(Server.is_active == True, Server.vip_only == False).all()
    else:
        servers = db.query(Server).filter(Server.is_active == True, Server.vip_only == False).all()
    
    result = []
    for s in servers:
        if user and check_subscription_access(user, s):
            result.append({
                "id": s.id,
                "name": s.name,
                "location": s.location,
                "country": s.country,
                "city": s.city,
                "load": s.current_load,
                "is_active": s.is_active
            })
    db.close()
    return jsonify({"servers": result})

@app.route("/api/servers/detailed")
def list_servers_detailed():
    db = SessionLocal()
    telegram_id = request.args.get("user_id")
    
    user = None
    if telegram_id:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user or not user.is_active():
        db.close()
        return jsonify({"error": "Subscription expired"}), 403
    
    if user.is_admin:
        servers = db.query(Server).filter(Server.is_active == True).all()
    elif user.status == "VIP":
        servers = db.query(Server).filter(Server.is_active == True, Server.vip_only == False).all()
    else:
        servers = db.query(Server).filter(Server.is_active == True, Server.vip_only == False).all()
    
    result = []
    for s in servers:
        if check_subscription_access(user, s):
            server_data = {
                "id": s.id,
                "name": s.name,
                "location": s.location,
                "country": s.country,
                "host": s.host,
                "port": s.port,
                "protocol": s.protocol,
                "method": s.method,
                "password": s.password,
                "uuid": s.uuid,
                "flow": s.flow,
                "security": s.security,
                "network": s.network,
                "header_type": s.header_type,
                "tls": s.tls,
                "sni": s.sni,
                "fingerprint": s.fingerprint,
                "alpn": s.alpn,
                "public_key": s.public_key,
                "short_id": s.short_id,
                "grpc_mode": s.grpc_mode,
                "grpc_service_name": s.grpc_service_name,
                "allow_insecure": s.allow_insecure,
                "load": s.current_load,
                "vip_only": s.vip_only
            }
            result.append(server_data)
    
    db.close()
    return jsonify({"servers": result})

@app.route("/api/user/subscription/status")
def subscription_status():
    db = SessionLocal()
    telegram_id = request.args.get("id")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    if user.is_admin:
        db.close()
        return jsonify({
            "is_active": True,
            "days_left": 9999,
            "traffic_used": user.traffic_used,
            "traffic_limit": 0,
            "is_admin": True
        })
    
    is_active = user.is_active()
    days_left = user.days_remaining()
    
    db.close()
    return jsonify({
        "is_active": is_active,
        "days_left": days_left,
        "traffic_used": user.traffic_used,
        "traffic_limit": user.traffic_limit,
        "is_admin": False
    })

@app.route("/api/happ/sslinks")
def ss_links():
    db = SessionLocal()
    telegram_id = request.args.get("id")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    if not user.is_active() and not user.is_admin:
        db.close()
        return jsonify({"error": "Subscription expired"}), 403
    
    if user.is_admin:
        servers = db.query(Server).filter(Server.is_active == True).all()
    elif user.status == "VIP":
        servers = db.query(Server).filter(Server.is_active == True, Server.vip_only == False).all()
    else:
        servers = db.query(Server).filter(Server.is_active == True, Server.vip_only == False).all()
    
    links = []
    
    for s in servers:
        if not check_subscription_access(user, s):
            continue
            
        if s.protocol == "shadowsocks":
            ss_string = f"{s.method}:{s.password}"
            ss_base64 = base64.b64encode(ss_string.encode()).decode()
            ss_link = f"ss://{ss_base64}@{s.host}:{s.port}#{s.name}"
            links.append({
                "name": s.name,
                "link": ss_link
            })
        elif s.protocol == "vless":
            params = [
                f"type={s.network or 'tcp'}",
                f"security={s.tls or 'none'}"
            ]
            if s.tls == "reality":
                params.append(f"pbk={s.public_key}")
                params.append(f"sni={s.sni or 'yandex.ru'}")
                params.append(f"fp={s.fingerprint or 'chrome'}")
                if s.short_id:
                    params.append(f"sid={s.short_id}")
            if s.flow:
                params.append(f"flow={s.flow}")
            if s.network == "grpc":
                params.append(f"serviceName={s.grpc_service_name or 'grpc-vless'}")
                params.append(f"mode={s.grpc_mode or 'gun'}")
            if s.alpn:
                params.append(f"alpn={s.alpn}")
            
            params_str = "&".join(params)
            vless_link = f"vless://{s.uuid}@{s.host}:{s.port}?{params_str}#{s.name}"
            links.append({
                "name": s.name,
                "link": vless_link
            })
    
    db.close()
    return jsonify({"links": links})

@app.route("/api/admin/users")
def admin_users():
    db = SessionLocal()
    telegram_id = request.args.get("admin_id")
    
    admin = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not admin or not admin.is_admin:
        db.close()
        return jsonify({"error": "Unauthorized"}), 403
    
    users = db.query(User).all()
    result = [u.to_dict() for u in users]
    db.close()
    return jsonify({"users": result})

@app.route("/api/admin/grant_admin", methods=["POST"])
def grant_admin():
    db = SessionLocal()
    data = request.json
    admin_id = data.get("admin_id")
    target_id = data.get("target_id")
    
    admin = db.query(User).filter(User.telegram_id == admin_id).first()
    if not admin or not admin.is_admin:
        db.close()
        return jsonify({"error": "Unauthorized"}), 403
    
    user = db.query(User).filter(User.telegram_id == target_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    user.is_admin = True
    user.vip_support_access = True
    user.priority_server_access = True
    user.status = "VIP"
    
    db.commit()
    db.close()
    
    return jsonify({"status": "ok"})

@app.route("/api/admin/statistics")
def admin_statistics():
    db = SessionLocal()
    telegram_id = request.args.get("admin_id")
    
    admin = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not admin or not admin.is_admin:
        db.close()
        return jsonify({"error": "Unauthorized"}), 403
    
    total_users = db.query(User).count()
    active = db.query(User).filter(User.status == "ACTIVE").count()
    vip = db.query(User).filter(User.status == "VIP").count()
    expired = db.query(User).filter(User.status == "EXPIRED").count()
    trial_used = db.query(User).filter(User.trial_used == True).count()
    admins = db.query(User).filter(User.is_admin == True).count()
    
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    
    payments_today = db.query(Payment).filter(
        Payment.created_at >= today,
        Payment.created_at < tomorrow,
        Payment.status == "CONFIRMED"
    ).count()
    
    revenue_today = db.query(Payment).filter(
        Payment.created_at >= today,
        Payment.created_at < tomorrow,
        Payment.status == "CONFIRMED"
    ).all()
    
    revenue_sum = sum(p.amount for p in revenue_today)
    
    servers = db.query(Server).filter(Server.is_active == True).count()
    vip_servers = db.query(Server).filter(Server.is_active == True, Server.vip_only == True).count()
    
    db.close()
    
    return jsonify({
        "total_users": total_users,
        "active": active,
        "vip": vip,
        "expired": expired,
        "trial_used": trial_used,
        "admins": admins,
        "payments_today": payments_today,
        "revenue_today": revenue_sum,
        "active_servers": servers,
        "vip_servers": vip_servers
    })

@app.route("/webapp")
@app.route("/webapp/<path:path>")
def serve_webapp(path="index.html"):
    return send_from_directory("webapp", path)

if __name__ == "__main__":
    init_servers()
    app.run(host=API_HOST, port=API_PORT, debug=True)