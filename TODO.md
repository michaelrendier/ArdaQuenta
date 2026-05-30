# DerivationEngineViewer — TODO

## Diagnostics Interface

- [ ] **OBD-II** — On-Board Diagnostics II live data display
  - Standard PID readout (engine load, MAP, RPM, timing advance, fuel trim, etc.)
  - Custom PID support for SMMIP-specific channels (CKP, CMP, sedenion charge, Fermat proximity)
  - DTC fault code display with SMMIP interpretations
  - Readiness monitor status panel

- [ ] **VCDS / VAG-COM (Volkswagen)** — Ross-Tech VCDS protocol integration
  - VAG-specific adaptation channel display
  - Long-term / short-term fuel trim visualization
  - Injection timing and quantity readout
  - Controller identification (part number, coding, WSC)
  - Guided fault code interpretation against SMMIP DTC table
