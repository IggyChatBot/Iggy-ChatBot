"""
nlp_engine.py - NLP Module
Component 3: NLP Module

Handles:
- Intent detection using semantic/example-based matching
- Entity extraction from student messages
- Context-aware response generation
- Confidence scoring and clarification fallback
- Keyword fallback when optional ML packages are unavailable

Notes:
- This module keeps the same public class name: NLPEngine.
- It works without internet access.
- If sentence-transformers is installed, it uses real sentence embeddings.
- If not, it falls back to scikit-learn TF-IDF similarity.
"""

from __future__ import annotations

import logging
import random
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Intent examples
# ---------------------------------------------------------------------------
# Instead of relying only on keywords, each intent has example user messages.
# The engine compares the user's message against these examples and chooses the
# closest meaning.

INTENT_EXAMPLES: Dict[str, List[str]] = {
    "enrollment_process_inquiry": [
        "How do I enroll?",
        "What is the enrollment process?",
        "How can I register as a new student?",
        "How do I apply for admission?",
        "What are the steps for enrollment?",
        "I want to enroll at ICCT Colleges.",
        "How to sign up as a student?",
    ],
    "enrollment_schedule_inquiry": [
        "When is enrollment?",
        "What is the enrollment schedule?",
        "When can I enroll for second semester?",
        "Is enrollment still open?",
        "Until when is enrollment?",
        "What are the dates for registration?",
        "When does admission start?",
    ],
    "requirements_inquiry": [
        "What are the enrollment requirements?",
        "What documents do I need to enroll?",
        "What should I bring for admission?",
        "Do I need Form 138?",
        "Are birth certificate and good moral required?",
        "What credentials are needed for transferees?",
    ],
    "course_inquiry": [
        "What courses do you offer?",
        "What programs are available?",
        "Do you offer BSIT?",
        "Tell me about computer science.",
        "What degree programs are in ICCT?",
        "Do you have nursing or engineering?",
        "What strands are available for senior high school?",
    ],
    "class_schedule_inquiry": [
        "What is my class schedule?",
        "Where can I see my timetable?",
        "What time are classes?",
        "Do you have morning classes?",
        "Are evening classes available?",
        "How do I get my section schedule?",
        "When are my subjects scheduled?",
    ],
    "schedule_inquiry": [
        "Schedule",
        "Schedules",
        "What are the schedules?",
        "Show me the schedule",
        "Tell me about the schedule",
        "What is the schedule?",
        "Give me schedule information",
        "View schedule",
    ],
    "tuition_inquiry": [
        "How much is the tuition?",
        "What are the fees?",
        "How much is the down payment?",
        "Can I pay by installment?",
        "What is the cost per unit?",
        "How much do I need to pay for enrollment?",
        "Are there miscellaneous fees?",
    ],
    "scholarship_inquiry": [
        "Do you offer scholarships?",
        "How can I apply for financial aid?",
        "Is CHED scholarship accepted?",
        "Do you have UniFAST?",
        "Can I get tuition assistance?",
        "What grants are available?",
    ],
    "policy_inquiry": [
        "What are the school policies?",
        "What is the dress code?",
        "Do students need to wear uniform?",
        "What is the attendance policy?",
        "How many absences are allowed?",
        "What are the school rules?",
        "What happens if I violate the code of conduct?",
    ],
    "contact_inquiry": [
        "How can I contact the registrar?",
        "What is the school phone number?",
        "Where is the campus located?",
        "What is the registrar email?",
        "Where is the office?",
        "How do I reach ICCT Colleges?",
        "What are the office hours?",
    ],
    "greeting": [
        "hello",
        "hi",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "kamusta",
        "musta",
    ],
    "farewell": [
        "bye",
        "goodbye",
        "thank you",
        "thanks",
        "salamat",
        "see you",
        "good night",
    ],
}

