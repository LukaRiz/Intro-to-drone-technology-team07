#!/usr/bin/env python3

# sudo apt install python3-opengl

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from math import pi

class imu_visualize():
	def __init__(self):
		#rotation
		self.x_axis = 0.0
		self.y_axis = 0.0
		self.z_axis = 0.0 
	 
		glutInit(sys.argv)
		glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
		glutInitWindowSize(640,480)
		glutInitWindowPosition(200,200)

		self.window = glutCreateWindow('IMU visualization')
	 
		glutDisplayFunc(self.DrawGLScene)
		glutIdleFunc(self.DrawGLScene)
		self.InitGL(640, 480)
		self.DrawGLScene()

	def set_axis (self, x_rad, y_rad, z_rad):
		self.x_axis = x_rad*180.0/pi
		self.y_axis = y_rad*180.0/pi	
		self.z_axis = z_rad*180.0/pi

	def update(self):
		self.DrawGLScene()

	def InitGL(self, Width, Height): 
		glClearColor(0.0, 0.0, 0.0, 0.0)
		glClearDepth(1.0) 
		glDepthFunc(GL_LESS)
		glEnable(GL_DEPTH_TEST)
		glShadeModel(GL_SMOOTH)   
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluPerspective(45.0, float(Width)/float(Height), 0.1, 100.0)
		glMatrixMode(GL_MODELVIEW)
	 
	def DrawGLScene(self):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	 
		glLoadIdentity()
		glTranslatef(0.0,0.0,-6.0)
	 
		glRotatef(self.x_axis, 1.0, 0.0, 0.0)
		glRotatef(self.y_axis, 0.0, 1.0, 0.0)
		glRotatef(self.z_axis, 0.0, 0.0, 1.0)
	 
		# Draw Cube (multiple quads)
		glBegin(GL_QUADS)
		glColor3f(1.0,0.0,0.0)
		glVertex3f( 1.0, 1.0,-1.0)
		glVertex3f(-1.0, 1.0,-1.0)
		glVertex3f(-1.0, 1.0, 1.0)
		glVertex3f( 1.0, 1.0, 1.0) 
	 
		glColor3f(0.33,0.33,0.33)
		glVertex3f( 1.0,-1.0, 1.0)
		glVertex3f(-1.0,-1.0, 1.0)
		glVertex3f(-1.0,-1.0,-1.0)
		glVertex3f( 1.0,-1.0,-1.0) 
	 
		glColor3f(0.0,1.0,0.0)
		glVertex3f( 1.0, 1.0, 1.0)
		glVertex3f(-1.0, 1.0, 1.0)
		glVertex3f(-1.0,-1.0, 1.0)
		glVertex3f( 1.0,-1.0, 1.0)
	 
		glColor3f(1.0,1.0,0.0)
		glVertex3f( 1.0,-1.0,-1.0)
		glVertex3f(-1.0,-1.0,-1.0)
		glVertex3f(-1.0, 1.0,-1.0)
		glVertex3f( 1.0, 1.0,-1.0)
	 
		glColor3f(0.0,0.0,1.0)
		glVertex3f(-1.0, 1.0, 1.0) 
		glVertex3f(-1.0, 1.0,-1.0)
		glVertex3f(-1.0,-1.0,-1.0) 
		glVertex3f(-1.0,-1.0, 1.0) 
	 
		glColor3f(1.0,0.0,1.0)
		glVertex3f( 1.0, 1.0,-1.0) 
		glVertex3f( 1.0, 1.0, 1.0)
		glVertex3f( 1.0,-1.0, 1.0)
		glVertex3f( 1.0,-1.0,-1.0)
		glEnd()
		glutSwapBuffers()
	 
