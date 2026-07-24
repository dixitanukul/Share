# Member DNA — Data Model Overview

> A unified member-level analytics layer built on a **Silver → Gold** medallion architecture.  
> Silver tables hold domain-specific data; Gold tables combine them into analytics-ready views.  
> All tables join on `MEMBER_ID`.

---

## Architecture

```
SILVER (domain tables)                        →   GOLD (analytics-ready)
─────────────────────────────────────────────────────────────────────────
tbl_member_bis_scaffold (eligibility)        ─┐
tbl_member_ccm_scaffold (comm prefs)         ─┼→ tbl_member_scaffold
tbl_member_facets_scaffold (plan detail)     ─┤
tbl_member_reltio_scaffold (geography)       ─┘
─────────────────────────────────────────────────────────────────────────
tbl_member_dnrmlzd_wide (denormalized)       ─┐
tbl_member_bis_sdoh (SVI / ADI / BISG)      ─┼→ tbl_member_sdoh
─────────────────────────────────────────────────────────────────────────
tbl_member_bis_ip_events (inpatient)         ─┐
tbl_member_bis_op_events (outpatient)        ─┼→ tbl_member_event_cost
─────────────────────────────────────────────────────────────────────────
tbl_member_bis_dxcg_v6_clinical_condition    ─┐
tbl_member_bis_dxcg_v6_risk_scores           ─┼→ tbl_member_clinicalcondition_and_riskscores
tbl_member_bis_dx_risk_factors               ─┘
─────────────────────────────────────────────────────────────────────────
tbl_member_bis_rx_pdc_clms (PDC detail)      ─┐
tbl_member_bis_rx_clms (pharmacy summary)    ─┼→ tbl_member_bis_financials_and_claims
tbl_member_bis_cost (medical cost)           ─┘
```

---

# 1. Member Scaffold

## Silver: tbl_member_bis_scaffold

**Purpose**: Member eligibility and enrollment from BIS.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Unique member identifier |
| MBR_MED_MEMBER_MONTHS | decimal | Medical member months enrolled |
| RX_MEMBER_MONTHS | decimal | Pharmacy member months enrolled |
| HCPK | string | Health Care Plan Key |
| SUBSCRIBER_ID | string | Subscriber identifier |
| MEMBER_DOB | date | Date of birth |
| AGE_IN_YEARS | int | Age in years |
| FEMALE_FLAG | int | 1 = female |
| SUBSCRIBER_FLAG | int | 1 = primary subscriber |
| SPOUSE_FLAG | int | 1 = spouse |
| GROUP_NUM | string | Employer group number |
| GROUP_NAME | string | Employer group name |
| PARENT_GROUP_NUM | string | Parent group number |

## Silver: tbl_member_ccm_scaffold

**Purpose**: Communication channel preferences from CCM system.

| Column | Type | Description |
| --- | --- | --- |
| member_id | string | Member identifier (join key) |
| MARKETING_EMAIL_PREF | string | Marketing email opt-in |
| SURVEY_EMAIL_PREF | string | Survey email preference |
| MARKETING_DIRECTMAIL_PREF | string | Direct mail preference |
| MANDATED_PREF | string | Mandated communication preference |
| DIGITAL_PRFL_ID | string | Digital profile ID |
| REGISTRATION_DATE | string | Portal registration date |
| PHONE_CALL_PREF | string | Phone call preference |
| SMS_PREF | string | SMS/text preference |

## Silver: tbl_member_facets_scaffold

