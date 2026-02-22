from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid
import os
import json
import random

from database import SessionLocal, User, Server, Payment, TrafficLog, Device, ReferralBonus, VIPSupportTicket
from config import API_HOST, API_PORT, TRIAL_DAYS, BASIC_DAYS, VIP_DAYS, REFERRAL_BONUS_DAYS, REFERRALS_NEEDED_FOR_BONUS, TRIAL_TRAFFIC_LIMIT_GB, BASIC_TRAFFIC_LIMIT_GB, VIP_TRAFFIC_LIMIT_GB

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
                "name": "Russia #1",
                "location": "RU",
                "country": "Россия",
                "city": "Москва",
                "host": "212.192.14.234",
                "port": 24441,
                "protocol": "shadowsocks",
                "method": "chacha20-ietf-poly1305",
                "password": "Ow8iSExQNaobZPY9bJ4EPI",
                "vip_only": False,
                "priority_level": 0
            },
            {
                "name": "Russia #2",
                "location": "RU",
                "country": "Россия",
                "city": "Санкт-Петербург",
                "host": "62.113.114.116",
                "port": 42320,
                "protocol": "shadowsocks",
                "method": "chacha20-ietf-poly1305",
                "password": "BShcek5ydlWbXEnhl2vlym",
                "vip_only": False,
                "priority_level": 0
            },
            {
                "name": "UK #1",
                "location": "GB",
                "country": "Великобритания",
                "city": "Лондон",
                "host": "series-a1.samanehha.co",
                "port": 443,
                "protocol": "shadowsocks",
                "method": "chacha20-ietf-poly1305",
                "password": "W74XFALLLuw6m5IA",
                "vip_only": False,
                "priority_level": 0
            },
            {
                "name": "UK #2",
                "location": "GB",
                "country": "Великобритания",
                "city": "Манчестер",
                "host": "admin.c2.havij.co",
                "port": 443,
                "protocol": "shadowsocks",
                "method": "chacha20-ietf-poly1305",
                "password": "kaQH3hGdcP80XEDI",
                "vip_only": False,
                "priority_level": 0
            },
            {
                "name": "France #1",
                "location": "FR",
                "country": "Франция",
                "city": "Париж",
                "host": "95.111.250.4",
                "port": 80,
                "protocol": "shadowsocks",
                "method": "aes-256-gcm",
                "password": "BbOUgNLUyT6rdrxE",
                "vip_only": False,
                "priority_level": 0
            },
            {
                "name": "USA #1",
                "location": "US",
                "country": "США",
                "city": "Нью-Йорк",
                "host": "154.38.176.7",
                "port": 80,
                "protocol": "shadowsocks",
                "method": "aes-256-gcm",
                "password": "nKeE2ZFWVaE4DyjR",
                "vip_only": False,
                "priority_level": 0
            },
            {
                "name": "Netherlands #1",
                "location": "NL",
                "country": "Нидерланды",
                "city": "Амстердам",
                "host": "82.38.31.62",
                "port": 8080,
                "protocol": "shadowsocks",
                "method": "chacha20-ietf-poly1305",
                "password": "oZloA69Q8yhcQV8ka3Pa3A",
                "vip_only": False,
                "priority_level": 0
            },
            {
                "name": "VIP Germany #1",
                "location": "DE",
                "country": "Германия",
                "city": "Франкфурт",
                "host": "vip.germany.premium",
                "port": 443,
                "protocol": "shadowsocks",
                "method": "chacha20-ietf-poly1305",
                "password": "VIPonly2026PremiumAccess",
                "vip_only": True,
                "priority_level": 10
            },
            {
                "name": "VIP Switzerland #1",
                "location": "CH",
                "country": "Швейцария",
                "city": "Цюрих",
                "host": "vip.swiss.premium",
                "port": 443,
                "protocol": "shadowsocks",
                "method": "aes-256-gcm",
                "password": "SwissVIP2026Secure",
                "vip_only": True,
                "priority_level": 10
            },
            {
                "name": "VIP Netherlands #1",
                "location": "NL",
                "country": "Нидерланды",
                "city": "Амстердам",
                "host": "vip.netherlands.premium",
                "port": 443,
                "protocol": "shadowsocks",
                "method": "chacha20-ietf-poly1305",
                "password": "DutchVIPFast2026",
                "vip_only": True,
                "priority_level": 10
            }
        ]
        
        for server_data in servers_data:
            server = Server(**server_data)
            db.add(server)
        
        db.commit()
    
    db.close()

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
    
    referral_code = f"VPN{uuid.uuid4().hex[:8].upper()}"
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        referral_code=referral_code,
        status="NO_SUBSCRIPTION",
        vip_support_access=False,
        priority_server_access=False
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
        user.vip_support_access = False
        user.priority_server_access = False
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
        user.vip_support_access = False
        user.priority_server_access = False
    
    end_date = datetime.utcnow() + timedelta(days=days)
    user.subscription_end = end_date
    user.traffic_limit = traffic_limit
    user.traffic_used = 0
    
    db.commit()
    db.close()
    
    return jsonify({"status": "ok", "expire": end_date.isoformat()})

