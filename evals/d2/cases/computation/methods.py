"""Two fixed composite quadratures, self-authored synthetic case input.

Both functions accept n=subinterval count, not evaluation budget.
Each call to f is one function evaluation. No caching or adaptivity is used.
The executor may instrument f but must preserve these formulas.
"""


def midpoint(f, n):
    if not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer")
    h = 1.0 / n
    return h * sum(f((i + 0.5) * h) for i in range(n))


def trapezoid(f, n):
    if not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer")
    h = 1.0 / n
    return h * (0.5 * f(0.0) + sum(f(i * h) for i in range(1, n)) + 0.5 * f(1.0))
