"""Placeholder avatar generation. Synthetic only, never a real face -- see
CLAUDE.md rule 3."""

import hashlib

PALETTE = ["#2563eb", "#7c3aed", "#059669", "#d97706", "#dc2626", "#0891b2"]


def initials(name: str) -> str:
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper()


def svg_avatar(name: str) -> bytes:
    idx = int(hashlib.sha256(name.encode()).hexdigest(), 16) % len(PALETTE)
    color = PALETTE[idx]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256">
  <rect width="256" height="256" fill="{color}"/>
  <text x="128" y="145" font-size="96" font-family="sans-serif" fill="white"
        text-anchor="middle" dominant-baseline="middle">{initials(name)}</text>
</svg>"""
    return svg.encode()
