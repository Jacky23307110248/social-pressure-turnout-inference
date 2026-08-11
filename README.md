# Social Pressure, Verified Turnout, and Causal Interpretation

This repository provides a design-aware reanalysis of a large household-randomized voter-turnout field experiment. It uses real administrative records from the 2006 Michigan primary and focuses on the effect of assignment to the Neighbors social-pressure mailer relative to no mailing.

The primary voter-level intention-to-treat estimate is an 8.131 percentage-point increase in verified turnout. The household-clustered standard error is 0.337 percentage points and the 99 percent confidence interval is 7.263 to 8.999 percentage points. Household aggregation, block-stratified randomization inference, baseline adjustment, exact-duplicate removal, balance checks, and leave-one-block-out analysis support the same substantive conclusion.

The defensible estimand is a household-assignment policy effect under the realized allocation environment. The design does not identify a pure recipient-level direct effect or a spillover dose-response because treatment saturation is essentially fixed within observed block sizes.

## Data

The analysis downloads the public file with identifier `42238` from the Yale Dataverse dataset [Social Pressure and Voter Turnout: Evidence from a Large-Scale Field Experiment](https://doi.org/10.60600/YU/CGMWNW). The expected access-response SHA-256 is:

`05807BCBEDAACF02EC6E6838E1B9C9B2FC99AD9D8C63F80C162991970044C6CE`

The data are distributed under CC0 1.0 and are not committed to this repository. The downloaded table contains coded demographic and turnout-history variables but no names, street addresses, email addresses, or telephone numbers.

## Reproduction

Create the Python environment and run the analyses in order:

```text
conda env create -f environment.yml
conda activate social-pressure-turnout
python scripts/run_primary_analysis.py
python scripts/run_robustness_analysis.py
python scripts/run_secondary_analysis.py
python scripts/generate_report_assets.py
pytest
```

After installing XeLaTeX, the complete cross-platform pipeline can also be run with:

```text
python scripts/run_all.py
```

Building the technical note additionally requires XeLaTeX from TeX Live 2024 or a compatible distribution:

```text
python scripts/build_report.py
```

The stable publication artifact is `output/pdf/social_pressure_technical_note.pdf`.

## Repository structure

- `scripts/` contains the empirical analyses, figure generation, and report build.
- `results/` contains machine-readable estimates.
- `output/` contains publication figures, tables, and the final technical note.
- `technical_note/` contains the XeLaTeX source.
- `docs/` records the analysis plan, provenance, and literature review.
- `tests/` checks the retained numerical claims and repository outputs.

## Research transparency

The positive result in the original article was public before this benchmark replication. The report therefore presents the work as a reproducible, design-aware reanalysis rather than a previously unknown discovery. Negative and unresolved findings remain visible, including one unresolved adjacent message contrast and non-identification of a spillover dose-response.

## License and citation

Repository code is released under the MIT License. The Yale data retain their CC0 1.0 terms. Cite the original experiment, the Yale dataset DOI, and this repository as described in `CITATION.cff`.
