---
type: state_anchor
domain: compliance
version: 0.5.0
status: CANONICAL
last_canonical_audit: 2026-03-15
last_canonical_auditor: J. Rivera (COO)
generated_at: 2026-01-10
---

# Acme Industrial Corp — Compliance State Anchor

*This is a fictional example for illustrative purposes. All entities,
figures, and facts are invented.*

---

# ENTITIES

## Acme Industrial Corp (AIC)
- **Legal name:** Acme Industrial Corp [CONFIRMED]
- **Entity type:** S-Corp [CONFIRMED]
- **Owner:** Jordan Rivera — sole shareholder [CONFIRMED]
- **State of incorporation:** Delaware (operates primarily in Ohio) [CONFIRMED]
- **EIN:** stored in `.env` as `AIC_EIN` [CONFIRMED]
- **Fiscal year:** Calendar year (Jan 1 – Dec 31) [CONFIRMED]
- **NAICS code:** 332710 — Machine Shops [CONFIRMED]
- **Annual revenue:** ~$4.2M gross (2025 actuals) [CONFIRMED]
- **Business model:** Contract machining for automotive OEMs; no inventory
  held by AIC (parts machined to spec and shipped direct) [CONFIRMED]
- **Primary accountant:** M. Chen, Lakeside Accounting (handles 1120-S,
  OH commercial activity tax, federal estimated tax) [CONFIRMED]

## Acme Performance LLC (AP)
- **Legal name:** Acme Performance LLC [CONFIRMED]
- **Entity type:** LLC taxed as sole proprietorship [CONFIRMED]
- **Owner:** Jordan Rivera [CONFIRMED]
- **Relationship to AIC:** Separate entity; Jordan's side business in
  performance parts retail. No shared employees or inventory with AIC. [CONFIRMED]
- **Revenue:** ~$180K/yr gross [CONFIRMED]
- **State:** Ohio — registered as foreign LLC in two additional states [CONFIRMED]

## Jordan Rivera (Operator)
- **Role in AIC:** Sole shareholder + President (officer W-2) [CONFIRMED]
- **Role in AP:** Sole member [CONFIRMED]
- **Filing status:** MFJ (Married Filing Jointly) with spouse Alex Rivera [CONFIRMED]
- **Day income:** AIC officer W-2 $95,000 + AIC K-1 pass-through ~$620K (2025) [CONFIRMED]
- **Estimated tax cadence:** Quarterly via Form 1040-ES [CONFIRMED]

---

# OPERATIONAL POSTURE

- **Federal 1120-S:** Filed annually, due Mar 15 (or extended to Sep 15).
  M. Chen handles. Last filed: Sep 2025 for FY2024. [CONFIRMED]
- **Ohio CAT (Commercial Activity Tax):** Annual filing, due May 10.
  M. Chen handles. [CONFIRMED]
- **Estimated federal tax:** Quarterly payments — Apr 15, Jun 15, Sep 15,
  Jan 15. Jordan pays based on prior-year safe harbor (~$41K/qtr). [CONFIRMED]
- **Payroll:** AIC has 12 employees. Third-party payroll provider
  (FastPayroll Inc.) handles 941 filings. [CONFIRMED]
- **Sales tax:** AIC sells B2B to OEMs; exempt under Ohio manufacturing
  exemption. AP collects and remits OH sales tax on retail sales. [CONFIRMED]

---

# OPEN POSITIONS

1. 2026-01-15 · **AP multi-state nexus:** AP shipped to customers in MI and
   IN last year. Need to determine whether economic nexus thresholds were
   crossed and whether retroactive registration is required.
   **Blocked on:** M. Chen's nexus analysis (requested 2026-01-15, ETA TBD).

2. 2026-02-03 · **AIC equipment depreciation:** Two CNC machines purchased
   Q4 2025 (~$340K total). Determining optimal depreciation treatment:
   Section 179 vs bonus depreciation vs MACRS spread. Decision deferred to
   tax planning session before 2025 return is filed.
   **Target resolution:** Before March 2026.

3. 2026-02-20 · **Jordan's stock basis carryforward:** M. Chen flagged a
   possible basis miscalculation from 2022 distributions. Need to verify
   Form 7203 for 2022 and 2023.
   **Blocked on:** Prior-year return documents from M. Chen's files.

---

# CANONICAL RULINGS

R-001 · 2026-01-12 · AIC · [s-corp, compensation] · Jordan's officer W-2
        must be set at $95K/yr minimum for 2025 and 2026 to satisfy reasonable
        compensation requirements given AIC's revenue level and Jordan's role.
        Source: compliance-session/2026-01-12/turn-003
        Supersedes: none

R-002 · 2026-01-12 · AP · [sole-prop, structure] · AP should remain a
        sole-prop LLC (not elect S-Corp status) until AP gross revenue
        consistently exceeds $300K/yr. Below that threshold, S-Corp election
        creates administrative overhead that exceeds the payroll tax savings.
        Source: compliance-session/2026-01-12/turn-007
        Supersedes: none

R-003 · 2026-02-03 · AIC · [deductions, equipment] · AIC's standard policy
        for equipment purchases under $50K: elect Section 179 for full
        first-year deduction. For purchases over $50K, defer to M. Chen for
        tax planning on a case-by-case basis. (Open Position #2 is above
        threshold — awaiting M. Chen.)
        Source: compliance-session/2026-02-03/turn-002
        Supersedes: none

R-004 · 2026-02-15 · AIC+AP · [entity-structure] · AIC and AP must maintain
        strict operational separation: no shared employees, no intercompany
        loans, no shared equipment without a written fair-market-value lease.
        Commingling would risk AIC's S-Corp status and expose both entities
        to IRS recharacterization.
        Source: compliance-session/2026-02-15/turn-001
        Supersedes: none

R-005 · 2026-03-10 · Jordan · [estimated-tax] · Prior-year safe harbor
        (100% of prior year liability if AGI ≤ $150K; 110% if AGI > $150K)
        is the correct estimated-tax strategy for 2026 given income
        variability. Do not use current-year method without M. Chen review.
        Source: compliance-session/2026-03-10/turn-005
        Supersedes: none

---

# REVOKED / SUPERSEDED

*(None as of v0.5.0)*
