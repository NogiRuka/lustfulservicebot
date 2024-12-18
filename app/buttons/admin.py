from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.types.keyboard_button import KeyboardButton
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove

cancel_btn = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Cancel 🚫")]])


clear_btn = ReplyKeyboardRemove()