@app.route("/api/user/subscription/extend", methods=["POST"])
def extend_subscription():
    db = SessionLocal()
    data = request.json
    telegram_id = data.get("id")
    days = data.get("days", 30)
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    if user.subscription_end and user.subscription_end > datetime.utcnow():
        user.subscription_end += timedelta(days=days)
    else:
        user.subscription_end = datetime.utcnow() + timedelta(days=days)
    
    if user.subscription_type == "vip":
        user.status = "VIP"
    else:
        user.status = "ACTIVE"
    
    db.commit()
    db.close()
    
    return jsonify({"status": "ok", "new_expire": user.subscription_end.isoformat()})

@app.route("/api/user/subscription/expire", methods=["POST"])
def expire_subscription():
    db = SessionLocal()
    data = request.json
    telegram_id = data.get("id")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    user.status = "EXPIRED"
    user.subscription_end = datetime.utcnow()
    user.vip_support_access = False
    user.priority_server_access = False
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
    
    if user and user.status == "VIP":
        servers = db.query(Server).filter(Server.is_active == True).all()
    else:
        servers = db.query(Server).filter(Server.is_active == True, Server.vip_only == False).all()
    
    result = []
    for s in servers:
        result.append({
            "id": s.id,
            "name": s.name,
            "location": s.location,
            "country": s.country,
            "city": s.city,
            "load": s.current_load,
            "vip_only": s.vip_only,
            "priority_level": s.priority_level,
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
    
    if user and user.status == "VIP":
        servers = db.query(Server).filter(Server.is_active == True).all()
    else:
        servers = db.query(Server).filter(Server.is_active == True, Server.vip_only == False).all()
    
    result = []
    for s in servers:
        result.append({
            "id": s.id,
            "name": s.name,
            "location": s.location,
            "country": s.country,
            "host": s.host,
            "port": s.port,
            "protocol": s.protocol,
            "method": s.method,
            "password": s.password if user and user.status == "VIP" or not s.vip_only else "VIP Only",
            "vip_only": s.vip_only,
            "load": s.current_load
        })
    db.close()
    return jsonify({"servers": result})

@app.route("/api/server/add", methods=["POST"])
def add_server():
    db = SessionLocal()
    data = request.json
    
    server = Server(
        name=data.get("name"),
        location=data.get("location"),
        country=data.get("country"),
        city=data.get("city"),
        host=data.get("host"),
        port=data.get("port", 443),
        protocol=data.get("protocol", "shadowsocks"),
        method=data.get("method"),
        password=data.get("password"),
        vip_only=data.get("vip_only", False),
        priority_level=data.get("priority_level", 0)
    )
    
    db.add(server)
    db.commit()
    db.refresh(server)
    db.close()
    
    return jsonify({"status": "ok", "server_id": server.id})

@app.route("/api/server/remove", methods=["POST"])
def remove_server():
    db = SessionLocal()
    data = request.json
    server_id = data.get("id")
    
    server = db.query(Server).filter(Server.id == server_id).first()
    if server:
        server.is_active = False
        db.commit()
    
    db.close()
    return jsonify({"status": "ok"})

@app.route("/api/server/update_load", methods=["POST"])
def update_server_load():
    db = SessionLocal()
    data = request.json
    server_id = data.get("id")
    load = data.get("load")
    active_users = data.get("active_users")
    
    server = db.query(Server).filter(Server.id == server_id).first()
    if server:
        server.current_load = load
        if active_users is not None:
            server.active_users = active_users
        server.last_check = datetime.utcnow()
        server.failed_checks = 0
        db.commit()
    
    db.close()
    return jsonify({"status": "ok"})

@app.route("/api/payments/create", methods=["POST"])
def create_payment():
    db = SessionLocal()
    data = request.json
    telegram_id = data.get("user_id")
    amount = data.get("amount")
    days = data.get("days", 30)
    sub_type = data.get("subscription_type", "basic")
    provider = data.get("provider", "cryptobot")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    payment_id = f"PAY{uuid.uuid4().hex[:12].upper()}"
    payment = Payment(
        user_id=user.id,
        amount=amount,
        provider=provider,
        provider_payment_id=payment_id,
        subscription_days=days,
        subscription_type=sub_type,
        status="PENDING"
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    db.close()
    
    return jsonify({
        "payment_id": payment_id,
        "status": "PENDING",
        "amount": amount,
        "provider": provider
    })

@app.route("/api/payments/confirm", methods=["POST"])
def confirm_payment():
    db = SessionLocal()
    data = request.json
    payment_id = data.get("payment_id")
    
    payment = db.query(Payment).filter(Payment.provider_payment_id == payment_id).first()
    if not payment:
        db.close()
        return jsonify({"error": "Payment not found"}), 404
    
    payment.status = "CONFIRMED"
    payment.confirmed_at = datetime.utcnow()
    
    user = db.query(User).filter(User.id == payment.user_id).first()
    if user:
        if payment.subscription_type == "vip":
            user.status = "VIP"
            user.vip_support_access = True
            user.priority_server_access = True
        else:
            user.status = "ACTIVE"
            user.vip_support_access = False
            user.priority_server_access = False
        
        if user.subscription_end and user.subscription_end > datetime.utcnow():
            user.subscription_end += timedelta(days=payment.subscription_days)
        else:
            user.subscription_end = datetime.utcnow() + timedelta(days=payment.subscription_days)
        
        user.subscription_type = payment.subscription_type
    
    db.commit()
    db.close()
    
    return jsonify({"status": "ok"})

@app.route("/api/payments/list")
def list_payments():
    db = SessionLocal()
    telegram_id = request.args.get("user_id")
    
    if telegram_id:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            payments = db.query(Payment).filter(Payment.user_id == user.id).all()
        else:
            payments = []
    else:
        payments = db.query(Payment).all()
    
    result = []
    for p in payments:
        result.append({
            "id": p.provider_payment_id,
            "amount": p.amount,
            "status": p.status,
            "subscription_days": p.subscription_days,
            "subscription_type": p.subscription_type,
            "created_at": p.created_at.isoformat(),
            "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None
        })
    
    db.close()
    return jsonify({"payments": result})

@app.route("/api/referral/add", methods=["POST"])
def add_referral():
    db = SessionLocal()
    data = request.json
    referrer_code = data.get("referrer_code")
    referred_id = data.get("referred_id")
    
    referrer = db.query(User).filter(User.referral_code == referrer_code).first()
    referred = db.query(User).filter(User.telegram_id == referred_id).first()
    
    if not referrer or not referred:
        db.close()
        return jsonify({"error": "Invalid referral"}), 400
    
    if referrer.id == referred.id:
        db.close()
        return jsonify({"error": "Self-referral not allowed"}), 400
    
    if referred.invited_by:
        db.close()
        return jsonify({"error": "User already referred"}), 400
    
    referred.invited_by = referrer.id
    referrer.referral_count += 1
    
    if referrer.referral_count % REFERRALS_NEEDED_FOR_BONUS == 0:
        bonus_days = REFERRAL_BONUS_DAYS
        bonus = ReferralBonus(
            referrer_id=referrer.id,
            referred_id=referred.id,
            bonus_days=bonus_days
        )
        db.add(bonus)
        
        referrer.bonus_days_earned += bonus_days
        
        if referrer.subscription_end and referrer.subscription_end > datetime.utcnow():
            referrer.subscription_end += timedelta(days=bonus_days)
    
    db.commit()
    db.close()
    
    return jsonify({"status": "ok"})

@app.route("/api/referral/list")
def list_referrals():
    db = SessionLocal()
    telegram_id = request.args.get("user_id")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    referrals = db.query(User).filter(User.invited_by == user.id).all()
    bonuses = db.query(ReferralBonus).filter(ReferralBonus.referrer_id == user.id).all()
    
    result = {
        "total_referrals": len(referrals),
        "total_bonus_days": user.bonus_days_earned,
        "referral_code": user.referral_code,
        "referrals": []
    }
    
    for r in referrals:
        result["referrals"].append({
            "username": r.username,
            "joined": r.created_at.isoformat(),
            "status": r.status
        })
    
    db.close()
    return jsonify(result)

@app.route("/api/traffic/report", methods=["POST"])
def report_traffic():
    db = SessionLocal()
    data = request.json
    telegram_id = data.get("id")
    used = data.get("used", 0)
    server_id = data.get("server_id")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        user.traffic_used += used
        user.last_active = datetime.utcnow()
        
        log = TrafficLog(
            user_id=user.id,
            server_id=server_id,
            bytes_sent=used / 2,
            bytes_received=used / 2
        )
        db.add(log)
        
        if user.traffic_limit > 0 and user.traffic_used > user.traffic_limit:
            user.status = "EXPIRED"
            user.vip_support_access = False
            user.priority_server_access = False
        
        db.commit()
    
    db.close()
    return jsonify({"status": "ok"})

@app.route("/api/traffic/usage")
def traffic_usage():
    db = SessionLocal()
    telegram_id = request.args.get("id")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    db.close()
    return jsonify({
        "used": user.traffic_used,
        "limit": user.traffic_limit,
        "percent": user.traffic_percent()
    })

@app.route("/api/subscription/json")
def subscription_json():
    db = SessionLocal()
    telegram_id = request.args.get("id")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    if user.status == "VIP":
        servers = db.query(Server).filter(Server.is_active == True).all()
    else:
        servers = db.query(Server).filter(Server.is_active == True, Server.vip_only == False).all()
    
    server_list = []
    for s in servers:
        server_list.append({
            "id": s.id,
            "name": s.name,
            "location": s.location,
            "host": s.host,
            "port": s.port,
            "protocol": s.protocol,
            "method": s.method,
            "password": s.password if user.status == "VIP" or not s.vip_only else None,
            "vip_only": s.vip_only
        })
    
    result = {
        "version": 2,
        "type": "subscription",
        "user_id": user.telegram_id,
        "uuid": user.uuid,
        "expire": user.subscription_end.isoformat() if user.subscription_end else None,
        "status": user.status,
        "subscription_type": user.subscription_type,
        "traffic_used": user.traffic_used,
        "traffic_limit": user.traffic_limit,
        "vip_support": user.vip_support_access,
        "priority_server": user.priority_server_access,
        "servers": server_list
    }
    
    db.close()
    return jsonify(result)

@app.route("/api/happ/configs")
def happ_configs():
    db = SessionLocal()
    telegram_id = request.args.get("id")
    server_id = request.args.get("server_id")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    if server_id:
        server = db.query(Server).filter(Server.id == server_id, Server.is_active == True).first()
        if not server:
            db.close()
            return jsonify({"error": "Server not found"}), 404
        
        if server.vip_only and user.status != "VIP":
            db.close()
            return jsonify({"error": "VIP only server"}), 403
        
        config = {
            "name": server.name,
            "server": server.host,
            "port": server.port,
            "password": server.password,
            "method": server.method,
            "protocol": server.protocol,
            "remark": f"{server.country} - {server.name}"
        }
        db.close()
        return jsonify(config)
    
    else:
        if user.status == "VIP":
            servers = db.query(Server).filter(Server.is_active == True).all()
        else:
            servers = db.query(Server).filter(Server.is_active == True, Server.vip_only == False).all()
        
        configs = []
        for s in servers:
            configs.append({
                "id": s.id,
                "name": s.name,
                "server": s.host,
                "port": s.port,
                "password": s.password,
                "method": s.method,
                "protocol": s.protocol,
                "location": s.location,
                "country": s.country,
                "vip_only": s.vip_only,
                "remark": f"{s.country} - {s.name}"
            })
        db.close()
        return jsonify({"configs": configs})

@app.route("/api/happ/sslinks")
def ss_links():
    db = SessionLocal()
    telegram_id = request.args.get("id")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    if user.status == "VIP":
        servers = db.query(Server).filter(Server.is_active == True).all()
    else:
        servers = db.query(Server).filter(Server.is_active == True, Server.vip_only == False).all()
    
    import base64
    links = []
    
    for s in servers:
        if s.protocol == "shadowsocks":
            ss_string = f"{s.method}:{s.password}"
            ss_base64 = base64.b64encode(ss_string.encode()).decode()
            ss_link = f"ss://{ss_base64}@{s.host}:{s.port}#{s.name}"
            links.append({
                "name": s.name,
                "link": ss_link,
                "vip_only": s.vip_only
            })
    
    db.close()
    return jsonify({"links": links})

@app.route("/api/vip/support/ticket", methods=["POST"])
def create_vip_ticket():
    db = SessionLocal()
    data = request.json
    telegram_id = data.get("user_id")
    subject = data.get("subject")
    message = data.get("message")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    if not user.vip_support_access:
        db.close()
        return jsonify({"error": "VIP only feature"}), 403
    
    ticket = VIPSupportTicket(
        user_id=user.id,
        subject=subject,
        message=message,
        status="OPEN",
        priority="HIGH"
    )
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    db.close()
    
    return jsonify({"status": "ok", "ticket_id": ticket.id})

@app.route("/api/vip/support/tickets")
def list_vip_tickets():
    db = SessionLocal()
    telegram_id = request.args.get("user_id")
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404
    
    if not user.vip_support_access:
        db.close()
        return jsonify({"error": "VIP only feature"}), 403
    
    tickets = db.query(VIPSupportTicket).filter(VIPSupportTicket.user_id == user.id).all()
    
    result = []
    for t in tickets:
        result.append({
            "id": t.id,
            "subject": t.subject,
            "message": t.message,
            "status": t.status,
            "created_at": t.created_at.isoformat(),
            "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None
        })
    
    db.close()
    return jsonify({"tickets": result})

@app.route("/api/admin/statistics")
def admin_statistics():
    db = SessionLocal()
    
    total_users = db.query(User).count()
    active = db.query(User).filter(User.status == "ACTIVE").count()
    vip = db.query(User).filter(User.status == "VIP").count()
    expired = db.query(User).filter(User.status == "EXPIRED").count()
    trial_used = db.query(User).filter(User.trial_used == True).count()
    
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
        "payments_today": payments_today,
        "revenue_today": revenue_sum,
        "active_servers": servers,
        "vip_servers": vip_servers
    })

@app.route("/api/admin/users")
def admin_users():
    db = SessionLocal()
    users = db.query(User).all()
    result = [u.to_dict() for u in users]
    db.close()
    return jsonify({"users": result})

@app.route("/api/admin/payments")
def admin_payments():
    db = SessionLocal()
    payments = db.query(Payment).all()
    result = []
    for p in payments:
        user = db.query(User).filter(User.id == p.user_id).first()
        result.append({
            "id": p.provider_payment_id,
            "user_id": user.telegram_id if user else None,
            "username": user.username if user else None,
            "amount": p.amount,
            "status": p.status,
            "subscription_days": p.subscription_days,
            "subscription_type": p.subscription_type,
            "created_at": p.created_at.isoformat(),
            "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None
        })
    db.close()
    return jsonify({"payments": result})

@app.route("/api/admin/servers")
def admin_servers():
    db = SessionLocal()
    servers = db.query(Server).all()
    result = []
    for s in servers:
        result.append({
            "id": s.id,
            "name": s.name,
            "location": s.location,
            "host": s.host,
            "port": s.port,
            "protocol": s.protocol,
            "method": s.method,
            "vip_only": s.vip_only,
            "is_active": s.is_active,
            "load": s.current_load
        })
    db.close()
    return jsonify({"servers": result})

@app.route("/api/admin/broadcast", methods=["POST"])
def admin_broadcast():
    data = request.json
    message = data.get("message")
    admin_id = data.get("admin_id")
    
    if admin_id not in [7383521067]:
        return jsonify({"error": "Unauthorized"}), 403
    
    return jsonify({"status": "ok", "message": "Broadcast queued", "recipients": 100})

@app.route("/webapp")
@app.route("/webapp/<path:path>")
def serve_webapp(path="index.html"):
    return send_from_directory("webapp", path)

@app.route("/webapp/index.html")
def serve_index():
    return send_from_directory("webapp", "index.html")

if __name__ == "__main__":
    init_servers()
    app.run(host=API_HOST, port=API_PORT, debug=True)