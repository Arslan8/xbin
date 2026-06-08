import xbin
import r2pipe
import os
import json
import time

# Radare2 Function Boundary Tool
# Uses r2pipe to perform rapid function discovery

@xbin.plugin(name="radare_boundaries", category="function_boundary")
class RadareBoundaryWorker:
    def on_new_binary(self, binary_path: str, requested_goals: list):
        if "function_boundary" not in requested_goals:
            return

        filename = os.path.basename(binary_path)
        print(f"[*] Radare2 searching for boundaries in: {filename}")
        
        try:
            # Open without relocs for speed
            r2 = r2pipe.open(binary_path, flags=['-n'])
            
            # Simple analysis (aa)
            print("[*] Running standard analysis (aa)...")
            r2.cmd("aa")
            
            # Get functions list with offsets and sizes
            print("[*] Extracting function boundaries...")
            functions = r2.cmdj("afllj")
            
            if not functions:
                print("[-] No functions found by Radare.")
                return

            from xbin.sdk import _current_worker
            
            count = 0
            for func in functions:
                addr = func['offset']
                size = func.get('size', 0)
                
                _current_worker.post_result(
                    item_key=hex(addr),
                    data={
                        "end": hex(addr + size),
                        "size": size,
                        "name_hint": func.get('name', f"fcn.{hex(addr)}")
                    },
                    confidence=0.85 # Radare is fast but slightly less precise than angr
                )
                count += 1
                
            print(f"[SUCCESS] Radare2 recovered {count} boundaries for {filename}")
            r2.quit()
            
        except Exception as e:
            print(f"[ERROR] Radare2 boundary analysis failed: {e}")

if __name__ == "__main__":
    xbin.start_worker()