**Purpose**: Plan enrollment detail from Facets — medical, dental, vision, pharmacy, life coverage. Also carries LOB hierarchy and race/ethnicity.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| CLASS_ID | string | Benefit class |
| MEDICAL_CLASS_PLAN_ID | string | Medical class plan |
| DENTAL_CLASS_PLAN_ID | string | Dental class plan |
| VISION_CLASS_PLAN_ID | string | Vision class plan |
| PHARMACY_CLASS_PLAN_ID | string | Pharmacy class plan |
| SUBGROUP_ID | string | Subgroup identifier |
| SUBGROUP_NAME | string | Subgroup name |
| MARKETS_LOB | string | Markets line of business |
| PRODUCT_LOB | string | Product line of business |
| RACE_CD | string | Race code |
| ETHNIC_CD | string | Ethnicity code |
| LANG_CD | string | Preferred language code |
| DX_SDOH_EDUCATION_IND | int | SDOH: education barrier |
| DX_SDOH_EMPLOYMENT_IND | int | SDOH: employment barrier |
| DX_SDOH_HOUSING_ECONOMIC_IND | int | SDOH: housing/economic instability |
| DX_SDOH_PSYCHOSOCIAL_IND | int | SDOH: psychosocial risk |

## Silver: tbl_member_reltio_scaffold

**Purpose**: Verified member addresses and identity from Reltio MDM. Geocoded home, mailing, and work locations.

| Column | Type | Description |
| --- | --- | --- |
| ENTITY_ID | string | Reltio master entity ID |
| FIRST_NAME | string | First name |
| LAST_NAME | string | Last name |
| GENDER | string | Gender |
| HOME_ADDRESSLINE1 | string | Home address line 1 |
| HOME_CITY | string | Home city |
| HOME_STATEPROVINCE | string | Home state |
| HOME_ZIP5 | string | Home ZIP-5 |
| HOME_LATITUDE | string | Geocoded latitude |
| HOME_LONGITUDE | string | Geocoded longitude |
| HOME_FIPSCOUNTYCODE | string | FIPS county code |
| HOME_CBSACODE | string | CBSA metro area code |
| HOME_TRACTCODE | string | Census tract |
| HOME_BLOCKGROUPCODE | string | Census block group |
| MAILING_ADDRESSLINE1 | string | Mailing address |
| MAILING_CITY | string | Mailing city |
| MAILING_STATEPROVINCE | string | Mailing state |
| MAILING_ZIP5 | string | Mailing ZIP-5 |

## → Gold: tbl_member_scaffold

**What it produces**: Single source of truth for member demographics, enrollment, contact info, and location — combining all 4 Silver tables above.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Unique member identifier |
| FIRST_NAME | string | First name |
| LAST_NAME | string | Last name |
| AGE_IN_YEARS | int | Member age |
| FEMALE_FLAG | int | 1 = female |
| SUBSCRIBER_FLAG | int | 1 = primary subscriber |
| DEPENDENT_FLAG | int | 1 = dependent |
| MEMBER_DOB | date | Date of birth |
| ADDRESS | string | Full address |
| CITY_NAME | string | City |
| STATE | string | State |
| ZIPCODE | string | ZIP code |
| COUNTY_NAME | string | County |
| CALIFORNIA_FLAG | int | 1 = CA resident |
| MARKETS_LOB | string | Line of business (market) |
| PRODUCT_LOB | string | Line of business (product) |
| MBR_MED_MNTHS | int | Medical member months |
| RX_MEMBER_MONTHS | int | Pharmacy member months |
| RACE_CD | string | Race code |
| ETHNIC_CD | string | Ethnicity code |
| LANG_CD | string | Preferred language |
| RE_MAX | string | Most probable imputed race/ethnicity |
| MARKETING_EMAIL_PREF | string | Email opt-in preference |
| SMS_PREF | string | SMS preference |
| PHONE_CALL_PREF | string | Phone preference |
| HOME_LATITUDE | string | Geocoded latitude |
| HOME_LONGITUDE | string | Geocoded longitude |
| CENSUS_TRACT_ID | string | Census tract (links to SDOH) |
| TARGETED_CM_FLAG | int | 1 = in targeted care management |
| PRENATAL_PROG_FLAG | int | 1 = in prenatal program |

---

# 2. Member SDOH (Social Determinants of Health)

## Silver: tbl_member_dnrmlzd_wide