# Optional keyword hints are still useful for tie-breaking and very short inputs.
KEYWORD_HINTS: Dict[str, List[str]] = {
    "enrollment_process_inquiry": ["how", "process", "steps", "procedure", "apply", "register", "sign up", "enroll"],
    "enrollment_schedule_inquiry": ["when", "schedule", "date", "dates", "deadline", "until", "open", "start", "end"],
    "requirements_inquiry": ["requirement", "requirements", "document", "documents", "needed", "bring", "form 138", "tor", "birth certificate", "good moral"],
    "course_inquiry": ["course", "courses", "program", "programs", "degree", "bsit", "bscs", "bscpe", "bsba", "bsa", "bsn", "strand"],
    "class_schedule_inquiry": ["class", "classes", "timetable", "subject", "subjects", "section", "morning", "afternoon", "evening"],
    "schedule_inquiry": ["schedule", "schedules"],
    "tuition_inquiry": ["tuition", "fee", "fees", "payment", "cost", "price", "how much", "installment", "down payment"],
    "scholarship_inquiry": ["scholarship", "financial aid", "ched", "unifast", "grant", "assistance", "subsidy"],
    "policy_inquiry": ["policy", "rules", "dress code", "uniform", "attendance", "absence", "conduct", "discipline"],
    "contact_inquiry": ["contact", "registrar", "office", "phone", "email", "address", "location", "where", "hotline", "facebook"],
    "greeting": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "kamusta", "musta"],
    "farewell": ["bye", "goodbye", "thank", "thanks", "salamat", "see you"],
}

