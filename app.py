from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import json
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='/')
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

# Email greetings and closings for different tones
TONE_TEMPLATES = {
    "Formal": {
        "greeting": "Dear Sir/Madam,",
        "closing": "Best regards,",
        "formal_words": {
            "need": "require", "want": "desire", "hi": "greetings",
            "thanks": "thank you", "ok": "acceptable", "get": "obtain"
        }
    },
    "Friendly": {
        "greeting": "Hi there!",
        "closing": "Cheers,",
        "friendly_words": {
            "require": "need", "desire": "want", "request": "ask",
            "obtain": "get", "sincerely": "truly"
        }
    },
    "Apology": {
        "greeting": "Dear Sir/Madam,",
        "closing": "I sincerely apologize for any inconvenience caused.",
        "apology_words": {"problem": "issue", "bad": "unfortunate", "sorry": "sincerely apologize"}
    },
    "Request": {
        "greeting": "Hello,",
        "closing": "I would greatly appreciate your assistance.",
        "request_words": {"need": "kindly request", "want": "humbly request"}
    },
    "Follow-up": {
        "greeting": "Hello,",
        "closing": "I look forward to your response.",
        "followup_words": {"waiting": "awaiting", "check": "follow up on"}
    },
    "Job Application": {
        "greeting": "Dear Hiring Manager,",
        "closing": "I look forward to discussing this opportunity with you.",
        "job_words": {"want": "am interested in", "good": "excellent", "experienced": "well-versed"}
    }
}

EMAIL_TEMPLATES = {
    "Job Application": {
        "template": "I am writing to express my strong interest in the [POSITION] role at [COMPANY]. With my experience in [SKILLS], I am confident I can contribute significantly to your team. I have attached my resume and would welcome the opportunity to discuss how I can help achieve your goals.",
        "subject": "Application for [POSITION] Position"
    },
    "Leave Request": {
        "template": "I am writing to request leave from [START_DATE] to [END_DATE]. I have ensured all my pending tasks are completed and will brief my team before my absence. I appreciate your consideration of this request.",
        "subject": "Leave Request - [START_DATE] to [END_DATE]"
    },
    "Complaint Email": {
        "template": "I am writing to bring to your attention a concern regarding [ISSUE]. This matter has affected [IMPACT] and requires your immediate attention. I trust we can work towards a amicable resolution.",
        "subject": "Urgent: Issue Regarding [ISSUE]"
    },
    "Meeting Request": {
        "template": "I would like to schedule a meeting with you to discuss [TOPIC]. I believe a discussion would be beneficial for [REASON]. Would you be available on [DATE] at [TIME]? Please let me know your availability.",
        "subject": "Meeting Request: [TOPIC]"
    },
    "Thank You Mail": {
        "template": "I wanted to express my sincere gratitude for [REASON]. Your [ACTION] has made a significant difference and is greatly appreciated. Thank you once again for your support and guidance.",
        "subject": "Thank You for [REASON]"
    },
    "Cold Email": {
        "template": "I hope this email finds you well. I came across your profile and was impressed by [ACHIEVEMENT]. I believe there could be valuable synergies between our organizations. I would love to explore potential opportunities for collaboration.",
        "subject": "Opportunity for Collaboration"
    },
    "Follow-Up Mail": {
        "template": "Following up on our previous conversation regarding [TOPIC], I wanted to check if you have had a chance to review [DOCUMENT]. I am happy to provide any additional information you may need.",
        "subject": "Follow-up: [TOPIC]"
    }
}

