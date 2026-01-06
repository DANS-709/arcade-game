import arcade
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE
from views import LoadingView

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    load_view = LoadingView()
    window.show_view(load_view)
    arcade.run()

if __name__ == "__main__":
    main()