RESPONSES: Dict[str, str] = {
    "enrollment_process_inquiry": (
        "**Enrollment Process at ICCT Colleges**\n\n"
        "Here are the usual steps:\n"
        "1. Visit the campus or official enrollment channel.\n"
        "2. Fill out the Student Information Sheet (SIS).\n"
        "3. Submit your documents to the Registrar's Office.\n"
        "4. Pay the enrollment or reservation fee at the Cashier.\n"
        "5. Claim or view your class schedule and school ID instructions.\n\n"
        "Would you like the requirements or the enrollment schedule?"
    ),
    "enrollment_schedule_inquiry": (
        "**Enrollment Schedule**\n\n"
        "The usual enrollment periods are:\n"
        "- **1st Semester:** June to July\n"
        "- **2nd Semester:** November to December\n"
        "- **Summer:** March to April\n\n"
        "For the exact current deadline, please confirm with the Registrar's Office or the official ICCT Colleges page, since dates may change per school year."
    ),
    "requirements_inquiry": (
        "**Enrollment Requirements at ICCT Colleges**\n\n"
        "For **New Students (College)**:\n"
        "- Original PSA Birth Certificate\n"
        "- Original Form 138 or Transcript of Records\n"
        "- Certificate of Good Moral Character\n"
        "- 2 pcs. 2x2 ID photos with white background\n"
        "- Valid government-issued ID\n"
        "- Photocopy of all documents\n\n"
        "For **Transferees**:\n"
        "- Transcript of Records (TOR)\n"
        "- Certificate of Transfer Credential / Honorable Dismissal\n"
        "- PSA Birth Certificate\n"
        "- 2 pcs. 2x2 ID photos\n\n"
        "Is this for a new student or a transferee?"
    ),
    "course_inquiry": (
        "**Courses Offered at ICCT Colleges**\n\n"
        "**College of Computer Studies:**\n"
        "- BS Information Technology (BSIT)\n"
        "- BS Computer Science (BSCS)\n"
        "- BS Computer Engineering (BSCpE)\n\n"
        "**College of Business:**\n"
        "- BS Business Administration (BSBA)\n"
        "- BS Accountancy (BSA)\n\n"
        "**College of Education:**\n"
        "- Bachelor of Elementary Education (BEEd)\n"
        "- Bachelor of Secondary Education (BSEd)\n\n"
        "**College of Nursing & Allied Health:**\n"
        "- BS Nursing (BSN)\n\n"
        "**Senior High School:**\n"
        "- STEM, ABM, HUMSS, GAS strands\n\n"
        "Please note that this list may not cover all programs currently offered. "
        "ICCT Colleges may have additional or updated courses not reflected here, as our information is based on "
        "publicly available data from their official website, Facebook page, and student portal. "
        "For the most accurate and complete list, please visit the ICCT Colleges official website, "
        "contact the Registrar's Office, or check their official Facebook page."
    ),
    "class_schedule_inquiry": (
        "**Class Schedule Information**\n\n"
        "ICCT Colleges usually offers flexible schedules:\n"
        "- **Morning:** 7:00 AM to 12:00 PM\n"
        "- **Afternoon:** 1:00 PM to 6:00 PM\n"
        "- **Evening:** 6:00 PM to 9:00 PM for select programs\n\n"
        "For your specific class schedule, log in to the Student Portal, visit the Registrar's Office, or contact your department secretary."
    ),
    "tuition_inquiry": (
        "**Tuition and Fees at ICCT Colleges**\n\n"
        "Tuition varies by course and year level. As a general guide:\n"
        "- Per-unit fee may vary by program\n"
        "- Miscellaneous fees may apply per semester\n"
        "- Payment may be full or installment depending on school policy\n\n"
        "For the exact and updated fee schedule, please contact the Cashier's Office or official school channels."
    ),
    "scholarship_inquiry": (
        "**Scholarships and Financial Aid**\n\n"
        "Possible options may include:\n"
        "- CHED scholarships\n"
        "- UniFAST / TDP\n"
        "- Academic scholarships\n"
        "- Athletic or leadership scholarships\n"
        "- Other student assistance programs\n\n"
        "To apply, visit the Scholarship or Student Affairs Office and prepare grades, income documents, and valid ID if required."
    ),
    "schedule_inquiry": (
        "**Enrollment Schedule**\n\n"
        "The usual enrollment periods are:\n"
        "- **1st Semester:** June to July\n"
        "- **2nd Semester:** November to December\n"
        "- **Summer:** March to April\n\n"
        "For the exact current deadline, please confirm with the Registrar's Office "
        "or the official ICCT Colleges page, since dates may change per school year.\n\n"
        "---\n\n"
        "**Class Schedule Information**\n\n"
        "ICCT Colleges usually offers flexible schedules:\n"
        "- **Morning:** 7:00 AM to 12:00 PM\n"
        "- **Afternoon:** 1:00 PM to 6:00 PM\n"
        "- **Evening:** 6:00 PM to 9:00 PM for select programs\n\n"
        "For your specific class schedule, log in to the Student Portal, "
        "visit the Registrar's Office, or contact your department secretary."
    ),
    "policy_inquiry": (
        "**School Policies**\n\n"
        "Common policy areas include attendance, dress code, school ID, academic integrity, examinations, and student conduct.\n\n"
        "For official rules, please refer to the Student Handbook or visit the Student Affairs Office."
    ),
    "contact_inquiry": (
        "**Contact ICCT Colleges**\n\n"
        "You may contact or visit the Registrar's Office during office hours.\n\n"
        "Typical office hours:\n"
        "- Monday to Friday: 8:00 AM to 5:00 PM\n"
        "- Saturday: 8:00 AM to 12:00 PM\n\n"
        "For urgent or updated concerns, use the official ICCT Colleges website or Facebook page."
    ),
    "greeting": (
        "Hi there! 👋 Welcome to ICCT Colleges Support Bot.\n\n"
        "I can help with enrollment, requirements, courses, schedules, tuition, scholarships, policies, and contact information.\n\n"
        "What would you like to know today?"
    ),
    "farewell": "You're welcome! 😊 Feel free to come back anytime. Good luck with your studies! 🎓",
    "fallback": (
        "I'm sorry, I didn't quite get that. 😅\n\n"
        "You can ask me about enrollment, requirements, courses, class schedules, tuition, scholarships, policies, or contact information."
    ),
}

