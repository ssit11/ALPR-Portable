import os
import time
import datetime
import io
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER, LEFT, RIGHT

# Native iOS PhotoKit Bridge
try:
    from Rubicon.objc import ObjCClass
    PHPhotoLibrary = ObjCClass('PHPhotoLibrary')
    UIImage = ObjCClass('UIImage')
    NSData = ObjCClass('NSData')
    HAS_IOS_NATIVE = True
except Exception:
    HAS_IOS_NATIVE = False


class ModernPlateWatcher(toga.App):
    def startup(self):
        self.watch_list = ["ABC123", "XYZ987"]
        self.last_detection_time = 0
        self.detection_cooldown = 4.0  # Cooldown between saved photos in seconds

        # Modern Dark Minimalist Styling
        self.main_box = toga.Box(style=Pack(direction=COLUMN, background_color="#101214", padding=12))

        # Top Bar
        header = toga.Label("PLATE WATCHER PRO", style=Pack(color="#2b7cff", font_size=18, font_weight="bold", padding_bottom=8))
        self.status_label = toga.Label("Status: Engine Ready", style=Pack(color="#aab0b9", font_size=12, padding_bottom=10))

        # UI Input Section
        input_box = toga.Box(style=Pack(direction=ROW, padding_bottom=12))
        self.plate_input = toga.TextInput(placeholder="Enter Plate (e.g. ABC123)", style=Pack(flex=1, padding_right=8))
        add_btn = toga.Button("Add Plate", on_press=self.add_plate, style=Pack(background_color="#2b7cff", color="white"))
        input_box.add(self.plate_input)
        input_box.add(add_btn)

        # Scanner HUD View Area
        self.camera_view = toga.ImageView(style=Pack(height=350, padding_bottom=12))

        # Watchlist Display
        self.watchlist_label = toga.Label(f"Watching: {', '.join(self.watch_list)}", style=Pack(color="#35d05a", font_size=13, font_weight="bold"))

        # Build Main View Layout
        self.main_box.add(header)
        self.main_box.add(self.status_label)
        self.main_box.add(input_box)
        self.main_box.add(self.camera_view)
        self.main_box.add(self.watchlist_label)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.main_box
        self.main_window.show()

    def add_plate(self, widget):
        plate = self.plate_input.value.strip().upper()
        if plate and plate not in self.watch_list:
            self.watch_list.append(plate)
            self.watchlist_label.text = f"Watching: {', '.join(self.watch_list)}"
            self.plate_input.value = ""

    def process_frame_fast(self, frame_np, latitude=None, longitude=None):
        """
        Fast frame analysis pipeline:
        Crops center ROI for speed -> Detects text -> Watermarks bottom right -> Saves to iPhone Photos
        """
        h, w, _ = frame_np.shape
        
        # 1. High Speed ROI (Region of Interest) - Center 60% box scan
        ymin, ymax = int(h * 0.2), int(h * 0.8)
        xmin, xmax = int(w * 0.2), int(w * 0.8)
        roi = frame_np[ymin:ymax, xmin:xmax]

        # Pre-process ROI for fast thresholding
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # Fast character check (Simulated target detection trigger)
        detected_plate = self.check_target_plate(thresh)

        if detected_plate and (time.time() - self.last_detection_time > self.detection_cooldown):
            self.last_detection_time = time.time()
            self.status_label.text = f"ALERT: Detected {detected_plate}!"
            
            # Save watermarked image asynchronously
            self.save_watermarked_snapshot(frame_np, detected_plate, latitude, longitude)

    def check_target_plate(self, roi_img):
        # High speed OCR / contour lookup placeholder
        return None

    def save_watermarked_snapshot(self, frame_np, plate_text, lat, lon):
        """Watermarks location and timestamp on bottom right and saves to iPhone Gallery."""
        # Convert BGR (OpenCV) to RGB (Pillow)
        rgb_img = cv2.cvtColor(frame_np, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)
        draw = ImageDraw.Draw(pil_img)

        # Metadata overlay text
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        loc_str = f"Lat: {lat:.5f}, Lon: {lon:.5f}" if (lat and lon) else "GPS: Unavailable"
        watermark_text = f"PLATE: {plate_text}\nTIME: {now_str}\n{loc_str}"

        # Calculate Bottom-Right Position
        w, h = pil_img.size
        margin = 20
        
        # Draw translucent background box bottom-right
        bbox = draw.multiline_textbbox((0, 0), watermark_text)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        bg_rect = [w - text_w - (margin * 2), h - text_h - (margin * 2), w - margin, h - margin]
        draw.rectangle(bg_rect, fill=(0, 0, 0, 180))

        # Burn Text to Photo
        draw.multiline_text(
            (w - text_w - margin, h - text_h - margin),
            watermark_text,
            fill=(53, 208, 90), # Bright Lime Accent
            align="right"
        )

        # Save to iOS Photo Library
        buf = io.BytesIO()
        pil_img.save(buf, format='JPEG', quality=90)
        img_bytes = buf.getvalue()

        if HAS_IOS_NATIVE:
            self.write_to_ios_photos(img_bytes)

    def write_to_ios_photos(self, jpeg_bytes):
        """Direct C-Bridge write into Apple Photo Library."""
        try:
            ns_data = NSData.dataWithBytes_length_(jpeg_bytes, len(jpeg_bytes))
            ui_image = UIImage.imageWithData_(ns_data)

            def perform_change():
                PHPhotoLibrary.sharedPhotoLibrary().performChanges_completionHandler_(
                    lambda: ObjCClass('PHAssetChangeRequest').creationRequestForAssetFromImage_(ui_image),
                    None
                )
            perform_change()
        except Exception as e:
            print(f"Failed to write to Photos library: {e}")


def main():
    return ModernPlateWatcher("Plate Watcher", "com.platewatcher.app")