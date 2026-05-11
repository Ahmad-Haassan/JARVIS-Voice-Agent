import json
import os
import re

log_path = r"C:\Users\Ahmad\.gemini\antigravity\brain\c37e7a07-dac4-494c-83a0-ccc3c4994885\.system_generated\logs\overview.txt"
output_path = r"C:\Users\Ahmad\Desktop\vc.agent\gui\main_window.py"

print(f"Scanning for main_window.py in {log_path}...")
best_content = ""
max_len = 0

with open(log_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "main_window.py" in line:
            try:
                data = json.loads(line)
                
                # Check Tool Response (view_file output)
                if data.get("type") == "TOOL_RESPONSE":
                    content = data.get("content", "")
                    if len(content) > max_len:
                        max_len = len(content)
                        best_content = content
                
                # Check Model/Planner Response (write_to_file input)
                if "tool_calls" in data:
                    for tc in data["tool_calls"]:
                        if "main_window.py" in str(tc):
                            # Try to get the actual CodeContent argument
                            try:
                                code = tc["args"]["CodeContent"]
                                if len(code) > max_len:
                                    max_len = len(code)
                                    best_content = code
                            except:
                                pass
            except:
                continue

if max_len > 0:
    print(f"Found candidate content with length {max_len}")
    
    # Clean up the content
    # If it's a tool response, it might have line numbers from view_file (e.g. "1: import...")
    if "1: " in best_content[:100] and "2: " in best_content[:200]:
        print("Detected view_file format, removing line numbers...")
        lines = best_content.split("\n")
        cleaned_lines = []
        for line in lines:
            # Remove "123: " prefix
            match = re.match(r"^\d+: (.*)", line)
            if match:
                cleaned_lines.append(match.group(1))
            else:
                cleaned_lines.append(line)
        final_code = "\n".join(cleaned_lines)
    else:
        final_code = best_content
    
    # Handle JSON string escapes if it's still double-encoded
    if final_code.startswith('"') and final_code.endswith('"'):
        try:
            final_code = json.loads(final_code)
        except:
            pass
    
    # One more check for literal \n
    if "\\n" in final_code and "\n" not in final_code:
         final_code = final_code.replace("\\n", "\n")

    with open(output_path, "w", encoding="utf-8") as out:
        out.write(final_code)
    print(f"Successfully restored {len(final_code)} bytes to {output_path}")
else:
    print("Could not find any suitable content in logs.")
