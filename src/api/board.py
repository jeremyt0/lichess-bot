import os
import numpy as np
from PIL import Image
from io import BytesIO
from cv2 import imread, inRange, threshold, boundingRect, findContours, moments, RETR_EXTERNAL, CHAIN_APPROX_NONE, cvtColor, COLOR_RGB2BGR, erode

from utils.resource import Resource

class Board(object):

    def __init__(self, board, my_colour):
        super().__init__()
        self.board = board
        # Board image settings
        self.width = board.size['width']        # Max width of board
        self.height = board.size['height']      # Max height of board
        self.x0 = board.location['x']           # Left co-ordinate
        self.y0 = board.location['y']           # Top co-ordinate
        self.square_width = self.width//8       # Width of square
        self.square_height = self.height//8     # Height of square
        self.file_boundaries = {}               # Dictionary of File (int): (lower co-ordinate, upper co-ordinate) (tuple - int) 
        self.rank_boundaries = {}               # Dictionary of Rank (int): (lower co-ordinate, upper co-ordinate) (tuple - int)
        self.BGR_LIGHT = (107, 210, 206)        # Constant of lighter green colour BGR tuple
        self.BGR_DARK = (58, 162, 171)          # Constant of darker green colour  BGR tuple

        self.image = None                       # Image file of current board
        self.image_file_name = None
        
        # Game settings
        self.colour = my_colour                 # Bot piece colour
        self.turn = "white"                     # True if my turn
        self.num_turns = 0
        


    def set_current_board_image(self):
        # Set self image of board
        self.image_file_name = os.path.join(Resource.get_images_dir(), f'{self.num_turns}{self.turn}.png')  # Latest image filename
        Image.open(BytesIO(self.board.screenshot_as_png)).save(self.image_file_name) # Save latest board update
        self.image = imread(self.image_file_name)               # Update self image
        
        # Set co-ordinate boundaries for file and rank
        self.set_coordinate_boundaries()  

    def set_coordinate_boundaries(self):
        self.file_boundaries = self.get_fr_boundary_coords(is_rank=False)   # File co-ordinate boundaries
        self.rank_boundaries = self.get_fr_boundary_coords(is_rank=True)    # Rank co-ordinate boundaries

    # Get co-ordinate boundaries given length of a square
    def get_fr_boundary_coords(self, is_rank=False):
        # Default for File
        lower_list, upper_list = range(0,8), range(1,9)
        length = self.square_width

        # is_rank reverses the coordinates (for Rank)
        if is_rank:
            lower_list, upper_list = range(7,-1,-1), range(8,0,-1)
            length = self.square_height
        
        lower_boundaries = list(map(lambda x: x*length , lower_list))
        upper_boundaries = list(map(lambda x: x*length , upper_list))

        boundaries = {}

        for n, upper_val in enumerate(upper_boundaries):
            b = (lower_boundaries[n], upper_val)
            boundaries[n+1] = b

        return boundaries


    def update_turn(self):
        # Update turn to the other colour
        self.set_turn("black") if self.turn == "white" else self.set_turn("white")
        self.num_turns += 1

    def set_turn(self, colour):
        self.turn = colour

    # Return True if current turn is bot's colour
    def my_turn(self):
        return True if self.colour == self.turn else False


    # Main method - from Image to Engine
    def to_engine_get_fr(self):
        print("To engine: start")
        old_coords, new_coords = self.to_engine_image_to_coords()
        print("To engine:", old_coords, new_coords)
        old_tup = self.to_engine_coords_to_tuple(old_coords)
        new_tup = self.to_engine_coords_to_tuple(new_coords)
        print("To engine:", old_tup, new_tup)
        old_fr = self.to_engine_tuple_to_fr(old_tup)
        new_fr = self.to_engine_tuple_to_fr(new_tup)
        print("To engine:", old_fr, new_fr)
        return f'{old_fr}{new_fr}'

    def to_engine_image_to_coords(self):
        img = self.image.copy()

        # Get masks of recently changed squared
        light_mask = self.get_light_mask(img)  # Mask - light green
        dark_mask = self.get_dark_mask(img)  # Mask - dark green

        # Erode masks to ensure not touching
        kernel = np.ones((2,2), np.uint8)
        light_mask_erode = erode(light_mask, kernel, iterations = 1)
        dark_mask_erode = erode(dark_mask, kernel, iterations = 1)

        # Get squares that have been recently changed
        light_squares = self.get_squares(light_mask_erode, light_square=True)
        dark_squares = self.get_squares(dark_mask_erode, light_square=False)

        # print("Light",light_squares)
        # print("Dark",dark_squares)

        source = None
        dest = None
        # Source
        if 'old' in light_squares:
            source = light_squares['old']
        else:
            source = dark_squares['old']
        # Destination
        if 'new' in light_squares:
            dest = light_squares['new']
        else:
            dest = dark_squares['new']

        return source, dest


    # Convert pixel co-ordinates to tuple co-ordinate
    def to_engine_coords_to_tuple(self, coords):
        # (200,300) -> (2,4)
        y, x = coords
        def get_key_file(key):
            lower, upper = self.file_boundaries[key]
            if x > lower and x < upper:
                return key
            return False
        def get_key_rank(key):
            lower, upper = self.rank_boundaries[key]
            if y > lower and y < upper:
                return key
            return False
        
        file = next(filter(get_key_file, self.file_boundaries))
        rank = next(filter(get_key_rank, self.rank_boundaries))

        return (file, rank)
                
    # Convert tuple co-ordinate to filerank
    def to_engine_tuple_to_fr(self, fr_tuple):
        # e.g. (2,5) -> b5
        f,r = fr_tuple

        for n,letter in enumerate(list('abcdefgh')):
            if f == n+1:
                return f'{letter}{r}'
        return False

    # Convert filerank to tuple co-ordinate
    def from_engine_fr_to_tuple(self, fr):
        # e.g. b5 -> (2,5)
        f, r = list(fr)

        for n, letter in enumerate(list("abcdefgh")):
            if f == letter:
                return (n+1, int(r))
        return False

    # Convert from tuple co-ordinate to pixel co-ordinate 
    def from_engine_tuple_to_coords(self, fr_tuple):
        # e.g. (2,5) -> (200, 450)
        y, x = fr_tuple
        lower_y, upper_y = self.rank_boundaries[y]
        lower_x, upper_x = self.file_boundaries[x]

        real_y = (lower_y + upper_y)//2
        real_x = (lower_x + upper_x)//2

        coords = (self.height-real_y, self.width-real_x)
        return coords

    # Main method - From Engine to UI
    def from_engine_convert(self, fr):
        print("From Engine:", fr)
        fr_tup = self.from_engine_fr_to_tuple(fr)
        print("From Engine:", fr_tup)
        coords = self.from_engine_tuple_to_coords(fr_tup)
        print("From Engine:", coords)
        return coords

    def from_engine_split_fr(self, fr_string):
        old, new = fr_string[:-2], fr_string[-2:]
        return old, new




    def get_light_mask(self, image):
        # Get boundaries of Light GREEN [106,210,205]
        lower_green = np.array(np.array(self.BGR_LIGHT)+20, dtype="uint8")
        upper_green = np.array(np.array(self.BGR_LIGHT)-20, dtype="uint8")
        mask = inRange(image, upper_green, lower_green)
        return mask

    def get_dark_mask(self, image):
        # Dark green boundaries [58,162,171]
        lower_green = np.array(np.array(self.BGR_DARK)+20, dtype="uint8")
        upper_green = np.array(np.array(self.BGR_DARK)-20, dtype="uint8")
        mask = inRange(image, upper_green, lower_green)
        return mask

    def get_squares(self, mask, light_square=True):
        bgr = self.BGR_DARK
        if light_square:
            bgr = self.BGR_LIGHT

        def within_threshold(x, orig, thresh=20):
            lower, upper = orig-thresh, orig+thresh

            if x > lower and x < upper:
                return True
            return False
        
        squares = {}

        ret,thresh = threshold(mask,127,255,0)
        # Find contours
        contours, hierarchy = findContours(thresh, RETR_EXTERNAL, CHAIN_APPROX_NONE)
        for c in contours:
            # Check if size of found-contour is within size of a square
            (x, y, w, h) = boundingRect(c)

            # Skip contours that are too small/large
            if not all(list(map(within_threshold, (w,h), (self.square_width, self.square_height) ))):
                continue

            m = moments(c)

            cX = int(m["m10"] / m["m00"])
            cY = int(m["m01"] / m["m00"])

            b,g,r  = self.image[(cY,cX)]
            pixel_val = (b,g,r)

            # Check if each (b,g,r) within threshold
            if all(list(map(within_threshold, pixel_val, bgr))):
                squares["old"] = (cY,cX)
            else:
                squares["new"] = (cY,cX)
            
        return squares

