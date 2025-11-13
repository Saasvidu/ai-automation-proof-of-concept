# agent.py - Tier 1: The NLP Agent (Powered by Gemini)
# -----------------------------------------------------
# --- 1. Import Modules ---
# -----------------------------------------------------
import os
import subprocess
import json
try:
    # NEW: Import Google Gemini
    import google.generativeai as genai
except ImportError:
    print("Error: 'google-generativeai' library not found.")
    print("Please install it: pip install google-generativeai")
    raise

# -----------------------------------------------------
# --- 2. Setup LLM Client & System Prompt ---
# -----------------------------------------------------

# THIS FUNCTION IS UNCHANGED
def create_system_prompt():
    """
    Creates the master prompt that forces the LLM
    to generate valid JSON.
    """
    return """
You are an expert Abaqus Finite Element Analyst. Your SOLE purpose is to convert a user's natural language request into a precise JSON configuration file for a simulation.

You MUST follow these rules:
1.  **JSON ONLY:** You MUST ONLY output the raw JSON text. Do NOT include any other text, explanations, or markdown tags like ```json ... ```.
2.  **SCHEMA:** The JSON MUST conform to the following schema.
3.  **DEFAULTS:** If the user does not provide a value, you MUST infer a reasonable engineering default.
    * Default material: 'Steel' (E=200e9, v=0.3)
    * Default load: 1000.0 N
    * Default mesh: 10 elements along the longest dimension, 4 in others.
    * Default geometry: If only length is given, assume a 10:1 aspect ratio (e.g., L=1.0 -> W=0.1, H=0.1).

---
## JSON SCHEMA
{
  "MODEL_NAME": "Unique_Model_Name",
  "TEST_TYPE": "CantileverBeam",

  "GEOMETRY": {
    "length_m": 1.0,
    "width_m": 0.1,
    "height_m": 0.1
  },
  "MATERIAL": {
    "name": "Steel",
    "youngs_modulus_pa": 200e9,
    "poisson_ratio": 0.3
  },
  "LOADING": {
    "tip_load_n": 1000.0
  },
  "DISCRETIZATION": {
    "elements_length": 10,
    "elements_width": 4,
    "elements_height": 4
  }
}
---
## EXAMPLE
User: "Sim a 1m long steel beam, 10cm high and wide, with a 1kN load at the tip. Use a 20x4x4 mesh."
Assistant:
{
  "MODEL_NAME": "Cantilever_1m_1kN_20x4x4",
  "TEST_TYPE": "CantileverBeam",
  "GEOMETRY": {
    "length_m": 1.0,
    "width_m": 0.1,
    "height_m": 0.1
  },
  "MATERIAL": {
    "name": "Steel",
    "youngs_modulus_pa": 200e9,
    "poisson_ratio": 0.3
  },
  "LOADING": {
    "tip_load_n": 1000.0
  },
  "DISCRETIZATION": {
    "elements_length": 20,
    "elements_width": 4,
    "elements_height": 4
  }
}
---
Now, process the user's request.
"""

# NEW: This function is rewritten for Gemini
def get_gemini_model(system_prompt):
    """
    Initializes the Gemini client.
    It automatically reads the 'GOOGLE_API_KEY'
    from your environment variables.
    """
    try:
        # Configure the API key
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
        
        # Set up the model generation config
        generation_config = {
            "temperature": 0.0,  # Set to 0 for deterministic JSON output
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 2048,
        }

        # Create the model with the system prompt
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-latest", # Or "gemini-pro"
            generation_config=generation_config,
            system_instruction=system_prompt
        )
        return model
    except Exception as e:
        print(f"Error: Could not initialize Gemini model.")
        print(f"Please make sure your GOOGLE_API_KEY is set.")
        print(f"Details: {e}")
        return None

# -----------------------------------------------------
# --- 3. Agent Core Functions ---
# -----------------------------------------------------