**Purpose**: Fully denormalized member table. Provides the geographic bridge (census tract, ZIP) that links each member to their neighborhood-level SDOH data.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| CENSUS_TRACT_ID | string | Census tract FIPS |
| ZIPCODE | string | ZIP code |
| STATE | string | State |
| COUNTY_NAME | string | County |

## Silver: tbl_member_bis_sdoh

**Purpose**: CDC Social Vulnerability Index (SVI), Area Deprivation Index (ADI), and BISG race/ethnicity imputation at census-tract level.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| FIPS | string | Census tract FIPS code |
| CENSUS_TRACT_ID | string | Census tract |
| AREA_SQMI | decimal | Tract area (sq mi) |
| E_TOTPOP | decimal | Total population |
| E_POV | decimal | Persons below poverty |
| E_UNEMP | decimal | Unemployed (16+) |
| E_PCI | decimal | Per capita income |
| E_NOHSDP | decimal | No HS diploma (25+) |
| E_AGE65 | decimal | Persons 65+ |
| E_LIMENG | decimal | Limited English proficiency |
| E_NOVEH | decimal | No vehicle households |
| E_UNINSUR | decimal | Uninsured persons |
| RPL_THEME1 | decimal | SVI: socioeconomic vulnerability |
| RPL_THEME2 | decimal | SVI: household/disability |
| RPL_THEME3 | decimal | SVI: minority/language |
| RPL_THEME4 | decimal | SVI: housing/transportation |
| RPL_THEMES | decimal | Overall SVI score (0=low, 1=high) |
| ADI_NATRANK | decimal | ADI national percentile (1-100) |
| ADI_STATERNK | decimal | ADI state decile (1-10) |
| IMPUTED_PROB_WHITE | decimal | BISG probability — White |
| IMPUTED_PROB_BLACK | decimal | BISG probability — Black |
| IMPUTED_PROB_HISPANIC | decimal | BISG probability — Hispanic |
| RE_MAX | string | Most probable race/ethnicity |
| RE_MAX_PROB | decimal | Confidence of imputed R/E |

## → Gold: tbl_member_sdoh

**What it produces**: SDOH profile per member — neighborhood vulnerability scores, deprivation index, and imputed race/ethnicity.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| FIPS | string | Census tract FIPS code |
| POP_DENSITY | string | Urban / suburban / rural |
| E_POV | decimal | Persons below poverty |
| E_UNEMP | decimal | Unemployed persons |
| E_PCI | decimal | Per capita income |
| E_NOHSDP | decimal | No HS diploma |
| E_AGE65 | decimal | Elderly (65+) |
| E_LIMENG | decimal | Limited English |
| E_NOVEH | decimal | No vehicle |
| E_UNINSUR | decimal | Uninsured |
| RPL_THEMES | decimal | Overall SVI (0=low, 1=high vulnerability) |
| RPL_THEME1 | decimal | SVI: socioeconomic |
| RPL_THEME2 | decimal | SVI: household/disability |
| RPL_THEME3 | decimal | SVI: minority/language |
| RPL_THEME4 | decimal | SVI: housing/transport |
| ADI_NATRANK | decimal | ADI national percentile (1-100) |
| ADI_STATERNK | decimal | ADI state decile (1-10) |
| RE_MAX | string | Most probable R/E (imputed) |
| RE_MAX_PROB | decimal | Confidence of imputed R/E |

---

# 3. Member Event Cost

## Silver: tbl_member_bis_ip_events

**Purpose**: Inpatient hospital admissions — one row per admission. Costs, length of stay, ICU days, readmission tracking.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| admit_dt | date | Admission date |
| discharge_dt | date | Discharge date |
| los | int | Length of stay (days) |
| billed_amt | double | Total billed |
| allowed_amt | double | Total allowed |
| paid_amt | double | Total paid |
| claims | int | Claim count |
| readm_elig_ind | int | Readmission-eligible |
| readm_readmission_ind | int | Was a readmission |
| icu_days | int | ICU days |
| ccu_days | int | Cardiac care days |
| nicu_days | int | Neonatal ICU days |
| psych_days | int | Psychiatric days |
| rehab_days | int | Rehabilitation days |

