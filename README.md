# RareAvatar — Synthetic Rare-Disease Patient Avatars
**Multimodal Clinical Simulation, Trainee Education, and Diagnostic AI Adversarial Arena**

---

## 1. Project Overview & Clinical Mission

Clinicians rarely encounter rare diseases during standard residency or fellowship training, yet must make time-critical decisions when such cases present in acute practice—often without immediate access to subspecialty genetics clinics or representative multi-institutional case repositories. Traditional textbook vignettes and static case reports fail to capture the full spectrum of demographic heterogeneity, longitudinal disease progression, and counterfactual therapeutic responses. Furthermore, as diagnostic AI algorithms emerge to assist in rare-disease triage, evaluating their clinical reliability under real-world clinical variance, missing data, and atypical presentations is vital.

**RareAvatar** is a state-of-the-art multimodal generative AI platform that synthesizes clinically grounded, state-persistent rare-disease patient avatars for two primary missions:
1. **Interactive Clinician & Trainee Education:** Active inquiry consoles, blinded diagnostic mystery challenges, longitudinal disease progression, and counterfactual what-if therapeutic explorations.
2. **Diagnostic AI Adversarial Arena & Stress-Testing:** Automated, reproducible benchmark harnesses and breaking-point delta finders that stress-test diagnostic AI models under clinically valid perturbations without generating physiologically impossible patients.

---

## 2. Core Architectural Principles & Guardrails

* **Real Biomedical Evidence Grounding:** All disease models and biomarker distributions are strictly anchored in peer-reviewed literature with verified PubMed IDs, clinical practice guidelines (EASL, European Consensus Guidelines, ACMG, Pastores et al., Ortiz et al.), and official OMIM records.
* **Separation of Evidence and Uncertainty:** Epistemic uncertainty (evidence density and guideline consensus level) is decoupled from aleatoric uncertainty (intrinsic biological variance and analytical instrument precision).
* **State Persistence vs Conversational Memory:** Patient state is held in an immutable, structured pathophysiological state vector rather than relying on stochastic LLM conversation memory, preventing clinical contradictions across interactions.
* **Anti-Memorization & Privacy Safety:** Built-in auditing checks 4-gram lexical overlap against reference literature case reports and calculates normalized multi-attribute distance to ensure synthetic avatars do not replicate real-patient records.
* **Honest Clinical Validation Labels:** Automated deterministic physiological and cross-modal consistency checks are explicitly labeled as **Algorithmic Rule Checks Passed** with **Formal Board-Certified Clinical Expert Review: Pending**.
* **Blinded Model Evaluation:** Evaluated diagnostic models strictly receive blinded inputs (demographics, reported symptoms, lab values, and imaging summaries). Reference labels, ground truth OMIM codes, and simulation states are strictly isolated from inference payloads.
* **Clinical White Workstation Theme:** Clean, modern hospital-grade white aesthetic default with seamless dark mode toggle.

---

## 3. Supported Rare-Disease Pathophysiological Models

| Disease | Genetic Basis & Identifiers | Key Phenotypes & Biomarkers | Imaging Findings & Modalities | Targeted Therapies |
| :--- | :--- | :--- | :--- | :--- |
| **Wilson Disease** | *ATP7B* mutation<br>OMIM #277900<br>Orpha: 905 | Serum Ceruloplasmin (<20 mg/dL)<br>24h Urinary Copper (>50 ug/24h)<br>Elevated AST/ALT & Thrombocytopenia | Brain MRI (Face of Giant Panda sign)<br>Slit-Lamp (Kayser-Fleischer rings)<br>Abdominal US (Micronodular cirrhosis) | D-Penicillamine / Trientine chelation<br>Maintenance Zinc |
| **Fabry Disease** | *GLA* mutation (X-linked)<br>OMIM #301500<br>Orpha: 324 | Plasma Lyso-Gb3 (>0.8 ng/mL)<br>Alpha-Galactosidase A deficiency<br>Proteinuria (>500 mg/24h) | Cardiac MRI (Low native T1 mapping, inferolateral basal LGE, concentric LVH) | Recombinant Agalsidase beta ERT<br>Chaperone (Migalastat) |
| **Gaucher Disease Type 1** | *GBA1* mutation<br>OMIM #230800<br>Orpha: 355 | Plasma Lyso-Gb1 (>1.5 ng/mL)<br>Acid Beta-Glucosidase deficiency<br>Thrombocytopenia & Anemia | Bilateral Femur X-Ray (Erlenmeyer Flask deformity)<br>Abdominal US (Massive splenomegaly 12x MNV) | Recombinant Imiglucerase ERT<br>Substrate Reduction (Eliglustat) |

