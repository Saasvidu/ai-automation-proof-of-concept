# 🗺️ Execution Roadmap

This roadmap builds the system from the stable engineering layer (Tier 3) back to the linguistic layer (Tier 1), ensuring a verifiable simulation engine is ready before AI integration.

---

## **Phase 1: Establish the Engine (Tier 3 Mastery)**

**Goal:** Create a robust, parameter-driven Abaqus script for the benchmark case.

* **Select Benchmark:** Commit to the Taylor Impact Test on a copper bar as the primary prototype.
* **Script Development:** Complete the Abaqus Python script for the Dynamic Explicit Taylor Impact Test, including Initial Velocity and Rigid Wall setup.
* **Initial Parameterization:** Replace all hard-coded values in the script with simple Python variables.
* **JSON Integration:** Modify the script so that all variables are read from and assigned by a separate Python function that loads and parses a local `config.json` file.
* **Verification:** Manually edit `config.json` and run the script from the command line (`abaqus cae script=...`). A change in the JSON should successfully change the simulation output.

---

## **Phase 2: Design the Interface (Tier 2 Finalization)**

**Goal:** Finalize the structure of the JSON file to handle multiple test types flexibly.

* **Define Full Schema:** Expand the `config.json` structure to include all necessary parameters not only for Taylor Impact but also for the next simplest case, like the 3-Point Bending test, even if the setup code is a placeholder. This ensures the schema is ready for scaling.
* **Implement Logic Switch:** Introduce the conditional logic (e.g., an if/else block) in the Abaqus Python script to read the `TEST_TYPE` and select the appropriate Abaqus setup code, thereby confirming the Tier 2 → Tier 3 coupling works.

---

## **Phase 3: Integrate the Brain (Tier 1 Development)**

**Goal:** Connect the Natural Language front-end to the stable JSON back-end.

* **Collect Training Data:** Gather pairs of (a) Natural Language Requests and (b) the corresponding perfectly formed JSON configuration files for various cases.
* **Develop/Train the Agent:** Implement the LLM/Agent solution whose sole function is to map the natural language input to the target JSON output.
* **End-to-End Test:** Execute a full end-to-end test: User types a natural language request → Agent outputs JSON → Abaqus script executes → Simulation runs. This systematic approach guarantees we build on a stable foundation.