## Silver: tbl_member_bis_op_events

**Purpose**: Outpatient events — ER visits, surgeries, costs, and NYU avoidable-ED classification.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| OP_EVENTS | int | Total outpatient events |
| ER_VISITS | int | ER visit count |
| DAYS_SINCE_LAST_ER | int | Days since last ER |
| OP_SURG_VISITS | int | Outpatient surgeries |
| OP_OTHER_VISITS | int | Other OP visits |
| OP_BILLED_AMT | decimal | OP billed amount |
| OP_ALLOWED_AMT | decimal | OP allowed amount |
| OP_PAID_AMT | decimal | OP paid amount |
| OP_CLAIMS | int | OP claim count |
| ASC_VISITS | int | Ambulatory surgery center visits |
| NYU_NON_EMER_PCT | decimal | % ER visits that were non-emergent |
| NYU_EMER_PRI_CARE_PCT | decimal | % treatable in primary care |
| NYU_EMER_DEPT_PCT | decimal | % ED truly needed |

## → Gold: tbl_member_event_cost

**What it produces**: Combined utilization and cost view — inpatient + outpatient per member.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| ER_VISITS | int | Emergency room visits |
| DAYS_SINCE_LAST_ER | int | ER recency |
| OP_EVENTS | int | Total outpatient events |
| OP_SURG_VISITS | int | Outpatient surgeries |
| OP_BILLED_AMT | decimal | OP billed |
| OP_PAID_AMT | decimal | OP paid |
| NYU_NON_EMER_PCT | decimal | % non-emergent (avoidable) |
| NYU_EMER_PRI_CARE_PCT | decimal | % primary-care treatable |
| IP_ADMITS | int | Inpatient admissions |
| IP_DAYS | int | Total inpatient days |
| IP_BILLED_AMT | decimal | IP billed |
| IP_PAID_AMT | decimal | IP paid |
| ICU_DAYS | int | ICU days |
| READM_READMISSIONS | int | Readmissions (within 30 days) |
| PSYCH_DAYS | int | Psychiatric days |
| NICU_DAYS | int | Neonatal ICU days |
| ACO_NAME | string | Attributed ACO |
| ACO_PARTICIPATION_IND | int | 1 = ACO participant |

---

# 4. Clinical Conditions & Risk Scores

## Silver: tbl_member_bis_dxcg_v6_clinical_condition

**Purpose**: DxCG v6 clinical condition category indicators — 31 ACHCC binary flags per member.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| DXCG_MODEL_POP | string | Model population segment |
| ACHCC_1 through ACHCC_31 | int | Clinical condition categories (1 = present) |

## Silver: tbl_member_bis_dxcg_v6_risk_scores

**Purpose**: Concurrent and prospective risk scores for medical, pharmacy, and hospitalization cost prediction.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| CLIN_CATEG_NM | string | Clinical category name |
| CLIN_COND_GRP_NM | string | Clinical condition group |
| COST_CAT_CODE | int | Cost category code |
| CONC_MED_MED_RISK | decimal | Concurrent medical risk |
| CONC_MED_TOT_RISK | decimal | Concurrent total risk |
| PROSP_MED_MED_RISK | decimal | Prospective medical risk |
| PROSP_MED_TOT_RISK | decimal | Prospective total risk |

## Silver: tbl_member_bis_dx_risk_factors

**Purpose**: Diagnosis-based behavioral and physical risk indicators.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| DX_HOMEBOUND_IND | int | Homebound |
| DX_HIST_ALCOHOL_IND | int | Alcohol use history |
| DX_HIST_SMOKING_IND | int | Smoking history |
| DX_HIST_OSTEOPENIA_IND | int | Osteopenia |
| DX_HIST_ABNORMAL_GAIT_IND | int | Abnormal gait |
| DX_HIST_NEURO_DEFICIT_IND | int | Neurological deficit |
| DX_HIST_WEAKNESS_IND | int | Weakness |
| DX_HIST_AGE_DEBILITY_IND | int | Age-related debility |
| DX_HIST_FALL_IND | int | Fall history |
| DX_HIST_MOBILITY_IND | int | Mobility impairment |

