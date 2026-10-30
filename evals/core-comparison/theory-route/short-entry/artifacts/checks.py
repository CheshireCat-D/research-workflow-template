"""Numeric and exact-rational checks only; mathematical proofs are in report.md."""
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import math
from pypdf import PdfReader

BASE = Path(__file__).resolve().parent
INPUT = BASE.parent / 'input'

alpha = Fraction(1, 20)
event_probability = Fraction(9, 10) ** 20
assert event_probability > alpha
v = rho = 0.25
b_squared = (v + rho) * math.log((v + rho) / (float(alpha)**2 * rho))
assert Fraction(5, 2) ** 8 > 800
assert b_squared < 4

c = 2 * math.log(20)
lo, hi = 0.0, 20.0
for _ in range(100):
    x = (lo + hi) / 2
    if x - math.log1p(x) < c:
        lo = x
    else:
        hi = x
x = (lo + hi) / 2
source_checks = []
for filename, expected_sha, page_numbers in [
    ('howard2020-arxiv-v7.pdf', 'e893683657ed89a92173f076e7b132d46300f32ddcf5eb574fa61a3a943b958e', [9, 10, 12, 13]),
    ('howard2021-arxiv-v9.pdf', 'eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8', [4, 5, 6, 9, 10, 12, 14, 19, 28, 29, 30, 35, 37]),
]:
    path = INPUT / 'sources' / filename
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    assert sha == expected_sha
    reader = PdfReader(str(path))
    source_checks.append({
        'file': filename, 'sha256': sha, 'pages': len(reader.pages),
        'inspected_page_text_lengths': {str(p): len(reader.pages[p-1].extract_text()) for p in page_numbers},
    })

results = {
    'scope': 'Arithmetic and supplied PDF identity checks; not proof certification',
    'B': {
        'alpha': '1/20', 'mu': '1/10', 'rho': '1/4', 'time': 20,
        'event': 'X_1=...=X_20=0 for iid Bernoulli(1/10)',
        'probability_formula': '(9/10)^20',
        'probability_exact': str(event_probability),
        'probability_decimal': float(event_probability),
        'b_squared_formula': 'log(800)/2',
        'b_squared': b_squared, 'b': math.sqrt(b_squared),
        'ci_upper_endpoint': math.sqrt(b_squared) / 20,
        'strict_probability_inequality': event_probability > alpha,
    },
    'C': {
        'root_equation': 'x-log(1+x)=2*log(20)',
        'x_alpha_numeric': x,
        'root_residual': x - math.log1p(x) - c,
        'envelope_formula': 'sqrt((1+x_alpha)*v)',
        'scope': 'Root arithmetic only; infinite-time failure proved using stipulated LIL in report',
    },
    'source_pdf_identity': source_checks,
}
(BASE / 'checks-results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
(BASE / 'audit.md').write_bytes((BASE / 'report.md').read_bytes())
print(json.dumps({'B_probability': str(event_probability), 'B_boundary': math.sqrt(b_squared), 'report_chars': len((BASE/'report.md').read_text()), 'pdf_pages': [s['pages'] for s in source_checks]}, ensure_ascii=False))
