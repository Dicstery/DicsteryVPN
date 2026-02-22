from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

from config import DATABASE_URL, TRIAL_TRAFFIC_LIMIT_GB, BASIC_TRAFFIC_LIMIT_GB, VIP_TRAFFIC_LIMIT_GB

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True)
    status = Column(String(20), default="NO_SUBSCRIPTION")
    subscription_end = Column(DateTime, nullable=True)
    subscription_type = Column(String(20), default="none")
    is_admin = Column(Boolean, default=False)
    traffic_used = Column(Float, default=0.0)
    traffic_limit = Column(Float, default=0.0)
    trial_used = Column(Boolean, default=False)
    trial_start = Column(DateTime, nullable=True)
    referral_code = Column(String(20), unique=True, nullable=True)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    referral_count = Column(Integer, default=0)
    bonus_days_earned = Column(Integer, default=0)
    vip_support_access = Column(Boolean, default=False)
    priority_server_access = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    referrals = relationship("User", backref="inviter", remote_side=[id])
    payments = relationship("Payment", back_populates="user")
    traffic_logs = relationship("TrafficLog", back_populates="user")
    devices = relationship("Device", back_populates="user")
    server_access = relationship("UserServerAccess", back_populates="user")

    def is_active(self):
        if not self.subscription_end:
            return False
        if self.is_admin:
            return True
        return self.subscription_end > datetime.utcnow()
    
    def days_remaining(self):
        if self.is_admin:
            return 9999
        if not self.subscription_end:
            return 0
        delta = self.subscription_end - datetime.utcnow()
        return max(0, delta.days)
    
    def traffic_percent(self):
        if self.traffic_limit <= 0 or self.is_admin:
            return 0
        return min(100, (self.traffic_used / self.traffic_limit) * 100)
    
    def to_dict(self):
        return {
            "id": self.telegram_id,
            "username": self.username,
            "uuid": self.uuid,
            "status": self.status,
            "subscription_end": self.subscription_end.isoformat() if self.subscription_end else None,
            "subscription_type": self.subscription_type,
            "is_admin": self.is_admin,
            "traffic_used": self.traffic_used,
            "traffic_limit": self.traffic_limit,
            "trial_used": self.trial_used,
            "referral_code": self.referral_code,
            "referral_count": self.referral_count,
            "bonus_days": self.bonus_days_earned,
            "vip_support": self.vip_support_access,
            "priority_server": self.priority_server_access,
            "created_at": self.created_at.isoformat()
        }

class Server(Base):
    __tablename__ = "servers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    location = Column(String(10), nullable=False)
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=443)
    protocol = Column(String(20), default="vless")
    method = Column(String(50), nullable=True)
    password = Column(String(255), nullable=True)
    uuid = Column(String(36), nullable=True)
    flow = Column(String(50), nullable=True)
    security = Column(String(20), default="none")
    network = Column(String(20), default="tcp")
    header_type = Column(String(20), default="none")
    tls = Column(String(20), nullable=True)
    sni = Column(String(255), nullable=True)
    fingerprint = Column(String(50), default="chrome")
    alpn = Column(String(50), nullable=True)
    public_key = Column(String(255), nullable=True)
    short_id = Column(String(50), nullable=True)
    grpc_mode = Column(String(20), nullable=True)
    grpc_service_name = Column(String(100), nullable=True)
    allow_insecure = Column(Boolean, default=False)
    vip_only = Column(Boolean, default=False)
    admin_only = Column(Boolean, default=False)
    priority_level = Column(Integer, default=0)
    current_load = Column(Float, default=0.0)
    max_load = Column(Float, default=100.0)
    is_active = Column(Boolean, default=True)
    total_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    bandwidth_used = Column(Float, default=0.0)
    bandwidth_limit = Column(Float, default=10000.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_check = Column(DateTime, default=datetime.utcnow)
    failed_checks = Column(Integer, default=0)
    
    user_access = relationship("UserServerAccess", back_populates="server")

class UserServerAccess(Base):
    __tablename__ = "user_server_access"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    server_id = Column(Integer, ForeignKey("servers.id"))
    subscription_end = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="server_access")
    server = relationship("Server", back_populates="user_access")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    provider = Column(String(50), nullable=False)
    provider_payment_id = Column(String(255), unique=True, nullable=True)
    status = Column(String(20), default="PENDING")
    subscription_days = Column(Integer, nullable=False)
    subscription_type = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="payments")

class TrafficLog(Base):
    __tablename__ = "traffic_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    server_id = Column(Integer, ForeignKey("servers.id"))
    bytes_sent = Column(Float, default=0.0)
    bytes_received = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    session_duration = Column(Integer, default=0)
    
    user = relationship("User", back_populates="traffic_logs")
    server = relationship("Server")

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    device_name = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)
    last_ip = Column(String(50), nullable=True)
    last_connected = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="devices")

class ReferralBonus(Base):
    __tablename__ = "referral_bonuses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(Integer, ForeignKey("users.id"))
    referred_id = Column(Integer, ForeignKey("users.id"))
    bonus_days = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)

class AdminAction(Base):
    __tablename__ = "admin_actions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)
    target_user_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class VIPSupportTicket(Base):
    __tablename__ = "vip_support_tickets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="OPEN")
    priority = Column(String(10), default="HIGH")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    user = relationship("User")

Base.metadata.create_all(bind=engine)