---

## 4. The 6 Advanced System Capabilities

### 1. Diagnostic AI Breaking Point Finder
* **Progressive Perturbation Search:** Systematically sweeps minimal adversarial perturbation delta ($\Delta$) across Gaussian lab noise, missing data masking, age shifts, or acute infection confounders.
* **Failure Modes Detected:**
  - `INCORRECT_PREDICTION`: Top-1 diagnosis flips away from ground truth.
  - `PREDICTION_INSTABILITY`: Prediction oscillates under minor variations.
  - `CONFIDENCE_COLLAPSE`: Confidence plummets by $\ge 35\%$ while retaining correct diagnosis.
* **Comparative Multi-Model Benchmarking:** Runs identical breaking-point sweeps across Reference Guideline Classifier, Mock Fragile Diagnostic AI, Mock Robust Diagnostic AI, and External HTTP Diagnostic APIs.

### 2. Clinical Consistency Guardian
* **5-Category Constraint Engine:**
  1. *Physiological Constraints:* Validates disease-specific biomarker bounds (e.g., ceruloplasmin $\le 20\text{ mg/dL}$ in Wilson disease, lyso-Gb3 elevation in Fabry).
  2. *Cross-Modal Concordance:* Verifies concordance between laboratory metrics, clinical symptoms, and radiological signs (e.g., neurological Wilson symptoms require Kayser-Fleischer rings and basal ganglia MRI findings).
  3. *Temporal Trajectory Consistency:* Enforces monotonic disease progression and non-decreasing organ damage under untreated conditions.
  4. *Treatment-Model Compatibility:* Ensures disease-specific response kinetics match established pharmacotherapy (e.g., urinary copper spikes under D-penicillamine, plasma lyso-Gb1 declines under Imiglucerase).
  5. *Evidence-Grounding Provenance:* Audits every abnormal finding against indexed PubMed literature and clinical guidelines.
* **Verdict Banner & Action Suggestions:** Displays `FULL_CLINICAL_CONCORDANCE`, `PROBABLE_CONCORDANCE_WITH_WARNINGS`, or `CRITICAL_INCONSISTENCIES_DETECTED` with specific recommended clinical actions.

### 3. Evidence Explorer
* **Literature Grounding Engine:** Indexed repository of verified PubMed literature (EASL 2012, ACMG 2020, Ferenci et al. 2003, Schiffmann et al. 2001, Pastores et al. 2004, Ortiz et al. 2018).
* **Patient Provenance Inspector:** Full provenance mapping for active patient avatars—linking every reported symptom, abnormal laboratory finding, imaging sign, and targeted therapy directly to its PMID, clinical guideline tier, and evidence strength.
* **Interactive Literature Search:** Filter by disease, biomarker, or keyword with direct external links to NCBI PubMed.

### 4. Clinical What-If Lab
* **Counterfactual Scenario Branching:** Fork patient simulation state at any point along the disease timeline into isolated, immutable deep-copied branches.
* **Intervention Protocols:**
  - Standard Guidelines Therapy (e.g., Trientine 1000 mg/day, Imiglucerase 60 U/kg).
  - High-Dose / Accelerated Therapy.
  - Subtherapeutic / Poor Adherence (e.g., 40% compliance).
  - Alternative Chaperone / Substrate Reduction Therapy.
  - Natural History (Untreated Progression).
