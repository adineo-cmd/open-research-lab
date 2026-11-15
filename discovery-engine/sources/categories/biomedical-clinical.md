# biomedical-clinical — 28 sources

| source | what you can do there | agent access | tier | url check |
|---|---|---|---|---|
| [ADNI (Alzheimer's Disease Neuroimaging Initiative)](https://adni.loni.usc.edu) | Longitudinal MRI/PET/genetics/clinical dataset standard for dementia-modeling research. | Register free, then use the ADNI download portal/API to pull imaging and clinical tables. | curated | 200 |
| [cBioPortal](https://www.cbioportal.org) | Visualization/query interface over 400+ cancer-genomics studies with harmonized clinical+omics data. | Use the cBioPortal REST API (cbioportal.org/api) for studies, patients and mutation queries. | curated | 200 |
| [CDC Data](https://data.cdc.gov) | US public health surveillance. | Socrata API. | curated | ok |
| [CDC WONDER](https://wonder.cdc.gov) | Online query system for US mortality, birth, disease and environmental health microdata summaries. | Submit the documented HTTP form requests to WONDER endpoints to retrieve aggregate tables (XML/HTML). | curated | 200 |
| [ChEMBL](https://www.ebi.ac.uk/chembl) | 2M+ bioactive molecules with activity data. | REST web services + Oracle/SQLite dumps. | curated | ok |
| [CIViC](https://civicdb.org) | Community-curated catalog of clinical interpretations of cancer variants (evidence levels, therapies). | Download the full-nightly TSV dumps or use the GraphQL API. | curated | 200 |
| [ClinicalTrials.gov](https://clinicaltrials.gov) | 450k+ registered clinical trials — endpoints, arms, results. | API v2 (clinicaltrials.gov/api/v2). | curated | ok |
| [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar) | Public archive of reported relationships between human variants and phenotypes with clinical significance. | Download the full XML/VCF release from ncbi.nlm.nih.gov/clinvar FTP. | curated | 200 |
| [CMS Data (data.cms.gov)](https://data.cms.gov) | Medicare/Medicaid claims and provider datasets: utilization, payments, hospital quality, market saturation. | Use the data.cms.gov API (data.cms.gov/api/1/datastore) plus direct CSV downloads. | curated | 403-bot |
| [COSMIC](https://cancer.sanger.ac.uk/cosmic) | Catalogue of somatic mutations in cancer with variant/gene/fusion annotations from the literature and projects. | Download curated mutation TSVs after free academic registration; web search open. | curated | 200 |
| [DailyMed (NLM)](https://dailymed.nlm.nih.gov) | Official structured product labels for US drugs with SPL XML for every marketed medication. | Use the DailyMed REST API (dailymed.nlm.nih.gov/dailymed/services) for label retrieval. | curated | 200 |
| [DepMap (Cancer Dependency Map)](https://depmap.org) | CRISPR/RNAi fitness screens across 1,000+ cancer cell lines linking gene dependencies to molecular features. | Download current release CSVs (gene_effect, expression, mutations) from depmap.org/portal/download. | curated | 200 |
| [DrugBank (open)](https://go.drugbank.com/releases/latest#open-data) | Drug targets, structures, interactions (open subset). | XML bulk (attribution). | curated | ok |
| [Europe PMC](https://europepmc.org) | Full-text Enriching Europe PMC incl. open full texts + citation network. | REST API + FTP full-text corpus. | curated | 403-bot |
| [FinnGen](https://finngen.fi) | Nationwide Finnish biobank GWAS: ~500k participants with open summary statistics for thousands of endpoints. | Download endpoint summary statistics (gzipped tabular) from the documented R5/R6 release buckets. | curated | 200 |
| [HealthData.gov](https://healthdata.gov) | US health datasets (claims, COVID, hospital capacity). | CKAN API/Socrata. | curated | ok |
| [IHME GBD Results](https://ghdx.healthdata.org/gbd-results-tool) | Global Burden of Disease: 369 diseases, 88 risk factors, all countries. | Bulk CSV via query tool. | curated | ok |
| [NeuroVault](https://neurovault.org) | Public repository of statistical brain maps (fMRI/VBM group results) in standardized space. | REST API (neurovault.org/api) to list collections and download NIfTI maps. | curated | 200 |
| [Nextstrain](https://nextstrain.org) | Real-time pathogen phylogenomics (SARS-CoV-2, flu, Ebola...) with live trees and sequences. | Fetch Auspice JSON trees and metadata from nextstrain.org endpoints for downstream analysis. | curated | 200 |
| [Open FDA](https://open.fda.gov) | FAERS adverse events, recalls, device data. | REST API, no key for low volume. | curated | ok |
| [Open Targets Platform](https://platform.opentargets.org) | Integrates genomics, literature and pharmacology to prioritize drug targets with evidence scores. | Use the Open Targets GraphQL API (api.platform.opentargets.org/api/v4/graphql) or download data dumps. | curated | 200 |
| [OpenPrescribing](https://openprescribing.net) | Monthly NHS prescribing data for every GP practice and drug in England, analyzed and downloadable. | Use its REST API (openprescribing.net/api) or grab raw BNF data exports. | curated | 403-bot |
| [outbreak.info](https://outbreak.info) | Harmonized SARS-CoV-2 (and RSV/flu) genomic and epidemiological data: variants, lineages, prevalence. | Use the documented REST APIs (api.outbreak.info) for lineage prevalence and mutation queries. | curated | 200 |
| [PubMed / MEDLINE](https://pubmed.ncbi.nlm.nih.gov) | 36M+ biomedical citations. | E-utilities API + annual baseline bulk XML. | curated | ok |
| [RxNav / RxNorm (NLM)](https://rxnav.nlm.nih.gov) | Normalized vocabulary for clinical drugs with ingredient/brand relationships and NDC codes. | Call the RxNav REST API (rxnav.nlm.nih.gov/REST) or download monthly RxNorm releases. | curated | 200 |
| [SEER](https://seer.cancer.gov) | US cancer registry statistics. | Research data (signed DUA) + public stats. | curated | ok |
| [WHO Global Health Observatory](https://www.who.int/data/gho) | Global health indicators per country. | OData API. | curated | ok |
| [WHO International Clinical Trials Registry Platform (ICTRP)](https://trialsearch.who.int) | WHO portal aggregating clinical-trial registrations from 20+ national registries into one searchable index. | Search UI plus downloadable registry export files for cross-registry analysis. | curated | 200 |
