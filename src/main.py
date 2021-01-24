import os
import threading

from utils.resource import Resource
from auto.bot import Bot


def create_bot(url, opponent="friend"):
    print("Creating bot/")
    chrome_driver_path = os.path.join(Resource.get_resource_dir(), "chromedriver.exe")
    
    bot = Bot(url)
    bot.set_driver_path(path=chrome_driver_path, browser_name="chrome")
    bot.set_opponent(opponent)

    bot.start()


def main():
    print("Main - Start")

    opponent = 'friend'  # (player, friend, computer)

    if opponent == "friend":
        url = "https://lichess.org/rymVPgkp"  # Url for chess match
    else:
        url = "https://lichess.org/"

    thread = threading.Thread(target=create_bot, args=(url, opponent))
    thread.start()


    print("Main - Finished")


if __name__ == "__main__":
    main()
