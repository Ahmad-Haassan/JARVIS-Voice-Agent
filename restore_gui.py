import json
import os

log_path = r"C:\Users\Ahmad\.gemini\antigravity\brain\c37e7a07-dac4-494c-83a0-ccc3c4994885\.system_generated\logs\overview.txt"
output_path = r"C:\Users\Ahmad\Desktop\vc.agent\gui\main_window.py"

print(f"Reading logs from: {log_path}")
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        if "main_window.py" in line and "write_to_file" in line:
            try:
                data = json.loads(line)
                for tc in data.get("tool_calls", []):
                    if tc.get("name") == "write_to_file" and "main_window.py" in tc["args"]["TargetFile"]:
                        content = tc["args"]["CodeContent"]
                        # Handle double encoding if present
                        if content.startswith('"') and content.endswith('"'):
                            try:
                                content = json.loads(content)
                            except:
                                pass
                        
                        # Fix actual newlines if they are literal \n
                        content = content.replace("\\n", "\n")
                        
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        with open(output_path, "w", encoding="utf-8") as out:
                            out.write(content)
                        print(f"Successfully restored to: {output_path}")
                        exit(0)
            except Exception as e:
                print(f"Error parsing line: {e}")
                continue
print("Could not find main_window.py in logs.")
exit(1)
