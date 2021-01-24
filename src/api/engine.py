from stockfish import Stockfish
import os

# from utils.resource import Resource
from utils.logger import Logger

class Engine(object):
    
    def __init__(self):
        super().__init__()
        self.engine = None
        self.max_time = 1000  # Milliseconds

        self.list_moves = []
    
    def set_engine(self, engine_name="stockfish", skill_level=10):
        if engine_name == "stockfish":
            # stockfish_dir = os.path.join(Resource.get_engine_dir(), "stockfish_20090216_x64.exe")
            stockfish_dir = os.path.join("E:\\Jeee\\Documents\\Projects\\Python\\Chess\\engines", "stockfish_20090216_x64.exe")
            self.engine = Stockfish(stockfish_dir)
            self.set_engine_skill_level(skill_level)
            

    def set_engine_skill_level(self, level):
        self.engine.set_skill_level(level)


    
    def get_best_move(self):
        move = self.engine.get_best_move()
        return move

    def move(self, move):
        self.list_moves.append(move)
        self.engine.set_position(self.list_moves)
        # self.print_board_visual()
        Logger.record_move(move)

    def print_board_visual(self):
        print(self.engine.get_board_visual())

    def close_engine(self):
        self.engine.__del__



def main():
    print("Main - Start")

    engines_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), "engines")
    engines_dir = "E:\\Jeee\\Documents\\Projects\\Python\\Chess\\engines"
    stockfish_dir = os.path.join(engines_dir, "stockfish_20090216_x64.exe")
    print(stockfish_dir)
    engine = Engine()
    engine.set_engine()


    # 1a
    move = engine.get_best_move()
    engine.move(move)
    print(engine.get_board_visual())

    # 1b
    move = 'c7c6'
    engine.move(move)
    print(engine.get_board_visual())

    # 2a
    move = engine.get_best_move()
    engine.move(move)
    print(engine.get_board_visual())


    print("Main - Finished")

if __name__ == "__main__":
    main()