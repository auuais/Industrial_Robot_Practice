# -*- coding: utf-8 -*-
"""Build the conceptual question bank PDF, reusing the notes pipeline and style."""
import build

build.CONTENT = build.BASE / 'content_q'
build.OUT = build.BASE.parent / 'Concept Question Bank (Lectures 1-7).pdf'
build.CHAPTERS = [
    ('L1.html', 'l1', '1', '#60a5fa'),
    ('L2.html', 'l2', '2', '#22d3ee'),
    ('L3.html', 'l3', '3', '#a78bfa'),
    ('L4.html', 'l4', '4', '#fbbf24'),
    ('L6.html', 'l6', '6', '#fb7185'),
    ('L7.html', 'l7', '7', '#4ade80'),
]

if __name__ == '__main__':
    build.main()
