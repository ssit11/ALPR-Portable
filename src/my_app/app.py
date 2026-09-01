import sys
import toga
from toga.style import Pack
from toga.style.pack import COLUMN

try:
    from rubicon.objc import ObjCClass, NSData
    IS_IOS = sys.platform == "ios"
except ImportError:
    IS_IOS = False


class ALPRPortableApp(toga.App):
    def startup(self):
        self.main_box = toga.Box(style=Pack(direction=COLUMN, padding=15))

        self.title_label = toga.Label(
            "ALPR-Portable (iOS Native Vision)",
            style=Pack(padding=10, font_weight="bold", font_size=18)
        )
        self.main_box.add(self.title_label)

        if not IS_IOS:
            self.main_box.add(toga.Label("Notice: App not running on iOS. Vision disabled.", style=Pack(padding=5)))
        else:
            self.main_box.add(toga.Label("Apple Vision Framework ready.", style=Pack(color="green", padding=5)))

        self.result_label = toga.Label("Recognized plates will appear here.", style=Pack(padding=15, font_weight="bold"))
        self.main_box.add(self.result_label)

        self.photo_button = toga.Button(
            "Take Photo & Scan Plate",
            on_press=self.take_and_scan_photo,
            style=Pack(padding=10)
        )
        self.main_box.add(self.photo_button)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.main_box
        self.main_window.show()

    async def take_and_scan_photo(self, widget):
        if not IS_IOS:
            self.result_label.text = "Error: Requires physical iPhone."
            return

        if not self.camera.has_permission:
            await self.camera.request_permission()

        try:
            self.result_label.text = "Opening camera..."
            image = await self.camera.take_photo()
            
            if image:
                self.result_label.text = "Processing via Apple Neural Engine..."
                text = self.scan_image_data(image.data)
                self.result_label.text = f"Detected Plate:\n{text}"
            else:
                self.result_label.text = "Scan cancelled."
                
        except Exception as e:
            self.result_label.text = f"Camera Error: {str(e)}"

    def scan_image_data(self, image_bytes):
        try:
            VNImageRequestHandler = ObjCClass("VNImageRequestHandler")
            VNRecognizeTextRequest = ObjCClass("VNRecognizeTextRequest")
            NSArray = ObjCClass("NSArray")

            ns_data = NSData.dataWithBytes_length_(image_bytes, len(image_bytes))

            request = VNRecognizeTextRequest.alloc().init()
            request.recognitionLevel = 0 
            request.usesLanguageCorrection = False 

            handler = VNImageRequestHandler.alloc().initWithData_options_(ns_data, None)

            request_array = NSArray.arrayWithObject_(request)
            success = handler.performRequests_error_(request_array, None)

            if success:
                results = request.results
                if results and results.count > 0:
                    detected_texts = []
                    for i in range(results.count):
                        observation = results.objectAtIndex_(i)
                        top_candidate = observation.topCandidates_(1).objectAtIndex_(0)
                        detected_texts.append(str(top_candidate.string))
                    
                    return "\n".join(detected_texts)
                else:
                    return "No plates detected."
            else:
                return "Vision framework failed to process image."

        except Exception as e:
            return f"OCR processing crash caught: {e}"


def main():
    return ALPRPortableApp("ALPR-Portable", "com.alprportable.app")