* **Multi-Branch Comparative Analytics:** Advance branches independently (+3, +6, +12 months) and view side-by-side progression curves, comparative biomarker delta tables, and exportable JSON/CSV trajectories.

### 5. Clinical Mystery Mode
* **Blinded Trainee Diagnostic Challenge:** Three difficulty tiers:
  - *Beginner:* Typical presentation, key cardinal hallmarks present, $10,000 diagnostic budget.
  - *Intermediate:* Mild / early-stage presentation, partial symptoms, $7,500 diagnostic budget.
  - *Advanced:* Atypical presentation, borderline biomarkers, intercurrent confounders, $5,000 diagnostic budget.
* **Active Interactive Dialogue:** Natural language history taking (e.g., family history, occupational exposure, symptom onset).
* **Priced Investigation Catalog:** Selective ordering from 15+ serum, urinary, enzymatic, genetic, and imaging modalities with realistic turnaround times and cost accumulation.
* **Multifactorial Scoring & Unmasked Debriefing:** Evaluates diagnostic accuracy (0–100%), test selection efficiency, cardinal hallmarks identified vs. missed, and cost utilization, accompanied by a comprehensive clinical supervisor debriefing.

### 6. Synthetic Patient Population Lab
* **Demographically Configurable Cohorts:** Batch generation of synthetic cohorts with custom disease distributions (Wilson, Fabry, Gaucher), age intervals, sex ratios, and random seeds.
* **Automated Batch Consistency Auditing:** Executes the 5-Category Consistency Guardian across the entire cohort, computing batch pass rates and flagging outliers.
* **Arena Bridge & Dataset Export:** Instant one-click bridging of generated cohorts directly into the Diagnostic AI Adversarial Arena for batch stress-testing, along with exportable JSON/CSV datasets.

---

## 5. System Architecture & Directory Structure

