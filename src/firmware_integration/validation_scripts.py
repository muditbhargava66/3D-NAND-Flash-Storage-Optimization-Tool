# src/firmware_integration/validation_scripts.py

import subprocess

class ValidationScriptExecutor:
    def __init__(self, script_dir):
        self.script_dir = script_dir

    def execute_script(self, script_name, args):
        script_path = f"{self.script_dir}/{script_name}"
        command = [script_path] + args
        try:
            output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
            return output
        except subprocess.CalledProcessError as e:
            print(f"Script execution failed with error code {e.returncode}:")
            print(e.output)
            raise