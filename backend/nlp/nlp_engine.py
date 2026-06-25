"""
nlp_engine.py – NLP Module
Component 3: NLP Module

Handles:
- Intent detection (what the user wants)
- Entity extraction (key details from the message)
- Context-aware response generation using transformer-based models
- Fallback to keyword matching for simple queries
"""

import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Intent Definitions ────────────────────────────────────────────
# Each intent has keywords that trigger it
INTENT_PATTERNS = {
    "enrollment_inquiry": [
        "enroll", "enrollment", "register", "registration", "sign up",
        "how to apply", "apply", "application", "admit", "admission"
    ],
    "requirements_inquiry": [
        "requirement", "requirements", "documents", "document", "needed",
        "what to bring", "credentials", "form 138", "tor", "birth certificate",
        "id", "photo", "2x2"
    ],
    "course_inquiry": [
        "course", "courses", "program", "programs", "degree", "bsit",
        "bscs", "bscpe", "bsba", "bsn", "nursing", "engineering",
        "information technology", "computer science", "strand"
    ],
    "schedule_inquiry": [
        "schedule", "schedules", "class", "classes", "time", "timetable",
        "when", "subject", "subjects", "semester", "section"
    ],
    "tuition_inquiry": [
        "tuition", "fee", "fees", "payment", "cost", "price", "how much",
        "pay", "installment", "down payment", "miscellaneous"
    ],
    "scholarship_inquiry": [
        "scholarship", "scholarships", "scholar", "financial aid",
        "ched", "unifast", "free tuition", "grant", "assistance", "subsidy"
    ],
    "policy_inquiry": [
        "policy", "policies", "rules", "rule", "regulation", "regulations",
        "dress code", "uniform", "attendance", "absence", "absences",
        "conduct", "discipline", "code of conduct"
    ],
    "contact_inquiry": [
        "contact", "office", "registrar", "admin", "administration",
        "phone", "email", "address", "location", "where", "hotline",
        "facebook", "website", "reach"
    ],
    "greeting": [
        "hello", "hi", "hey", "good morning", "good afternoon",
        "good evening", "musta", "kamusta", "sup"
    ],
    "farewell": [
        "bye", "goodbye", "see you", "thank you", "thanks", "salamat",
        "paalam", "good night"
    ],
}