```
RareAvatar (PS3)
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes_arena.py            # Diagnostic AI Adversarial Arena & batch runs
│   │   │   ├── routes_auth.py             # Trainee & Supervisor authentication & scoring
│   │   │   ├── routes_diagnostic.py       # Diagnostic evaluation & Breaking Point Finder
│   │   │   ├── routes_evidence.py         # Literature search, biomarker catalog & provenance
│   │   │   ├── routes_mystery.py          # Clinical Mystery Mode workflow & pricing
│   │   │   ├── routes_patients.py         # Avatar generation, retrieval & blinded trainee view
│   │   │   ├── routes_population.py       # Cohort generation, batch validation & export
│   │   │   ├── routes_simulation.py       # Longitudinal progression & interactive inquiry
│   │   │   ├── routes_validation.py       # Consistency Guardian (5 categories) & privacy audit
│   │   │   └── routes_what_if.py          # Counterfactual branching & comparative trajectories
│   │   ├── disease_models/                # Pathophysiological models (Wilson, Fabry, Gaucher)
│   │   │   ├── wilson_disease.py          # ATP7B kinetics, Kayser-Fleischer, basal ganglia MRI
│   │   │   ├── fabry_disease.py           # GLA deficiency, Lyso-Gb3, cardiac LGE, acroparesthesias
│   │   │   └── gaucher_disease.py         # GBA1 mutation, Lyso-Gb1, Erlenmeyer flask, splenomegaly
│   │   ├── engine/                        # Core simulation engines
│   │   │   ├── dialogue_manager.py        # Natural dialogue & intent-to-clinical response
│   │   │   ├── scenario_engine.py         # Dynamic longitudinal pathophysiological engine
│   │   │   ├── state_store.py             # Persistent patient repository
│   │   │   ├── what_if_lab.py             # Counterfactual branching & multi-branch comparison
│   │   │   └── mystery_mode.py            # Blinded challenge engine & scoring rubrics
│   │   ├── generators/
│   │   │   ├── patient_generator.py       # Seed-controlled multimodal synthetic avatars
│   │   │   └── population_lab.py          # Batch cohort generation & distribution sampling
│   │   ├── knowledge/
│   │   │   ├── disease_knowledge.py       # Clinical guidelines, thresholds & diagnostic criteria
│   │   │   └── evidence_catalog.py        # PubMed citations database & provenance linker
│   │   ├── schemas/                       # Comprehensive Pydantic v2 data models
│   │   │   ├── patient.py                 # Avatar state vectors, labs, imaging, modalities
│   │   │   ├── diagnostic.py              # Blinding schemas, Breaking Point requests & results
│   │   │   ├── arena.py                   # Adversarial configurations, sweeps & metrics
│   │   │   ├── validation.py              # Consistency Guardian 5-category verdicts
│   │   │   ├── what_if.py                 # Branch configs, states & trajectory reports
│   │   │   ├── mystery.py                 # Session views, investigation pricing & debriefings
│   │   │   ├── population.py              # Cohort configs, demographics & roster records
│   │   │   └── evidence.py                # Provenance items, citations & catalog schemas
│   │   ├── stress_testing/
│   │   │   ├── adversarial_arena.py       # Automated benchmark harness & failure categorization
│   │   │   ├── benchmark_runner.py        # Baseline, fragile & robust model evaluators
│   │   │   ├── perturbation_engine.py     # Constraint-aware noise, missingness & confounders
│   │   │   └── breaking_point_finder.py   # Progressive delta search & vulnerability bounds
│   │   ├── validation/
│   │   │   ├── consistency_checker.py     # Deterministic physiological validation
│   │   │   ├── consistency_guardian.py    # 5-category constraint guardian engine
│   │   │   └── privacy_auditor.py         # 4-gram memorization & differential privacy audit
│   │   └── main.py                        # Unified FastAPI application entrypoint
│   └── tests/                             # 53 comprehensive unit and integration tests
├── frontend/
│   ├── index.html                         # Unified single-page clinical application
│   ├── css/style.css                      # Modern clinical white workstation theme & dark mode
│   └── js/
│       ├── api.js                         # REST API client connecting all backend endpoints
│       ├── state.js                       # Reactive state manager
│       ├── app.js                         # Navigation orchestrator & role-based view guarding
│       ├── components/
│       │   ├── patientWorkspace.js        # Demographics, vital signs & active avatar status
│       │   ├── interactiveConsultation.js # Active dialogue consultation console
│       │   ├── multimodalViewer.js        # Lab panels & SVG/Canvas radiological viewers
│       │   ├── scenarioSimulation.js      # Longitudinal progression & treatment controls
│       │   ├── adversarialArena.js        # Adversarial Arena & Breaking Point Finder dashboard
│       │   ├── breakingPointFinder.js     # Progressive delta search controls & step tables
│       │   ├── consistencyGuardian.js     # 5-category Guardian verdict banner & chips
│       │   ├── evidenceExplorer.js        # Literature search & active finding provenance
│       │   ├── whatIfLab.js               # Counterfactual branch formulation & trajectory view
│       │   ├── mysteryMode.js             # Blinded trainee challenge & scorecard debriefing
│       │   ├── populationLab.js           # Cohort synthesis, batch validation & roster table
│       │   ├── supervisorOversight.js     # Cohort performance oversight & debrief review
│       │   ├── traineeSubmission.js       # Blinded diagnostic submission form & instant score
│       │   ├── stressTesting.js           # Single avatar manual perturbation sandbox
│       │   ├── uncertaintyEvidence.js     # Literature citation explorer
│       │   └── validationPrivacy.js       # Guardian checks & 4-gram privacy audit
│       └── utils/                         # ChartRenderer and ImagingRenderer
└── pytest.ini                             # Pytest configuration
```

---

## 6. Installation & Quickstart Guide

