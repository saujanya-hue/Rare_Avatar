"""Privacy Safeguards, Anti-Memorization, and Re-Identification Auditing."""
import re
from typing import List, Tuple, Dict, Any
from app.schemas.patient import SyntheticPatientSpecification
from app.schemas.validation import PrivacyCheckResult

# Representative literature case report reference summaries (simulating public clinical case archives)
REFERENCE_PUBLISHED_CASES = [
    {
        "case_id": "LIT-CASE-WD-2014-01",
        "disease_id": "wilson_disease",
        "age": 19,
        "sex": "Female",
        "ceruloplasmin": 5.2,
        "urinary_copper": 215.0,
        "ast": 160.0,
        "narrative": "A 19-year-old female university student presented with progressive handwriting deterioration and bilateral hand tremor."
    },
    {
        "case_id": "LIT-CASE-FD-2016-03",
        "disease_id": "fabry_disease",
        "age": 28,
        "sex": "Male",
        "lyso_gb3": 54.0,
        "alpha_gal": 0.2,
        "narrative": "A 28-year-old male with severe episodic burning pain in the extremities triggered by exercise and hot baths."
    },
    {
        "case_id": "LIT-CASE-GD-2018-02",
        "disease_id": "gaucher_disease",
        "age": 22,
        "sex": "Male",
        "lyso_gb1": 140.0,
        "platelets": 55.0,
        "narrative": "A 22-year-old male evaluated for chronic left upper quadrant fullness, recurrent epistaxis, and bilateral knee pain."
    }
]


class PrivacyAuditor:
    def _extract_ngrams(self, text: str, n: int = 4) -> set:
        words = [w.lower() for w in re.findall(r'\b[a-z]{3,}\b', text)]
        if len(words) < n:
            return set()
        return set(tuple(words[i:i + n]) for i in range(len(words) - n + 1))

    def audit_privacy(self, patient: SyntheticPatientSpecification) -> Tuple[List[PrivacyCheckResult], float, float]:
        results = []

        # 1. Lexical N-Gram Memorization Audit
        # Check generated clinical notes against reference published literature narratives
        combined_notes = " ".join([note.hpi + " " + note.chief_complaint for note in patient.clinical_notes])
        gen_ngrams = self._extract_ngrams(combined_notes, n=4)

        max_ngram_overlap = 0.0
        worst_ref_id = "None"

        for ref in REFERENCE_PUBLISHED_CASES:
            ref_ngrams = self._extract_ngrams(ref["narrative"], n=4)
            if not ref_ngrams or not gen_ngrams:
                continue
            intersection = gen_ngrams.intersection(ref_ngrams)
            overlap = len(intersection) / float(len(gen_ngrams))
            if overlap > max_ngram_overlap:
                max_ngram_overlap = overlap
                worst_ref_id = ref["case_id"]

        ngram_passed = max_ngram_overlap < 0.20
        results.append(PrivacyCheckResult(
            check_name="Literature N-Gram Lexical Memorization Audit",
            metric="Max 4-Gram Overlap Coefficient",
            threshold=0.20,
            computed_score=round(max_ngram_overlap, 3),
            passed=ngram_passed,
            details=(
                f"Generated clinical narrative evaluated against indexed reference case reports. "
                f"Peak overlap={round(max_ngram_overlap*100, 1)}% with {worst_ref_id}. Verbatim memorization check: {'PASSED' if ngram_passed else 'ALERT'}."
            )
        ))

        # 2. Nearest-Neighbor Clinical Attribute Distance Check
        # Ensure avatar does not duplicate a real patient's multi-attribute fingerprint
        min_dist = 999.0
        nearest_case_id = "None"

        for ref in REFERENCE_PUBLISHED_CASES:
            if ref["disease_id"] != patient.disease.disease_id:
                continue

            # Normalized distance across age and sex
            age_dist = abs(patient.demographics.age_years - ref["age"]) / 50.0
            sex_dist = 0.0 if patient.demographics.biological_sex == ref["sex"] else 0.5
            dist = (age_dist**2 + sex_dist**2)**0.5
            if dist < min_dist:
                min_dist = dist
                nearest_case_id = ref["case_id"]

        if min_dist == 999.0:
            min_dist = 1.0  # Default safe distance if no same-disease reference case

        dist_passed = min_dist >= 0.15
        results.append(PrivacyCheckResult(
            check_name="Nearest-Neighbor Reference Patient Attribute Distance",
            metric="Normalized Euclidean Feature Distance",
            threshold=0.15,
            computed_score=round(min_dist, 3),
            passed=dist_passed,
            details=(
                f"Evaluated normalized feature space distance against reference real-patient cases. "
                f"Nearest reference case: {nearest_case_id} (distance={round(min_dist, 3)}). Identity cloning check: {'PASSED' if dist_passed else 'ALERT'}."
            )
        ))

        return results, max_ngram_overlap, min_dist


privacy_auditor = PrivacyAuditor()
