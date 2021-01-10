import tkinter as tk
from tkinter import *
from tkinter import filedialog
import subprocess
import os
import pyautogui
import snipingTool
import tableOCR


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        """
            ----------Initial Windows----------
            create Windows and Buttons.
            They get filled in their methods
        """
        # set Window Width and Height
        windowWidth = 350  # width
        windowHeight = 75  # height, for every button 25 px

        # Main Window
        self.master = master
        self.take_snip_btn = tk.Button(self.master)  # create Button
        self.take_img_btn = tk.Button(self.master)
        self.quit_btn = tk.Button(self.master)

        # Export Window
        self.export = tk.Toplevel()
        self.export_csv_btn = tk.Button(self.export)
        self.export_excel_btn = tk.Button(self.export)
        self.export_clip_btn = tk.Button(self.export)
        self.export.withdraw()

        # start the main Window
        self.main_window(windowWidth, windowHeight)

    """
       ----------Escape Function----------
    """
    def keyup(self, event):
        if event.keycode == 27:                     # escape key
            self.exit_application()           # exit app

    def exit_application(self):
        print("Application exit")
        self.master.quit()
        self.master.destroy()

    """
       ----------Main Window Functions----------
    """
    def select_from_screen(self):
        root.withdraw()
        fileName = snipingTool.create_screenshot()

        if fileName == -1 or fileName == "" or fileName is None:
            self.exit_application()
        else:
            cwd = (os.getcwd().replace('\\', '/')) + "/snips/" + fileName + ".png"

            root.config(cursor="wait")

            df = tableOCR.table_to_ocr(cwd, debug=False)

            root.config(cursor="")

            self.export_window(df)
            print("Take Screenshot")

    def select_existing_img(self):
        root.withdraw()
        filePath = filedialog.askopenfilename(title="Bild Datei auswählen")  # select file Filetypes doesnt work

        if filePath == "":
            self.exit_application()
        else:
            root.config(cursor="wait")

            df = tableOCR.table_to_ocr(filePath, debug=False)

            root.config(cursor="")
            self.export_window(df)
            print("Use Existing File")

    """
       ----------Export Window Functions----------
    """
    def export_csv(self, df):
        cwd = os.getcwd()
        outputPath = filedialog.asksaveasfilename(title="Exportieren nach:", filetypes=[("CSV", "*.csv")])

        # get path and File name
        name = outputPath[outputPath.rfind("/")+1::]
        outputDir = outputPath[:outputPath.rfind("/")+1:]
        os.chdir(outputDir)

        df.to_csv(name + ".csv", index=False, header=False)

        os.chdir(cwd)
        subprocess.Popen(r"explorer /select," + os.path.normpath(outputPath + ".csv"))
        print("Exported as CSV")
        self.exit_application()

    def export_excel(self, df):
        cwd = os.getcwd()
        outputPath = filedialog.asksaveasfilename(title="Exportieren nach:", filetypes=[("Excel", "*.xlsx")])

        # get path and File name
        name = outputPath[outputPath.rfind("/")+1::]
        outputDir = outputPath[:outputPath.rfind("/")+1:]
        os.chdir(outputDir)

        df.to_excel(name + ".xlsx", index=False, header=False)

        os.chdir(cwd)
        subprocess.Popen(r"explorer /select," + os.path.normpath(outputPath + ".xlsx"))
        print("Exported as Excel")
        self.exit_application()

    def export_clipboard(self, df):
        df.to_clipboard(excel=True, index=False, header=False)
        print("Copied to clipboard")
        self.exit_application()

    """--------------------"""

    def main_window(self, window_width, window_height):
        """
            ----------Main Window Content----------

            fill the Main Window with Options:
            0. "Aus einem Screenshot"           creates new Screenshot
            1. "Aus einer vorhandenen Datei"    opens Explorer for file selection
            2. "Schließen"                      quits the Application
        """
        # Window itself
        # position window at current Cursor position
        x, y = pyautogui.position()  # get Cursor position

        # create Frame with Size: Width x Height at Pos X + Y
        self.master.geometry(str(window_width) + "x" + str(window_height) + "+" + str(x) + "+" + str(y))
        self.master.iconbitmap('icon.ico')
        self.master.bind("<KeyRelease>", self.keyup)
        self.master.title("Table OCR")  # set Window Title
        self.master.resizable(False, False)  # not resizable
        self.pack()  # display

        # create Buttons
        self.take_snip_btn["text"] = "Aus einem Screenshot"  # Text for Button
        self.take_snip_btn["command"] = self.select_from_screen  # Function on press
        self.take_snip_btn["anchor"] = "w"  # align text left
        self.take_snip_btn.config(width=window_width)  # set Width of Button
        self.take_snip_btn.pack()  # display Button

        self.take_img_btn["text"] = "Aus einer vorhandenen Datei"
        self.take_img_btn["command"] = self.select_existing_img
        self.take_img_btn["anchor"] = "w"
        self.take_img_btn.config(width=window_width)
        self.take_img_btn.pack()

        self.quit_btn["text"] = "Schließen"
        self.quit_btn["fg"] = "red"
        self.quit_btn["command"] = self.master.destroy
        self.quit_btn["anchor"] = "w"
        self.quit_btn.config(width=window_width)
        self.quit_btn["anchor"] = "w"
        self.quit_btn.pack()

        self.master.focus()

    def export_window(self, df):
        """
            ----------Export Window Content----------

            Possible Outputs:
            0. "cvs" => DEFAULT creates new Sheet in CSV format on a given Path
            1. "excel"          creates new Excel Sheet on a given Path
            2. "clipboard"      copies Table to Clipboard for pasting to file

        """
        # Window itself
        windowWidth = root.winfo_width()

        self.export.iconbitmap('icon.ico')
        self.export.bind("<KeyRelease>", self.keyup)
        self.export.title("Table OCR Exportieren...")  # set Window Title
        self.export.resizable(False, False)  # not resizable
        self.export.geometry(root.winfo_geometry())
        self.pack()

        # create Buttons
        self.export_csv_btn["text"] = "In eine .CSV Datei wandeln"
        self.export_csv_btn["command"] = lambda: self.export_csv(df)
        self.export_csv_btn["anchor"] = "w"
        self.export_csv_btn.config(width=windowWidth)
        self.export_csv_btn.pack()

        self.export_excel_btn["text"] = "In eine Excel Datei wandeln"
        self.export_excel_btn["command"] = lambda: self.export_excel(df)
        self.export_excel_btn["anchor"] = "w"
        self.export_excel_btn.config(width=windowWidth)
        self.export_excel_btn.pack()

        self.export_clip_btn["text"] = "In die Zwischenablage kopieren"
        self.export_clip_btn["command"] = lambda: self.export_clipboard(df)
        self.export_clip_btn["anchor"] = "w"
        self.export_clip_btn.config(width=windowWidth)
        self.export_clip_btn.pack()

        root.update()
        self.export.deiconify()
        self.export.focus()


if __name__ == '__main__':
    root = Tk()
    app = Application(master=root)
    root.mainloop()
