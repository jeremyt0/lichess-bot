from selenium import webdriver
import time
import re

from api.board import Board
from api.engine import Engine


class Bot(object):

    def __init__(self, url, driver_path=None, browser_name=None, opponent="Friend"):
        super().__init__()
        self.url = url
        self.driver_path = driver_path
        self.driver = None
        self.browser_name = None

        self.opponent = opponent
        
        self.engine = None

        self.last_move_tracker = None
        self.match_end = False

    def set_driver_path(self, path, browser_name):
        self.driver_path = path
        self.browser_name = browser_name
    
    def set_opponent(self, opponent):
        self.opponent = opponent

    def create_browser(self):
        if self.browser_name.lower() == "chrome":
            self.driver = webdriver.Chrome(executable_path=self.driver_path)
        else:
            self.driver = webdriver.Firefox()

    def close_driver(self):
        self.driver.close()

    def create_engine(self):
        self.engine = Engine()
        self.engine.set_engine()  # Default = stockfish
    
    def click_coords(self, coords):
        y, x = coords
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(self.board_web_element, y, x)
        action.click()
        action.perform()
        print("Clicked:", coords)
        return True

    def click_accept(self):
        try:
            button = self.driver.find_element_by_xpath("//form[@class='accept']/button")
            button.click()
            return True
        except Exception as e:
            print(e)
            return False

    def create_board(self, board, my_colour):
        self.main_board = Board(board, my_colour)

        self.main_board.set_current_board_image()       # Set screenshot image

    def make_move(self):
        move = self.engine.get_best_move()
        print("BOT: Best move -", move)
        # Make move on GUI

        pp_piece = None  # Pawn promotion piece
        if len(move) == 5:
            pp_piece = move[-1].lower()
            move = move[:-1]

        # Get coordinates of rank/file (old_square, new_square)
        old_fr, new_fr = self.main_board.from_engine_split_fr(move) # Split string to old, new
        old_square = self.main_board.from_engine_convert(old_fr)    # Co-ordinates to click
        new_square = self.main_board.from_engine_convert(new_fr)    # Co-ordinates to click 
        # Click old_square
        self.click_coords(old_square)
        time.sleep(0.1)
        # Click new_square
        self.click_coords(new_square)

        # Select new piece if pawn promoted
        if pp_piece:
            height, width = new_square
            if pp_piece == "q":
                pass  # Click again same square
            elif pp_piece == "n":
                height = height + self.main_board.square_height      # Click 1 square down
            elif pp_piece == "r":
                height = height + (self.main_board.square_height*2)  # Click 2 squares down
            elif pp_piece == "b":
                height = height + (self.main_board.square_height*3)  # Click 3 squares down
            time.sleep(0.2)
            self.click_coords( (height, width) )


        # Update engine with new move
        self.update_engine(move)

        # Update bot with last move
        self.last_move_tracker = new_fr
        print("My move finished.\n")

    def update_engine(self, move):
        self.engine.move(move)



    def start(self):
        print("Bot starting...")

        self.create_browser()
        
        self.driver.get(self.url)            
        
        if self.opponent == "friend":
            print("Playing against a friend")
            if not self.click_accept():
                print("No accept button so: Spectating")
                return           
        elif self.opponent == "computer":
            print("Playing against computer")
        elif self.opponent == "player":
            print("Playing against a player")

        my_colour_text = self.driver.find_element_by_xpath("//div[contains(@class, 'cg-wrap')]").get_attribute("class")
        my_colour = re.search(r'orientation-(\w+) ', my_colour_text).group(1)


        print("I am",my_colour)
        
        
        if my_colour == "black":
            print("Flip the board")
            flip_btn = self.driver.find_element_by_xpath("//button[contains(@title, 'Flip board')]").click()
        
        # Find main board in browser
        self.board_web_element = self.driver.find_element_by_tag_name('cg-board')
        # Create a board object
        self.create_board(self.board_web_element, my_colour)
        # Create engine
        self.create_engine()
        # self.engine.set_engine_skill_level(5)

        

        
        
        # If white then: Move first
        if self.main_board.my_turn():
            self.make_move()
            self.main_board.update_turn()


        while True:

            # If game ended (Checkmate) then break
            if self.match_end:
                break
            
            time.sleep(3)  # Sleep for 3 seconds
            try:
                # Get last move
                move_list_parent = self.driver.find_element_by_tag_name('l4x')  # Does not exist if there are no moves i.e. white first
                last_move = move_list_parent.find_element_by_xpath("//u8t[contains(@class, 'a1t')]").text
                print("Ultimate last move", last_move)
                castle_move = None
                pawn_promotion = None
                new_pp_piece = None

                if cst_n := last_move.count('-'):  # O-O or O-O-O
                    print("Castle")
                    if cst_n == 1:
                        castle_move = "e1g1" if self.main_board.turn == "white" else "e8g8"  # If white turn:   O-O: e1g1, if black: e8g8
                    elif cst_n == 2:
                        castle_move = "e1c1" if self.main_board.turn == "white" else "e8c8"  # If white turn: O-O-O: e1c1, if black: e8c8 
                elif pawn_promotion := last_move.count('='):  # b8=Q
                    print("Pawn promotion")
                    last_move = last_move.strip('+=')  # If check with new piece
                    new_pp_piece = last_move[-1]
                    last_move = last_move[:-1]
                elif any(x in last_move for x in ('+','#')):  # Bxf7+
                    print("Check")
                    if '#' in last_move:
                        self.match_end = True
                        break
                    last_move = last_move.strip('+#')[-2:]
                    
                print("Last move:",last_move)



                # Whose turn it is
                turn_text = self.driver.find_element_by_xpath("//div[contains(@class, 'rclock-turn__text')]").text
                print(turn_text)

                if turn_text == "Your turn":
                    # Update board with their latest move
                    self.main_board.set_current_board_image()
                    self.main_board.update_turn()

                    # If move is castle then set opponent move as one generated previously
                    if castle_move:
                        opponent_move = castle_move
                    else:
                        opponent_move = self.main_board.to_engine_get_fr()
                    
                    if pawn_promotion:
                        opponent_move += new_pp_piece
                    # Update engine
                    self.update_engine(opponent_move)

                    # I finally make my move
                    self.make_move()  # My move
                    # Update board with my latest move
                    self.main_board.set_current_board_image()
                    self.main_board.update_turn()
                    
                    # Set last move
                    # self.last_move_tracker = last_move

                elif turn_text == "Waiting for opponent":
                    pass
                    # print("Waiting for their move")
                else:
                    print("Error: User turn text is wrong.")
    
            except Exception as e:
                print(e)
            
            # End of while loop



            

        # Close engine
        self.engine.close_engine()        
        # Close web driver
        self.close_driver()