## → Gold: tbl_member_clinicalcondition_and_riskscores

**What it produces**: Complete clinical risk profile — conditions, risk scores, risk factors, and medication adherence.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| ACHCC_01 – ACHCC_31 | int | Clinical condition categories (1 = present) |
| DXCG_PROSP_MED | decimal | Prospective medical cost risk |
| DXCG_PROSP_RX | decimal | Prospective pharmacy cost risk |
| DXCG_PROSP_HOSP | decimal | Prospective hospitalization risk |
| DXCG_CONC_MED | decimal | Concurrent medical risk |
| CC_HYPERTENSION_IND | int | Has hypertension |
| CC_TYPE1_DIABETES_IND | int | Has Type 1 diabetes |
| CC_COMORBID_DIABETES_IND | int | Comorbid diabetes |
| CC_KIDNEY_FAILURE_IND | int | Kidney failure |
| CC_HIV_IND | int | HIV |
| DX_HIST_FALL_IND | int | History of falls |
| DX_HIST_SMOKING_IND | int | History of smoking |
| DX_HIST_ALCOHOL_IND | int | Alcohol use |
| DX_HIST_MOBILITY_IND | int | Mobility impairment |
| DX_HOMEBOUND_IND | int | Homebound |
| PDC_DIABETES | decimal | Medication adherence — diabetes (0–1) |
| DIABETES_IS_ADHERENT | int | 1 = adherent (PDC ≥ 0.8) |
| PDC_HYPERTENSION | decimal | Medication adherence — hypertension |
| HYPERTENSION_IS_ADHERENT | int | 1 = adherent |
| PDC_STATINS | decimal | Medication adherence — statins |
| STATINS_IS_ADHERENT | int | 1 = adherent |

---

# 5. Financials & Claims

## Silver: tbl_member_bis_cost

**Purpose**: Medical claims cost summary — claim counts and paid amounts by service category, PMPM, medical vs Rx split.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| FOP_CLM_CNT | int | Facility outpatient claims |
| FOP_AMT | decimal | Facility outpatient paid |
| FIP_CLM_CNT | int | Facility inpatient claims |
| FIP_AMT | decimal | Facility inpatient paid |
| PROF_CLM_CNT | int | Professional claims |
| PROF_AMT | decimal | Professional paid |
| RX_CLM_CNT | int | Pharmacy claims |
| RX_AMT | decimal | Pharmacy paid |
| TOTAL_EXPEND | decimal | Total expenditure (med + Rx) |
| TOTAL_MED | decimal | Total medical spend |
| TOTAL_PMPM | decimal | Per-member-per-month cost |
| MED_PMPM | decimal | Medical PMPM |
| RX_PMPM | decimal | Pharmacy PMPM |
| MED_EXPEND_PCT | decimal | Medical as % of total |
| RX_EXPEND_PCT | decimal | Rx as % of total |

## Silver: tbl_member_bis_rx_clms

**Purpose**: Pharmacy claims aggregated summary — annual and quarterly Rx fill counts, costs, mail vs retail.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| RX_CLAIMS | string | Rx claims reference |
| ANNUAL_DAYS_SUPPLY | int | Annual total days supply |
| ANNUAL_RX_CNT | int | Annual fill count |
| ANNUAL_RX_ALLOW_AMT | decimal | Annual Rx allowed |
| ANNUAL_RX_COPAY_AMT | decimal | Annual Rx copay |
| ANNUAL_RX_TRUE_OOP_AMT | decimal | Annual Rx out-of-pocket |
| ANNUAL_RX_MAIL_CNT | int | Mail-order fills |
| ANNUAL_RX_RETAIL_CNT | int | Retail pharmacy fills |
| ANNUAL_GCN_CNT | int | Distinct generic drugs |
| ANNUAL_NDC_CNT | int | Distinct NDCs |