def correct_grammar(text):
    """Apply basic grammar corrections"""
    # Common grammar fixes
    text = re.sub(r'\b(a)\s+([aeiou])', r'an \2', text, flags=re.IGNORECASE)
    text = re.sub(r'\btheir\s+is\b', 'there is', text, flags=re.IGNORECASE)
    text = re.sub(r'\byour\s+(are|is)\b', 'you\'re', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+,', ',', text)
    text = re.sub(r'\s+\.', '.', text)
    text = re.sub(r'([!?.])([A-Za-z])', r'\1 \2', text)
    return text

def restructure_sentences(text):
    """Improve sentence structure"""
    sentences = text.split('.')
    restructured = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Add capital letter
        sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
        restructured.append(sentence)
    
    return '. '.join(restructured) + ('.' if text.endswith('.') else '')

def enhance_politeness(text):
    """Make text more polite"""
    politeness_map = {
        r'\bcan you\b': 'could you please',
        r'\bmust\b': 'should',
        r'\byou have to\b': 'you may need to',
        r'\byou need to\b': 'you might consider',
        r'\bdont\b': 'do not',
        r'\bcant\b': 'cannot',
    }
    
    result = text
    for pattern, replacement in politeness_map.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result

def adjust_length(text, length_type):
    """Adjust email length"""
    if length_type == "Short":
        sentences = text.split('.')
        text = '.'.join(sentences[:max(1, len(sentences)//3)]) + '.'
    elif length_type == "Detailed":
        words = text.split()
        if len(words) < 150:
            text += "\n\nPlease find below additional details and context. I believe this information will help you better understand the situation and make an informed decision."
    
    return text

def calculate_readability_score(text):
    """Calculate readability score (0-100)"""
    words = len(text.split())
    sentences = len(text.split('.'))
    
    if sentences == 0:
        return 0
    
    avg_word_length = sum(len(word) for word in text.split()) / max(1, words)
    avg_sentence_length = words / max(1, sentences)
    
    # Flesch Kincaid style calculation
    score = 206.835 - 1.015 * avg_sentence_length - 84.6 * (avg_word_length / 5)
    score = max(0, min(100, score))
    
    return round(score, 1)

def calculate_politeness_score(text):
    """Calculate politeness meter (0-100)"""
    polite_words = ['please', 'thank', 'appreciate', 'kindly', 'would', 'could', 'sincerely', 'respect', 'regard', 'regard', 'value']
    rude_words = ['must', 'demand', 'require', 'stupid', 'bad', 'wrong', 'immediately', 'asap']
    
    text_lower = text.lower()
    polite_count = sum(1 for word in polite_words if word in text_lower)
    rude_count = sum(1 for word in rude_words if word in text_lower)
    
    score = (polite_count * 10) - (rude_count * 15)
    score = max(0, min(100, score))
    
    return max(0, min(100, score))

def detect_tone(text):
    """Detect the tone of the text"""
    text_lower = text.lower()
    
    tone_indicators = {
        "Formal": ['sir', 'madam', 'hereby', 'regards', 'sincerely', 'respectfully'],
        "Friendly": ['hi', 'hey', 'cheers', 'thanks', 'great', 'awesome', 'brilliant'],
        "Apology": ['sorry', 'apologize', 'apologies', 'regret', 'unfortunate'],
        "Request": ['request', 'please', 'kindly', 'could', 'would'],
        "Angry": ['angry', 'furious', 'unacceptable', 'ridiculous', 'terrible']
    }
    
    scores = {}
    for tone, keywords in tone_indicators.items():
        scores[tone] = sum(1 for keyword in keywords if keyword in text_lower)
    
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "Neutral"

def format_email(text, tone, length='Medium', apply_grammar=True, apply_politeness=True):
    """Main email formatting function"""
    
    # Get tone template
    template = TONE_TEMPLATES.get(tone, TONE_TEMPLATES["Formal"])
    greeting = template["greeting"]
    closing = template["closing"]
    
    # Process text
    processed_text = text.strip()
    
    if apply_grammar:
        processed_text = correct_grammar(processed_text)
        processed_text = restructure_sentences(processed_text)
    
    if apply_politeness:
        processed_text = enhance_politeness(processed_text)
    
    # Adjust length
    processed_text = adjust_length(processed_text, length)
    
    # Add paragraph spacing
    paragraphs = processed_text.split('\n')
    formatted_body = '\n\n'.join(p.strip() for p in paragraphs if p.strip())
    
    # Final format
    signature = f"\n\nBest regards,"
    formatted = f"{greeting}\n\n{formatted_body}{signature}"
    
    return formatted

def generate_subject_line(text, tone):
    """Generate intelligent subject line"""
    words = text.split()
    
    # Find important words (longer, non-common words)
    important_words = [w for w in words if len(w) > 4 and w.lower() not in ['this', 'that', 'these', 'those', 'about', 'email']]
    
    if tone == "Apology":
        return f"Apology and Resolution: {important_words[0] if important_words else 'Important Matter'}"
    elif tone == "Request":
        return f"Request for {important_words[0] if important_words else 'Your Assistance'}"
    elif tone == "Follow-up":
        return f"Follow-up: {important_words[0] if important_words else 'Previous Discussion'}"
    elif tone == "Job Application":
        return "Application for Position - Attached Resume"
    else:
        subject = ' '.join(important_words[:3]) if important_words else "Email"
        return subject[:50]

@app.route("/format", methods=["POST"])
def format_api():
    data = request.json
    text = data.get("text", "")
    tone = data.get("tone", "Formal")
    length = data.get("length", "Medium")
    apply_grammar = data.get("grammar", True)
    apply_politeness = data.get("politeness", True)
    
    if not text.strip():
        return jsonify({"error": "Text cannot be empty"}), 400
    
    formatted = format_email(text, tone, length, apply_grammar, apply_politeness)
    subject = generate_subject_line(text, tone)
    
    return jsonify({
        "formatted": formatted,
        "subject": subject,
        "metadata": {
            "word_count": len(text.split()),
            "readability_score": calculate_readability_score(formatted),
            "politeness_score": calculate_politeness_score(formatted),
            "detected_tone": detect_tone(text)
        }
    })

@app.route("/templates", methods=["GET"])
def get_templates():
    """Return available email templates"""
    return jsonify(EMAIL_TEMPLATES)

@app.route("/analyze", methods=["POST"])
def analyze_email():
    """Analyze email metrics"""
    data = request.json
    text = data.get("text", "")
    
    if not text.strip():
        return jsonify({"error": "Text cannot be empty"}), 400
    
    return jsonify({
        "readability_score": calculate_readability_score(text),
        "politeness_score": calculate_politeness_score(text),
        "detected_tone": detect_tone(text),
        "word_count": len(text.split()),
        "sentence_count": len(text.split('.'))
    })

if __name__ == "__main__":
    app.run(debug=True)
