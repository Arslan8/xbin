import xbin
import os
import time

# External Boundary Ranker
# Listens to both initial analysis and validator vouches.
# Applies a custom judgment to the score.

@xbin.plugin(name="boundary_ranker", category="function_boundary", is_ranker=True)
class BoundaryRanker:
    def on_update(self, category, item_key, new_hypothesis, top_hypothesis):
        # We only rank function boundaries
        if category != "function_boundary":
            return
            
        # Ignore our own rank updates to avoid loops
        # Our update broadcasts 'is_rank_update' in the event
        # (Note: In a real SDK, we'd add this to the callback signature)
        
        validators = top_hypothesis.get('validators', [])
        v_count = len(validators)
        raw_conf = top_hypothesis.get('raw_conf', 1.0)
        
        # Heuristic: 
        # Base score is just raw confidence.
        # Every validator gives a +0.5 boost.
        # If we have 2+ validators, we give a 'Consensus Bonus' of +1.0.
        
        new_score = raw_conf + (v_count * 0.5)
        if v_count >= 2:
            new_score += 1.0
            
        # Only update if the score is significantly different
        if abs(new_score - top_hypothesis.get('score', 0)) > 0.01:
            print(f"[RANKER] Judging {item_key}: {v_count} vouches -> New Score: {new_score}")
            from xbin.sdk import _current_worker
            _current_worker.update_rank(
                item_key=item_key, 
                target_id=top_hypothesis['id'], 
                new_score=new_score
            )

if __name__ == "__main__":
    xbin.start_worker()
