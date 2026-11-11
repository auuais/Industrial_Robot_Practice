# -*- coding: utf-8 -*-
"""Build the Lecture 10 study notes, reusing the notes pipeline and style."""
import build

build.CONTENT = build.BASE / 'content_l10'
build.OUT = build.BASE.parent / 'Lecture 10 Study Notes.pdf'
build.CHAPTERS = [('L10.html', 'l10', '10', '#60a5fa')]
build.TITLE = 'Intelligent Robot Practice — Lecture 10 Study Notes: Tracking Control'
build.SUBJECT = ('Kinematic bicycle model, Pure Pursuit, Stanley, longitudinal dynamics, PI speed control, '
                 'actuator maps, online estimation, adaptive control, anti-windup, Kanayama trajectory tracking')

if __name__ == '__main__':
    build.main()
