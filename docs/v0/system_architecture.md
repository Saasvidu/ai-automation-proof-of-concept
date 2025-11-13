# 🏗️ System Architecture Plan: NLP to Abaqus API

Our system is a **three-tier architecture** designed to isolate the linguistic complexity (**Tier 1**) from the engineering execution (**Tier 3**) using a highly structured intermediate format (**Tier 2**).

---, machine-readable data.


## **Tier 1: The Agentic / Linguistic Layer (The Brain)**

This layer interprets human intent and translates it into structured
**Component:** NLP Agent (e.g., an LLM trained or prompted to act as a Simulation Assistant)
**Input:** Natural Language Request (e.g., “Simulate a copper bar, 100 mm long, hitting a wall at $180~m/s$.”)
**Output:** JSON Configuration File (Tier 2)

**Key Task:**
Linguistic parsing and parameter validation.
The Agent must identify all necessary parameters (`L`, `V`, Material Type, Test Type) and ensure they are valid (e.g., `180 m/s` is a number, *Copper* is a defined material).

---

## **Tier 2: The Interface Layer (The Contract)**

This is the most critical component, serving as the formal interface between the AI and the engineering software.
It provides a structured, common format for all required simulation parameters.

**Component:** `config.json` (JSON Configuration File)
**Structure:** A flexible schema that includes a high-level test type switch, followed by nested, detailed parameters.

**Control Parameter (The Switch):**

```json
"TEST_TYPE": "Taylor Impact"
```

**Core Parameters (Nested):**

```json
"GEOMETRY": {
  "length_mm": 100,
  "diameter_mm": 10,
  "height_mm": 20
},
"MATERIAL": {
  "name": "Copper",
  "youngs_modulus_Pa": 110e9,
  "poisson_ratio": 0.34
},
"LOADING": {
  "initial_velocity_m_per_s": 180,
  "impact_duration_ms": 5
},
"DISCRETIZATION": {
  "element_size_mm": 1,
  "solver_type": "explicit"
}
```

---

## **Tier 3: The Engineering / Execution Layer (The Engine)**

This layer consumes the structured data and executes the simulation using commercial software APIs.

**Component:** `simulation_runner.py` (Abaqus Python API Script)
**Input:** Parsed data from the JSON Configuration File (Tier 2)

**Logic:**

1. **Read JSON:** Import and parse the configuration file.
2. **Logic Switch:** Use the `TEST_TYPE` variable to execute the correct block of Abaqus API commands (e.g., run `Taylor_Impact_Setup()` if `TEST_TYPE == "Taylor Impact"`).
3. **Setup and Run:** Pass the remaining parameters (e.g., `length_mm`) directly into the Abaqus API calls.

**Output:** Abaqus simulation results (`.odb` file), which can be post-processed for displacement, strain, and stress data.
