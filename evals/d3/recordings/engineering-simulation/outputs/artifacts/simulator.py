"""Thermal controller numerical model; original supplied code remains inputs/simulator.py."""
import math


def simulate(model, scenario, dt):
    horizon = model['horizon_s']
    count = round(horizon / dt)
    if dt <= 0 or not math.isclose(count * dt, horizon, abs_tol=1e-9):
        raise ValueError('positive dt must divide horizon')
    temperatures = []
    rows = []
    delay = scenario['sensor_delay_s']
    for step in range(count + 1):
        t = step * dt
        temperature = scenario['initial_C'] if step == 0 else temperature
        temperatures.append(temperature)
        past = (t - delay) / dt
        if past <= 0:
            measured = scenario['initial_C']
        elif past >= step:
            measured = temperature
        else:
            left = int(math.floor(past))
            weight = past - left
            measured = temperatures[left] * (1 - weight) + temperatures[left + 1] * weight
        request = model['loss_W_per_K'] * (model['target_C'] - scenario['ambient_C']) + model['gain_W_per_K'] * (model['target_C'] - measured)
        actual = min(model['actuator_max_W'], max(model['actuator_min_W'], request))
        rows.append({'time_s': round(t, 10), 'temperature_C': temperature, 'measured_C': measured, 'requested_W': request, 'actual_W': actual})
        if step < count:
            temperature += dt * (actual - model['loss_W_per_K'] * (temperature - scenario['ambient_C'])) / model['capacity_J_per_K']
    return rows
