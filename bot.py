"""
╔══════════════════════════════════════════════════════════════╗
║           🎓 EDUBOT PRO — aiogram 3.x versiyasi              ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
TZ = timezone(timedelta(hours=5))
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery, KeyboardButton, Message,
    ReplyKeyboardMarkup, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

# ─────────────────────────────────────────────
#  🔧 SOZLAMALAR
# ─────────────────────────────────────────────
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"   # ← Shu yerga tokeningizni yozing
ADMIN_ID  = 123456789               # ← Sizning Telegram ID (int)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# ─────────────────────────────────────────────
#  📁 JSON DATABASE
# ─────────────────────────────────────────────
DB_FILE = "students.json"

def load_db() -> dict:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(data: dict):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_student(user_id: int) -> dict | None:
    return load_db().get(str(user_id))

def save_student(user_id: int, student: dict):
    db = load_db()
    db[str(user_id)] = student
    save_db(db)

# ─────────────────────────────────────────────
#  📌 FSM STATES
# ─────────────────────────────────────────────
class Reg(StatesGroup):
    name  = State()
    klass = State()
    phone = State()

class EditProfile(StatesGroup):
    value = State()

class AddNote(StatesGroup):
    text = State()

class AddFeedback(StatesGroup):
    text = State()

class AiHelper(StatesGroup):
    question = State()

# ─────────────────────────────────────────────
#  ⌨️ KLAVIATURALAR
# ─────────────────────────────────────────────
def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📚 Dars jadvali"),   KeyboardButton(text="✅ Vazifalarim")],
        [KeyboardButton(text="🧠 AI Yordamchi"),   KeyboardButton(text="📝 Eslatmalar")],
        [KeyboardButton(text="🎯 Maqsadlarim"),    KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="🏆 Yutuqlar"),        KeyboardButton(text="💬 Fikr-mulohaza")],
        [KeyboardButton(text="⚙️ Sozlamalar"),      KeyboardButton(text="📞 Bog'lanish")],
    ], resize_keyboard=True)

def back_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True
    )

def phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

def class_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="5-sinf"),  KeyboardButton(text="6-sinf"),  KeyboardButton(text="7-sinf")],
        [KeyboardButton(text="8-sinf"),  KeyboardButton(text="9-sinf"),  KeyboardButton(text="10-sinf")],
        [KeyboardButton(text="11-sinf"), KeyboardButton(text="Talaba")],
    ], resize_keyboard=True, one_time_keyboard=True)

# ─────────────────────────────────────────────
#  🚀 /start
# ─────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    student = get_student(message.from_user.id)

    if student:
        await message.answer(
            f"👋 Xush kelibsiz, *{student['name']}*!\n\n"
            f"🏫 Sinf: *{student['class']}*\n"
            f"📅 Bugun: *{datetime.now().strftime('%d.%m.%Y')}*\n\n"
            "Pastdagi menyudan tanlang 👇",
            reply_markup=main_kb(), parse_mode="Markdown"
        )
        return

    await message.answer(
        "🎓 *EduBot Pro*ga xush kelibsiz!\n\n"
        "Bu sizning shaxsiy ta'lim yordamchingiz.\n"
        "Avval ro'yxatdan o'tamiz.\n\n"
        "📝 *Ismingizni* kiriting:",
        reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown"
    )
    await state.set_state(Reg.name)

# ─────────────────────────────────────────────
#  📋 RO'YXATDAN O'TISH
# ─────────────────────────────────────────────
@router.message(Reg.name)
async def reg_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Ism kamida 2 ta harf bo'lsin. Qaytadan kiriting:")
        return
    await state.update_data(name=name)
    await message.answer(
        f"✅ Ajoyib, *{name}*!\n\nQaysi sinfda o'qiysiz? 👇",
        reply_markup=class_kb(), parse_mode="Markdown"
    )
    await state.set_state(Reg.klass)

@router.message(Reg.klass)
async def reg_class(message: Message, state: FSMContext):
    await state.update_data(klass=message.text.strip())
    await message.answer(
        "📞 Telefon raqamingizni yuboring yoki qo'lda kiriting (+998XXXXXXXXX):",
        reply_markup=phone_kb()
    )
    await state.set_state(Reg.phone)

@router.message(Reg.phone, F.contact)
async def reg_phone_contact(message: Message, state: FSMContext):
    await _finish_reg(message, state, message.contact.phone_number)

@router.message(Reg.phone)
async def reg_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not re.match(r'^\+?[0-9]{9,13}$', phone):
        await message.answer("❌ Noto'g'ri format. Masalan: +998901234567")
        return
    await _finish_reg(message, state, phone)

async def _finish_reg(message: Message, state: FSMContext, phone: str):
    data = await state.get_data()
    student = {
        "name": data["name"], "class": data["klass"], "phone": phone,
        "joined": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "tasks": [], "notes": [], "goals": [],
        "score": 0, "badges": [], "schedule": {}
    }
    save_student(message.from_user.id, student)
    await state.clear()
    await message.answer(
        f"🎉 *Ro'yxatdan o'tish muvaffaqiyatli!*\n\n"
        f"👤 Ism: *{student['name']}*\n"
        f"🏫 Sinf: *{student['class']}*\n"
        f"📱 Telefon: `{phone}`\n\n"
        "Endi barcha imkoniyatlardan foydalaning! 🚀",
        reply_markup=main_kb(), parse_mode="Markdown"
    )

# ─────────────────────────────────────────────
#  📚 DARS JADVALI
# ─────────────────────────────────────────────
@router.message(F.text == "📚 Dars jadvali")
async def schedule_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Dushanba",   callback_data="day_Monday"),
         InlineKeyboardButton(text="Seshanba",   callback_data="day_Tuesday")],
        [InlineKeyboardButton(text="Chorshanba", callback_data="day_Wednesday"),
         InlineKeyboardButton(text="Payshanba",  callback_data="day_Thursday")],
        [InlineKeyboardButton(text="Juma",       callback_data="day_Friday"),
         InlineKeyboardButton(text="Shanba",     callback_data="day_Saturday")],
        [InlineKeyboardButton(text="✏️ Dars qo'shish", callback_data="add_schedule")],
    ])
    await message.answer("📚 *Dars jadvali*\n\nQaysi kunni ko'rmoqchisiz?",
                         reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("day_"))
async def cb_day(call: CallbackQuery):
    await call.answer()
    day = call.data.replace("day_", "")
    day_uz = {
        "Monday": "Dushanba", "Tuesday": "Seshanba", "Wednesday": "Chorshanba",
        "Thursday": "Payshanba", "Friday": "Juma", "Saturday": "Shanba"
    }
    student = get_student(call.from_user.id)
    lessons = student.get("schedule", {}).get(day, [])

    if lessons:
        text = f"📅 *{day_uz.get(day, day)} dars jadvali:*\n\n"
        for i, l in enumerate(lessons, 1):
            text += f"{i}. 🕐 {l['time']} — *{l['subject']}*\n"
    else:
        text = (f"📅 *{day_uz.get(day, day)}*\n\n"
                "Hali dars qo'shilmagan.\n`/add_lesson Dushanba 08:00 Fan`")

    await call.message.edit_text(text, parse_mode="Markdown")

@router.callback_query(F.data == "add_schedule")
async def cb_add_schedule(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "✏️ Dars qo'shish:\n\n`/add_lesson Dushanba 08:00 Matematika`",
        parse_mode="Markdown"
    )

# ─────────────────────────────────────────────
#  ✅ VAZIFALAR
# ─────────────────────────────────────────────
@router.message(F.text == "✅ Vazifalarim")
async def tasks_menu(message: Message):
    student = get_student(message.from_user.id)
    tasks = student.get("tasks", [])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Qo'shish",    callback_data="task_add")],
        [InlineKeyboardButton(text="✅ Bajarildi",   callback_data="task_done"),
         InlineKeyboardButton(text="🗑 O'chirish",  callback_data="task_del")],
    ])
    if tasks:
        text = "✅ *Mening vazifalarim:*\n\n"
        for i, t in enumerate(tasks, 1):
            icon = "✅" if t.get("done") else "⏳"
            text += f"{icon} *{i}.* {t['subject']} — {t['title']}\n    📅 {t['deadline']}\n\n"
    else:
        text = "📭 Hali vazifa yo'q. Qo'shish uchun tugmani bosing."
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("task_"))
async def cb_task(call: CallbackQuery):
    await call.answer()
    msgs = {
        "task_add":  "➕ Qo'shish:\n`/task Fan Nom Muddat`\nMisol: `/task Matematika Tenglamalar 25.03.2025`",
        "task_done": "✅ Bajarilgan raqamni yuboring:\n`/done 1`",
        "task_del":  "🗑 O'chirish:\n`/del_task 1`",
    }
    await call.message.edit_text(msgs[call.data], parse_mode="Markdown")

# ─────────────────────────────────────────────
#  🧠 AI YORDAMCHI
# ─────────────────────────────────────────────
@router.message(F.text == "🧠 AI Yordamchi")
async def ai_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📐 Matematika",   callback_data="ai_math"),
         InlineKeyboardButton(text="🔬 Fizika",       callback_data="ai_physics")],
        [InlineKeyboardButton(text="⚗️ Kimyo",        callback_data="ai_chemistry"),
         InlineKeyboardButton(text="🌍 Tarix",        callback_data="ai_history")],
        [InlineKeyboardButton(text="📖 Adabiyot",     callback_data="ai_lit"),
         InlineKeyboardButton(text="🇬🇧 Ingliz tili", callback_data="ai_english")],
        [InlineKeyboardButton(text="💡 Umumiy savol", callback_data="ai_general")],
    ])
    await message.answer(
        "🧠 *AI Yordamchi*\n\nQaysi fan bo'yicha yordam kerak?",
        reply_markup=keyboard, parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("ai_"))
async def cb_ai_subject(call: CallbackQuery, state: FSMContext):
    await call.answer()
    subjects = {
        "ai_math":      "📐 Matematika",
        "ai_physics":   "🔬 Fizika",
        "ai_chemistry": "⚗️ Kimyo",
        "ai_history":   "🌍 Tarix",
        "ai_lit":       "📖 Adabiyot",
        "ai_english":   "🇬🇧 Ingliz tili",
        "ai_general":   "💡 Umumiy",
    }
    subject = subjects[call.data]
    await state.update_data(ai_subject=subject)
    await state.set_state(AiHelper.question)
    await call.message.edit_text(
        f"*{subject}* bo'yicha savol\n\n✍️ Savolingizni yuboring:",
        parse_mode="Markdown"
    )

@router.message(AiHelper.question)
async def ai_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    subject = data.get("ai_subject", "Umumiy")
    await state.clear()
    await message.answer("🤔 Javob tayyorlanmoqda...")
    answer = smart_response(subject, message.text)
    await message.answer(
        f"🧠 *{subject} — Javob:*\n\n{answer}\n\n"
        "─────────────────\n"
        "❓ Yana savol uchun /menu",
        parse_mode="Markdown", reply_markup=main_kb()
    )

def smart_response(subject: str, question: str) -> str:
    q = question.lower()

    if "Matematika" in subject:
        if "kvadrat" in q:
            return ("📐 *Kvadrat tenglama:* ax²+bx+c=0\n\n"
                    "D = b²−4ac\n• D>0 → x=(−b±√D)/2a\n"
                    "• D=0 → x=−b/2a\n• D<0 → yechim yo'q\n\n"
                    "📌 x²−5x+6=0 → x₁=3, x₂=2 ✅")
        if "pifagor" in q:
            return "📐 *Pifagor:* a²+b²=c²\n\n📌 a=3,b=4 → c=5 ✅"
        if "foiz" in q:
            return ("📐 *Foiz:*\nfoiz = (qism/umumiy)×100\n\n"
                    "📌 20 dan 5 necha foiz?\n5/20×100 = *25%* ✅")

    if "Fizika" in subject:
        if any(w in q for w in ["tezlik", "harakat"]):
            return "🔬 *Kinematika:*\nv=s/t\na=(v−v₀)/t\ns=v₀t+at²/2"
        if "kuch" in q:
            return "🔬 *Newton II:* F=m×a\nF(N), m(kg), a(m/s²)"
        if "energi" in q:
            return "🔬 *Energiya:*\nKinetik: Ek=mv²/2\nPotensial: Ep=mgh"

    if "Ingliz" in subject:
        if any(w in q for w in ["grammar", "grammatika"]):
            return ("🇬🇧 *Asosiy zamonlar:*\n\n"
                    "• Simple Present: I work\n• Simple Past: I worked\n"
                    "• Present Cont.: I am working\n• Future: I will work")
        if "tarji" in q:
            return "🇬🇧 Tarjima uchun savolingizni to'liq yozing."

    if "Tarix" in subject:
        if any(w in q for w in ["mustaqillik", "istiqlol"]):
            return ("🌍 *O'zbekiston mustaqilligi:*\n\n"
                    "📅 1991-yil 31-avgust\n"
                    "👤 Birinchi Prezident: Islom Karimov\n"
                    "🗓 Mustaqillik kuni: 1-sentabr")

    if "Kimyo" in subject:
        if "mendeleev" in q or "jadval" in q:
            return "⚗️ *Mendeleev jadvali:* 118 ta element.\nDavrlar: 7 ta, Gruppalar: 18 ta."

    return (f"💡 *Savol:* _{question}_\n\n"
            "Tavsiya:\n1️⃣ Darslikni o'qing\n"
            "2️⃣ O'qituvchidan so'rang\n"
            "3️⃣ YouTube'dan qidiring\n\n"
            "🤖 _Kelajakda bu botga AI API ulanib to'liq javob beradi._")

# ─────────────────────────────────────────────
#  📝 ESLATMALAR
# ─────────────────────────────────────────────
@router.message(F.text == "📝 Eslatmalar")
async def notes_menu(message: Message):
    student = get_student(message.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi eslatma", callback_data="note_add")],
        [InlineKeyboardButton(text="📋 Ko'rish",      callback_data="note_list"),
         InlineKeyboardButton(text="🗑 O'chirish",    callback_data="note_del")],
    ])
    await message.answer(
        f"📝 *Eslatmalar*\nJami: *{len(student.get('notes', []))}* ta",
        reply_markup=keyboard, parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("note_"))
async def cb_note(call: CallbackQuery, state: FSMContext):
    await call.answer()
    student = get_student(call.from_user.id)
    if call.data == "note_add":
        await state.set_state(AddNote.text)
        await call.message.edit_text("✍️ Eslatmangizni yuboring:")
    elif call.data == "note_list":
        notes = student.get("notes", [])
        if notes:
            text = "📋 *Eslatmalar:*\n\n"
            for i, n in enumerate(notes, 1):
                text += f"*{i}.* {n['text']}\n    _{n['date']}_\n\n"
        else:
            text = "📭 Eslatmalar yo'q."
        await call.message.edit_text(text, parse_mode="Markdown")
    elif call.data == "note_del":
        await call.message.edit_text("🗑 O'chirish: `/del_note 1`", parse_mode="Markdown")

@router.message(AddNote.text)
async def save_note(message: Message, state: FSMContext):
    await state.clear()
    student = get_student(message.from_user.id)
    notes = student.get("notes", [])
    notes.append({"text": message.text, "date": datetime.now().strftime("%d.%m.%Y %H:%M")})
    student["notes"] = notes
    save_student(message.from_user.id, student)
    await message.answer("📝 Eslatma saqlandi! ✅", reply_markup=main_kb())

# ─────────────────────────────────────────────
#  🎯 MAQSADLAR
# ─────────────────────────────────────────────
@router.message(F.text == "🎯 Maqsadlarim")
async def goals_menu(message: Message):
    student = get_student(message.from_user.id)
    goals = student.get("goals", [])
    done = sum(1 for g in goals if g.get("done"))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Yangi maqsad",  callback_data="goal_add")],
        [InlineKeyboardButton(text="📊 Ko'rish",       callback_data="goal_list"),
         InlineKeyboardButton(text="🏆 Bajardim!",     callback_data="goal_done")],
    ])
    await message.answer(
        f"🎯 *Maqsadlarim*\n\n✅ Bajarilgan: *{done}*\n⏳ Kutilayotgan: *{len(goals)-done}*",
        reply_markup=keyboard, parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("goal_"))
async def cb_goal(call: CallbackQuery):
    await call.answer()
    student = get_student(call.from_user.id)
    if call.data == "goal_add":
        await call.message.edit_text(
            "🎯 Format: `/goal Nom Muddat`\nMisol: `/goal Matematikadan_5 01.06.2025`",
            parse_mode="Markdown"
        )
    elif call.data == "goal_list":
        goals = student.get("goals", [])
        if goals:
            text = "🎯 *Maqsadlar:*\n\n"
            for i, g in enumerate(goals, 1):
                icon = "✅" if g.get("done") else "⏳"
                text += f"{icon} *{i}.* {g['title']}\n    📅 {g['deadline']}\n\n"
        else:
            text = "📭 Maqsad yo'q."
        await call.message.edit_text(text, parse_mode="Markdown")
    elif call.data == "goal_done":
        await call.message.edit_text("🏆 Qaysi maqsad? `/achieved 1`", parse_mode="Markdown")

# ─────────────────────────────────────────────
#  📊 STATISTIKA
# ─────────────────────────────────────────────
@router.message(F.text == "📊 Statistika")
async def statistics(message: Message):
    s = get_student(message.from_user.id)
    tasks = s.get("tasks", [])
    goals = s.get("goals", [])
    done_t = sum(1 for t in tasks if t.get("done"))
    done_g = sum(1 for g in goals if g.get("done"))

    def bar(done, total):
        pct = int(done / total * 100) if total else 0
        return "🟩" * (pct // 10) + "⬜" * (10 - pct // 10) + f" {pct}%"

    await message.answer(
        f"📊 *{s['name']} — Statistika*\n\n"
        f"🏫 {s['class']} | 📅 {s['joined']}\n\n"
        f"✅ Vazifalar: {done_t}/{len(tasks)}\n{bar(done_t, len(tasks))}\n\n"
        f"🎯 Maqsadlar: {done_g}/{len(goals)}\n{bar(done_g, len(goals))}\n\n"
        f"📝 Eslatmalar: *{len(s.get('notes', []))}* ta\n"
        f"⭐ Ball: *{s.get('score', 0)}*\n"
        f"🏆 Yutuqlar: *{len(s.get('badges', []))}* ta",
        parse_mode="Markdown", reply_markup=main_kb()
    )

# ─────────────────────────────────────────────
#  🏆 YUTUQLAR
# ─────────────────────────────────────────────
@router.message(F.text == "🏆 Yutuqlar")
async def achievements(message: Message):
    s = get_student(message.from_user.id)
    score = s.get("score", 0)
    notes_count = len(s.get("notes", []))
    done_tasks = sum(1 for t in s.get("tasks", []) if t.get("done"))
    done_goals = sum(1 for g in s.get("goals", []) if g.get("done"))

    all_badges = [
        ("🌟 Birinchi qadam",  "Botdan foydalanish boshlandi", True),
        ("📝 Yozuvchi",        "5 ta eslatma qo'shildi",       notes_count >= 5),
        ("✅ Ishchan",          "10 ta vazifa bajarildi",       done_tasks >= 10),
        ("🎯 Maqsadli",        "3 ta maqsadga erishildi",      done_goals >= 3),
        ("💎 VIP o'quvchi",    "100 ball to'plandi",           score >= 100),
    ]
    text = "🏆 *Yutuqlar:*\n\n"
    for name, desc, earned in all_badges:
        text += f"{'✅' if earned else '🔒'} *{name}*\n   _{desc}_\n\n"
    text += f"━━━━━━━━━━━━\n⭐ Umumiy ball: *{score}*"
    await message.answer(text, parse_mode="Markdown", reply_markup=main_kb())

# ─────────────────────────────────────────────
#  💬 FIKR-MULOHAZA
# ─────────────────────────────────────────────
@router.message(F.text == "💬 Fikr-mulohaza")
async def feedback_start(message: Message, state: FSMContext):
    await state.set_state(AddFeedback.text)
    await message.answer(
        "💬 Fikr yoki taklifingizni yozing:",
        reply_markup=back_kb()
    )

@router.message(AddFeedback.text)
async def feedback_save(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("🏠 Asosiy menyu:", reply_markup=main_kb())
        return
    await state.clear()
    s = get_student(message.from_user.id)
    try:
        await bot.send_message(
            ADMIN_ID,
            f"💬 *Yangi fikr:*\n👤 {s['name']} ({s['class']})\n\n_{message.text}_",
            parse_mode="Markdown"
        )
    except Exception:
        pass
    await message.answer("✅ Fikringiz uchun rahmat! 🙏", reply_markup=main_kb())

# ─────────────────────────────────────────────
#  ⚙️ SOZLAMALAR
# ─────────────────────────────────────────────
@router.message(F.text == "⚙️ Sozlamalar")
async def settings_menu(message: Message):
    s = get_student(message.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Ism",    callback_data="edit_name"),
         InlineKeyboardButton(text="🏫 Sinf",   callback_data="edit_class")],
        [InlineKeyboardButton(text="📱 Telefon", callback_data="edit_phone")],
        [InlineKeyboardButton(text="🗑 Profilni o'chirish", callback_data="edit_delete")],
    ])
    await message.answer(
        f"⚙️ *Sozlamalar*\n\n👤 {s['name']}\n🏫 {s['class']}\n📱 {s['phone']}",
        reply_markup=keyboard, parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("edit_"))
async def cb_settings(call: CallbackQuery, state: FSMContext):
    await call.answer()
    if call.data == "edit_delete":
        db = load_db()
        db.pop(str(call.from_user.id), None)
        save_db(db)
        await call.message.edit_text("🗑 Profil o'chirildi. /start bilan qayta boshlang.")
        return
    field_map = {"edit_name": "name", "edit_class": "class", "edit_phone": "phone"}
    field = field_map.get(call.data)
    if field:
        await state.set_state(EditProfile.value)
        await state.update_data(edit_field=field)
        labels = {"name": "ismingizni", "class": "sinfingizni", "phone": "telefon raqamingizni"}
        await call.message.edit_text(f"✏️ Yangi *{labels[field]}* yuboring:", parse_mode="Markdown")

@router.message(EditProfile.value)
async def save_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data["edit_field"]
    await state.clear()
    s = get_student(message.from_user.id)
    s[field] = message.text.strip()
    save_student(message.from_user.id, s)
    await message.answer(f"✅ Yangilandi!", reply_markup=main_kb())

# ─────────────────────────────────────────────
#  📞 BOG'LANISH
# ─────────────────────────────────────────────
@router.message(F.text == "📞 Bog'lanish")
async def contact_info(message: Message):
    await message.answer(
        "📞 *Bog'lanish*\n\n"
        "👨‍💻 Dasturchi: @your_username\n"
        "📧 Email: your@email.com\n"
        "🌐 Kanal: @your_channel\n\n"
        "⏰ Ish vaqti: Du–Ju 09:00–18:00",
        parse_mode="Markdown", reply_markup=main_kb()
    )

# ─────────────────────────────────────────────
#  📌 SLASH COMMANDS
# ─────────────────────────────────────────────
@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu:", reply_markup=main_kb())

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 *Buyruqlar:*\n\n"
        "/start — Botni boshlash\n/menu — Asosiy menyu\n\n"
        "📋 *Vazifalar:*\n"
        "`/task Fan Nom Muddat`\n`/done 1`\n`/del_task 1`\n\n"
        "🎯 *Maqsadlar:*\n"
        "`/goal Nom Muddat`\n`/achieved 1`\n\n"
        "📚 *Jadval:*\n"
        "`/add_lesson Dushanba 08:00 Fan`\n\n"
        "📝 *Eslatmalar:*\n"
        "`/note Matn`\n`/del_note 1`",
        parse_mode="Markdown", reply_markup=main_kb()
    )

@router.message(Command("task"))
async def cmd_add_task(message: Message):
    args = message.text.split()[1:]
    if len(args) < 3:
        await message.answer("❌ Format: `/task Matematika Tenglamalar 25.03.2025`",
                             parse_mode="Markdown"); return
    s = get_student(message.from_user.id)
    tasks = s.get("tasks", [])
    tasks.append({
        "subject": args[0].replace("_", " "), "title": args[1].replace("_", " "),
        "deadline": args[2], "done": False,
        "added": datetime.now().strftime("%d.%m.%Y")
    })
    s["tasks"] = tasks
    s["score"] = s.get("score", 0) + 5
    save_student(message.from_user.id, s)
    await message.answer(
        f"✅ Vazifa qo'shildi! +5 ball\n📚 *{args[0].replace('_',' ')}* — {args[1].replace('_',' ')}\n📅 {args[2]}",
        parse_mode="Markdown", reply_markup=main_kb()
    )

@router.message(Command("done"))
async def cmd_done_task(message: Message):
    args = message.text.split()[1:]
    if not args or not args[0].isdigit():
        await message.answer("❌ Format: `/done 1`", parse_mode="Markdown"); return
    s = get_student(message.from_user.id)
    tasks = s.get("tasks", [])
    idx = int(args[0]) - 1
    if 0 <= idx < len(tasks):
        tasks[idx]["done"] = True
        s["tasks"] = tasks
        s["score"] = s.get("score", 0) + 10
        save_student(message.from_user.id, s)
        await message.answer(
            f"🎉 Bajarildi! +10 ball\n✅ _{tasks[idx]['title']}_",
            parse_mode="Markdown", reply_markup=main_kb()
        )
    else:
        await message.answer("❌ Bunday vazifa topilmadi.")

@router.message(Command("del_task"))
async def cmd_del_task(message: Message):
    args = message.text.split()[1:]
    if not args or not args[0].isdigit():
        await message.answer("❌ Format: `/del_task 1`", parse_mode="Markdown"); return
    s = get_student(message.from_user.id)
    tasks = s.get("tasks", [])
    idx = int(args[0]) - 1
    if 0 <= idx < len(tasks):
        removed = tasks.pop(idx)
        s["tasks"] = tasks
        save_student(message.from_user.id, s)
        await message.answer(f"🗑 O'chirildi: _{removed['title']}_",
                             parse_mode="Markdown", reply_markup=main_kb())
    else:
        await message.answer("❌ Topilmadi.")

@router.message(Command("goal"))
async def cmd_add_goal(message: Message):
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer("❌ Format: `/goal Nom Muddat`", parse_mode="Markdown"); return
    s = get_student(message.from_user.id)
    goals = s.get("goals", [])
    goals.append({"title": args[0].replace("_", " "), "deadline": args[1], "done": False})
    s["goals"] = goals
    s["score"] = s.get("score", 0) + 5
    save_student(message.from_user.id, s)
    await message.answer(
        f"🎯 Maqsad qo'shildi! +5 ball\n*{args[0].replace('_',' ')}* — {args[1]}",
        parse_mode="Markdown", reply_markup=main_kb()
    )

@router.message(Command("achieved"))
async def cmd_achieved(message: Message):
    args = message.text.split()[1:]
    if not args or not args[0].isdigit():
        await message.answer("❌ Format: `/achieved 1`", parse_mode="Markdown"); return
    s = get_student(message.from_user.id)
    goals = s.get("goals", [])
    idx = int(args[0]) - 1
    if 0 <= idx < len(goals):
        goals[idx]["done"] = True
        s["goals"] = goals
        s["score"] = s.get("score", 0) + 20
        save_student(message.from_user.id, s)
        await message.answer(
            f"🏆 Maqsadga yetdingiz! +20 ball 🎉\n_{goals[idx]['title']}_",
            parse_mode="Markdown", reply_markup=main_kb()
        )
    else:
        await message.answer("❌ Topilmadi.")

@router.message(Command("note"))
async def cmd_note(message: Message):
    text = message.text.partition(" ")[2].strip()
    if not text:
        await message.answer("❌ Format: `/note Matn`", parse_mode="Markdown"); return
    s = get_student(message.from_user.id)
    notes = s.get("notes", [])
    notes.append({"text": text, "date": datetime.now().strftime("%d.%m.%Y %H:%M")})
    s["notes"] = notes
    save_student(message.from_user.id, s)
    await message.answer(f"📝 Saqlandi!\n_{text}_", parse_mode="Markdown", reply_markup=main_kb())

@router.message(Command("del_note"))
async def cmd_del_note(message: Message):
    args = message.text.split()[1:]
    if not args or not args[0].isdigit():
        await message.answer("❌ Format: `/del_note 1`", parse_mode="Markdown"); return
    s = get_student(message.from_user.id)
    notes = s.get("notes", [])
    idx = int(args[0]) - 1
    if 0 <= idx < len(notes):
        removed = notes.pop(idx)
        s["notes"] = notes
        save_student(message.from_user.id, s)
        await message.answer(f"🗑 O'chirildi: _{removed['text'][:50]}_",
                             parse_mode="Markdown")

@router.message(Command("add_lesson"))
async def cmd_add_lesson(message: Message):
    args = message.text.split()[1:]
    if len(args) < 3:
        await message.answer("❌ Format: `/add_lesson Dushanba 08:00 Matematika`",
                             parse_mode="Markdown"); return
    day_map = {
        "dushanba": "Monday", "seshanba": "Tuesday", "chorshanba": "Wednesday",
        "payshanba": "Thursday", "juma": "Friday", "shanba": "Saturday"
    }
    day = day_map.get(args[0].lower(), args[0])
    s = get_student(message.from_user.id)
    schedule = s.get("schedule", {})
    schedule.setdefault(day, []).append({"time": args[1], "subject": " ".join(args[2:])})
    schedule[day].sort(key=lambda x: x["time"])
    s["schedule"] = schedule
    save_student(message.from_user.id, s)
    await message.answer(
        f"✅ Dars qo'shildi!\n📅 *{args[0]}* {args[1]} — *{' '.join(args[2:])}*",
        parse_mode="Markdown", reply_markup=main_kb()
    )

# ─────────────────────────────────────────────
#  👑 ADMIN BUYRUQLARI
# ─────────────────────────────────────────────
@router.message(Command("stats"))
async def cmd_admin_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Ruxsat yo'q."); return
    db = load_db()
    classes: dict = {}
    for s in db.values():
        c = s.get("class", "?")
        classes[c] = classes.get(c, 0) + 1
    text = f"👑 *Admin statistikasi*\n\n👥 Jami: *{len(db)}* ta\n\n🏫 Sinflar:\n"
    for c, n in sorted(classes.items()):
        text += f"• {c}: {n} ta\n"
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Ruxsat yo'q."); return
    text = message.text.partition(" ")[2].strip()
    if not text:
        await message.answer("Format: `/broadcast Matn`", parse_mode="Markdown"); return
    db = load_db()
    sent = failed = 0
    for uid in db:
        try:
            await bot.send_message(int(uid), f"📢 *EduBot xabari:*\n\n{text}",
                                   parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1
    await message.answer(f"✅ Yuborildi: {sent}\n❌ Xato: {failed}")

# ─────────────────────────────────────────────
#  🔙 ORQAGA
# ─────────────────────────────────────────────
@router.message(F.text == "🔙 Orqaga")
async def go_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu:", reply_markup=main_kb())

# ─────────────────────────────────────────────
#  ❓ NOMA'LUM XABAR
# ─────────────────────────────────────────────
@router.message()
async def unknown(message: Message):
    s = get_student(message.from_user.id)
    if not s:
        await message.answer("Avval /start bilan ro'yxatdan o'ting.")
        return
    await message.answer("💡 Menyudan tanlang yoki /help", reply_markup=main_kb())

# ─────────────────────────────────────────────
#  🚀 ISHGA TUSHIRISH
# ─────────────────────────────────────────────
async def main():
    logger.info("🚀 EduBot Pro (aiogram 3.x) ishga tushdi!")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
