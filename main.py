from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
import asyncio
import mediapipe as mp
import cv2
import Constants

players = {} # Dictionary to store sessions and figures

# Create bot
bot = Bot(token=Constants.API_TOKEN)

dp = Dispatcher()


# Func to recognize figure based on geometry of points
def get_figure(hand_landmarks):
    pts = hand_landmarks.landmark
    # Two fingers much far from wrist than others
    if all([d(pts[i], pts[0]) < d(pts[i-8], pts[0]) / 2 for i in [16, 20]]):
        return 'scissors'
    # Ends of fingers closer to wrist than knuckles
    elif all([d(pts[i], pts[0]) < d(pts[i-2], pts[0]) for i in [8, 12, 16, 20]]):
        return 'rock'
    # Starts of fingers closer to wrist that ends
    elif all([d(pts[i], pts[0]) < d(pts[i+3], pts[0]) for i in [5, 9, 13, 17]]):
        return 'paper'
    else:
        return 'nothing'


# Distances
def d(p1, p2):
  return abs(p1.x - p2.x) + abs(p1.y - p2.y)


# Mediapipe model for hands recognition
mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    )


# Func to process photo and return decision
async def photo(file_id):
    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, "user_image.jpg")

    frame = cv2.imread('user_image.jpg')

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(frame)

    hls = results.multi_hand_landmarks
    # If no detection or figure
    if hls is None:
        return 'nothing'

    return get_figure(hls[0])


@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="Rock-Paper-Scissors")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Select a game"
    )
    await message.answer("What game will you play?", reply_markup=keyboard)


@dp.message(F.text.lower() == "rock-paper-scissors")
async def with_puree(message: types.Message):
    await message.answer("You chose Rock-Paper-Scissors. \n"
                         "Send me a photo of your figure!", reply_markup=types.ReplyKeyboardRemove())


@dp.message(F.content_type == 'photo')
async def get_picture(message: types.Message):
    file_id = message.photo[-1].file_id

    fig = (await (photo(file_id)))
    if fig == 'nothing':
        await(message.answer('Please, send another image'))
        return

    await(message.answer('I got your photo! \n'
                         'Just wait for another player'))

    players[message.from_user.id] = fig

    while True:
        enemy = ''
        for key in players:
            if key != message.from_user.id:
                enemy = players[key]
        if (enemy == 'Rock' and fig == 'Paper') or (enemy == 'Paper' and fig == 'Scissors') or (
                enemy == 'Scissors' and fig == 'Rock'):
            await(message.answer('You won!\n' + 'Your figure: ' + fig + '\nEnemy figure: ' + enemy))
            break
        elif enemy == fig:
            await(message.answer('Draw!\n' + 'Your figure: ' + fig + '\nEnemy figure: ' + enemy))
            break
        elif enemy != '':
            await(message.answer('You lost!\n' + 'Your figure: ' + fig + '\nEnemy figure: ' + enemy))
            break
        await asyncio.sleep(2)
    await asyncio.sleep(3)
    players.pop(message.from_user.id)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