### Prerequisites
* **Python 3.10+** (Tested on Python 3.13)
* Dependencies: `fastapi`, `uvicorn`, `pydantic`, `numpy`, `scipy`, `requests`, `pytest`

### Step 1: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 2: Run the Automated Pytest Suite
Verify that all 53 unit and integration tests pass:
```bash
python -m pytest
```

### Step 3: Run Live E2E Integration Verification
Verify all 6 advanced features against the live API server:
```bash
python scratch/test_e2e_features.py
```

### Step 4: Launch Application Server
Start the unified FastAPI server which serves both the REST API and the interactive frontend:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 5: Access the Application
Open your browser and navigate to:
* **Interactive Clinical Workstation:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Interactive OpenAPI (Swagger) Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 7. REST API Endpoints Catalog

### Diagnostic AI Adversarial Arena & Breaking Point Finder
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/diagnostic-arena/capabilities` | Returns supported diseases, perturbations, models, constraints, and strategies. |
| `POST` | `/api/diagnostic-arena/experiments/run` | Runs an automated batch adversarial stress-testing experiment. |
| `GET` | `/api/diagnostic-arena/experiments` | Lists historical experiment summaries with timestamps and KPIs. |
| `GET` | `/api/diagnostic-arena/experiments/{id}` | Retrieves full experiment results, metrics, and case records. |
| `GET` | `/api/diagnostic-arena/cases/{case_id}` | Retrieves an individual adversarial case record with diff and transformation log. |
| `GET` | `/api/diagnostic-arena/experiments/{id}/export` | Exports benchmark results as JSON or CSV (`?format=json\|csv`). |
| `POST` | `/api/diagnostic-eval/breaking-point` | Executes progressive adversarial perturbation search for minimal failure delta $\Delta$. |

### Clinical Consistency Guardian & Privacy Audit
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/validation/audit/{id}` | Consistency rule checks and 4-gram privacy/memorization audit. |
| `GET` | `/api/validation/consistency-guardian/{id}` | Comprehensive 5-category constraint validation with verdict and suggestions. |

### Evidence Explorer & Literature Provenance
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/evidence/list` | Returns complete peer-reviewed literature evidence catalog. |
| `GET` | `/api/evidence/search` | Full-text search across PubMed citations and clinical guidelines (`?q=...&disease=...`). |
| `GET` | `/api/evidence/catalog` | Full catalog of indexed PubMed publications and supported biomarkers. |
| `GET` | `/api/evidence/summary` | High-level metrics: total publications, diseases covered, average evidence tier. |
| `GET` | `/api/evidence/by-disease/{id}` | Literature citations specific to a disease model. |
| `GET` | `/api/evidence/provenance/{id}` | Complete finding-by-finding literature provenance for an active synthetic patient. |
| `GET` | `/api/evidence/finding-provenance/{id}/{feature}` | Literature provenance for a single specific clinical finding or biomarker. |

### Clinical What-If Lab
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/what-if/branches/create` | Formulates an isolated counterfactual branch from a patient snapshot. |
| `GET` | `/api/what-if/branches/patient/{id}` | Lists all active counterfactual branches for a patient avatar. |
| `GET` | `/api/what-if/branches/{branch_id}` | Retrieves detailed state, trajectory history, and therapy config for a branch. |
| `POST` | `/api/what-if/branches/{branch_id}/advance` | Advances counterfactual timeline (+3, +6, +12 months) under branch therapy. |
| `POST` | `/api/what-if/branches/compare` | Multi-branch side-by-side comparison report with trajectory metrics. |

