import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from PIL import Image

# Safeguard non-native iOS C-extension libraries
try:
    import cv2
except ImportError:
    cv2 = None

try:
    import pytesseract
except ImportError:
    pytesseract = None


class ALPRPortableApp(toga.App):
    def startup(self):
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=15))

        title_label = toga.Label(
            "ALPR-Portable",
            style=Pack(padding=10, font_weight="bold", font_size=18)
        )
        status_label = toga.Label(
            "Application initialized successfully.",
            style=Pack(padding=5)
        )
        
        main_box.add(title_label)
        main_box.add(status_label)

        if cv2 is None or pytesseract is None:
            warning_label = toga.Label(
                "Notice: Native vision tools (OpenCV/Tesseract) require embedded iOS binaries.",
                style=Pack(padding=5)
            )
            main_box.add(warning_label)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()


def main():
    return ALPRPortableApp("ALPR-Portable", "com.alprportable.app")