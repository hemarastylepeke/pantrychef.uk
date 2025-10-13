import re
from datetime import datetime
from django.utils import timezone

class ExpiryDateDetector:
    """
    Mock vision service for expiry date detection
    In production, this would integrate with Google Vision API
    """
    
    def detect_expiry_date(self, image_path):
        """
        Detect expiry date from image
        In real implementation, this would call Google Vision API
        """
        # Mock implementation - in real app, this would use OCR
        mock_results = {
            'detected_text': 'EXPIRY DATE: 2024-12-31\nUSE BY: 2024-12-31',
            'expiry_date': '2024-12-31',
            'confidence': 0.85,
            'dates_found': ['2024-12-31']
        }
        
        return mock_results
    
    def parse_expiry_date(self, text):
        """
        Parse expiry date from detected text
        """
        # Patterns for different date formats
        patterns = [
            r'expir(y|ation)[\s:]*(?:date)?[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'use[\s]*by[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'best[\s]*before[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Generic date pattern
        ]
        
        dates_found = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1) if 'expir' in pattern else match.group(1)
                try:
                    # Try different date formats
                    for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%Y-%m-%d']:
                        try:
                            date = datetime.strptime(date_str, fmt).date()
                            dates_found.append(date)
                            break
                        except ValueError:
                            continue
                except:
                    continue
        
        if dates_found:
            # Return the latest date as expiry date (most conservative)
            return max(dates_found)
        
        return None