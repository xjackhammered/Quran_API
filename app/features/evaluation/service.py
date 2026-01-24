"""
Recitation Evaluation Service
=============================
Core logic for evaluating Quran recitation accuracy.

Features:
- Arabic text normalization
- Word-by-word comparison using SequenceMatcher
- Levenshtein distance for similarity scoring
- Color-coded feedback (Green/Yellow/Red)
- Handles Quranic text variations
"""

import re
import unicodedata
from difflib import SequenceMatcher
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class WordStatus(str, Enum):
    """Status for each word in evaluation"""
    CORRECT = "correct"
    SIMILAR = "similar"
    WRONG = "wrong"
    MISSING = "missing"
    EXTRA = "extra"


@dataclass
class WordFeedback:
    """Feedback for a single word"""
    reference_word: str
    user_word: str
    status: WordStatus
    color: str
    accuracy: float
    note: Optional[str] = None


@dataclass
class EvaluationResult:
    """Complete evaluation result"""
    overall_accuracy: float
    total_words: int
    correct_words: int
    similar_words: int
    wrong_words: int
    missing_words: int
    extra_words: int
    reference_text: str
    user_text: str
    word_feedback: List[WordFeedback]
    suggestions: List[str]


class ArabicTextNormalizer:
    """
    Normalizes Arabic text for comparison.
    
    Handles:
    - Diacritics (harakat) removal
    - Hamza normalization
    - Alef variations
    - Teh marbuta / heh
    - Common Quranic variations
    """
    
    # Arabic diacritics (tashkeel/harakat)
    DIACRITICS = re.compile(r'[\u064B-\u065F\u0670\u06D6-\u06ED]')
    
    # Hamza variations
    HAMZA_MAP = {
        'أ': 'ا',  # Alef with hamza above
        'إ': 'ا',  # Alef with hamza below
        'آ': 'ا',  # Alef with madda
        'ٱ': 'ا',  # Alef wasla
        'ؤ': 'و',  # Waw with hamza
        'ئ': 'ي',  # Yeh with hamza
        'ء': '',   # Standalone hamza (remove)
    }
    
    # Alef variations
    ALEF_VARIATIONS = {
        'ٰ': 'ا',   # Superscript alef
        'ى': 'ي',   # Alef maksura to yeh
    }
    
    # Common Quranic variations (acceptable alternatives)
    ACCEPTABLE_VARIATIONS = {
        'الرحمن': ['الرحمان'],
        'الرحيم': ['الرحيم'],
        'العالمين': ['العلمين', 'العالمين'],
        'الصراط': ['السراط'],
        'صراط': ['سراط'],
    }
    
    @classmethod
    def normalize(cls, text: str) -> str:
        """
        Normalize Arabic text for comparison.
        
        Steps:
        1. Remove diacritics
        2. Normalize hamza
        3. Normalize alef variations
        4. Clean whitespace
        """
        if not text:
            return ""
        
        # Remove diacritics
        text = cls.DIACRITICS.sub('', text)
        
        # Normalize hamza
        for char, replacement in cls.HAMZA_MAP.items():
            text = text.replace(char, replacement)
        
        # Normalize alef variations
        for char, replacement in cls.ALEF_VARIATIONS.items():
            text = text.replace(char, replacement)
        
        # Remove tatweel (kashida)
        text = text.replace('ـ', '')
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """Split text into words"""
        normalized = cls.normalize(text)
        return [w for w in normalized.split() if w]
    
    @classmethod
    def is_acceptable_variation(cls, reference: str, user_word: str) -> bool:
        """Check if user's word is an acceptable Quranic variation"""
        ref_normalized = cls.normalize(reference)
        user_normalized = cls.normalize(user_word)
        
        if ref_normalized in cls.ACCEPTABLE_VARIATIONS:
            return user_normalized in [
                cls.normalize(v) for v in cls.ACCEPTABLE_VARIATIONS[ref_normalized]
            ]
        return False


