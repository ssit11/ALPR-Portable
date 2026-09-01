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
            "ALPR-Portable (Safe Mode)",
            style=Pack(padding=10, font_weight="bold", font_size=18)
        )
        self.main_box.add(self.title_label)

        status_text = "Apple Vision Framework ready." if IS_IOS else "Notice: App not running on iOS."
        self.main_box.add(toga.Label(status_text, style=Pack(padding=5)))

        self.result_label = toga.Label("Ready to scan plates.", style=Pack(padding=15, font_weight="bold"))
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
            
            if image and hasattr(image, "data"):
                self.result_label.text = "Processing image..."
                # Defer execution safely away from main thread UI loop
                text = self.safe_scan(image.data)
                self.result_label.text = f"Result:\n{text}"
            else:
                self.result_label.text = "Scan cancelled or no data."
                
        except Exception as e:
            self.result_label.text = f"Error: {str(e)}"

    def safe_scan(self, image_bytes):
        """Safely invokes Vision framework with heavy error handling to catch ANE faults."""
        try:
            if not image_bytes:
                return "Error: Empty image buffer."

            VNImageRequestHandler = ObjCClass("VNImageRequestHandler")
            VNRecognizeTextRequest = ObjCClass("VNRecognizeTextRequest")
            NSArray = ObjCClass("NSArray")

            ns_data = NSData.dataWithBytes_length_(image_bytes, len(image_bytes))
            if not ns_data:
                return "Error: Failed to create NSData."

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
                return "No text recognized."
            return "Vision handler execution failed."
        except Exception as err:
            return f"Vision Exception: {err}"


def main():
    return ALPRPortableApp("ALPR-Portable", "com.alprportable.v2.app")