from white_keeper.calculator import calculate_exposure

def approx(a, b, tol=1e-6):
    return abs(a-b) <= tol

# Example from spec: 2026-07-15 10:00-13:20 sunny, no_reapply
res = calculate_exposure(
    start_time="10:00",
    end_time="13:20",
    date_value="2026-07-15",
    weather="sunny",
    sunscreen="no_reapply",
)
print("result:", res)
print("total ~= 5.0 ->", res['total'], approx(res['total'], 5.0))
print("duration ~= 3.3333 ->", res['duration_hours'])
print("season_coefficient ->", res['season_coefficient'])
print("time_coefficient ->", res['time_coefficient'])

# Another quick check: cloudy with no sunscreen
res2 = calculate_exposure(
    start_time="09:30",
    end_time="11:15",
    date_value="2026-05-01",
    weather="cloudy",
    sunscreen="none",
)
print("result2:", res2)