# ---------------------------------------------------------------------------
# Out-of-scope witty responses
# ---------------------------------------------------------------------------
# Shown when a user asks a valid, meaningful question that is simply outside
# the bot's domain (e.g. weather, games, life advice).
# generate_response() picks one at random so replies don't feel repetitive.

OUT_OF_SCOPE_RESPONSES: List[str] = [
    "Ha, great question — but I'm afraid I left my crystal ball at the registrar's office. 😄 "
    "I'm only trained to help with ICCT Colleges stuff like enrollment, courses, tuition, and the like. "
    "Anything school-related I can help with?",

    "I wish I could help with that, but my expertise stops at ICCT's campus gates. 🎓 "
    "I'm your go-to for enrollment, requirements, schedules, and school info — not much else, sadly!",

    "Ooh, I'd love to answer that, but I'm a bot of very specific talents. 😅 "
    "Think of me as the ultimate ICCT Colleges FAQ. For everything else, Google's got you! "
    "Anything school-related I can answer for you?",

    "That's a fun one, but it's a little outside my lane! 🚗 "
    "I'm best at things like enrollment schedules, tuition fees, courses, and school policies. "
    "Want to ask me something along those lines?",

    "As much as I'd love to chat about that, my brain is 100% ICCT Colleges-certified. 🏫 "
    "I can help with enrollment, requirements, fees, and more — just not that. "
    "What school-related question can I take on?",
]

CLARIFICATION_LABELS: Dict[str, str] = {
    "enrollment_process_inquiry": "enrollment process",
    "enrollment_schedule_inquiry": "enrollment schedule or deadline",
    "requirements_inquiry": "requirements or documents",
    "course_inquiry": "courses or programs",
    "class_schedule_inquiry": "class schedule",
    "schedule_inquiry": "schedule information (enrollment dates and class times)",
    "tuition_inquiry": "tuition or fees",
    "scholarship_inquiry": "scholarships or financial aid",
    "policy_inquiry": "school policies",
    "contact_inquiry": "contact details or office location",
}


# ---------------------------------------------------------------------------
# Gibberish detection
# ---------------------------------------------------------------------------