# ── Response Templates ────────────────────────────────────────────
RESPONSES = {
    "enrollment_inquiry": (
        "**Enrollment at ICCT Colleges**\n\n"
        "Here's how to enroll:\n"
        "1. Visit the ICCT Colleges campus or go to the official website.\n"
        "2. Fill out the Student Information Sheet (SIS).\n"
        "3. Submit your required documents to the Registrar's Office.\n"
        "4. Pay the enrollment/reservation fee at the Cashier.\n"
        "5. Claim your Class Schedule and School ID.\n\n"
        "**Enrollment periods:**\n"
        "- 1st Semester: June – July\n"
        "- 2nd Semester: November – December\n"
        "- Summer: March – April\n\n"
        "Would you like to know the specific requirements for enrollment?"
    ),
    "requirements_inquiry": (
        "**Enrollment Requirements at ICCT Colleges**\n\n"
        "For **New Students (College)**:\n"
        "- Original PSA Birth Certificate\n"
        "- Original Form 138 (Grade 12 Report Card) or Transcript of Records\n"
        "- Certificate of Good Moral Character\n"
        "- 2 pcs. 2x2 ID photos (white background)\n"
        "- Valid Government-Issued ID\n"
        "- Photocopy of all documents\n\n"
        "For **Transferees**:\n"
        "- Transcript of Records (TOR)\n"
        "- Certificate of Transfer Credential (Honorable Dismissal)\n"
        "- PSA Birth Certificate\n"
        "- 2 pcs. 2x2 ID photos\n\n"
        "Is there a specific course you're enrolling in? I can give more details!"
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
        "**Senior High School (SHS):**\n"
        "- STEM, ABM, HUMSS, GAS strands\n\n"
        "Would you like details about a specific course?"
    ),
    "schedule_inquiry": (
        "**Class Schedule Information**\n\n"
        "ICCT Colleges offers flexible scheduling:\n"
        "- **Morning classes:** 7:00 AM – 12:00 PM\n"
        "- **Afternoon classes:** 1:00 PM – 6:00 PM\n"
        "- **Evening classes:** 6:00 PM – 9:00 PM (select programs)\n\n"
        "Class schedules are assigned during enrollment based on your section.\n\n"
        "For your **specific class schedule**, please:\n"
        "1. Log in to the Student Portal\n"
        "2. Visit the Registrar's Office in person\n"
        "3. Contact your department secretary\n\n"
        "Do you need help with anything else about schedules?"
    ),
    "tuition_inquiry": (
        "**Tuition & Fees at ICCT Colleges**\n\n"
        "Tuition fees vary per course and year level. As a general guide:\n"
        "- **Per unit fee:** approximately ₱300 – ₱500/unit depending on the program\n"
        "- **Miscellaneous fees:** vary per semester\n\n"
        "**Payment Options:**\n"
        "- Full payment (with possible discount)\n"
        "- Installment basis (down payment + balance)\n"
        "- Scholarship / Financial aid deductions applied at enrollment\n\n"
        "For the **exact and updated fee schedule**, please visit the Cashier's Office "
        "or the official ICCT Colleges website, as fees may change per school year.\n\n"
        "Would you like to know about available scholarships?"
    ),
    "scholarship_inquiry": (
        "**Scholarships at ICCT Colleges**\n\n"
        "**Government Scholarships:**\n"
        "- **UniFAST / TDP** – Free tuition for qualified state-subsidized students\n"
        "- **CHED Scholarships** – Merit-based grants from CHED\n"
        "- **DSWD Assistance** – For financially disadvantaged students\n\n"
        "**Private / Institutional Scholarships:**\n"
        "- Academic scholarships (based on GWA / grades)\n"
        "- Athletic scholarships\n"
        "- Leadership / organizational scholarships\n\n"
        "**How to apply:**\n"
        "1. Visit the Scholarship / Student Affairs Office\n"
        "2. Submit required documents (grades, income certificate, ID)\n"
        "3. Attend the scholarship interview if required\n\n"
        "Would you like to know the requirements for a specific scholarship?"
    ),
    "policy_inquiry": (
        "**ICCT Colleges School Policies**\n\n"
        "**Attendance Policy:**\n"
        "- Maximum of 20% absences per subject per semester\n"
        "- Exceeding the limit may result in a grade of 5.0 (Failed)\n\n"
        "**Dress Code:**\n"
        "- Smart casual attire; school ID must be worn at all times\n"
        "- PE uniform required during PE classes\n\n"
        "**Academic Integrity:**\n"
        "- Cheating and plagiarism are strictly prohibited\n"
        "- Violations may lead to suspension or expulsion\n\n"
        "**Examination Policy:**\n"
        "- Prelim, Midterm, Semi-Finals, and Finals each semester\n"
        "- Permit must be settled before taking exams\n\n"
        "For the complete Code of Conduct, visit the Student Affairs Office."
    ),
    "contact_inquiry": (
        "**Contact ICCT Colleges**\n\n"
        "**Main Campus – Cainta, Rizal:**\n"
        "- 📍 Cainta, Rizal (along Ortigas Ave. Extension)\n"
        "- 📞 Contact the Registrar's Office during office hours\n"
        "- 🌐 Visit the official ICCT Colleges website\n"
        "- 📘 Facebook: ICCT Colleges Official Page\n\n"
        "**Office Hours:**\n"
        "- Monday – Friday: 8:00 AM – 5:00 PM\n"
        "- Saturday: 8:00 AM – 12:00 PM\n\n"
        "For urgent concerns, visit the campus in person or message their official Facebook page."
    ),
    "greeting": (
        "Hi there! 👋 Welcome to ICCT Colleges Support Bot!\n\n"
        "I'm here to help you with:\n"
        "- 🎓 Enrollment process\n"
        "- 📋 Admission requirements\n"
        "- 📚 Available courses\n"
        "- 🗓️ Class schedules\n"
        "- 💰 Tuition & fees\n"
        "- 🏅 Scholarships\n"
        "- 📜 School policies\n"
        "- 📞 Contact information\n\n"
        "What would you like to know today?"
    ),
    "farewell": (
        "You're welcome! 😊 Feel free to come back anytime you have questions. "
        "Good luck with your studies at ICCT Colleges! 🎓"
    ),
    "fallback": (
        "I'm sorry, I didn't quite understand that. 😅\n\n"
        "I can help you with the following topics:\n"
        "- Enrollment process & requirements\n"
        "- Courses and programs offered\n"
        "- Class schedules\n"
        "- Tuition fees & payment\n"
        "- Scholarships & financial aid\n"
        "- School rules and policies\n"
        "- Contact & office information\n\n"
        "Could you rephrase your question or choose a topic above?"
    ),
}


