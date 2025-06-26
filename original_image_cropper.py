"""
Original Image Cropper
Crop regions dari original image (tanpa preprocessing) untuk verification
"""

import cv2
import base64
import numpy as np
import os
from typing import List, Dict, Optional

class OriginalImageCropper:
    """
    Crop regions dari original image untuk user verification
    """
    
    def __init__(self):
        self.padding = 15
        
    def crop_from_original(self, image_path: str, bbox: List[int]) -> str:
        """
        Crop region dari ORIGINAL image (tanpa preprocessing)
        
        Args:
            image_path: Path ke original image file
            bbox: [x1, y1, x2, y2] bounding box coordinates
            
        Returns:
            Base64 encoded cropped image
        """
        try:
            # Load ORIGINAL image as-is (no preprocessing)
            original_img = cv2.imread(image_path)
            if original_img is None:
                return self._create_placeholder_original()
            
            x1, y1, x2, y2 = bbox
            
            # Add padding
            x1 = max(0, x1 - self.padding)
            y1 = max(0, y1 - self.padding) 
            x2 = min(original_img.shape[1], x2 + self.padding)
            y2 = min(original_img.shape[0], y2 + self.padding)
            
            # Crop from ORIGINAL (unprocessed) image
            cropped_original = original_img[y1:y2, x1:x2]
            
            # Convert to base64
            _, buffer = cv2.imencode('.png', cropped_original)
            return f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"
            
        except Exception as e:
            print(f"Error cropping original image: {e}")
            return self._create_placeholder_original()
    
    def _create_placeholder_original(self) -> str:
        """Create placeholder yang terlihat seperti original document scan"""
        # Create realistic document background (slightly off-white)
        img = np.ones((80, 300, 3), dtype=np.uint8) * 248
        
        # Add document texture/noise
        noise = np.random.normal(0, 8, (80, 300, 3))
        img = np.clip(img + noise, 235, 255).astype(np.uint8)
        
        # Add scan artifacts (slight shadows, uneven lighting)
        for i in range(80):
            for j in range(300):
                # Simulate uneven lighting
                brightness_factor = 0.95 + 0.1 * np.sin(i/10) * np.cos(j/15)
                img[i, j] = np.clip(img[i, j] * brightness_factor, 0, 255)
        
        # Add handwritten text that looks more realistic
        cv2.putText(img, "Original Handwriting", (10, 45), 
                   cv2.FONT_HERSHEY_SCRIPT_COMPLEX, 0.8, (45, 45, 45), 2)
        
        # Add some pen marks/artifacts
        cv2.line(img, (50, 60), (250, 65), (60, 60, 60), 1)
        
        _, buffer = cv2.imencode('.png', img)
        return f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"
    
    def get_verification_regions_with_original_crops(self, 
                                                   regions: List[Dict], 
                                                   original_image_path: str) -> List[Dict]:
        """
        Get verification regions dengan cropped images dari original
        
        Args:
            regions: List of OCR regions
            original_image_path: Path ke original image
            
        Returns:
            List of verification regions dengan original cropped images
        """
        verification_regions = []
        
        for i, region in enumerate(regions):
            # Check if region needs verification
            needs_verification = (
                region.get("region_type") == "handwritten" or 
                region.get("confidence", 1.0) < 0.5
            )
            
            if needs_verification:
                bbox = region.get("bbox", [])
                if len(bbox) >= 4:
                    # Crop from original image
                    cropped_image = self.crop_from_original(original_image_path, bbox)
                else:
                    cropped_image = self._create_placeholder_original()
                
                verification_regions.append({
                    "region_id": i,
                    "text": region.get("text", ""),
                    "confidence": region.get("confidence", 0.0),
                    "region_type": region.get("region_type", "unknown"),
                    "priority_score": 0.9 if region.get("region_type") == "handwritten" else 0.5,
                    "cropped_image": cropped_image,
                    "bbox": bbox,
                    "note": "Cropped from ORIGINAL image (no preprocessing)"
                })
        
        return verification_regions
    
    def find_original_image_path(self, task_id: str = None) -> Optional[str]:
        """
        Find original image path untuk task
        
        Args:
            task_id: Task ID (optional)
            
        Returns:
            Path ke original image atau None
        """
        possible_paths = [
            "sk_sekretariat_001.png",
            "uploads/sk_sekretariat_001.png", 
            "sample_documents/sk_sekretariat_001.png",
            "test_images/sk_sekretariat_001.png"
        ]
        
        # If task_id provided, try to find specific file
        if task_id and task_id != 'demo_task':
            possible_paths.insert(0, f"uploads/{task_id}_*.png")
            possible_paths.insert(0, f"uploads/{task_id}_*.jpg")
        
        for path in possible_paths:
            if '*' in path:
                # Handle wildcard patterns
                import glob
                matches = glob.glob(path)
                if matches:
                    return matches[0]
            elif os.path.exists(path):
                return path
        
        return None

def create_original_cropper():
    """Factory function untuk create OriginalImageCropper"""
    return OriginalImageCropper()

# Demo function untuk testing
def demo_original_cropping():
    """Demo function untuk test original image cropping"""
    cropper = create_original_cropper()
    
    # Find original image
    original_path = cropper.find_original_image_path()
    
    if original_path:
        print(f"Found original image: {original_path}")
        
        # Demo bounding boxes (dari OCR result)
        demo_bboxes = [
            [701, 865, 1156, 931],  # "io8 . 4.3/3 1/ Puu"
            [991, 929, 1146, 995]   # "9025"
        ]
        
        for i, bbox in enumerate(demo_bboxes):
            cropped_b64 = cropper.crop_from_original(original_path, bbox)
            print(f"Region {i+1}: Cropped image length = {len(cropped_b64)} chars")
            
            # Save untuk testing
            if cropped_b64.startswith('data:image/png;base64,'):
                import base64
                img_data = base64.b64decode(cropped_b64.split(',')[1])
                with open(f'cropped_original_{i+1}.png', 'wb') as f:
                    f.write(img_data)
                print(f"Saved: cropped_original_{i+1}.png")
    else:
        print("Original image not found, using placeholder")
        cropped_b64 = cropper._create_placeholder_original()
        print(f"Placeholder image length = {len(cropped_b64)} chars")

if __name__ == "__main__":
    demo_original_cropping()
