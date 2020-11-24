import board
import neopixel
import time

pixel_pin = board.D21
num_pixels = 8
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, auto_write=False)


def turn_on_green():
    blank = (0, 255, 0)
    pixels.fill(blank)
    pixels.show()
    time.sleep(5)
    blank = (0, 0, 0)
    pixels.fill(blank)
    pixels.show()


def turn_on_yellow():
    blank = (255, 255, 0)
    pixels.fill(blank)
    pixels.show()


def turn_on_red():
    blank = (255, 0, 0)
    pixels.fill(blank)
    pixels.show()


def turn_on_lamp():
    blank = (255, 255, 255)
    pixels.fill(blank)
    pixels.show()


def turn_off_all():
    blank = (0, 0, 0)
    pixels.fill(blank)
    pixels.show()
