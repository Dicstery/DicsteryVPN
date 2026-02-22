import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import uuid
from datetime import datetime, timedelta
import threading
import time
import os

from config import BOT_TOKEN, API_URL, ADMIN_IDS
from database import SessionLocal, User, Payment, AdminAction

bot = telebot.TeleBot(BOT_TOKEN)

def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🚀 Личный кабинет", web_app={"url": f"{API_URL}/webapp"}),
        InlineKeyboardButton("💳 Купить подписку", callback_data="buy_subscription")
    )
    markup.add(
        InlineKeyboardButton("👥 Реферальная система", callback_data="referral"),
        InlineKeyboardButton("ℹ О боте", callback_data="about")
    )
    markup.add(
        InlineKeyboardButton("📊 Мой трафик", callback_data="traffic"),
        InlineKeyboardButton("🖥 Сервера", callback_data="servers_list")
    )
    return markup

def admin_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
    )
    markup.add(
        InlineKeyboardButton("💰 Платежи", callback_data="admin_payments"),
        InlineKeyboardButton("🖥 Сервера", callback_data="admin_servers")
    )
    markup.add(
        InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    referrer_code = None
    
    if len(args) > 1:
        referrer_code = args[1]
    
    telegram_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    
    response = requests.post(f"{API_URL}/api/user/create", json={
        "id": telegram_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name
    })
    
    data = response.json()
    
    if referrer_code and data.get("status") == "ok":
        requests.post(f"{API_URL}/api/referral/add", json={
            "referrer_code": referrer_code,
            "referred_id": telegram_id
        })
    
    welcome_text = (
        f"👋 Добро пожаловать, {first_name or username}!\n\n"
        f"🔐 Это VPN сервис нового поколения\n"
        f"• Быстрые сервера по всему миру\n"
        f"• Защита ваших данных\n"
        f"• Неограниченная скорость\n\n"
        f"Используй кнопки ниже для навигации"
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "buy_subscription":
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🎁 Пробная 3 дня", callback_data="sub_trial"),
            InlineKeyboardButton("⭐ Базовая 30 дней", callback_data="sub_basic")
        )
        markup.add(
            InlineKeyboardButton("👑 VIP 30 дней", callback_data="sub_vip"),
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
        )
        bot.edit_message_text(
            "💳 Выберите тип подписки:\n\n"
            "🎁 Пробная - 3 дня / 20 ГБ (1 раз)\n"
            "⭐ Базовая - 30 дней / Безлимит\n"
            "👑 VIP - 30 дней / Безлимит + Привилегии",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif call.data == "sub_trial":
        response = requests.post(f"{API_URL}/api/user/subscription/activate", json={
            "id": call.from_user.id,
            "type": "trial"
        })
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                bot.answer_callback_query(call.id, "❌ Пробный период уже использован", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "✅ Пробная подписка активирована!")
                bot.send_message(
                    call.message.chat.id,
                    "🎉 Пробная подписка активирована!\n"
                    "Перейдите в личный кабинет для настройки подключения."
                )
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка активации", show_alert=True)
    
    elif call.data == "sub_basic":
        payment_id = f"PAY{uuid.uuid4().hex[:12].upper()}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Оплатить 500₽", callback_data=f"pay_{payment_id}_basic"))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="buy_subscription"))
        
        bot.edit_message_text(
            "⭐ Базовая подписка\n"
            "Стоимость: 500₽\n"
            "Срок: 30 дней\n"
            "Трафик: Безлимит\n\n"
            "Нажмите кнопку для оплаты",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif call.data == "sub_vip":
        payment_id = f"PAY{uuid.uuid4().hex[:12].upper()}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Оплатить 1500₽", callback_data=f"pay_{payment_id}_vip"))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="buy_subscription"))
        
        bot.edit_message_text(
            "👑 VIP подписка\n"
            "Стоимость: 1500₽\n"
            "Срок: 30 дней\n"
            "Трафик: Безлимит\n"
            "Приоритетные сервера\n"
            "VIP поддержка 24/7\n\n"
            "Нажмите кнопку для оплаты",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif call.data.startswith("pay_"):
        parts = call.data.split("_")
        payment_id = parts[1]
        sub_type = parts[2]
        
        amount = 500 if sub_type == "basic" else 1500
        days = 30
        
        response = requests.post(f"{API_URL}/api/payments/create", json={
            "user_id": call.from_user.id,
            "amount": amount,
            "days": days,
            "subscription_type": sub_type,
            "provider": "telegram"
        })
        
        data = response.json()
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"confirm_{data['payment_id']}"))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="buy_subscription"))
        
        bot.edit_message_text(
            f"🧾 Счет на оплату:\n"
            f"Сумма: {amount}₽\n"
            f"Тип: {sub_type.upper()}\n"
            f"ID: {data['payment_id']}\n\n"
            f"Демо-режим: нажмите подтвердить",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif call.data.startswith("confirm_"):
        payment_id = call.data.replace("confirm_", "")
        
        response = requests.post(f"{API_URL}/api/payments/confirm", json={
            "payment_id": payment_id
        })
        
        if response.status_code == 200:
            bot.answer_callback_query(call.id, "✅ Оплата подтверждена! Подписка активирована.")
            bot.send_message(
                call.message.chat.id,
                "🎉 Подписка успешно активирована!\n"
                "Перейдите в личный кабинет для подключения."
            )
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка подтверждения", show_alert=True)
    
    elif call.data == "referral":
        response = requests.get(f"{API_URL}/api/referral/list", params={"user_id": call.from_user.id})
        
        if response.status_code == 200:
            data = response.json()
            
            text = (
                f"👥 Реферальная система\n\n"
                f"Ваша ссылка: https://t.me/{(bot.get_me()).username}?start={data['referral_code']}\n"
                f"Приглашено друзей: {data['total_referrals']}\n"
                f"Получено бонусных дней: {data['total_bonus_days']}\n\n"
                f"🎁 5 друзей = 1 день подписки!"
            )
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "traffic":
        response = requests.get(f"{API_URL}/api/traffic/usage", params={"id": call.from_user.id})
        
        if response.status_code == 200:
            data = response.json()
            
            if data["limit"] == 0:
                text = f"📊 Использование трафика\n\nБезлимит\nИспользовано: {(data['used']/1024):.2f} ГБ"
            else:
                used_gb = data["used"] / 1024
                limit_gb = data["limit"] / 1024
                bar_length = 20
                filled = int((data["percent"] / 100) * bar_length)
                bar = "█" * filled + "░" * (bar_length - filled)
                
                text = (
                    f"📊 Использование трафика\n\n"
                    f"{bar} {data['percent']:.1f}%\n"
                    f"Использовано: {used_gb:.2f} ГБ / {limit_gb:.2f} ГБ\n"
                )
                
                if data["percent"] > 90:
                    text += "\n⚠️ Внимание! Лимит трафика почти исчерпан"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "servers_list":
        response = requests.get(f"{API_URL}/api/servers", params={"user_id": call.from_user.id})
        
        if response.status_code == 200:
            data = response.json()
            
            text = "🖥 Доступные сервера:\n\n"
            for s in data["servers"]:
                load_emoji = "🟢" if s["load"] < 50 else "🟡" if s["load"] < 80 else "🔴"
                text += f"{s['name']} {load_emoji} {s['load']:.0f}%\n"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "about":
        text = (
            "ℹ О боте\n\n"
            "Dicstery VPN\n"
            "Версия: 3.0.0\n\n"
            "Особенности:\n"
            "• 14+ серверов по всему миру\n"
            "• VIP сервера с приоритетом\n"
            "• Безлимитный трафик\n"
            "• Реферальная система\n"
            "• VIP поддержка 24/7"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "admin_stats":
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "❌ Доступ запрещен", show_alert=True)
            return
        
        response = requests.get(f"{API_URL}/api/admin/statistics", params={"admin_id": call.from_user.id})
        
        if response.status_code == 200:
            data = response.json()
            text = (
                f"📊 Статистика\n\n"
                f"Всего пользователей: {data['total_users']}\n"
                f"Активных: {data['active']}\n"
                f"VIP: {data['vip']}\n"
                f"Админов: {data['admins']}\n"
                f"С истекшей: {data['expired']}\n"
                f"Использовали триал: {data['trial_used']}\n\n"
                f"Платежей сегодня: {data['payments_today']}\n"
                f"Выручка сегодня: {data['revenue_today']}₽\n"
                f"Активных серверов: {data['active_servers']}\n"
                f"VIP серверов: {data['vip_servers']}"
            )
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=admin_menu())
    
    elif call.data == "admin_users":
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "❌ Доступ запрещен", show_alert=True)
            return
        
        response = requests.get(f"{API_URL}/api/admin/users", params={"admin_id": call.from_user.id})
        
        if response.status_code == 200:
            data = response.json()
            text = "👥 Последние 10 пользователей:\n\n"
            
            for i, u in enumerate(data["users"][-10:]):
                status_emoji = "👑" if u["status"] == "VIP" else "✅" if u["status"] == "ACTIVE" else "❌"
                text += f"{status_emoji} {u['username'] or 'No name'} - {u['status']}\n"
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=admin_menu())
    
    elif call.data == "admin_payments":
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "❌ Доступ запрещен", show_alert=True)
            return
        
        response = requests.get(f"{API_URL}/api/admin/payments")
        
        if response.status_code == 200:
            data = response.json()
            text = "💰 Последние платежи:\n\n"
            
            for i, p in enumerate(data["payments"][-5:]):
                status_emoji = "✅" if p["status"] == "CONFIRMED" else "⏳"
                text += f"{status_emoji} {p['username']}: {p['amount']}₽ - {p['status']}\n"
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=admin_menu())
    
    elif call.data == "admin_servers":
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "❌ Доступ запрещен", show_alert=True)
            return
        
        response = requests.get(f"{API_URL}/api/admin/servers")
        
        if response.status_code == 200:
            data = response.json()
            text = "🖥 Сервера:\n\n"
            
            for s in data["servers"]:
                vip_mark = "👑 " if s.get("vip_only") else ""
                text += f"{vip_mark}{s['name']} - нагрузка {s['load']:.0f}%\n"
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=admin_menu())
    
    elif call.data == "admin_broadcast":
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "❌ Доступ запрещен", show_alert=True)
            return
        
        msg = bot.send_message(call.message.chat.id, "📢 Введите текст рассылки:")
        bot.register_next_step_handler(msg, process_broadcast)
    
    elif call.data == "back_to_main":
        bot.edit_message_text(
            "Главное меню:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu()
        )