class NLPEngine:
    """
    NLP Engine for the ICCT Colleges Chatbot.

    Uses keyword/pattern-based intent detection as the primary layer,
    with hooks for plugging in a transformer-based model (e.g. BERT,
    DistilBERT via HuggingFace) as a secondary classifier.
    """

    def __init__(self):
        self._ready = False
        self._load_model()

    def _load_model(self):
        """
        Load NLP resources.
        Extend this method to load a HuggingFace transformer model, e.g.:
            from transformers import pipeline
            self.classifier = pipeline('text-classification', model='distilbert-base-uncased')
        """
        try:
            # Compile regex patterns for each intent (fast keyword matching)
            self._patterns = {}
            for intent, keywords in INTENT_PATTERNS.items():
                pattern = r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b'
                self._patterns[intent] = re.compile(pattern, re.IGNORECASE)

            self._ready = True
            logger.info("NLPEngine: keyword patterns loaded successfully.")
        except Exception as e:
            logger.error(f"NLPEngine: failed to load — {e}")
            self._ready = False

    def is_ready(self):
        return self._ready

    def detect_intent(self, text: str) -> str:
        """
        Detect the user's intent from their message.
        Returns the intent name (str) or 'fallback'.
        """
        if not text or not text.strip():
            return "fallback"

        scores = {}
        for intent, pattern in self._patterns.items():
            matches = pattern.findall(text)
            if matches:
                scores[intent] = len(matches)

        if not scores:
            return "fallback"

        # Return the intent with the most keyword matches
        return max(scores, key=scores.get)

    def extract_entities(self, text: str) -> dict:
        """
        Extract key entities from the user's message.
        Returns a dict of entity_type -> value.

        Extend this to use spaCy NER or a HuggingFace NER model.
        """
        entities = {}

        # Course name detection
        course_map = {
            "bsit": "BS Information Technology",
            "bscs": "BS Computer Science",
            "bscpe": "BS Computer Engineering",
            "bsba": "BS Business Administration",
            "bsa":  "BS Accountancy",
            "bsn":  "BS Nursing",
            "beed": "Bachelor of Elementary Education",
            "bsed": "Bachelor of Secondary Education",
        }
        for abbr, full in course_map.items():
            if re.search(r'\b' + abbr + r'\b', text, re.IGNORECASE):
                entities["course"] = full
                break

        # Semester detection
        if re.search(r'\b(1st|first)\s+semester\b', text, re.IGNORECASE):
            entities["semester"] = "1st Semester"
        elif re.search(r'\b(2nd|second)\s+semester\b', text, re.IGNORECASE):
            entities["semester"] = "2nd Semester"

        # Year level detection
        year_match = re.search(r'\b(1st|2nd|3rd|4th|first|second|third|fourth)\s+year\b', text, re.IGNORECASE)
        if year_match:
            entities["year_level"] = year_match.group(0)

        return entities

    def generate_response(self, text: str, db_context: dict = None) -> dict:
        """
        Main method called by the back-end routes.
        Returns a dict with 'reply', 'intent', and 'entities'.

        db_context: optional dict of data fetched from the database
                    to enrich the response.
        """
        intent   = self.detect_intent(text)
        entities = self.extract_entities(text)

        # If database returned specific data, prefer it over the template
        if db_context and db_context.get("answer"):
            reply = db_context["answer"]
        else:
            reply = RESPONSES.get(intent, RESPONSES["fallback"])

        # Personalize reply if entities were found
        if entities.get("course") and intent == "course_inquiry":
            reply = f"You asked about **{entities['course']}**.\n\n" + reply

        logger.info(f"NLP → intent: {intent} | entities: {entities}")

        return {
            "reply":    reply,
            "intent":   intent,
            "entities": entities,
            "source":   "database" if (db_context and db_context.get("answer")) else "nlp_template",
            "timestamp": datetime.utcnow().isoformat()
        }
