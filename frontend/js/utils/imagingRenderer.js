/**
 * Calibrated SVG Anatomical Slice Visualization Utility
 */
const ImagingRenderer = {
    renderSliceSVG(container, study) {
        if (!container) return;
        if (!study || !study.schematic_data || Object.keys(study.schematic_data).length === 0) {
            container.innerHTML = `
                <div style="text-align:center; color:#64748b; font-size:0.85rem; padding:40px;">
                    <p>No parametric visual schematic available for this study modality.</p>
                </div>
            `;
            return;
        }

        const data = study.schematic_data;
        const type = data.type;

        let svgContent = '';

        if (type === 'brainstem_slice') {
            // Midbrain Tegmentum / Face of Giant Panda Sign
            svgContent = `
                <svg width="340" height="220" viewBox="0 0 340 220" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <radialGradient id="tegmentumGlow" cx="50%" cy="50%" r="50%">
                            <stop offset="0%" stop-color="#64748b" stop-opacity="0.8"/>
                            <stop offset="100%" stop-color="#1e293b" stop-opacity="0.3"/>
                        </radialGradient>
                    </defs>
                    <!-- Midbrain Outline -->
                    <path d="M 80,180 C 60,110 90,40 170,40 C 250,40 280,110 260,180 C 220,170 170,195 170,195 C 170,195 120,170 80,180 Z" 
                          fill="#151e33" stroke="#475569" stroke-width="2"/>
                    <!-- Cerebral Aqueduct (The Mouth) -->
                    <ellipse cx="170" cy="165" rx="10" ry="6" fill="#030712" stroke="#64748b" stroke-width="1.5"/>
                    <!-- Hyperintense Tegmentum Signal -->
                    <ellipse cx="170" cy="115" rx="65" ry="40" fill="url(#tegmentumGlow)"/>
                    <!-- Red Nuclei - Preserved Hypointense (The Eyes) -->
                    <circle cx="135" cy="115" r="14" fill="#030712" stroke="#ffedd5" stroke-width="2"/>
                    <circle cx="205" cy="115" r="14" fill="#030712" stroke="#ffedd5" stroke-width="2"/>
                    <!-- Substantia Nigra (The Ears) -->
                    <path d="M 90,75 C 95,60 120,60 125,75" fill="none" stroke="#030712" stroke-width="7" stroke-linecap="round"/>
                    <path d="M 215,75 C 220,60 245,60 250,75" fill="none" stroke="#030712" stroke-width="7" stroke-linecap="round"/>
                    <!-- Annotations -->
                    <text x="170" y="25" fill="#334155" font-size="11" font-family="Plus Jakarta Sans" font-weight="700" text-anchor="middle">MIDBRAIN TEGMENTUM (AXIAL T2/FLAIR)</text>
                    <text x="170" y="210" fill="#facc15" font-size="10" font-family="JetBrains Mono" font-weight="600" text-anchor="middle">★ Pathognomonic "Face of Giant Panda" Sign</text>
                </svg>
            `;
        } else if (type === 'cornea_ring_slice') {
            // Kayser-Fleischer Rings in Cornea
            svgContent = `
                <svg width="340" height="220" viewBox="0 0 340 220" xmlns="http://www.w3.org/2000/svg">
                    <!-- Sclera -->
                    <circle cx="170" cy="110" r="90" fill="#0f172a" stroke="#475569" stroke-width="3"/>
                    <!-- Iris -->
                    <circle cx="170" cy="110" r="65" fill="#1e293b" stroke="#334155" stroke-width="2"/>
                    <!-- Pupil -->
                    <circle cx="170" cy="110" r="26" fill="#020617"/>
                    <!-- Kayser-Fleischer Golden-Brown Copper Band (Descemet's Membrane) -->
                    <circle cx="170" cy="110" r="68" fill="none" stroke="#b8860b" stroke-width="7" opacity="0.9" stroke-dasharray="10, 2"/>
                    <!-- Slit-Lamp Optical Beam Overlay -->
                    <path d="M 120,20 L 220,200" stroke="#fef08a" stroke-width="6" opacity="0.45" stroke-linecap="round"/>
                    <!-- Annotation -->
                    <text x="170" y="25" fill="#e2e8f0" font-size="11" font-family="Plus Jakarta Sans" font-weight="700" text-anchor="middle">SLIT-LAMP BIOMICROSCOPY (CORNEAL PERIPHERY)</text>
                    <text x="170" y="212" fill="#eab308" font-size="10" font-family="JetBrains Mono" font-weight="600" text-anchor="middle">Golden-Brown Kayser-Fleischer Ring (360° Descemet's)</text>
                </svg>
            `;
        } else if (type === 'cardiac_short_axis_slice') {
            // Cardiac Short-Axis MRI LVH + LGE
            svgContent = `
                <svg width="340" height="220" viewBox="0 0 340 220" xmlns="http://www.w3.org/2000/svg">
                    <!-- Right Ventricle Crescent -->
                    <path d="M 110,60 C 70,80 70,140 110,160 C 120,130 120,90 110,60 Z" fill="#090d16" stroke="#475569" stroke-width="2"/>
                    <!-- Hypertrophied Left Ventricle Wall (17mm Interventricular Septum) -->
                    <circle cx="180" cy="110" r="70" fill="#1e293b" stroke="#94a3b8" stroke-width="2"/>
                    <!-- Blood Pool Lumen -->
                    <circle cx="180" cy="110" r="34" fill="#020617"/>
                    <!-- Thickened Septum (Left Side of LV) -->
                    <path d="M 125,75 C 145,95 145,125 125,145" fill="none" stroke="#c084fc" stroke-width="18" stroke-linecap="round"/>
                    <!-- Basal Inferolateral Wall Late Gadolinium Enhancement (Fibrosis) -->
                    <path d="M 235,95 C 242,105 242,120 235,130" fill="none" stroke="#f43f5e" stroke-width="12" stroke-linecap="round"/>
                    <!-- Annotations -->
                    <text x="170" y="25" fill="#c084fc" font-size="11" font-family="Plus Jakarta Sans" font-weight="700" text-anchor="middle">CARDIAC MRI SHORT-AXIS (FABRY CARDIOMYOPATHY)</text>
                    <text x="170" y="210" fill="#f43f5e" font-size="10" font-family="JetBrains Mono" font-weight="600" text-anchor="middle">Concentric LVH (17mm) + Inferolateral LGE Fibrosis</text>
                </svg>
            `;
        } else if (type === 'skeletal_femur_slice') {
            // Erlenmeyer Flask Deformity
            svgContent = `
                <svg width="340" height="220" viewBox="0 0 340 220" xmlns="http://www.w3.org/2000/svg">
                    <!-- Femoral Shaft Diaphysis with Distal Erlenmeyer Metaphyseal Flaring -->
                    <path d="M 140,30 L 140,110 C 130,130 90,160 85,185 L 255,185 C 250,160 210,130 200,110 L 200,30 Z" 
                          fill="#1e293b" stroke="#475569" stroke-width="2"/>
                    <!-- Medullary Trabecular Osteopenia (Loss of Cortical Density) -->
                    <path d="M 152,40 L 152,105 C 145,125 105,155 102,175 L 238,175 C 235,155 195,125 188,105 L 188,40 Z" 
                          fill="#0b0f19" stroke="#94a3b8" stroke-width="1" stroke-dasharray="3, 3"/>
                    <!-- Metaphyseal Flaring Dimension Guides -->
                    <line x1="85" y1="192" x2="255" y2="192" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="2, 2"/>
                    <text x="170" y="25" fill="#334155" font-size="11" font-family="Plus Jakarta Sans" font-weight="700" text-anchor="middle">FEMUR RADIOGRAPH (DISTAL METAPHYSIS)</text>
                    <text x="170" y="210" fill="#f59e0b" font-size="10" font-family="JetBrains Mono" font-weight="600" text-anchor="middle">Classical "Erlenmeyer Flask Deformity" Flaring</text>
                </svg>
            `;
        } else if (type === 'visceral_organ_slice') {
            // Massive Splenomegaly & Hepatomegaly
            svgContent = `
                <svg width="340" height="220" viewBox="0 0 340 220" xmlns="http://www.w3.org/2000/svg">
                    <!-- Enlarged Liver Span -->
                    <path d="M 80,60 C 130,40 170,70 170,140 C 170,160 100,170 70,150 C 50,130 50,80 80,60 Z" 
                          fill="#1e293b" stroke="#475569" stroke-width="2"/>
                    <!-- Massive Spleen (12x Normal Volume) -->
                    <path d="M 210,50 C 260,60 280,120 270,175 C 250,195 200,185 190,140 C 180,100 190,60 210,50 Z" 
                          fill="#2e1065" stroke="#a855f7" stroke-width="2.5"/>
                    <text x="105" y="115" fill="#94a3b8" font-size="11" font-family="Plus Jakarta Sans" font-weight="600">Liver (18.5cm)</text>
                    <text x="220" y="125" fill="#e9d5ff" font-size="11" font-family="Plus Jakarta Sans" font-weight="700">Spleen (22.8cm)</text>
                    <text x="170" y="25" fill="#e2e8f0" font-size="11" font-family="Plus Jakarta Sans" font-weight="700" text-anchor="middle">ABDOMINAL VISCERAL VOLUMETRY</text>
                    <text x="170" y="212" fill="#c084fc" font-size="10" font-family="JetBrains Mono" font-weight="600" text-anchor="middle">Massive Splenomegaly (12x Multiples of Normal Volume)</text>
                </svg>
            `;
        } else {
            svgContent = `
                <div style="text-align:center; color:#64748b; font-size:0.85rem; padding:40px;">
                    <p>Parametric schematic generated for: ${study.modality}</p>
                </div>
            `;
        }

        container.innerHTML = svgContent;
    }
};