def process_broadcast(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    text = message.text
    
    response = requests.post(f"{API_URL}/api/admin/broadcast", json={
        "message": text,
        "admin_id": message.from_user.id
    })
    
    if response.status_code == 200:
        bot.send_message(
            message.chat.id,
            "✅ Рассылка запущена!",
            reply_markup=admin_menu()
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Ошибка запуска рассылки",
            reply_markup=admin_menu()
        )

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(
            message.chat.id,
            "🔐 Панель администратора",
            reply_markup=admin_menu()
        )
    else:
        bot.send_message(message.chat.id, "❌ Доступ запрещен")

def check_expired_subscriptions():
    while True:
        time.sleep(3600)
        
        db = SessionLocal()
        now = datetime.utcnow()
        
        expiring_soon = db.query(User).filter(
            User.subscription_end <= now + timedelta(days=1),
            User.subscription_end > now,
            User.status.in_(["ACTIVE", "VIP"])
        ).all()
        
        for user in expiring_soon:
            hours_left = int((user.subscription_end - now).total_seconds() / 3600)
            if hours_left <= 24 and hours_left > 23:
                bot.send_message(
                    user.telegram_id,
                    f"⚠️ Ваша подписка истекает через {hours_left} часов!"
                )
            elif hours_left <= 3 and hours_left > 2:
                bot.send_message(
                    user.telegram_id,
                    f"⚠️ Ваша подписка истекает через {hours_left} часа! Продлите сейчас."
                )
        
        expired = db.query(User).filter(
            User.subscription_end <= now,
            User.status.in_(["ACTIVE", "VIP"])
        ).all()
        
        for user in expired:
            user.status = "EXPIRED"
            bot.send_message(
                user.telegram_id,
                "❌ Срок действия подписки истек. Продлите подписку для доступа."
            )
        
        db.commit()
        db.close()

def check_server_load():
    while True:
        time.sleep(60)
        
        db = SessionLocal()
        servers = db.query(Server).filter(Server.is_active == True).all()
        
        import random
        for server in servers:
            server.current_load = random.uniform(10, 80)
            server.last_check = datetime.utcnow()
        
        db.commit()
        db.close()

threading.Thread(target=check_expired_subscriptions, daemon=True).start()
threading.Thread(target=check_server_load, daemon=True).start()

if __name__ == "__main__":
    bot.infinity_polling()