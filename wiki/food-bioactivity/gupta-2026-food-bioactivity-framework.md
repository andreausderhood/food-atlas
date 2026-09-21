# Gupta et al. 2026: Food Bioactivity Framework

> Sources: Gupta, Gunning, Ahmed & Tagkopoulos, npj Science of Food, 2026-08-25
> Raw: [From metabolomics dark matter to bioactivity](../../raw/food-bioactivity/2026-08-25-from-metabolomics-dark-matter-to-bioactivity.md)
> Updated: 2026-09-17

## Overview

The study builds a multilayer pipeline that turns untargeted food mass-spectrometry data into a ranked shortlist of testable bioactive compounds. It runs across 322 commonly consumed foods in the United States, comprising 30,343 small molecules, and combines structure prediction, LLM-harmonised assay evidence, concentration-aware activity mapping and machine learning. Its own summary of the result is a shift "from a completeness-driven paradigm to an inference-driven paradigm".

## The pipeline

| Layer | What it does | Result |
| :--- | :--- | :--- |
| Retention-index model | Predicts chromatographic retention from structure, then matches unidentified features against formula-constrained PubChem candidates | R² = 0.95, PCC = 0.97; structural coverage rises from 7.4% to over 78% of detected features |
| Confidence tiers | Stratifies matches by retention agreement | 15,593 High, 4046 Medium and 6,036 Low putative annotations |
| Assay harmonisation | A two-stage LLM workflow maps heterogeneous assay text to standardised bioactivity classes | 39,158 assay protocols covering 119,633 chemical-assay measurements from ChEMBL |
| Concentration mapping | Converts LC-MS intensities into molar concentrations anchored to FoodAtlas values | A 322 × 30,343 food × molecule matrix |
| Prediction | A Random Forest trained on whole-food FRAP measurements | R² = 0.73, Pearson correlation 0.85 |
| Mechanistic triage | Boltz-2 structure-based screening against the KEAP1 Kelch domain | A shortlist for wet-lab work |

## Findings that matter to a food atlas

- **The metabolome is food-specific.** Of 27,713 detected features, 44% were unique to a single food and 85% were present in five foods or fewer.
- **Culinary labels are weak proxies.** HDBSCAN found 4 clusters plus 52 outlier foods. White rice clustered with processed foods while wild rice clustered with seeds and grains; only 33 unique metabolites were identified in white rice against 411 in wild rice. Xanthan gum, a microbial product, clustered with nuts and seeds, sharing 33 metabolites with walnuts.
- **Whole-food activity is not additive.** Using only the 3610 molecules with measured absolute concentrations gave suboptimal performance compared with the full profile, which the authors report as the best result; a preliminary model that simply summed activity loads was uninformative.
- **Rankings are not health claims.** Anise hyssop (*Agastache foeniculum*) achieved the highest overall summed bioactivity scores; tomato ranked highest for anticancer-associated compound evidence and carrots ranked highly for antidiabetic and anticancer evidence. The authors state these "are not interpreted as clinical efficacy claims".
- **Only antioxidant activity is modelled at food level.** The other bioactivity categories are compound-level evidence layers used for prioritisation, not food-level predictions.

## Stated limitations

The authors are explicit about what the framework does not establish:
- the whole-food model relies solely on FRAP, so it captures a single mechanism;
- retention-index annotations stay probabilistic, especially for isomers, and need MS/MS or authentic standards;
- concentration estimation is "a major bottleneck", with conversion factors spanning roughly seven orders of magnitude and an error of roughly 18-fold on average;
- digestion, bioavailability, metabolism and inter-individual variability are not modelled at all.

Shortlisted foods and compounds are therefore "preliminary, hypothesis-generating candidates".

## Use in the Food Atlas

The atlas takes this work as a **bioactivity evidence layer**, never as a health claim: predictions enter at tier 4 with their model name and version, and compound-level evidence is labelled as evidence. The raw PTFI data behind the study cannot ship under MIT, so the atlas uses the paper's CC BY text and open primary FRAP sources instead.

## See Also

- [Nutritional dark matter](nutritional-dark-matter.md)
- [Traceability contract](../food-atlas-project/traceability-contract.md)
- [Licensing food data for an MIT atlas](../food-atlas-project/mit-licensing-of-food-data.md)
