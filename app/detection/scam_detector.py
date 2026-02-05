"""
Scam Detection Module
Yeh file messages ko check karti hai ki scam hai ya nahi
"""

import re
from typing import Dict, List

class ScamDetector:
    def __init__(self):
        # Scam ke common words
        self.scam_keywords = {
            'prize': ['congratulations', 'won', 'winner', 'prize', 'lottery', 'lucky draw'],
            'urgency': ['urgent', 'immediately', 'now', 'hurry', 'limited time', 'expires'],
            'money': ['claim', 'payment', 'transfer', 'send money', 'pay', 'rupees', 'rs'],
            'verification': ['verify', 'confirm', 'update', 'kyc', 'account', 'details'],
            'threat': ['blocked', 'suspended', 'unauthorized', 'fraud', 'security alert']
        }
        
        self.confidence_threshold = 0.6
    
    def detect_scam(self, message: str) -> Dict:
        """
        Main function jo scam detect karta hai
        
        Args:
            message (str): User ka message
            
        Returns:
            Dict: Scam detection result
        """
        message_lower = message.lower()
        
        # Step 1: Keywords check karo
        keyword_score = self._check_keywords(message_lower)
        
        # Step 2: Suspicious patterns check karo
        pattern_score = self._check_patterns(message)
        
        # Step 3: Final score calculate karo
        final_score = (keyword_score + pattern_score) / 2
        
        # Step 4: Scam type identify karo
        scam_type = self._identify_scam_type(message_lower)
        
        # Step 5: Result return karo
        is_scam = final_score >= self.confidence_threshold
        
        return {
            'is_scam': is_scam,
            'confidence': round(final_score, 2),
            'scam_type': scam_type if is_scam else None,
            'message': 'Scam detected!' if is_scam else 'Message seems safe'
        }
    
    def _check_keywords(self, message: str) -> float:
        """Keywords ke basis pe score nikalo"""
        total_matches = 0
        total_keywords = 0
        
        for category, keywords in self.scam_keywords.items():
            total_keywords += len(keywords)
            matches = sum(1 for keyword in keywords if keyword in message)
            total_matches += matches
        
        # Score = matched keywords / total keywords
        score = total_matches / total_keywords if total_keywords > 0 else 0
        return min(score * 3, 1.0)  # Multiply by 3 to boost score
    
    def _check_patterns(self, message: str) -> float:
        """Suspicious patterns check karo"""
        score = 0.0
        
        # Pattern 1: URL hai?
        if self._has_url(message):
            score += 0.3
        
        # Pattern 2: UPI ID hai?
        if self._has_upi_id(message):
            score += 0.3
        
        # Pattern 3: Phone number hai?
        if self._has_phone_number(message):
            score += 0.2
        
        # Pattern 4: Account number jaisa kuch hai?
        if re.search(r'\b\d{9,18}\b', message):
            score += 0.2
        
        return min(score, 1.0)
    
    def _identify_scam_type(self, message: str) -> str:
        """Scam type pata karo"""
        # Prize/Lottery scam
        if any(word in message for word in ['prize', 'won', 'lottery', 'winner']):
            return 'prize_scam'
        
        # Phishing scam
        if any(word in message for word in ['verify', 'confirm', 'update', 'click']):
            return 'phishing'
        
        # Job scam
        if any(word in message for word in ['work from home', 'earn', 'job', 'part time']):
            return 'job_scam'
        
        # Payment scam
        if any(word in message for word in ['payment', 'transfer', 'send money']):
            return 'payment_scam'
        
        return 'unknown'
    
    def _has_url(self, message: str) -> bool:
        """URL hai ya nahi"""
        url_pattern = r'http[s]?://|www\.|\.com|\.in'
        return bool(re.search(url_pattern, message))
    
    def _has_upi_id(self, message: str) -> bool:
        """UPI ID hai ya nahi"""
        upi_pattern = r'\b[\w\.-]+@[\w\.-]+\b'
        matches = re.findall(upi_pattern, message)
        # Check if it looks like UPI (has @paytm, @phonepe etc)
        return any('@' in match and any(provider in match.lower() 
                   for provider in ['paytm', 'phonepe', 'gpay', 'ybl']) 
                   for match in matches)
    
    def _has_phone_number(self, message: str) -> bool:
        """Indian phone number hai ya nahi"""
        phone_pattern = r'\b[6-9]\d{9}\b'
        return bool(re.search(phone_pattern, message))


# Test function (optional - testing ke liye)
if __name__ == "__main__":
    detector = ScamDetector()
    
    # Test messages
    test_messages = [
        "Hi, how are you?",
        "Congratulations! You won Rs 50,000 prize. Send Rs 500 to claim.",
        "Your account will be blocked. Verify now at bit.ly/verify",
        "Call me on 9876543210 for work from home job opportunity"
    ]
    
    print("Testing Scam Detector:\n")
    for msg in test_messages:
        result = detector.detect_scam(msg)
        print(f"Message: {msg}")
        print(f"Result: {result}\n")