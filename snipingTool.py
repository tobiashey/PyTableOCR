from tkinter import *
import pyautogui

import datetime


def create_screenshot():
    root = Tk()
    snip = Screenshot(root)
    snip.create_screen_canvas()
    root.mainloop()
    return snip.fileName


class Screenshot:
    def __init__(self, master):

        self.fileName = None
        self.master = master
        self.rect = None
        self.x = self.y = 0
        self.start_x = None
        self.start_y = None
        self.curX = None
        self.curY = None

        self.master_screen = Toplevel(master)
        self.master_screen.withdraw()
        self.master_screen.attributes("-transparent", "blue")
        self.picture_frame = Frame(self.master_screen, background="blue")
        self.picture_frame.pack(fill=BOTH, expand=YES)

    def take_bounded_screenshot(self, x1, y1, x2, y2):
        im = pyautogui.screenshot(region=(x1, y1, x2, y2))
        x = datetime.datetime.now()
        self.fileName = x.strftime("%f")
        im.save("snips/" + self.fileName + ".png")

    def create_screen_canvas(self):
        self.master_screen.deiconify()
        self.master.withdraw()

        self.screenCanvas = Canvas(self.picture_frame, cursor="cross", bg="grey11")
        self.screenCanvas.pack(fill=BOTH, expand=YES)

        self.screenCanvas.bind("<ButtonPress-1>", self.on_button_press)
        self.screenCanvas.bind("<B1-Motion>", self.on_move_press)
        self.screenCanvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.master_screen.attributes('-fullscreen', True)
        self.master_screen.attributes('-alpha', .3)
        self.master_screen.lift()
        self.master_screen.attributes("-topmost", True)

        self.picture_frame.bind("<KeyRelease>", self.keyup)
        self.master.bind("<KeyRelease>", self.keyup)
        self.master_screen.bind("<KeyRelease>", self.keyup)
        self.screenCanvas.bind("<KeyRelease>", self.keyup)

    def on_button_release(self, event):
        self.rec_position()

        if self.start_x <= self.curX and self.start_y <= self.curY:
            print("right down")
            self.take_bounded_screenshot(self.start_x, self.start_y, self.curX - self.start_x, self.curY - self.start_y)

        elif self.start_x >= self.curX and self.start_y <= self.curY:
            print("left down")
            self.take_bounded_screenshot(self.curX, self.start_y, self.start_x - self.curX, self.curY - self.start_y)

        elif self.start_x <= self.curX and self.start_y >= self.curY:
            print("right up")
            self.take_bounded_screenshot(self.start_x, self.curY, self.curX - self.start_x, self.start_y - self.curY)

        elif self.start_x >= self.curX and self.start_y >= self.curY:
            print("left up")
            self.take_bounded_screenshot(self.curX, self.curY, self.start_x - self.curX, self.start_y - self.curY)

        self.exit_screenshot_mode()
        return event

    def keyup(self, event):
        if event.keycode == 27:                     # escape key
            self.exit_screenshot_mode()           # exit app
            self.fileName = -1

    def exit_screenshot_mode(self):
        print("Screenshot Mode exit")
        self.screenCanvas.destroy()
        self.master_screen.withdraw()
        self.master.quit()
        self.master.destroy()

    def on_button_press(self, event):
        # save mouse drag start position
        self.start_x = self.screenCanvas.canvasx(event.x)
        self.start_y = self.screenCanvas.canvasy(event.y)

        self.rect = self.screenCanvas.create_rectangle(self.x, self.y, 1, 1, outline='green', width=3, fill="blue")

    def on_move_press(self, event):
        self.curX, self.curY = (event.x, event.y)
        # expand rectangle as you drag the mouse
        self.screenCanvas.coords(self.rect, self.start_x, self.start_y, self.curX, self.curY)

    def rec_position(self):
        print(self.start_x)
        print(self.start_y)
        print(self.curX)
        print(self.curY)
