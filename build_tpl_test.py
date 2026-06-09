import os

tmpl = ""
# PART 1: Header + CSS Variables
tmpl += '{% extends "base.html" %}\n'
tmpl += '{% block title %}Investir | TokenFlow Trading{% endblock %}\n'
tmpl += '{% block page_styles %}\n'
tmpl += '@import url(\'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap\');\n'
tmpl += ':root {\n'
tmpl += '  --bg-page:#F0F4FF; --bg-card:rgba(255,255,255,0.90); --bg-glass:rgba(255,255,255,0.60);\n'
tmpl += '  --border-card:rgba(148,163,184,0.18); --border-glow:rgba(99,102,241,0.25);\n'
tmpl += '  --profit-green:#10B981; --profit-green-glow:rgba(16,185,129,0.15);\n'
tmpl += '  --gold:#F59E0B; --gold-glow:rgba(245,158,11,0.15);\n'
tmpl += '  --primary:#6366F1; --primary-glow:rgba(99,102,241,0.18);\n'
tmpl += '  --primary-gradient:linear-gradient(135deg,#6366F1 0%,#8B5CF6 100%);\n'
tmpl += '  --grad-r40:linear-gradient(135deg,#10B981 0%,#059669 100%);\n'
tmpl += '  --grad-r45:linear-gradient(135deg,#6366F1 0%,#8B5CF6 100%);\n'
tmpl += '  --grad-r51:linear-gradient(135deg,#F59E0B 0%,#EF4444 100%);\n'
tmpl += '  --grad-custom:linear-gradient(135deg,#06B6D4 0%,#3B82F6 100%);\n'
tmpl += '  --text-primary:#0F172A; --text-secondary:#475569; --text-muted:#94A3B8;\n'
tmpl += '}\n'
print("Part1 built, length:", len(tmpl))
