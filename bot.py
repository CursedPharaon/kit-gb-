import json
import random
import asyncio
from datetime import datetime, timedelta
from vkbottle import Bot, Message
from vkbottle.bot import BotLabeler
from vkbottle.tools import Keyboard, KeyboardButtonColor, Text

GROUP_TOKEN = "vk1.a.qEQRPf1EYW95Y-UiPyMyKvF-3iogLfN45MLQzDjnk_0ww5Q-tf8CfxGKzjVqQ5PIBiYS9tecoswzP7_RVRID8KKotSQTQJQHsZ_cjAk-lJD8vn1rsXRvVvSVvxWI-uhJ3tvu0s1kyjakMHrI1vCgKBVIEtgIWzBDRk5iT64GlfzrHvK2siH2isU-aEBYBvulB8KWLpFF7uQCS5Wx-yaIOQ"
bot = Bot(token=GROUP_TOKEN)
labeler = BotLabeler()
bot.labeler = labeler

def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}}

def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

data = load_data()

def get_user(user_id):
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "money": 1000,
            "last_bonus": None,
            "last_treasure": None,
            "doors_cooldown": None
        }
        save_data(data)
    return data["users"][uid]

def main_keyboard():
    kb = Keyboard(one_time=False)
    kb.add(Text("/бонус"), color=KeyboardButtonColor.POSITIVE)
    kb.add(Text("/клад"), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("/двери"), color=KeyboardButtonColor.SECONDARY)
    kb.add(Text("/казино"), color=KeyboardButtonColor.NEGATIVE)
    kb.row()
    kb.add(Text("/топ"))
    kb.add(Text("/баланс"))
    return kb

@bot.on.private_message(text="/бонус")
@bot.on.chat_message(text="/бонус")
async def bonus_handler(message: Message):
    user = get_user(message.peer_id)
    now = datetime.now()
    
    if user["last_bonus"]:
        last = datetime.fromisoformat(user["last_bonus"])
        if now - last < timedelta(hours=24):
            remain = timedelta(hours=24) - (now - last)
            await message.reply(f"⏰ Бонус через {remain.seconds//3600}ч {(remain.seconds%3600)//60}мин")
            return
    
    amount = random.randint(100, 1000)
    user["money"] += amount
    user["last_bonus"] = now.isoformat()
    save_data(data)
    await message.reply(f"🎁 +{amount}💰 | Баланс: {user['money']}💰", keyboard=main_keyboard())

@bot.on.private_message(text="/клад")
@bot.on.chat_message(text="/клад")
async def treasure_handler(message: Message):
    user = get_user(message.peer_id)
    now = datetime.now()
    
    if user["last_treasure"]:
        last = datetime.fromisoformat(user["last_treasure"])
        if now - last < timedelta(hours=12):
            remain = timedelta(hours=12) - (now - last)
            await message.reply(f"⏰ Клад через {remain.seconds//3600}ч {(remain.seconds%3600)//60}мин")
            return
    
    if random.random() < 0.7:
        reward = random.randint(500, 3000)
        user["money"] += reward
        msg = f"💰 Клад! +{reward}💰"
    else:
        penalty = random.randint(100, 500)
        user["money"] -= penalty
        msg = f"💀 Ловушка! -{penalty}💰"
    
    user["last_treasure"] = now.isoformat()
    save_data(data)
    await message.reply(f"{msg} | Баланс: {user['money']}💰", keyboard=main_keyboard())

@bot.on.private_message(text="/двери")
@bot.on.chat_message(text="/двери")
async def doors_handler(message: Message):
    user = get_user(message.peer_id)
    now = datetime.now()
    
    # Получаем текст команды от пользователя
    import re
    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        choice = int(parts[1])
        if choice not in [1,2,3]:
            await message.reply("Выбери дверь 1, 2 или 3")
            return
        
        # Проверяем кулдаун 30 секунд
        if user["doors_cooldown"]:
            last = datetime.fromisoformat(user["doors_cooldown"])
            if datetime.now() - last < timedelta(seconds=30):
                await message.reply("⏰ Подожди 30 секунд перед новой попыткой!")
                return
        
        results = {1: random.randint(100, 500), 2: random.randint(-200, 800), 3: random.randint(0, 1000)}
        reward = results[choice]
        user["money"] += reward
        user["doors_cooldown"] = datetime.now().isoformat()
        save_data(data)
        await message.reply(f"🚪 Дверь {choice} → {'+' if reward>=0 else ''}{reward}💰 | Баланс: {user['money']}💰")
    else:
        await message.reply("🎲 Игра 'Двери'!\nНапиши: `/двери 1`, `/двери 2` или `/двери 3`", keyboard=main_keyboard())

@bot.on.private_message(text="/казино")
@bot.on.chat_message(text="/казино")
async def casino_handler(message: Message):
    user = get_user(message.peer_id)
    
    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        bet = int(parts[1])
        if bet < 50:
            await message.reply("Минимальная ставка 50💰")
            return
        if bet > user["money"]:
            await message.reply(f"Не хватает! У тебя {user['money']}💰")
            return
        
        user["money"] -= bet
        if random.random() < 0.4:
            win = bet * random.uniform(1.5, 3.5)
            user["money"] += win
            await message.reply(f"🎰 ВЫИГРЫШ! +{int(win)}💰 | Баланс: {user['money']}💰")
        else:
            await message.reply(f"💸 Проигрыш! -{bet}💰 | Баланс: {user['money']}💰")
        save_data(data)
    else:
        await message.reply("🎰 Казино!\nНапиши: `/казино [сумма]`\nПример: `/казино 100`", keyboard=main_keyboard())

@bot.on.private_message(text="/топ")
@bot.on.chat_message(text="/топ")
async def leaderboard_handler(message: Message):
    sorted_users = sorted(data["users"].items(), key=lambda x: x[1]["money"], reverse=True)[:10]
    if not sorted_users:
        await message.reply("Пока никого нет :(")
        return
    
    top_text = "🏆 ТОП 10:\n"
    for i, (uid, udata) in enumerate(sorted_users, 1):
        try:
            name = (await bot.api.users.get(user_ids=int(uid)))[0].first_name
        except:
            name = f"ID{uid}"
        top_text += f"{i}. {name} - {udata['money']}💰\n"
    await message.reply(top_text, keyboard=main_keyboard())

@bot.on.private_message(text="/баланс")
@bot.on.chat_message(text="/баланс")
async def balance_handler(message: Message):
    user = get_user(message.peer_id)
    await message.reply(f"💰 Твой баланс: {user['money']} монет", keyboard=main_keyboard())

async def main():
    print("✅ Бот запущен! Жду команды...")
    await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
