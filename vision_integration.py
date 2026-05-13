"""
Vision Integration for Visual Intelligence
Lazy-loaded to keep startup fast - only imports when vision mode is activated
"""
import mss
import io
from PIL import Image
from typing import Optional, List, Tuple

class VisionIntegration:
    def __init__(self):
        self.yolo_model = None
        self.moondream_available = False
        self.is_active = False
        
    def activate(self) -> bool:
        """Activate vision mode - loads models on first use"""
        if self.is_active:
            return True
            
        print("Activating vision mode...")
        try:
            # Try to import and load YOLO
            from ultralytics import YOLO
            self.yolo_model = YOLO('yolov8n.pt')  # Nano model for speed
            self.is_active = True
            print("Vision mode activated with YOLO")
            return True
        except Exception as e:
            print(f"Could not activate vision mode: {e}")
            return False
    
    def deactivate(self):
        """Deactivate vision mode to free memory"""
        self.yolo_model = None
        self.is_active = False
        print("Vision mode deactivated")
    
    def capture_screen(self) -> Optional[Image.Image]:
        """Capture current screen"""
        try:
            with mss.mss() as sct:
                # Capture primary monitor
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                return img
        except Exception as e:
            print(f"Screenshot error: {e}")
            return None
    
    def detect_objects(self, image: Optional[Image.Image] = None) -> List[str]:
        """Detect objects in image using YOLO"""
        if not self.is_active or self.yolo_model is None:
            return []
        
        try:
            # Capture screen if no image provided
            if image is None:
                image = self.capture_screen()
                if image is None:
                    return []
            
            # Run detection
            results = self.yolo_model(image, verbose=False)
            
            # Extract detected objects
            detected = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    if conf > 0.5:  # Confidence threshold
                        label = result.names[cls]
                        detected.append(label)
            
            return detected
        except Exception as e:
            print(f"Object detection error: {e}")
            return []
    
    def describe_screen(self) -> str:
        """Describe what's on screen"""
        if not self.is_active:
            return "Vision mode is not active."
        
        objects = self.detect_objects()
        
        if not objects:
            return "I don't see anything recognizable on the screen."
        
        # Count occurrences
        from collections import Counter
        object_counts = Counter(objects)
        
        # Build description
        descriptions = []
        for obj, count in object_counts.most_common(5):  # Top 5
            if count > 1:
                descriptions.append(f"{count} {obj}s")
            else:
                descriptions.append(f"a {obj}")
        
        if len(descriptions) == 1:
            return f"I can see {descriptions[0]} on the screen."
        elif len(descriptions) == 2:
            return f"I can see {descriptions[0]} and {descriptions[1]} on the screen."
        else:
            return f"I can see {', '.join(descriptions[:-1])}, and {descriptions[-1]} on the screen."
    
    def find_object(self, object_name: str) -> bool:
        """Check if a specific object is visible"""
        if not self.is_active:
            return False
        
        objects = self.detect_objects()
        object_name_lower = object_name.lower()
        
        for obj in objects:
            if object_name_lower in obj.lower():
                return True
        
        return False
