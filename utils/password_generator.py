import string
import random
import re
from typing import Dict

class PasswordGenerator:
    def __init__(self):
        self.similar_chars = '1lI0Oo'
        self.char_sets = {
            'uppercase': string.ascii_uppercase,
            'lowercase': string.ascii_lowercase,
            'numbers': string.digits,
            'symbols': string.punctuation
        }

    def generate_password(self, preferences: Dict) -> str:
        """Generate password based on preferences"""
        chars = ''
        required_chars = []
        
        # Build character set based on preferences
        if preferences.get('use_uppercase', True):
            chars += self.char_sets['uppercase']
            required_chars.append(random.choice(self.char_sets['uppercase']))
            
        if preferences.get('use_lowercase', True):
            chars += self.char_sets['lowercase']
            required_chars.append(random.choice(self.char_sets['lowercase']))
            
        if preferences.get('use_numbers', True):
            chars += self.char_sets['numbers']
            required_chars.append(random.choice(self.char_sets['numbers']))
            
        if preferences.get('use_symbols', True):
            chars += self.char_sets['symbols']
            required_chars.append(random.choice(self.char_sets['symbols']))
            
        # Remove similar characters if specified
        if preferences.get('avoid_similar', True):
            chars = ''.join(c for c in chars if c not in self.similar_chars)
            
        # Generate password
        length = max(preferences.get('min_length', 12), len(required_chars))
        password_chars = required_chars + [random.choice(chars) for _ in range(length - len(required_chars))]
        random.shuffle(password_chars)
        
        return ''.join(password_chars)
        
    def analyze_password(self, password: str) -> Dict:
        """Analyze password strength and characteristics"""
        analysis = {
            'length': len(password),
            'uppercase': bool(re.search(r'[A-Z]', password)),
            'lowercase': bool(re.search(r'[a-z]', password)),
            'numbers': bool(re.search(r'\d', password)),
            'symbols': bool(re.search(r'[^A-Za-z0-9]', password)),
            'similar_chars': any(c in self.similar_chars for c in password)
        }
        
        # Calculate base score
        score = 0
        if analysis['length'] >= 12: score += 20
        if analysis['uppercase']: score += 20
        if analysis['lowercase']: score += 20
        if analysis['numbers']: score += 20
        if analysis['symbols']: score += 20
        
        # Penalties
        if analysis['similar_chars']: score -= 10
        if analysis['length'] < 8: score -= 20
        
        analysis['score'] = max(0, min(100, score))
        return analysis
