import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
import httpx
import os

def load_vocabulary():
    vocabulary = {}
    excel_file = 'vocabulary.xlsx'

    for lesson in range(1, 6):
        sheet_name = f'lesson{lesson}'
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        df = df.dropna(subset=['Word', 'Meaning'])

        words_list = df.apply(lambda row: f"🔹 {row['Word']} - {row['Meaning']}", axis=1).tolist()
        vocabulary[sheet_name] = words_list

    return vocabulary

vocabulary = load_vocabulary()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📘 درس 1", callback_data='lesson1'),
         InlineKeyboardButton("📙 درس 2", callback_data='lesson2')],
        [InlineKeyboardButton("📕 درس 3", callback_data='lesson3'),
         InlineKeyboardButton("📒 درس 4", callback_data='lesson4')],
        [InlineKeyboardButton("📗 درس 5", callback_data='lesson5'),
         InlineKeyboardButton("📓 درس 6", callback_data='lesson6')],
        [InlineKeyboardButton("📥 دانلود کتاب", callback_data='download_book'),
         InlineKeyboardButton("🎵 فایل‌های صوتی", callback_data='audio_files')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 سلام دوست خوبم! \n\n🔍 میخوای لغات مهم درس‌ها رو یاد بگیری؟\n\n"
        "✅ پس یکی از درس‌ها رو از لیست زیر انتخاب کن تا برات لغات رو بفرستم:",
        reply_markup=reply_markup
    )

async def show_vocabulary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    selected_lesson = query.data

    if selected_lesson == 'download_book':
        await query.answer("📥 فایل ما حدودا 10 مگ هست و برای دریافتش یکم باید منتظر باشی... دارم برات ارسال میکنم", show_alert=True)
        # ارسال کتاب به کاربر (کد بدون تغییر)
        # ...
        return

    if selected_lesson == 'audio_files':
        keyboard = []
        for i in range(1, 50):
            if i % 2 == 1:
                row = [InlineKeyboardButton(f"فایل صوتی {i}", callback_data=f'audio_{i}')]

                if i + 1 <= 49:  
                    row.append(InlineKeyboardButton(f"فایل صوتی {i + 1}", callback_data=f'audio_{i + 1}'))
                keyboard.append(row)

        keyboard.append([InlineKeyboardButton("🔙 برگشت به منوی اصلی", callback_data='back_to_menu')])  # دکمه برگشت به منو
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text="🎵 اینجا 49 فایل صوتی داریم:\nلطفاً یکی را انتخاب کنید:",
            reply_markup=reply_markup
        )
        return

    # دریافت لغات
    words = vocabulary.get(selected_lesson, [])
    if words:
        message = "🌟 لغات مهم انتخابی شما:\n\n" + "\n".join(words) + "\n\n📖 می‌تونی دوباره از لیست زیر درس دیگه‌ای انتخاب کنی!"
    else:
        message = "😅 هنوز لغتی برای این درس ندارم... صبر کن یه کم یاد بگیرم بعداً برات می‌فرستم!"

    keyboard = [
        [InlineKeyboardButton("📘 درس 1", callback_data='lesson1'),
         InlineKeyboardButton("📙 درس 2", callback_data='lesson2')],
        [InlineKeyboardButton("📕 درس 3", callback_data='lesson3'),
         InlineKeyboardButton("📒 درس 4", callback_data='lesson4')],
        [InlineKeyboardButton("📗 درس 5", callback_data='lesson5'),
         InlineKeyboardButton("📓 درس 6", callback_data='lesson6')],
        [InlineKeyboardButton("📥 دانلود کتاب", callback_data='download_book'),
         InlineKeyboardButton("🎵 فایل‌های صوتی", callback_data='audio_files')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=message, reply_markup=reply_markup)

audio_queue = asyncio.Queue()

async def send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    audio_index = int(query.data.split('_')[1])  # دریافت شماره فایل صوتی

    # اضافه کردن درخواست به صف
    await audio_queue.put((query, audio_index))
    await process_audio_queue()

async def process_audio_queue():
    while not audio_queue.empty():
        query, audio_index = await audio_queue.get()
        await query.answer("🔊 لطفاً یکی دو دقیقه صبر کن، فایلتو دریافت می‌کنی...", show_alert=True)
        await asyncio.sleep(2)  # شبیه‌سازی بارگذاری

        audio_file_path = f'audio/Track {audio_index}.mp3'
        try:
            with open(audio_file_path, "rb") as audio_file:
                await query.message.reply_audio(audio_file, caption=f"🎧 فایل صوتی درس {audio_index}")
        except FileNotFoundError:
            await query.message.reply_text(f"🚫 فایل صوتی درس {audio_index} موجود نیست.")

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await start(query, context)  # فراخوانی تابع start با query به جای update

def main():
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_vocabulary, pattern='^(lesson[1-6]|download_book|audio_files)$'))
    application.add_handler(CallbackQueryHandler(send_audio, pattern='^audio_[1-9][0-9]?$'))  # برای شماره‌های 1 تا 49
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='back_to_menu'))  # دکمه برگشت به منو

    application.run_polling(drop_pending_updates=True, timeout=10000)

if __name__ == '__main__':
    main()
