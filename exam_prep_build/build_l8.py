# -*- coding: utf-8 -*-
"""Build the Lecture 8 study notes, reusing the notes pipeline and style."""
import build

build.CONTENT = build.BASE / 'content_l8'
build.OUT = build.BASE.parent / 'Lecture 8 Study Notes.pdf'
build.CHAPTERS = [('L8.html', 'l8', '8', '#fb923c')]
build.TITLE = 'Intelligent Robot Practice — Lecture 8 Study Notes: Global Planning and Route Execution'
build.SUBJECT = 'Shortest paths, Dijkstra, A*, Weighted A*/ARA*, LPA*, D* Lite, HPA*, Contraction Hierarchies, route FSM'

if __name__ == '__main__':
    build.main()
