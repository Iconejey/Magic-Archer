import pygame as pg
from math import atan2, pi


class Player:
	def __init__(self, pos: list, img_bank: dict):
		self.pos = [0, 0]
		self.img_bank = img_bank
		self.orientation = 0
		self.sight = [0, 1]
		self.shoot_frame = 0
		self.movement = 'run'


	def move(self, dx: int, dy: int):
		self.pos[0] += dx
		self.pos[1] += dy
		if dx == dy == 0:
			self.movement = 'stay'
		else:
			self.sight = [dx, dy]
			self.orientation = int((atan2(dx, dy)/pi*4)%8)
			self.movement = 'run'


	def getCenter(self) -> tuple:
		return [v + 16 for v in self.pos]


	def show(self, s: pg.Surface, frame: int):
		o, m = self.orientation, self.movement
		n = 0 if m == 'stay' else (frame//3) % 6
		s.blit(self.img_bank[m][f'{o}_{n}'], self.pos)


	def shoot(self, frame):
		if frame - self.shoot_frame >= 20:
			self.shoot_frame = frame
			return Bullet(self.getCenter(), self.sight)



class Bullet:
	@staticmethod
	def mag(x, y):
		return (x**2 + y**2)**.5
	
	
	def __init__(self, pos: list, vel: list):
		self.pos = pos
		self.vel = [v/Bullet.mag(*vel)*2 for v in vel]
		self.trace = [self.intPos() for i in range(2)]


	def __str__(self):
		return f'Bullet({self.pos}, {self.vel})'

	
	def move(self):
		for i in [0, 1]:
			self.pos[i] += self.vel[i]
			self.vel[i] *= 0.99
		self.trace.pop(0)
		self.trace.append(self.intPos())


	def intPos(self) -> list:
		return [int(v) for v in self.pos]


	def show(self, s: pg.Surface):
		pg.draw.lines(s, [255]*3, False, self.trace, 2)