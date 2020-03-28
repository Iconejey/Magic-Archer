import pygame as pg
from math import atan2, pi
from random import random, randint


class Human:
	"""Class for Humans with animation."""

	def __init__(self, pos: list, img_bank: dict, anim_rate: int = 5):
		self.pos = pos
		self.img_bank = img_bank
		self.anim_rate = anim_rate
		self.orientation = 0
		self.sight = [0, 1]
		self.shoot_frame = 0
		self.movement = 'run'
		self.health = 10
		self.hitbox = 12, 9, 6, 13


	def getRect(self) -> pg.Rect:
		px, py = self.pos
		hx, hy, hw, hh = self.hitbox
		return pg.Rect(px+hx, py+hy, hw, hh)


	def move(self, dx: int, dy: int):
		"""Move the player by adding dx, dy to self.pos and changes player orientation and movement."""
		self.pos[0] += dx
		self.pos[1] += dy
		if dx == dy == 0:
			self.movement = 'stay'
		else:
			self.sight = [dx, dy]
			self.orientation = int((atan2(dx, dy)/pi*4) % 8)
			self.movement = 'run'


	def getCenter(self) -> list:
		"""Return player center."""
		return [v + 16 for v in self.pos]


	def show(self, s: pg.Surface, frame: int, blood: bool = False):
		"""Blit player on given pygame Surface."""
		o, m = self.orientation, self.movement
		n = 0 if m == 'stay' else (frame//self.anim_rate) % 6
		img = self.img_bank[m][f'{o}_{n}'].copy()
		if blood:
			r = range(30)
			for y in r:
				for x in r:
					if img.get_at([x, y])[3] > 200:
						img.set_at([x, y], [randint(192, 255), 0, 0, 255])
					else:
						img.set_at([x, y], [0]*4)
		s.blit(img, self.pos)


	def shoot(self, frame: int):
		"""Return a new Bullet in the direction the player looks at if 20 frames passed since last hit or shot."""
		if frame - self.shoot_frame >= 20:
			self.shoot_frame = frame
			return Particle(self.getCenter(), self.sight)


	def hit(self, other, frame: int):
		"""Hit another Humman if 20 frames passed since last hit or shot with some random."""
		if frame - self.shoot_frame >= 20:
			self.shoot_frame = frame
			other.health -= 1


class Particle:
	"""Class for the particles of bloob and bullets."""

	@staticmethod
	def mag(x: int, y: int) -> float:
		"""Return magnitude of the vector (x, y)."""
		return (x**2 + y**2)**.5


	def __init__(self, pos: list, vel: list, trace: int = 2, slow: float = .99):
		self.pos = pos
		self.vel = [v/Particle.mag(*vel)*2 for v in vel]
		self.trace = [self.intPos() for i in range(trace)]
		self.slow = slow


	def __str__(self):
		return f'Particle({self.pos}, {self.vel})'


	def move(self):
		"""Move the particle."""
		for i in [0, 1]:
			self.pos[i] += self.vel[i]
			self.vel[i] *= self.slow
		self.trace.pop(0)
		self.trace.append(self.intPos())


	def intPos(self) -> list:
		"""Return particle position with integers."""
		return [int(v) for v in self.pos]


	def show(self, s: pg.Surface, size: int = 1, color = [255, 255, 255], circle = False):
		"""Draw particle on a given pygame Surface."""
		if circle:
			pg.draw.circle(s, color, self.trace[-1], size//2)
		else:
			pg.draw.lines(s, color, False, self.trace, size)