import xbin
import angr
import os
import time

# Function Boundary Discovery Tool
# Uses angr to recover exact function boundaries

@xbin.plugin(name="angr_boundaries", category="function_boundary")
class AngrBoundaryWorker:
    def on_new_binary(self, binary_path: str, requested_goals: list):
        if "function_boundary" not in requested_goals:
            return

        print(f"[*] Angr searching for boundaries in: {binary_path}")
        filename = os.path.basename(binary_path)
        
        try:
            # Load project without libs for speed
            proj = angr.Project(binary_path, auto_load_libs=False)
            
            # Generate CFG to recover function boundaries
            print("[*] Running CFGFast to recover boundaries...")
            cfg = proj.analyses.CFGFast()
            
            from xbin.sdk import _current_worker
            
            count = 0
            for addr, func in cfg.kb.functions.items():
                # Post start address as key, with end and size as data
                _current_worker.post_result(
                    item_key=hex(addr),
                    data={
                        "end": hex(addr + func.size),
                        "size": func.size,
                        "name_hint": func.name
                    },
                    confidence=1.0 # angr is very confident in its CFG recovery
                )
                count += 1
                
            print(f"[SUCCESS] Recovered {count} function boundaries for {filename}")
            
        except Exception as e:
            print(f"[ERROR] Angr boundary analysis failed: {e}")

if __name__ == "__main__":
    xbin.start_worker()