### Clinical Mystery Mode
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/mystery/sessions/start` | Initiates a blinded diagnostic session under Beginner, Intermediate, or Advanced tier. |
| `GET` | `/api/mystery/sessions/{session_id}` | Retrieves active blinded case view, dialogue history, and ordered tests. |
| `POST` | `/api/mystery/sessions/{session_id}/inquire` | Conducts natural history interview with the blinded avatar. |
| `POST` | `/api/mystery/sessions/{session_id}/order-investigation` | Orders a priced laboratory or imaging investigation with turnaround tracking. |
| `POST` | `/api/mystery/sessions/{session_id}/submit-diagnosis` | Evaluates final diagnostic formulation, yielding accuracy score and debriefing. |
| `GET` | `/api/mystery/sessions/supervisor/all` | Supervisor oversight endpoint aggregating all trainee mystery challenge attempts. |
| `GET` | `/api/mystery/catalog/pricing` | Retrieves the investigation pricing catalog with costs ($) and turnaround times. |

### Synthetic Patient Population Lab
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/population/generate` | Synthesizes a configurable patient cohort with demographic distributions. |
| `GET` | `/api/population/cohorts` | Lists all generated synthetic patient cohorts. |
| `GET` | `/api/population/cohorts/{cohort_id}` | Retrieves full cohort demographics, batch consistency audit, and member roster. |

### Patient & Trainee View Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/patients` | Lists all bootstrapped synthetic patient avatars. |
| `GET` | `/api/patients/{id}` | Retrieves full unblinded patient specification (Supervisor mode). |
| `GET` | `/api/patients/{id}/trainee-view` | Retrieves blinded clinical view (hides ground truth and un-ordered tests). |
| `POST` | `/api/patients/generate` | Generates a new seed-controlled synthetic patient avatar. |

### Authentication & Role-Based Workflows
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authenticates clinical trainees (`<trainee_id>@ggmail.com`) and supervisors. |
| `POST` | `/api/auth/trainee-submit-diagnosis` | Evaluates trainee primary diagnosis, differentials, and ordering efficiency. |
| `GET` | `/api/auth/supervisor/trainee-records` | Supervisor audit aggregating cohort pass rates, mean accuracy, and debriefings. |

---

## 8. Role-Based Dashboards & Workflows

### 1. Clinical Trainee Portal (`<id>@ggmail.com`)
* **Strict Authentication:** Login requires institutional email format containing Trainee ID ending in `@ggmail.com` (e.g., `TR-8041@ggmail.com`).
* **Blinded Workstation:** Genetic mutations, ICD/OMIM codes, and un-ordered tests are concealed (`[Hidden in Trainee Mode]`).
* **Interactive Consultation:** Conduct natural dialogue interviews with patient avatars.
* **Blinded Investigation Ordering:** Order serum, urinary, enzymatic, and imaging investigations from the priced catalog.
* **Mystery Challenge Mode:** Test clinical reasoning under time and budget constraints with immediate debriefing scorecards.
* **Trainee Diagnostic Submission (`#tab-trainee-submission`):** Formulate primary diagnosis, rank differentials, submit clinical justification, and receive automated diagnostic accuracy, efficiency %, and feedback.

### 2. Clinical Supervisor & AI Evaluator Command Center (`SUP-...@ggmail.com`)
* **Elevated Privileges:** Dedicated supervisor authentication (e.g., `SUP-001@ggmail.com`).
* **Unblinded Ground Truth:** Full access to underlying genetic mutations (*ATP7B*, *GLA*, *GBA1*), true pathophysiological stages, and baseline laboratory panels.
* **Trainee Cohort Oversight (`#tab-supervisor-oversight`):** Real-time aggregate statistics: total submissions, cohort pass rate %, average accuracy score, test efficiency, and detailed trainee debriefing reviews.
* **Diagnostic AI Adversarial Arena (`#tab-arena`):** Automated parameter sweeps, borderline adversarial search, and Breaking Point minimal delta discovery.
* **Clinical Consistency Guardian (`#tab-validation`):** 5-category audit across physiological, cross-modal, temporal, treatment, and evidence constraints.
* **Counterfactual What-If Lab (`#tab-what-if`):** Multi-branch parallel therapeutic simulation and comparison.
* **Population Lab (`#tab-population`):** Batch cohort generation with distribution controls, consistency audits, and direct Arena bridging.

