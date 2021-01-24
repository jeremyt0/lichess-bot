import os
import sys

class Resource:
    
    @staticmethod
    def get_resource_dir():
        # resource_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0]))), "resources")
        resource_dir = os.path.join("E:\\Jeee\\Documents\\Projects\\Python\\Chess\\lichess", "resources")
        if not os.path.exists(resource_dir):
            os.mkdir(resource_dir)
        return resource_dir

    @staticmethod
    def get_engine_dir():
        engine_dir = "E:\\Jeee\\Documents\\Projects\\Python\\Chess\\engines"
        if not os.path.exists(engine_dir):
            os.mkdir(engine_dir)
        return engine_dir

    @staticmethod
    def get_images_dir():
        src_dir = "E:\\Jeee\\Documents\\Projects\\Python\\Chess\\lichess"
        images_dir = os.path.join(src_dir, "images")
        if not os.path.exists(images_dir):
            os.mkdir(images_dir)
        return images_dir
