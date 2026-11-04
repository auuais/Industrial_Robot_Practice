# -*- coding: utf-8 -*-
"""Build the Lecture 9 study notes, reusing the notes pipeline and style."""
import build

build.CONTENT = build.BASE / 'content_l9'
build.OUT = build.BASE.parent / 'Lecture 9 Study Notes.pdf'
build.CHAPTERS = [('L9.html', 'l9', '9', '#2dd4bf')]
build.TITLE = 'Intelligent Robot Practice — Lecture 9 Study Notes: Local Trajectory Planning'
build.SUBJECT = ('Frenet coordinates, quintic lateral plans, candidate generation, collision and limit checks, '
                 'cost-based selection, receding-horizon planning')

if __name__ == '__main__':
    build.main()
