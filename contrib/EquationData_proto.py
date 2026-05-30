#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
#Builtins

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebKitWidgets import *
from PyQt5.QtSvg import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKit import *

from ast import literal_eval
from math import *

# from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg

import sys

class EquationData(QMainWindow):

	def __init__(self, equations=['sqrt(3364 - (x**2))', '-(sqrt(3364 - x ** 2))', "50 * sin(0.1 * x)"], range=[-100, 100, -100, 100],  parent=None):
		super(EquationData, self).__init__(parent)
		QMainWindow.__init__(self)

		self.plotWidget = QWidget(self)
		self.setCentralWidget(self.plotWidget)
		
		self.equations = equations
		print("EQUATIONS: ", self.equations)
		self.range = range
		
		# self.colorsAll = [(r, g, b) for r in range(0, 254) for g in range(0, 254) for b in range(0, 254)]
		self.colors = [(r, g, b) for r in (0, 1) for g in (0, 1) for b in (0, 1)]
		
		self.red = (255, 0, 0)
		self.darkRed = (128, 0, 0)
		self.green = (0, 255, 0)
		self.darkGreen = (0, 128, 0)
		self.blue = (0, 0, 255)
		self.cyan = (0, 255, 255)
		self.magenta = (255, 0, 255)
		self.yellow = (255, 255, 0)
		self.darkyellow = (128, 128, 0)
		self.darkBlue = (0, 0, 128)
		self.white = (255, 255, 255)
		self.black = (0, 0, 0)
		self.pink = (255, 200, 200)
		self.grey = (79, 79, 79)

		self.initUi()

	def initUi(self):

		self.pw = pg.PlotWidget(name='Archimedes Equations')
		
		self.layout = QVBoxLayout()
		self.layout.addWidget(self.pw)
		self.plotWidget.setLayout(self.layout)

		self.plot = self.pw.plot()
		self.plot.setPen((200, 200, 100))
		

		self.pw.setLabel('left', 'Y', units='Units')
		self.pw.setLabel('bottom', 'X', units='Units')
		self.pw.setXRange(self.range[0], self.range[1])
		self.pw.setYRange(self.range[2], self.range[3])
		
		self.drawPlot()
		
		
		# x = np.cos(np.linspace(0, 2 * np.pi, 1000))
		# y = np.sin(np.linspace(0, 16 * np.pi, 1000))
		# self.pw.plot(x, y)
		
		
		pass
	
	def drawPlot(self):
		
		for equation in self.equations:
			xlist = []
			ylist = []
			start = self.range[0]
			stop = self.range[1]
			total = abs(self.range[0]) + abs(self.range[1])
			print("TOTAL: ", total)
			step = (int(total / 10))
			print("STEP: ", step)
			for x in range(0, total, step):
				print("NEW X")
				xlist.append(x)
				print("X: ", x, "EQUATION: ", equation, "EQUALS: ", eval(equation))
				ylist.append(eval(equation))
				print(xlist, "\n", ylist)
			# y = eval(equation)
			print("PLOTTING AGAINST YOU")
			self.pw.plot(xlist, ylist)


	def resizeEvent(self, event):
		
		pass
	
	def clicked(self):
			print("curve clicked")

			self.curve.sigClicked.connect(self.clicked)

	def rand(self, n):
		data = np.random.random(n)
		data[int(n * 0.1):int(n * 0.13)] += .5
		data[int(n * 0.18)] += 2
		data[int(n * 0.1):int(n * 0.13)] *= 5
		data[int(n * 0.18)] *= 20
		data *= 1e-12
		return data, np.arange(n, n + len(data)) / float(n)


	def updateData(self, ):
		yd, xd = self.rand(10000)
		self.plot.setData(y=yd, x=xd)


def main():

	app = QApplication(sys.argv)
	app.setApplicationName('Archimedes Equation - Ptolemy')
	app.setFont(QFont('DejaVu Sans'))


	Phaleron = EquationData()
	Phaleron.resize(int(QDesktopWidget().geometry().width() * 0.8), int(QDesktopWidget().geometry().height() * 0.8))
	Phaleron.setWindowTitle('Archimedes Equation - Ptolemy')

	Phaleron.win = Phaleron.frameGeometry()
	Phaleron.show()

	# trayIcon = SystemTrayIcon(QIcon('images/ptol.svg'), parent=Phaleron)
	# trayIcon.show()

	# trayIcon = SystemTrayIcon(QIcon('images/ptol.svg'))
	# trayIcon.show()

	# It's exec_ because exec is a reserved word in Python
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()

