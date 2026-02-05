"""
AI Agent — THE BRAIN OF THE SYSTEM
Scammer se baat karta hai
OpenAI GPT use karta hai
"""

import os
import random
from typing import Dict, List
from dotenv import load_dotenv
from openai import OpenAI
from app.extraction.intel_extractor import IntelligenceExtractor

load_dotenv()


class ConversationalAgent:
    def __init__(self):
        # OpenAI client
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Intelligence extractor
        self.extractor = IntelligenceExtractor()

        # Conversation history — yaad rakhtaa hai
        self.conversation_history = []

        # Extracted data
        self.all_extracted = {
            'upi_ids': [],
            'bank_accounts': [],
            'phone_numbers': [],
            'urls': [],
            'suspicious_urls': []
        }

        # Persona — fake victim ka character
        self.persona = self._create_persona()

    def _create_persona(self) -> str:
        """
        Fake victim banao — itna real hona chahiye
        ki scammer ko lagega real person hai
        """
        personas = [
            """You are Ramesh Kumar, a 45-year-old small shop owner in Delhi.
- Not very good with technology
- Uses UPI for business but not an expert  
- Speaks simple Hinglish
- Worried about money
- Gets excited about money opportunities
- Trusts official sounding people""",

            """You are Sunita Devi, a 60-year-old retired teacher.
- Very polite and trusting
- Not comfortable with phones
- Confused by technical terms
- Worried about her savings
- Asks same questions again
- Very respectful in conversation""",

            """You are Vikram, a 28-year-old looking for extra income.
- Interested in side hustles
- Uses UPI daily
- Casual and friendly tone
- Asks practical questions
- Hopeful about opportunities"""
        ]
        return random.choice(personas)

    def generate_response(self, scammer_message: str, scam_type: str = "unknown") -> str:
        """
        Scammer ka message lo → Reply do

        Args:
            scammer_message: Scammer ne kya bheja
            scam_type: Kaunsa scam hai

        Returns:
            AI ka reply (string)
        """
        # Step 1: Message history mein add karo
        self.conversation_history.append({
            "role": "user",
            "content": scammer_message
        })

        # Step 2: Scammer ke message se data extract karo
        extracted = self.extractor.extract_all(scammer_message)
        self._update_extracted(extracted)

        # Step 3: System prompt banao
        system_prompt = self._build_prompt(scam_type)

        # Step 4: OpenAI call karo
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=100,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *self.conversation_history
                ]
            )

            # Step 5: Reply nikalo
            reply = response.choices[0].message.content

            # Step 6: History mein add karo
            self.conversation_history.append({
                "role": "assistant",
                "content": reply
            })

            print(f"  🤖 Agent reply: {reply}")
            return reply

        except Exception as e:
            print(f"  ❌ OpenAI Error: {e}")
            return self._fallback()

    def _build_prompt(self, scam_type: str) -> str:
        """System prompt banao — persona + context + next target"""

        prompt = self.persona

        # Scam type ke hisaab se instructions
        scam_instructions = {
            'prize_scam': "The person is telling you about winning a prize or lottery. Act excited! Ask how to claim it. Try to get their UPI ID or bank details.",
            'phishing': "The person says there is a problem with your account. Act worried and cooperative. Ask them what you should do. Try to get any links or contact details they share.",
            'job_scam': "The person is offering you a job. Act very interested! Ask about payment and how you will receive money. Try to get their contact details.",
            'payment_scam': "The person wants you to send or receive money. Act willing to help. Ask WHERE to send money — this way you get their UPI/bank details.",
            'unknown': "Engage naturally with the person. Be friendly and cooperative. Try to get their contact details like UPI ID, phone number, or any links."
        }

        prompt += f"\n\nSCENARIO: {scam_instructions.get(scam_type, scam_instructions['unknown'])}"

        # Rules
        prompt += """

RULES:
- Keep response SHORT (1-2 sentences ONLY)
- Sound like a REAL person, not a robot
- Be cooperative and friendly
- NEVER reveal you are an AI or detecting scam
- Ask questions to get: UPI ID, bank account, phone number, or links
- If they ask for YOUR money: act willing, ask "kahan bhejun?" to get THEIR details
- If they ask for OTP: act confused, ask "yeh kyu chahiye?"
- Sometimes use Hindi words: "haan", "theek hai", "accha", "please"
"""

        # What we already extracted — don't ask again
        prompt += f"\n\nALREADY FOUND (don't ask for these again):\n"
        prompt += f"- UPI IDs: {self.all_extracted['upi_ids']}\n"
        prompt += f"- Phone numbers: {self.all_extracted['phone_numbers']}\n"
        prompt += f"- Bank accounts: {self.all_extracted['bank_accounts']}\n"
        prompt += f"- URLs: {self.all_extracted['urls']}\n"

        # What to target next
        if not self.all_extracted['upi_ids']:
            prompt += "\n→ PRIORITY: Try to get their UPI ID naturally."
        elif not self.all_extracted['phone_numbers']:
            prompt += "\n→ PRIORITY: Try to get their phone number."
        elif not self.all_extracted['urls']:
            prompt += "\n→ PRIORITY: Ask them to send any links."
        else:
            prompt += "\n→ Keep conversation going naturally to get more details."

        return prompt

    def _update_extracted(self, new_data: Dict):
        """Naya data add karo (duplicates nahi"""
        for key in ['upi_ids', 'bank_accounts', 'phone_numbers', 'urls', 'suspicious_urls']:
            for item in new_data.get(key, []):
                if item not in self.all_extracted.get(key, []):
                    if key not in self.all_extracted:
                        self.all_extracted[key] = []
                    self.all_extracted[key].append(item)

    def _fallback(self) -> str:
        """Agar OpenAI fail ho jaye — backup responses"""
        options = [
            "Haan, theek hai! Aur batao please?",
            "Accha! Yeh interesting hai, details batao?",
            "Samajh gaya, aage kya karna hai?",
            "Theek hai bhai, mujhe thoda time do?",
        ]
        return random.choice(options)

    def get_extracted_intelligence(self) -> Dict:
        """Abhi tak ka sab extracted data"""
        return self.all_extracted

    def get_conversation_history(self) -> List[Dict]:
        """Puri conversation history"""
        return self.conversation_history

    def get_turn_count(self) -> int:
        """Kitne turns ho chuke"""
        return len([m for m in self.conversation_history if m["role"] == "user"])