---

## 9. Verification & Automated Test Suite

RareAvatar is backed by **53 passing tests** across 15 specialized test suites (100% pass rate):

| Test Suite | Tests | Scope & Capabilities Verified |
| :--- | :---: | :--- |
| `test_adversarial_arena.py` | 12 | Deterministic generation, transformation tracking, blinded input isolation, constraint violations & rejection, baseline vs. fragile vs. robust models, metric formulas, external model timeouts, reproducibility, and JSON/CSV export. |
| `test_auth.py` | 5 | Trainee `@ggmail.com` validation, supervisor role privileges, trainee diagnosis scoring (accuracy & test efficiency), hallmark detection, and supervisor oversight roster aggregation. |
| `test_breaking_point.py` | 4 | Progressive delta search, minimum delta $\Delta$ identification, failure mode classification (`INCORRECT_PREDICTION`, `PREDICTION_INSTABILITY`, `CONFIDENCE_COLLAPSE`), and multi-model vulnerability benchmark. |
| `test_consistency_guardian.py` | 4 | 5-category constraint validator (Physiological, Cross-Modal, Temporal, Treatment-Model, Evidence-Grounding), verdict generation (`FULL_CLINICAL_CONCORDANCE`), and suggested actions. |
| `test_consistency_validation.py` | 2 | Automated detection of intentional physiological and cross-modal constraint violations. |
| `test_dialogue_manager.py` | 5 | State-grounded inquiry responses, clinical intent classification, and history-taking conversation trees. |
| `test_disease_models.py` | 4 | Physiological ranges, genetic mutations, and disease stages for Wilson, Fabry, and Gaucher disease models. |
| `test_e2e_integration.py` | 1 | Full end-to-end API integration workflow from avatar synthesis to diagnostic evaluation. |
| `test_evidence_explorer.py` | 4 | Indexed PubMed publication search, biomarker catalog retrieval, active patient finding-by-finding provenance linking, and guideline tier verification. |
| `test_mystery_mode.py` | 2 | Blinded case intake, Beginner/Intermediate/Advanced tier generation, inquiry dialogue, priced investigation ordering, and automated scorecard generation. |
| `test_patient_generator.py` | 2 | Seed-based reproducibility, demographic variance, and literature evidence attribution. |
| `test_population_lab.py` | 2 | Batch cohort generation, custom disease distributions, batch consistency audit pass rates, and roster export. |
| `test_privacy_auditor.py` | 1 | 4-gram lexical non-memorization audit and multi-attribute feature space distance. |
| `test_stress_testing.py` | 2 | Noise injection, missing data dropout, and baseline classifier robustness scoring. |
| `test_what_if.py` | 3 | Immutable deep-copy branch formulation, independent timeline progression (+3M/+6M), and multi-branch comparative trajectory reports. |
| **Total** | **53** | **100% Passed (1.48s execution time)** |

---

## 10. Known Limitations & Research Boundaries

1. **Synthetic Educational Platform:** RareAvatar is a research and clinical education platform. Simulated scenarios do not constitute formal medical advice or independently certified diagnostic claims for living human patients.
2. **Clinical Expert Validation:** All automated checks are deterministic and rule-based. Formal board-certified clinical expert evaluation is pending and required prior to real-world patient-facing deployment.
3. **Parametric vs Generative Diffusion 3D DICOM Images:** The platform outputs structured DICOM radiology reports, quantitative z-scores, and calibrated 2D anatomical SVG slices. Generating pixel-level 3D volumetric DICOM volumes requires high-memory offline GPU diffusion clusters, for which standard integration hooks are provided.
4. **Third-Party Model Integrations:** External diagnostic models can be connected via HTTP POST to `/api/diagnostic-eval/submit-external` or evaluated in batch via the Adversarial Arena. When an external model is not connected, the system provides built-in reference guideline and demonstration classifiers.
