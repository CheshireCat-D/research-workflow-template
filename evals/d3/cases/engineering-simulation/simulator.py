"""Original nominal thermal-control simulator, standard library only."""
import json
from pathlib import Path

def simulate(model, scenario):
    dt = model["dt_s"]
    n = round(model["horizon_s"] / dt)
    temperature = scenario["initial_C"]
    rows = []
    for step in range(n + 1):
        ambient = scenario["ambient_C"]
        measured = temperature
        requested_w = (model["loss_W_per_K"] * (model["target_C"] - ambient)
                       + model["gain_W_per_K"] * (model["target_C"] - measured))
        rows.append({"time_s": round(step * dt, 10), "temperature_C": temperature,
                     "requested_W": requested_w})
        if step < n:
            temperature += dt * (requested_w - model["loss_W_per_K"] * (temperature - ambient)) / model["capacity_J_per_K"]
    return rows

if __name__ == "__main__":
    packet = json.loads(Path(__file__).with_name("scenarios.json").read_text())
    nominal = next(s for s in packet["scenarios"] if s["id"] == "nominal")
    rows = simulate(packet["model"], nominal)
    print(json.dumps({"scenario": nominal["id"], "steps": len(rows),
                      "last_temperature_C": rows[-1]["temperature_C"],
                      "max_temperature_C": max(r["temperature_C"] for r in rows)}, indent=2))