class RecitationEvaluator:
    """
    Evaluates Quran recitation by comparing user's transcription
    against reference text.
    """
    
    def __init__(self):
        self.normalizer = ArabicTextNormalizer()
        
        # Thresholds for scoring
        self.exact_match_threshold = 1.0
        self.similar_threshold = 0.7
        self.partial_threshold = 0.5
    
    def _levenshtein_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings using Levenshtein distance.
        Returns value between 0 and 1.
        """
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        # Use SequenceMatcher for efficiency
        return SequenceMatcher(None, s1, s2).ratio()
    
    def _get_color_for_status(self, status: WordStatus) -> str:
        """Get color code for word status"""
        color_map = {
            WordStatus.CORRECT: "green",
            WordStatus.SIMILAR: "yellow",
            WordStatus.WRONG: "red",
            WordStatus.MISSING: "red",
            WordStatus.EXTRA: "orange",
        }
        return color_map.get(status, "gray")
    
    def _get_note_for_status(self, status: WordStatus, accuracy: float) -> str:
        """Get Arabic note for word status"""
        if status == WordStatus.CORRECT:
            return "ممتاز! ✓"
        elif status == WordStatus.SIMILAR:
            return f"قريب - {accuracy:.0f}%"
        elif status == WordStatus.WRONG:
            return "خطأ - حاول مرة أخرى"
        elif status == WordStatus.MISSING:
            return "كلمة مفقودة"
        elif status == WordStatus.EXTRA:
            return "كلمة زائدة"
        return ""
    
    def compare_words(
        self, 
        reference_word: str, 
        user_word: str
    ) -> Tuple[WordStatus, float]:
        """
        Compare two words and return status and accuracy.
        
        Returns:
            Tuple of (WordStatus, accuracy percentage)
        """
        # Normalize both words
        ref_normalized = self.normalizer.normalize(reference_word)
        user_normalized = self.normalizer.normalize(user_word)
        
        # Exact match
        if ref_normalized == user_normalized:
            return WordStatus.CORRECT, 100.0
        
        # Check acceptable variations
        if self.normalizer.is_acceptable_variation(reference_word, user_word):
            return WordStatus.CORRECT, 100.0
        
        # Calculate similarity
        similarity = self._levenshtein_similarity(ref_normalized, user_normalized)
        accuracy = similarity * 100
        
        # Determine status based on similarity
        if similarity >= self.similar_threshold:
            return WordStatus.SIMILAR, accuracy
        else:
            return WordStatus.WRONG, accuracy
    
    def evaluate(
        self, 
        reference_text: str, 
        user_text: str
    ) -> EvaluationResult:
        """
        Evaluate user's recitation against reference text.
        
        Args:
            reference_text: The correct Quran text
            user_text: User's transcribed recitation
            
        Returns:
            EvaluationResult with detailed feedback
        """
        # Tokenize both texts
        ref_words = self.normalizer.tokenize(reference_text)
        user_words = self.normalizer.tokenize(user_text)
        
        # Handle empty inputs
        if not ref_words:
            return EvaluationResult(
                overall_accuracy=0,
                total_words=0,
                correct_words=0,
                similar_words=0,
                wrong_words=0,
                missing_words=0,
                extra_words=len(user_words),
                reference_text=reference_text,
                user_text=user_text,
                word_feedback=[],
                suggestions=["النص المرجعي فارغ"]
            )
        
        # Use SequenceMatcher to align words
        matcher = SequenceMatcher(None, ref_words, user_words)
        
        # Initialize counters
        feedback: List[WordFeedback] = []
        correct_count = 0
        similar_count = 0
        wrong_count = 0
        missing_count = 0
        extra_count = 0
        
        # Process matching operations
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Words match exactly
                for idx in range(i2 - i1):
                    ref_word = ref_words[i1 + idx]
                    user_word = user_words[j1 + idx]
                    
                    feedback.append(WordFeedback(
                        reference_word=ref_word,
                        user_word=user_word,
                        status=WordStatus.CORRECT,
                        color="green",
                        accuracy=100.0,
                        note="ممتاز! ✓"
                    ))
                    correct_count += 1
            
            elif tag == 'replace':
                # Words are different - compare each pair
                ref_segment = ref_words[i1:i2]
                user_segment = user_words[j1:j2]
                
                # Align by length
                max_len = max(len(ref_segment), len(user_segment))
                
                for idx in range(max_len):
                    ref_word = ref_segment[idx] if idx < len(ref_segment) else None
                    user_word = user_segment[idx] if idx < len(user_segment) else None
                    
                    if ref_word and user_word:
                        status, accuracy = self.compare_words(ref_word, user_word)
                        
                        if status == WordStatus.CORRECT:
                            correct_count += 1
                        elif status == WordStatus.SIMILAR:
                            similar_count += 1
                        else:
                            wrong_count += 1
                        
                        feedback.append(WordFeedback(
                            reference_word=ref_word,
                            user_word=user_word,
                            status=status,
                            color=self._get_color_for_status(status),
                            accuracy=accuracy,
                            note=self._get_note_for_status(status, accuracy)
                        ))
                    
                    elif ref_word:
                        # Missing word
                        missing_count += 1
                        feedback.append(WordFeedback(
                            reference_word=ref_word,
                            user_word="[مفقود]",
                            status=WordStatus.MISSING,
                            color="red",
                            accuracy=0.0,
                            note="كلمة مفقودة"
                        ))
                    
                    else:
                        # Extra word
                        extra_count += 1
                        feedback.append(WordFeedback(
                            reference_word="[زائد]",
                            user_word=user_word,
                            status=WordStatus.EXTRA,
                            color="orange",
                            accuracy=0.0,
                            note="كلمة زائدة"
                        ))
            
            elif tag == 'delete':
                # User missed these words
                for idx in range(i1, i2):
                    missing_count += 1
                    feedback.append(WordFeedback(
                        reference_word=ref_words[idx],
                        user_word="[مفقود]",
                        status=WordStatus.MISSING,
                        color="red",
                        accuracy=0.0,
                        note="كلمة مفقودة"
                    ))
            
            elif tag == 'insert':
                # User added extra words
                for idx in range(j1, j2):
                    extra_count += 1
                    feedback.append(WordFeedback(
                        reference_word="[زائد]",
                        user_word=user_words[idx],
                        status=WordStatus.EXTRA,
                        color="orange",
                        accuracy=0.0,
                        note="كلمة زائدة"
                    ))
        
        # Calculate overall accuracy
        total_words = len(ref_words)
        weighted_correct = correct_count + (similar_count * 0.7)
        overall_accuracy = (weighted_correct / total_words * 100) if total_words > 0 else 0
        
        # Generate suggestions
        suggestions = self._generate_suggestions(
            correct_count, similar_count, wrong_count, 
            missing_count, extra_count, total_words
        )
        
        return EvaluationResult(
            overall_accuracy=round(overall_accuracy, 1),
            total_words=total_words,
            correct_words=correct_count,
            similar_words=similar_count,
            wrong_words=wrong_count,
            missing_words=missing_count,
            extra_words=extra_count,
            reference_text=reference_text,
            user_text=user_text,
            word_feedback=feedback,
            suggestions=suggestions
        )
    
    def _generate_suggestions(
        self,
        correct: int,
        similar: int,
        wrong: int,
        missing: int,
        extra: int,
        total: int
    ) -> List[str]:
        """Generate helpful suggestions based on evaluation"""
        suggestions = []
        
        accuracy = (correct + similar * 0.7) / total * 100 if total > 0 else 0
        
        if accuracy >= 90:
            suggestions.append("ممتاز! قراءتك رائعة 🌟")
        elif accuracy >= 70:
            suggestions.append("جيد جداً! استمر في التحسن")
        elif accuracy >= 50:
            suggestions.append("جيد! حاول التركيز أكثر على النطق")
        else:
            suggestions.append("حاول مرة أخرى مع التركيز على كل كلمة")
        
        if missing > 0:
            suggestions.append(f"⚠️ فاتتك {missing} كلمة - حاول القراءة بشكل أبطأ")
        
        if extra > 0:
            suggestions.append(f"⚠️ أضفت {extra} كلمة زائدة")
        
        if wrong > 2:
            suggestions.append("💡 نصيحة: استمع للتلاوة الصحيحة قبل المحاولة")
        
        return suggestions


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_evaluator_instance: Optional[RecitationEvaluator] = None


def get_evaluator() -> RecitationEvaluator:
    """Get singleton instance of RecitationEvaluator"""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = RecitationEvaluator()
    return _evaluator_instance