def _is_gibberish(text: str) -> bool:
    """
    Returns True if the input appears random or meaningless (no real question intent).
    Returns False if the input looks like a genuine — even if off-topic — human message.

    Checks for:
    - Single character input           (e.g. "a", "1", "?")
    - Purely numeric input             (e.g. "12", "999", "2025")
    - Purely symbolic / punctuation    (e.g. "???", "!!!", "...", "@#$")
    - Mixed numbers and symbols only   (e.g. "123!", "#1")
    - Very short non-word input        (e.g. "xy", "zz")
    - Known keyboard-mash filler words (e.g. "asdf", "test", "qwerty")
    - Single token with no vowels      (e.g. "fghsd", "zxcvb")
    - Single token with very high consonant-cluster density (e.g. "dfjkls")
    - Cut-off sentence fragments       (e.g. "when is the", "what a")
    """
    clean = text.strip().lower()

    # Empty after stripping
    if not clean:
        return True

    # Single character — always meaningless regardless of what it is
    if len(clean) == 1:
        return True

    # Purely numeric — no linguistic content (e.g. "12", "999", "2025")
    if re.fullmatch(r"\d+", clean):
        return True

    # Purely symbolic / punctuation (e.g. "???", "!!!", "...", "@#$%")
    if re.fullmatch(r"[\W_]+", clean):
        return True

    # Mix of numbers and symbols only — no letters at all (e.g. "123!", "#1", "007")
    if re.fullmatch(r"[\d\W_]+", clean):
        return True

    # Common unfinished fragments. These contain question words, but they do
    # not contain enough meaning to safely answer or search the FAQ database.
    # Examples: "when is the", "what a", "how to", "can i", "where is".
    cut_off_patterns = [
        r"^(when|what|where|who|why|how)$",
        r"^(when|what|where|who|why|how)\s+(is|are|do|does|did|can|could|would|will|should)$",
        r"^(when|what|where|who|why|how)\s+(is|are|do|does|did|can|could|would|will|should)\s+(the|a|an|my|your|our|this|that|it)$",
        r"^(what|such|quite|very|really)\s+(a|an|the)$",
        r"^(how\s+to|can\s+i|do\s+you|is\s+there|are\s+there|i\s+want\s+to)$",
        r"^(tell\s+me\s+about|give\s+me|show\s+me)$",
    ]
    if any(re.fullmatch(pattern, clean) for pattern in cut_off_patterns):
        return True

    # Very short (2-3 chars) -- only allow known meaningful short words
    common_short = {
        # Common 2-letter English words
        "hi", "ok", "no", "go", "do", "be", "me", "we", "he", "it",
        "is", "am", "an", "as", "at", "by", "if", "in", "of", "on",
        "or", "so", "to", "up", "us", "my", "ah", "oh", "ow", "ew",
        # Common 3-letter English words / greetings
        "yes", "yep", "nah", "hey", "bye", "sup", "how", "why", "who",
        "the", "and", "can", "did", "get", "got", "has", "had", "his",
        "its", "let", "may", "now", "our", "out", "was", "way", "you",
        # Filipino short words
        "oo", "di", "ba", "po", "nga", "ano", "ate", "kuya", "oo po", "di po",
    }
    if len(clean) <= 3 and clean not in common_short:
        return True

    # Known filler / keyboard-mash / test words
    filler_words = {
        "test", "testing", "asdf", "qwerty", "lol", "haha",
        "blah", "asd", "zxc", "qwe", "abc", "xyz",
    }
    if clean in filler_words:
        return True

    # Single-token deeper checks
    tokens = clean.split()
    if len(tokens) == 1:
        token = tokens[0]
        vowels = set("aeiou")

        # No vowels at all → almost certainly not a real word
        if len(token) > 2 and not any(c in vowels for c in token):
            return True

        # Very high consonant-cluster density (keyboard mashing)
        if len(token) >= 6:
            clusters = re.findall(r"[bcdfghjklmnpqrstvwxyz]{3,}", token)
            cluster_chars = sum(len(c) for c in clusters)
            if cluster_chars / len(token) > 0.65:
                return True

            # Single long words that do not contain any common English/Filipino
            # letter patterns are usually keyboard mashes, not real questions.
            # This catches examples like "dadjhakad" while preserving real words
            # like "weather", "computer", "science", "enrollment", etc.
            common_letter_patterns = {
                "the", "and", "ing", "ion", "ent", "men", "ter", "com",
                "pro", "sch", "cou", "our", "urse", "sci", "cie", "enc",
                "nce", "wea", "eat", "ath", "her", "gam", "ame", "mes",
                "reg", "enr", "rol", "oll", "fee", "pay", "tui", "ion",
                "cla", "ass", "che", "edu", "cat", "ate", "ara", "ano",
                "kam", "amu", "mus", "ust", "sta",
            }
            if token.isalpha() and not any(pattern in token for pattern in common_letter_patterns):
                return True

    return False


@dataclass
class IntentResult:
    intent: str
    confidence: float
    alternatives: List[Tuple[str, float]]
    method: str


