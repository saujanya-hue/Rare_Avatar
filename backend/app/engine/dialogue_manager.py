"""State-Grounded Clinical Dialogue Manager for Interactive Patient Avatar."""
import re
from typing import List, Tuple
from app.schemas.patient import SyntheticPatientSpecification
from app.schemas.simulation import DialogueResponse


class DialogueManager:
    def process_inquiry(self, patient: SyntheticPatientSpecification, query_text: str) -> DialogueResponse:
        q_clean = query_text.lower().strip()

        entities_found = []
        revealed_findings = []
        citations = []
        uncertainty_note = None

        # 1. Check for Investigation Orders in text
        if any(term in q_clean for term in ["order", "check lab", "run test", "get mri", "perform scan", "take an x-ray", "do ultrasound"]):
            intent = "INVESTIGATION_ORDER_INTENT"
            avatar_response = (
                "As the patient, I don't run tests myself, but you can place the diagnostic order through the Diagnostic Order Workstation on the right. "
                "Once ordered, my laboratory or imaging reports will be finalized and added to my active medical chart."
            )
            return DialogueResponse(
                patient_id=patient.patient_id,
                query_text=query_text,
                avatar_response=avatar_response,
                intent_detected=intent,
                clinical_entities_identified=["Order Request"],
                revealed_findings=[],
                uncertainty_statement="Diagnostic tests must be explicitly ordered before objective findings are disclosed.",
                evidence_citations=[],
                simulation_month=patient.current_simulation_month
            )

        # 2. Check for Onset / Duration / Timeline Questions (e.g. "how many days", "how long", "when did it start", "since when")
        duration_patterns = [
            "how many days", "how many weeks", "how many months", "how many years", "how long",
            "when did it start", "when did this start", "when did you start", "since when",
            "how long have you", "duration", "how long has this", "when was the onset",
            "first notice", "first noticed", "from when", "since how long",
            "days are you having", "days you have", "days have you", "weeks have you", "months have you"
        ]
        if any(term in q_clean for term in duration_patterns):
            intent = "ONSET_AND_DURATION_INQUIRY"
            
            # Find earliest symptom onset
            earliest_sym = min(patient.symptoms, key=lambda s: s.onset_month, default=None)
            earliest_month = earliest_sym.onset_month if earliest_sym else 3
            estimated_days = earliest_month * 30
            recent_weeks = max(2, int(earliest_month * 1.5))

            active_symptoms = [s for s in patient.symptoms if s.onset_month <= patient.current_simulation_month]
            if not active_symptoms and earliest_sym:
                active_symptoms = [earliest_sym]

            for s in active_symptoms:
                s.is_revealed = True
                revealed_findings.append(s.name)
                citations.extend(s.evidence_ids)

            avatar_response = (
                f"Doctor, I've had these symptoms for about {earliest_month} months now (roughly {estimated_days} days). "
                f"It started very gradually around month {earliest_month} with mild, subtle fatigue and feeling 'off'. "
                f"However, over the last {recent_weeks} to {recent_weeks + 2} weeks, the problems have escalated significantly, "
                f"which is what really prompted me to seek medical evaluation."
            )
            uncertainty_note = "Exact day of symptom onset is based on subjective patient recall and estimated timeline."

            return DialogueResponse(
                patient_id=patient.patient_id,
                query_text=query_text,
                avatar_response=avatar_response,
                intent_detected=intent,
                clinical_entities_identified=["Symptom Duration", "Onset Timeline"],
                revealed_findings=revealed_findings,
                uncertainty_statement=uncertainty_note,
                evidence_citations=list(set(citations)),
                simulation_month=patient.current_simulation_month
            )

        # 3. Check for Progression / Severity / Daily Life Impact
        progression_patterns = [
            "getting worse", "worsen", "progressing", "how severe", "affect your work", "daily life",
            "daily activities", "can you work", "how does it feel", "difficulty walking", "affect your daily",
            "impact on your life", "interference"
        ]
        if any(term in q_clean for term in progression_patterns):
            intent = "PROGRESSION_AND_SEVERITY_INQUIRY"
            severe_syms = [s for s in patient.symptoms if s.severity_score >= 6.0 and s.onset_month <= patient.current_simulation_month]
            for s in severe_syms:
                s.is_revealed = True
                revealed_findings.append(s.name)
                citations.extend(s.evidence_ids)

            names_str = ", ".join([s.name.lower() for s in severe_syms]) if severe_syms else "my symptoms"
            avatar_response = (
                f"Yes, it has been steadily getting worse over time. At first I thought I was just overworked, but now {names_str} "
                f"is having a major impact on my daily routine. I find myself having to stop and rest frequently, "
                f"and simple tasks that used to be second nature now require enormous concentration."
            )
            uncertainty_note = "Severity grading reflects patient-reported functional impairment."

            return DialogueResponse(
                patient_id=patient.patient_id,
                query_text=query_text,
                avatar_response=avatar_response,
                intent_detected=intent,
                clinical_entities_identified=["Functional Impairment", "Disease Progression"],
                revealed_findings=revealed_findings,
                uncertainty_statement=uncertainty_note,
                evidence_citations=list(set(citations)),
                simulation_month=patient.current_simulation_month
            )

        # 4. Check for Family / Genetic History
        if any(term in q_clean for term in ["family", "parent", "mother", "father", "brother", "sister", "uncle", "genetics", "relative", "ancestry", "heritage"]):
            intent = "FAMILY_HISTORY_INQUIRY"
            if patient.disease.disease_id == "wilson_disease":
                avatar_response = (
                    "My parents are both alive and healthy with no history of liver or tremor issues, though my mother mentions they may be distant cousins. "
                    "None of my siblings or immediate relatives have ever been diagnosed with liver or brain conditions."
                )
                citations = ["EASL_2012_GUIDELINES", "LANCET_2015_WILSON"]
            elif patient.disease.disease_id == "fabry_disease":
                avatar_response = (
                    "My mother has had mild kidney issues and unexplained episodes of burning hand pain, and my maternal uncle tragically passed away in his late forties "
                    "from sudden heart failure after having been on hemodialysis. Nobody had a clear genetic name for it at that time."
                )
                citations = ["ORPHANET_2010_FABRY"]
            else:  # Gaucher
                avatar_response = (
                    "Our family is of Ashkenazi Jewish heritage on both sides. My maternal aunt had a history of an enlarged spleen and easy bruising, "
                    "and my grandfather struggled with chronic deep bone aches and needed an early hip replacement."
                )
                citations = ["REGISTRY_2000_GAUCHER"]

            return DialogueResponse(
                patient_id=patient.patient_id,
                query_text=query_text,
                avatar_response=avatar_response,
                intent_detected=intent,
                clinical_entities_identified=["Family Pedigree"],
                revealed_findings=["Inherited Risk Factor"],
                uncertainty_statement="Family report is based on patient recall and lacks direct verified genetic records.",
                evidence_citations=citations,
                simulation_month=patient.current_simulation_month
            )

        # 5. Check for Medication / Treatment
        if any(term in q_clean for term in ["medication", "medicine", "treatment", "pill", "therapy", "drug", "taking", "prescribe", "prescription"]):
            intent = "TREATMENT_INQUIRY"
            if patient.active_treatment:
                avatar_response = f"I am currently receiving: {patient.active_treatment}. I'm following the protocol as closely as possible."
            else:
                avatar_response = "I am currently not taking any targeted rare-disease medications. I've only tried over-the-counter painkillers and vitamins, but they haven't provided any noticeable relief."

            return DialogueResponse(
                patient_id=patient.patient_id,
                query_text=query_text,
                avatar_response=avatar_response,
                intent_detected=intent,
                clinical_entities_identified=["Current Medications"],
                revealed_findings=[],
                uncertainty_statement="Patient adherence cannot be fully verified without drug monitoring.",
                evidence_citations=[],
                simulation_month=patient.current_simulation_month
            )

        # 6. Check for General Symptom / Problem Queries (e.g. "what symptoms", "what problem", "what is wrong", "what brings you")
        general_sym_queries = [
            "what symptoms", "what problem", "what problems", "what is wrong", "what are your symptoms",
            "what brings you", "tell me about your", "describe your problem", "what is bothering you",
            "what seems to be", "what is the issue"
        ]
        if any(term in q_clean for term in general_sym_queries):
            intent = "GENERAL_SYMPTOM_EXPLORATION"
            active_symptoms = [s for s in patient.symptoms if s.onset_month <= patient.current_simulation_month]
            for s in active_symptoms:
                s.is_revealed = True
                revealed_findings.append(s.name)
                citations.extend(s.evidence_ids)

            sym_phrases = [f"{s.name.lower()} (which began around month {s.onset_month})" for s in active_symptoms]
            sym_text = ", ".join(sym_phrases)

            avatar_response = (
                f"Doctor, the main issues I've been struggling with are: {sym_text}. "
                f"It began insidiously, but over the last few months it has really been worsening and making it very difficult to function normally."
            )

            return DialogueResponse(
                patient_id=patient.patient_id,
                query_text=query_text,
                avatar_response=avatar_response,
                intent_detected=intent,
                clinical_entities_identified=["Primary Manifestations"],
                revealed_findings=revealed_findings,
                uncertainty_statement="Patient-reported presentation summary.",
                evidence_citations=list(set(citations)),
                simulation_month=patient.current_simulation_month
            )

        # 7. Check for specific clinical symptom keywords
        # Expand synonym mapping for symptoms
        symptom_synonyms = {
            "wd_sym_tremor": ["tremor", "tremors", "shake", "shaking", "writing", "hand", "hands", "finger", "posture"],
            "wd_sym_jaundice": ["jaundice", "yellow", "yellowing", "eyes", "sclera", "icterus", "tea-colored", "dark urine"],
            "wd_sym_fatigue": ["fatigue", "tired", "lethargy", "exhausted", "weakness", "energy"],
            "wd_sym_dysarthria": ["speech", "slur", "slurring", "talking", "articulation", "voice"],
            "wd_sym_dystonia": ["face", "grimace", "smile", "mood", "dystonia", "spasm"],
            "wd_sym_ruq_pain": ["belly", "stomach", "abdomen", "abdominal", "right side", "ruq", "liver pain"],
            "fd_sym_acroparesthesia": ["pain", "burning", "feet", "tingling", "hands and feet", "crisis", "crises"],
            "fd_sym_hypohidrosis": ["sweat", "sweating", "heat", "hot", "exercise", "flush", "flushing"],
            "fd_sym_angiokeratoma": ["skin", "spots", "rash", "red spots", "purple", "papules", "umbilicus", "groin"],
            "fd_sym_cardiac": ["heart", "chest", "breath", "shortness of breath", "dyspnea", "palpitations"],
            "gd_sym_splenomegaly": ["belly", "swelling", "stomach", "spleen", "satiety", "full", "fullness", "left side"],
            "gd_sym_bleeding": ["bleed", "bleeding", "bruise", "bruising", "nosebleed", "epistaxis", "petechiae"],
            "gd_sym_bone_pain": ["bone", "bones", "ache", "aches", "legs", "thighs", "knees", "skeletal"]
        }

        symptom_matches = []
        for sym in patient.symptoms:
            # Direct word matching
            sym_words = [w.lower() for w in re.findall(r'\b[a-z]{4,}\b', sym.name)]
            synonyms = symptom_synonyms.get(sym.symptom_id, [])
            
            matched = False
            if any(w in q_clean for w in sym_words):
                matched = True
            elif any(syn in q_clean for syn in synonyms):
                matched = True
            elif any(c in q_clean for c in sym.category.lower().split() if len(c) > 3):
                matched = True

            if matched:
                symptom_matches.append(sym)
                entities_found.append(sym.name)

        if symptom_matches:
            intent = "SYMPTOM_EXPLORATION"
            responses = []
            for m in symptom_matches:
                m.is_revealed = True
                revealed_findings.append(m.name)
                responses.append(
                    f"Regarding my {m.name.lower()}: I first noticed it around month {m.onset_month} of my illness. {m.description}"
                )
                citations.extend(m.evidence_ids)

            avatar_response = " ".join(responses)
            uncertainty_note = "Symptom severity and recall subject to patient subjective perception."

            return DialogueResponse(
                patient_id=patient.patient_id,
                query_text=query_text,
                avatar_response=avatar_response,
                intent_detected=intent,
                clinical_entities_identified=entities_found,
                revealed_findings=revealed_findings,
                uncertainty_statement=uncertainty_note,
                evidence_citations=list(set(citations)),
                simulation_month=patient.current_simulation_month
            )

        # 8. Default Natural First-Person Response
        intent = "GENERAL_CHIEF_COMPLAINT"
        # Formulate a natural first-person conversational response grounded in revealed symptoms
        active_symptoms = [s for s in patient.symptoms if s.is_revealed or s.onset_month <= patient.current_simulation_month]
        top_syms = [s.name.lower() for s in active_symptoms[:2]]
        sym_desc = " and ".join(top_syms) if top_syms else "feeling progressively unwell"
        
        avatar_response = (
            f"Doctor, my main trouble is {sym_desc}. "
            f"It's been troubling me for the past several months, and it has been getting noticeably harder to cope with each week. "
            f"I really hope you can help figure out what's causing it."
        )

        return DialogueResponse(
            patient_id=patient.patient_id,
            query_text=query_text,
            avatar_response=avatar_response,
            intent_detected=intent,
            clinical_entities_identified=["Chief Complaint"],
            revealed_findings=[],
            uncertainty_statement="General patient spontaneous narrative.",
            evidence_citations=[],
            simulation_month=patient.current_simulation_month
        )


dialogue_manager = DialogueManager()