## Silver: tbl_member_bis_rx_pdc_clms

**Purpose**: Pharmacy fill-level detail for Proportion of Days Covered (PDC) medication adherence calculation.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| FILL_DT | date | Prescription fill date |
| DAYS_SUPPLY | int | Days supply this fill |
| FIRST_FILL_DATE | date | First fill for this drug class |
| RUNNING_DAYS_SUPPLY | int | Cumulative days supply |
| DRUG_CLASS_NAME | string | Drug class (antidepressants, statins, etc.) |
| NDC | string | National Drug Code |
| GNRC_NM | string | Generic drug name |
| RX_MAIL_FLAG | int | 1 = mail order |
| RX_RETAIL_FLAG | int | 1 = retail pharmacy |

## → Gold: tbl_member_bis_financials_and_claims

**What it produces**: Consolidated financial profile — medical + pharmacy cost summary per member.

| Column | Type | Description |
| --- | --- | --- |
| MEMBER_ID | string | Member identifier |
| FOP_CLM_CNT | int | Facility outpatient claims |
| FOP_AMT | decimal | Facility outpatient paid |
| FIP_CLM_CNT | int | Facility inpatient claims |
| FIP_AMT | decimal | Facility inpatient paid |
| PROF_CLM_CNT | int | Professional claims |
| PROF_AMT | decimal | Professional paid |
| RX_CLM_CNT | int | Pharmacy claims |
| RX_AMT | decimal | Pharmacy paid |
| TOTAL_EXPEND | decimal | Total expenditure (med + Rx) |
| TOTAL_MED | decimal | Total medical spend |
| TOTAL_PMPM | decimal | Per-member-per-month cost |
| MED_PMPM | decimal | Medical PMPM |
| RX_PMPM | decimal | Pharmacy PMPM |
| MED_EXPEND_PCT | decimal | Medical % of total |
| RX_EXPEND_PCT | decimal | Rx % of total |
| ANNUAL_RX_CNT | int | Annual Rx fills |
| ANNUAL_DAYS_SUPPLY | int | Annual days supply |
| ANNUAL_RX_ALLOW_AMT | decimal | Annual Rx allowed |
| ANNUAL_RX_COPAY_AMT | decimal | Annual Rx copay |
| ANNUAL_RX_TRUE_OOP_AMT | decimal | Annual Rx out-of-pocket |
| ANNUAL_RX_MAIL_CNT | int | Mail-order fills |
| ANNUAL_RX_RETAIL_CNT | int | Retail fills |

---

# How Gold Tables Connect

All five Gold tables join on `MEMBER_ID`, enabling a **360° member view**:

```
┌─────────────────────────────┐
│     tbl_member_scaffold     │  WHO: demographics, enrollment, contact
└─────────────┬───────────────┘
              │ MEMBER_ID
    ┌─────────┼─────────────────────────────────┐
    │         │                                 │
    ▼         ▼                                 ▼
┌────────┐ ┌──────────────┐ ┌────────────────────────────────────┐
│  sdoh  │ │  event_cost  │ │  clinicalcondition_and_riskscores  │
│ WHERE  │ │ WHAT HAPPENED│ │  HOW SICK / HOW RISKY              │
└────────┘ └──────────────┘ └────────────────────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │  financials_and_claims        │
                        │  HOW MUCH IT COSTS            │
                        └───────────────────────────────┘
```

| Gold Table | Question it answers |
| --- | --- |
| tbl_member_scaffold | **Who** is this member? Where do they live? What plan are they on? |
| tbl_member_sdoh | **Where** do they live and how vulnerable is their neighborhood? |
| tbl_member_event_cost | **What** healthcare services did they use (ER, hospital, surgery)? |
| tbl_member_clinicalcondition_and_riskscores | **How sick** are they and what's their predicted future risk? |
| tbl_member_bis_financials_and_claims | **How much** does their care cost? |