# NEW: This function is rewritten for Gemini
def get_simulation_config_from_gemini(model, user_request):
    """
    Sends the user request to the Gemini model
    and gets the JSON config string back.
    """
    print("Sending request to Gemini...")
    try:
        # The API call is much simpler
        response = model.generate_content(user_request)
        json_string = response.text
        
        # Add robustness: strip markdown tags if the model adds them
        if json_string.startswith("```json"):
            json_string = json_string[7:].strip() # remove ```json\n
        if json_string.endswith("```"):
            json_string = json_string[:-3].strip() # remove ```
            
        return json_string
    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        return None

# THIS FUNCTION IS UNCHANGED
def save_config_and_run_abaqus(json_string, config_path, runner_script_path):
    """
    Step 3: Validate the JSON.
    Step 4: Save config and Run Abaqus.
    """
    
    # --- Step 3: Validate the Prompt (JSON) ---
    try:
        config_data = json.loads(json_string)
        print("\n--- CONFIGURATION GENERATED ---")
        print(json.dumps(config_data, indent=2))
        print("-------------------------------")
    except json.JSONDecodeError:
        print("\n--- LLM VALIDATION FAILED ---")
        print("The LLM did not return valid JSON. Aborting.")
        print("Raw output:", json_string)
        return

    # --- Step 4 (Part 1): Save config file ---
    try:
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        print(f"Configuration file saved to {config_path}")
    except IOError as e:
        print(f"Error saving config file: {e}")
        return

    # --- Step 4 (Part 2): Run Abaqus ---
    script_dir = os.path.dirname(runner_script_path)
    run_env = os.environ.copy()
    run_env["ABAQUS_CONFIG_PATH"] = config_path
    
    # Use -script, as you discovered it's more reliable
    command = ["abaqus", "cae", "-script", os.path.basename(runner_script_path)]
    
    print(f"\nRunning Abaqus command: {' '.join(command)}")
    print("This may take a moment. Check 'abaqus.log' for details.")
    
    try:
        subprocess.run(
            command, 
            env=run_env, 
            cwd=script_dir, 
            check=True, 
            capture_output=True,
            text=True
        )
        print("\n--- Abaqus Run Successful ---")
        print(f"Check 'abaqus.log' and '{config_data['MODEL_NAME']}.odb' for results.")
        
    except subprocess.CalledProcessError as e:
        print("\n--- Abaqus Run FAILED ---")
        print("Abaqus returned a non-zero exit code.")
        print("Check 'abaqus.log' in your directory for the full error message.")
    except FileNotFoundError:
        print("\n--- Abaqus Run FAILED ---")
        print("Error: 'abaqus' command not found.")
        print("Is Abaqus installed and in your system's PATH?")

# -----------------------------------------------------
# --- 4. Main Execution Loop ---
# -----------------------------------------------------
def main():
    print("Initializing Abaqus NLP Agent (Gemini Edition)...")
    
    # Find paths (unchanged)
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()
    config_path = os.path.join(script_dir, "config.json")
    runner_script_path = os.path.join(script_dir, "simulation_runner.py")
    if not os.path.exists(runner_script_path):
        print(f"Error: 'simulation_runner.py' not found in {script_dir}")
        return

    # Create the master prompt
    system_prompt = create_system_prompt()
    
    # Connect to the LLM (MODIFIED)
    model = get_gemini_model(system_prompt)
    if not model:
        return
    print("Gemini Model connected.")
    
    print("Abaqus NLP Agent is ready.")
    
    # --- Step 1: Take User Input ---
    while True:
        print("\n" + "="*50)
        user_request = input("> What simulation would you like to run? (or 'q' to quit)\n> ")
        
        if user_request.lower() in ('q', 'quit', 'exit'):
            break
            
        # --- Step 2: Produce Config File (MODIFIED) ---
        json_string = get_simulation_config_from_gemini(model, user_request)
        
        if json_string:
            # --- Step 3 & 4: Validate and Run (UNCHANGED) ---
            save_config_and_run_abaqus(json_string, config_path, runner_script_path)

    print("Agent shutting down. Goodbye.")

if __name__ == '__main__':
    main()