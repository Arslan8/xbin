# xbin SDK Reference Guide

The `xbin` SDK is a reactive, event-driven framework that allows you to build binary analysis plugins that collaborate via a central blackboard.

## 🏗️ System Architecture

The following diagram illustrates how the **Orchestrator**, **Redis (Blackboard)**, and **Workers** interact:

```text
       +-----------------------+
       |     User Dashboard    |
       |  (FastAPI + Web UI)   |
       +-----------+-----------+
                   | (REST)
       +-----------v-----------+          +-----------------------+
       |     ORCHESTRATOR      | <------> |   REDIS BLACKBOARD    |
       |    (Message Router)   |  (gRPC)  |   (State & Pub/Sub)   |
       +-----------+-----------+          +-----------------------+
                   |
     +-------------+-------------+-------------+
     |             |             |             |
+----v-----+  +----v-----+  +----v-----+  +----v-----+
| Worker A |  | Worker B |  | Validator|  |  Ranker  |
| (angr)   |  | (radare) |  | (Checks) |  | (Judges) |
+----------+  +----------+  +----------+  +----------+
```

## 🔄 The Analysis Lifecycle

1. **Producer** (Analyzer) posts a new hypothesis.
2. **Orchestrator** saves it and broadcasts a `BLACKBOARD_UPDATE`.
3. **Validator** hears the update and decides to "vouch" for it.
4. **Ranker** hears the vouch, applies a custom heuristic, and issues an `update_rank` command.
5. **Orchestrator** applies the new score.

```text
 [ ANALYZER ]          [ ORCHESTRATOR ]          [ VALIDATOR ]          [ RANKER ]
      |                      |                        |                     |
      | -- post_result() --> |                        |                     |
      |                      | -- on_update event --> |                     |
      |                      |                        | -- validation() --> |
      |                      | <----------------------+                     |
      |                      | -- on_update event ------------------------> |
      |                      |                                              |
      |                      | <----------------------- update_rank() ------|
      |                      | -- Score Overridden! --> [ DASHBOARD / UI ]  |
```

## 🚀 Quick Start Example: "The Hello World Worker"

This example shows a plugin that identifies a "Hello World" string and a validator that confirms it.

### The Analyzer (Producer)
This tool searches for a specific string and posts a symbol hypothesis.

```python
import xbin
from xbin.sdk import _current_worker

@xbin.plugin(name="hello_finder", category="symbol_matching")
class HelloFinder:
    def on_new_binary(self, binary_path, requested_goals):
        if "symbol_matching" not in requested_goals:
            return

        with open(binary_path, "rb") as f:
            data = f.read()
            if b"Hello, World!" in data:
                # We found it! Post the result to the blackboard
                _current_worker.post_result(
                    item_key="0x401000", 
                    data="main_entry_greeting", 
                    confidence=0.8
                )

if __name__ == "__main__":
    xbin.start_worker()
```

### The Validator (Verifier)
This tool listens for the `hello_finder`'s output and vouches for it if it meets certain criteria.

```python
import xbin
from xbin.sdk import _current_worker

@xbin.plugin(name="hello_validator", category="symbol_matching", is_validator=True)
class HelloValidator:
    def on_update(self, category, item_key, new_hypothesis, top_hypothesis):
        # If the new finding is our target string, vouch for it!
        if category == "symbol_matching" and new_hypothesis['data'] == "main_entry_greeting":
            _current_worker.post_validation(item_key=item_key, target_id="TOP")

if __name__ == "__main__":
    xbin.start_worker()
```

### The Ranker (Judge)
Rankers listen to both analysis and validation events and apply global ranking heuristics.

```python
import xbin
from xbin.sdk import _current_worker

@xbin.plugin(name="hello_ranker", category="symbol_matching", is_ranker=True)
class HelloRanker:
    def on_update(self, category, item_key, new_hypothesis, top_hypothesis):
        # We only care about symbol matching updates
        if category != "symbol_matching":
            return

        # Heuristic: If we have any validators, boost the score to a high fixed value
        v_count = len(top_hypothesis.get('validators', []))
        if v_count >= 1:
            _current_worker.update_rank(item_key, top_hypothesis['id'], 2.0)

if __name__ == "__main__":
    xbin.start_worker()
```

---

## 🛠️ API Reference

### Decorator: `@xbin.plugin`
Registers your class with the orchestrator.
- `name` (str): Unique tool ID.
- `category` (str): Blackboard category (e.g., `cfg_generation`).
- `is_validator` (bool): Set to `True` for verification-only tools.
- `is_ranker` (bool): Set to `True` for tools that judge and re-rank hypotheses.

### Callbacks (Implemented in your class)
...
#### `on_update(self, category, item_key, new_hypothesis, top_hypothesis)`
Called every time the blackboard changes. Use this to build collaborative tools, Validators, or Rankers.
...
### Methods (via `xbin.sdk._current_worker`)
#### `post_result(item_key, data, confidence)`
Submit a new finding. If the data is unique, it creates a new hypothesis. If it matches an existing one, it acts as a vouch.
- `item_key`: Unique subject identifier.
- `data`: Any JSON-serializable object.
- `confidence`: Your certainty (0.0 to 1.0).

#### `post_validation(item_key, target_id="TOP", confidence=1.0)`
Specifically for validators. Boosts the score of an existing hypothesis.
- `target_id`: The ID of the hypothesis to vouch for, or `"TOP"` for the leader.

#### `update_rank(item_key, target_id, new_score)`
Specifically for Rankers. Updates the absolute consensus score of a hypothesis.
- `item_key`: The subject identifier.
- `target_id`: The unique hash ID of the hypothesis.
- `new_score`: The new float score.

#### `get_analysis(category, item_key=None)`
...