class NLPEngine:
    """NLP Engine for the ICCT Colleges Chatbot."""

    def __init__(self, confidence_threshold: float = 0.42, ambiguity_margin: float = 0.08):
        self.confidence_threshold = confidence_threshold
        self.ambiguity_margin = ambiguity_margin
        self._ready = False
        self._model_type = "none"
        self._load_model()

    def _load_model(self) -> None:
        """Load the best available semantic matcher."""
        self._patterns = self._compile_keyword_patterns()
        self._intent_names = list(INTENT_EXAMPLES.keys())
        self._example_texts = []
        self._example_intents = []

        for intent, examples in INTENT_EXAMPLES.items():
            for example in examples:
                self._example_texts.append(self._normalize(example))
                self._example_intents.append(intent)

        # Best option: sentence-transformers, if the package/model exists locally.
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
            self._example_vectors = self._encoder.encode(
                self._example_texts, normalize_embeddings=True)
            self._model_type = "sentence_transformers"
            self._ready = True
            logger.info(
                "NLPEngine: sentence-transformers semantic matcher loaded.")
            return
        except Exception as exc:
            logger.warning(
                "NLPEngine: sentence-transformers unavailable, using TF-IDF fallback. %s", exc)

        # Practical fallback: TF-IDF similarity. This is still example-based and
        # much better than counting a single keyword such as 'enrollment'.
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore

            self._vectorizer = TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 5),
                lowercase=True,
            )
            self._example_vectors = self._vectorizer.fit_transform(
                self._example_texts)
            self._model_type = "tfidf"
            self._ready = True
            logger.info("NLPEngine: TF-IDF semantic matcher loaded.")
            return
        except Exception as exc:
            logger.warning(
                "NLPEngine: scikit-learn unavailable, using keyword fallback. %s", exc)

        self._model_type = "keyword"
        self._ready = True
        logger.info("NLPEngine: keyword fallback loaded.")

    def _compile_keyword_patterns(self) -> Dict[str, re.Pattern]:
        patterns = {}
        for intent, keywords in KEYWORD_HINTS.items():
            escaped = sorted((re.escape(k)
                             for k in keywords), key=len, reverse=True)
            patterns[intent] = re.compile(
                r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)
        return patterns

    def _normalize(self, text: str) -> str:
        text = text or ""
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def is_ready(self) -> bool:
        return self._ready

    def detect_intent(self, text: str) -> str:
        """Backward-compatible method. Returns only the intent string."""
        return self.detect_intent_details(text).intent

    def detect_intent_details(self, text: str) -> IntentResult:
        """Return intent, confidence, alternatives, and method."""
        clean_text = self._normalize(text)
        if not clean_text or _is_gibberish(clean_text):
            return IntentResult("fallback", 0.0, [], self._model_type)

        if self._model_type == "sentence_transformers":
            result = self._detect_with_sentence_transformers(clean_text)
        elif self._model_type == "tfidf":
            result = self._detect_with_tfidf(clean_text)
        else:
            result = self._detect_with_keywords(clean_text)

        adjusted = self._apply_keyword_tie_breakers(clean_text, result)
        return self._apply_confidence_rules(adjusted)

    def _detect_with_sentence_transformers(self, clean_text: str) -> IntentResult:
        import numpy as np  # type: ignore

        query_vector = self._encoder.encode(
            [clean_text], normalize_embeddings=True)[0]
        scores = np.dot(self._example_vectors, query_vector)
        return self._aggregate_example_scores(scores.tolist(), "sentence_transformers")

    def _detect_with_tfidf(self, clean_text: str) -> IntentResult:
        from sklearn.metrics.pairwise import cosine_similarity  # type: ignore

        query_vector = self._vectorizer.transform([clean_text])
        scores = cosine_similarity(
            self._example_vectors, query_vector).ravel().tolist()
        return self._aggregate_example_scores(scores, "tfidf")

    def _aggregate_example_scores(self, example_scores: List[float], method: str) -> IntentResult:
        intent_scores: Dict[str, float] = {
            intent: 0.0 for intent in self._intent_names}

        for intent, score in zip(self._example_intents, example_scores):
            # Keep the best example match for each intent.
            intent_scores[intent] = max(intent_scores[intent], float(score))

        ranked = sorted(intent_scores.items(),
                        key=lambda item: item[1], reverse=True)
        top_intent, top_score = ranked[0]
        return IntentResult(top_intent, round(top_score, 4), ranked[:5], method)

    def _detect_with_keywords(self, clean_text: str) -> IntentResult:
        scores = {}
        for intent, pattern in self._patterns.items():
            matches = pattern.findall(clean_text)
            if matches:
                scores[intent] = len(matches)

        if not scores:
            return IntentResult("fallback", 0.0, [], "keyword")

        max_count = max(scores.values())
        ranked = sorted(((intent, count / max_count) for intent,
                        count in scores.items()), key=lambda item: item[1], reverse=True)
        return IntentResult(ranked[0][0], round(ranked[0][1], 4), ranked[:5], "keyword")

    def _apply_keyword_tie_breakers(self, clean_text: str, result: IntentResult) -> IntentResult:
        """Use keywords lightly to improve close semantic matches."""
        if result.intent == "fallback":
            return result

        scores = {intent: score for intent, score in result.alternatives}
        for intent, pattern in self._patterns.items():
            match_count = len(pattern.findall(clean_text))
            if match_count:
                scores[intent] = scores.get(
                    intent, 0.0) + min(0.06 * match_count, 0.18)

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_intent, top_score = ranked[0]
        return IntentResult(top_intent, round(min(top_score, 1.0), 4), ranked[:5], result.method)

    def _apply_confidence_rules(self, result: IntentResult) -> IntentResult:
        if result.intent in {"greeting", "farewell"}:
            return result

        if result.confidence < self.confidence_threshold:
            return IntentResult("fallback", result.confidence, result.alternatives, result.method)

        if len(result.alternatives) >= 2:
            first = result.alternatives[0][1]
            second = result.alternatives[1][1]
            if first - second < self.ambiguity_margin:
                return IntentResult("clarification", round(first, 4), result.alternatives[:3], result.method)

        return result

    def extract_entities(self, text: str) -> dict:
        """Extract useful entities from the user's message."""
        clean_text = self._normalize(text)
        entities = {}

        course_map = {
            "bsit": "BS Information Technology",
            "information technology": "BS Information Technology",
            "bscs": "BS Computer Science",
            "computer science": "BS Computer Science",
            "bscpe": "BS Computer Engineering",
            "computer engineering": "BS Computer Engineering",
            "bsba": "BS Business Administration",
            "business administration": "BS Business Administration",
            "bsa": "BS Accountancy",
            "accountancy": "BS Accountancy",
            "bsn": "BS Nursing",
            "nursing": "BS Nursing",
            "beed": "Bachelor of Elementary Education",
            "elementary education": "Bachelor of Elementary Education",
            "bsed": "Bachelor of Secondary Education",
            "secondary education": "Bachelor of Secondary Education",
            "stem": "STEM Strand",
            "abm": "ABM Strand",
            "humss": "HUMSS Strand",
            "gas": "GAS Strand",
        }
        for keyword, full_name in course_map.items():
            if re.search(r"\b" + re.escape(keyword) + r"\b", clean_text, re.IGNORECASE):
                entities["course"] = full_name
                break

        semester_patterns = [
            (r"\b(1st|first)\s+sem(?:ester)?\b", "1st Semester"),
            (r"\b(2nd|second)\s+sem(?:ester)?\b", "2nd Semester"),
            (r"\bsummer\b", "Summer"),
        ]
        for pattern, value in semester_patterns:
            if re.search(pattern, clean_text, re.IGNORECASE):
                entities["semester"] = value
                break

        year_match = re.search(
            r"\b(1st|2nd|3rd|4th|first|second|third|fourth)\s+year\b", clean_text, re.IGNORECASE)
        if year_match:
            entities["year_level"] = year_match.group(0)

        student_type_patterns = [
            (r"\btransferee|transfer student|transfer\b", "Transferee"),
            (r"\bnew student|freshman|first year applicant\b", "New Student"),
            (r"\breturning student|returnee\b", "Returning Student"),
        ]
        for pattern, value in student_type_patterns:
            if re.search(pattern, clean_text, re.IGNORECASE):
                entities["student_type"] = value
                break

        return entities

    def _build_clarification_reply(self, alternatives: List[Tuple[str, float]]) -> str:
        options = []
        for intent, _score in alternatives:
            if intent in CLARIFICATION_LABELS and intent not in [item[0] for item in options]:
                options.append((intent, CLARIFICATION_LABELS[intent]))
            if len(options) == 3:
                break

        if not options:
            return RESPONSES["fallback"]

        lines = [
            "I want to make sure I understood you correctly. Are you asking about:"]
        for index, (_intent, label) in enumerate(options, start=1):
            lines.append(f"{index}. {label}")
        lines.append(
            "\nPlease reply with the number or rephrase your question.")
        return "\n".join(lines)

    def _personalize_reply(self, reply: str, intent: str, entities: dict) -> str:
        prefixes = []
        if entities.get("course"):
            prefixes.append(f"You mentioned **{entities['course']}**.")
        if entities.get("semester"):
            prefixes.append(f"You asked about **{entities['semester']}**.")
        if entities.get("student_type"):
            prefixes.append(
                f"This seems to be for a **{entities['student_type']}**.")

        if prefixes and intent not in {"greeting", "farewell"}:
            return " ".join(prefixes) + "\n\n" + reply
        return reply

    def is_gibberish(self, text: str) -> bool:
        """Public wrapper — lets routes call gibberish detection without importing _is_gibberish directly."""
        return _is_gibberish(text)

    def get_fallback_reply(self, text: str) -> str:
        """
        Returns the right fallback reply based on input type:
        - Gibberish / meaningless  →  plain 'I didn't quite understand' message
        - Valid but out-of-scope   →  witty, human-feeling redirect (random pick)
        """
        if _is_gibberish(text):
            return RESPONSES["fallback"]
        return random.choice(OUT_OF_SCOPE_RESPONSES)

    def generate_response(self, text: str, db_context: Optional[dict] = None) -> dict:
        """
        Main method called by the backend routes.
        Returns reply, intent, confidence, entities, source, timestamp, and NLP method.
        """
        if _is_gibberish(text):
            entities = {}
            reply = RESPONSES["fallback"]
            logger.info(
                "NLP -> gibberish/non-context input rejected before intent matching.")
            return {
                "reply": reply,
                "intent": "fallback",
                "confidence": 0.0,
                "entities": entities,
                "alternatives": [],
                "source": "nlp_fallback_gibberish",
                "method": self._model_type,
                "timestamp": datetime.utcnow().isoformat(),
            }

        intent_result = self.detect_intent_details(text)
        intent = intent_result.intent
        entities = self.extract_entities(text)

        if db_context and db_context.get("answer"):
            reply = db_context["answer"]
            source = "database"
        elif intent == "clarification":
            reply = self._build_clarification_reply(intent_result.alternatives)
            source = "nlp_clarification"
        elif intent == "fallback":
            # ── Smart fallback: gibberish gets the plain message,
            #    real human questions get a witty out-of-scope reply. ──
            if _is_gibberish(text):
                reply = RESPONSES["fallback"]
                source = "nlp_fallback_gibberish"
            else:
                reply = random.choice(OUT_OF_SCOPE_RESPONSES)
                source = "nlp_fallback_out_of_scope"
        else:
            reply = RESPONSES.get(intent, RESPONSES["fallback"])
            source = "nlp_semantic"

        reply = self._personalize_reply(reply, intent, entities)

        logger.info(
            "NLP -> intent: %s | confidence: %.4f | method: %s | entities: %s",
            intent,
            intent_result.confidence,
            intent_result.method,
            entities,
        )

        return {
            "reply": reply,
            "intent": intent,
            "confidence": intent_result.confidence,
            "entities": entities,
            "alternatives": intent_result.alternatives,
            "source": source,
            "method": intent_result.method,
            "timestamp": datetime.utcnow().isoformat(),
        }
