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

        # Get coordinates of rank/file (old_square, new_square)
        old_fr, new_fr = self.main_board.from_engine_split_fr(move) # Split string to old, new
        old_square = self.main_board.from_engine_convert(old_fr)    # Co-ordinates to click
        new_square = self.main_board.from_engine_convert(new_fr)    # Co-ordinates to click 
        # Click old_square
        self.click_coords(old_square)
        time.sleep(0.1)
        # Click new_square
        self.click_coords(new_square)

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
                # print("Got move list parent", move_list_parent)
                # move_list = move_list_parent.find_elements_by_css_selector("u8t")  # List of moves tag
                last_move = move_list_parent.find_element_by_xpath("//u8t[contains(@class, 'a1t')]").text[-2:]
                print("Last move:",last_move, "Self:", self.last_move_tracker)

                # IF MATCH ENDED
                try:
                    results = move_list_parent.find_element_by_xpath("//div[contains(@class, 'result-wrap')]//p[contains(@class, 'status')]").text
                    self.match_end = True
                    print("Match has ended:", results)
                    continue
                except Exception as e:
                    print("Match not ended yet -",e)


                # If there has been a new move
                if last_move != self.last_move_tracker:
                    # print("Someone has moved!")
                    self.last_move_tracker = last_move

                    # Whose turn it is
                    turn_text = self.driver.find_element_by_xpath("//div[contains(@class, 'rclock-turn__text')]").text
                    # print(turn_text)

                    if turn_text == "Your turn":
                        # Update board with their latest move
                        self.main_board.update_turn()
                        self.main_board.set_current_board_image()

                        opponent_move = self.main_board.to_engine_get_fr()
                        # Update engine
                        self.engine.move(opponent_move)

                        # I finally make my move
                        self.make_move()  # My move
                        # Update board with my latest move
                        self.main_board.update_turn()
                        self.main_board.set_current_board_image()

                    elif turn_text == "Waiting for opponent":
                        print("Waiting for their move")
                    else:
                        print("Error: User turn text is wrong.")


                else:
                    print("No change yet")
                
            except Exception as e:
                print(e)
            



            

        # Close engine
        self.engine.close_engine()        
        # Close web driver
        self.close_driver()
