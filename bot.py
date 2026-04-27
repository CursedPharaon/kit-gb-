import json
import random
import asyncio
from datetime import datetime, timedelta
from vkbottle import Bot, Message, API
from vkbottle.bot import BotLabeler, MessageEvent
from vkbottle.tools import Keyboard, KeyboardButtonColor, Text, Callback

# ===== КОНФИГ =====
GROUP_TOKEN = "vk1.a.qEQRPf1EYW95Y-UiPyMyKvF-3iogLfN45MLQzDjnk_0ww5Q-tf8CfxGKzjVqQ5PIBiYS9tecoswzP7_RVRID8KKotSQTQJQHsZ_cjAk-lJD8vn1rsXRvVvSVvxWI-uhJ3tvu0s1kyjakMHrI1vCgKBVIEtgIWzBDRk5iT64GlfzrHvK2siH2isU-aEBYBvulB8KWLpFF7uQCS5Wx-yaIOQ"
bot = Bot(token=GROUP_TOKEN)
labeler = BotLabeler()
bot.labeler = labeler

# ===== ЗАГРУЗКА/СОХРАНЕНИЕ ДАННЫХ =====
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "last_clean": datetime.now().isoformat()}

def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

data = load_data()

# Очистка просроченных штрафов
def check_penalties():
    now = datetime.now()
    for uid in list(data["users"].keys()):
        user = data["users"][uid]
        if "penalty_until" in user and datetime.fromisoformat(user["penalty_until"]) < now:
            user["penalty"] = False
            del user["penalty_until"]

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def get_user(user_id):
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "money": 1000,
            "cars": ["Lada"],
            "businesses": [],
            "vip": False,
            "vip_until": None,
            "last_bonus": None,
            "last_treasure": None,
            "penalty": False
        }
        save_data(data)
    return data["users"][uid]

def save_stats():
    save_data(data)

# ===== КЛАВИАТУРЫ =====
def main_keyboard():
    kb = Keyboard(one_time=False)
    kb.add(Text("/бонус"), color=KeyboardButtonColor.POSITIVE)
    kb.add(Text("/клад"), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("/двери"), color=KeyboardButtonColor.SECONDARY)
    kb.add(Text("/бизнесы"), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("/казино"), color=KeyboardButtonColor.NEGATIVE)
    kb.add(Text("/топ"))
    return kb

def doors_keyboard(user_id):
    kb = Keyboard(one_time=True)
    for i in range(1, 4):
        kb.add(Callback(f"{i}", payload={"cmd": "door", "user": user_id, "choice": i}), color=KeyboardButtonColor.PRIMARY)
        if i < 3:
            kb.row()
    return kb

# ===== КОМАНДЫ =====
@bot.on.private_message(text="/бонус")
@bot.on.chat_message(text="/бонус")
async def bonus_handler(message: Message):
    user = get_user(message.peer_id)
    now = datetime.now()
    
    if user["last_bonus"]:
        last = datetime.fromisoformat(user["last_bonus"])
        if now - last < timedelta(hours=24):
            remain = timedelta(hours=24) - (now - last)
            await message.reply(f"⏰ Бонус будет через {remain.seconds//3600}ч {(remain.seconds%3600)//60}мин")
            return
    
    amount = random.randint(100, 1000)
    user["money"] += amount
    user["last_bonus"] = now.isoformat()
    save_stats()
    await message.reply(f"🎁 Вы получили {amount} монет! Баланс: {user['money']}💰", keyboard=main_keyboard())

