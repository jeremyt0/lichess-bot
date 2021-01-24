import os
import logging
import datetime

log_filename = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S") + '.log'
moves_log = "moves_log.log"

# Barebones logging
class Logger:

    @staticmethod
    def log(string):
        log_path = os.path.join(Logger.get_log_dir(), log_filename)
        logging.basicConfig(filename=log_path, encoding='utf-8', level=logging.INFO)
        logging.info(string)

    @staticmethod
    def record_move(move):
        log_path = os.path.join(Logger.get_log_dir(), moves_log)
        logging.basicConfig(filename=log_path, level=logging.INFO)
        logging.info(f'{move}')


    @staticmethod
    def get_log_dir():
        src_dir = "E:\\Jeee\\Documents\\Projects\\Python\\Chess\\lichess-bot"
        log_dir = os.path.join(src_dir, "logs")
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        return log_dir