@bot.on.private_message(text="/клад")
@bot.on.chat_message(text="/клад")
async def treasure_handler(message: Message):
    user = get_user(message.peer_id)
    now = datetime.now()
    
    if user["last_treasure"]:
        last = datetime.fromisoformat(user["last_treasure"])
        if now - last < timedelta(hours=12):
            remain = timedelta(hours=12) - (now - last)
            await message.reply(f"⏰ Клад появится через {remain.seconds//3600}ч {(remain.seconds%3600)//60}мин")
            return
    
    # Рандомные клады
    treasures = [(500, 2000), (100, 500), (2000, 5000), (-300, -100)]
    if random.random() < 0.7:  # 70% удачи
        reward = random.randint(500, 3000)
        user["money"] += reward
        msg = f"💰 Нашли клад! +{reward} монет!"
    else:
        penalty = random.randint(-500, -100)
        user["money"] += penalty
        msg = f"💀 Ловушка! Теряете {-penalty} монет!"
    
    user["last_treasure"] = now.isoformat()
    save_stats()
    await message.reply(f"{msg} Баланс: {user['money']}💰", keyboard=main_keyboard())

@bot.on.private_message(text="/двери")
@bot.on.chat_message(text="/двери")
async def doors_handler(message: Message):
    user_id = message.peer_id
    await message.reply(
        "🚪 Выберите дверь (1-3):",
        keyboard=doors_keyboard(user_id)
    )

@bot.on.raw_event(MessageEvent, dataclass=MessageEvent)
async def handle_callback(event: MessageEvent):
    if event.payload.get("cmd") == "door" and event.payload.get("user") == event.object.peer_id:
        choice = event.payload["choice"]
        results = {
            1: random.randint(100, 500),
            2: random.randint(-200, 800),
            3: random.randint(0, 1000)
        }
        reward = results[choice]
        user = get_user(event.object.peer_id)
        user["money"] += reward
        save_stats()
        
        msg = f"🚪 Дверь {choice} → {'+' if reward>=0 else ''}{reward} монет! Баланс: {user['money']}💰"
        await bot.api.messages.send_message_event_answer(
            event_id=event.object.event_id,
            user_id=event.object.user_id,
            peer_id=event.object.peer_id,
            event_data=json.dumps({"type": "show_snackbar", "text": msg})
        )

@bot.on.private_message(text="/казино")
@bot.on.chat_message(text="/казино")
async def casino_handler(message: Message):
    user = get_user(message.peer_id)
    if user["money"] < 100:
        await message.reply("❌ Нужно минимум 100 монет!")
        return
    
    bet = random.randint(100, min(1000, user["money"]))
    user["money"] -= bet
    
    if random.random() < 0.4:  # 40% выигрыша
        win = bet * random.uniform(1.5, 3)
        user["money"] += win
        await message.reply(f"🎰 ДЖЕКПОТ! Выиграли {int(win)} монет! Баланс: {user['money']}💰")
    else:
        await message.reply(f"💸 Проиграли {bet} монет. Баланс: {user['money']}💰")
    save_stats()

@bot.on.private_message(text="/топ")
@bot.on.chat_message(text="/топ")
async def leaderboard_handler(message: Message):
    sorted_users = sorted(data["users"].items(), key=lambda x: x[1]["money"], reverse=True)[:10]
    top_text = "🏆 ТОП 10 ИГРОКОВ:\n"
    for i, (uid, udata) in enumerate(sorted_users, 1):
        try:
            name = (await bot.api.users.get(user_ids=int(uid)))[0].first_name
        except:
            name = f"User_{uid}"
        top_text += f"{i}. {name} - {udata['money']}💰\n"
    await message.reply(top_text, keyboard=main_keyboard())

@bot.on.private_message(text="/бизнесы")
@bot.on.chat_message(text="/бизнесы")
async def businesses_handler(message: Message):
    user = get_user(message.peer_id)
    businesses = {
        "Ферма": 2000,
        "Кафе": 5000,
        "ИТ-стартап": 10000
    }
    
    if not user["businesses"]:
        await message.reply("📊 Доступные бизнесы:\n" + "\n".join([f"{name} - {price}💰" for name, price in businesses.items()]) + "\n\nНапишите /купить бизнес [название]")
    else:
        income = 0
        for biz in user["businesses"]:
            income += businesses.get(biz, 0) // 10
        await message.reply(f"Ваши бизнесы: {', '.join(user['businesses'])}\nДоход в час: {income}💰")

# ===== ЗАПУСК =====
async def main():
    print("Бот запущен!")
    await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())