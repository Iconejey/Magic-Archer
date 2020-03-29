import pygame as pg
from math import atan2, pi
from random import random, randint


class Entity:
	"""Class for every image-based entities."""

	@staticmethod
	def order(entities: list, /) -> list:
		"""Return a list of given entities ordered from farthest to nearest."""
		new_list = []
		while len(entities):
			farthest = min([e.getFoot() for e in entities])
			for i, e in enumerate(entities):
				if e.getFoot() == farthest:
					new_list.append(entities.pop(i))
					break
		return new_list


	def __init__(self, pos: list, default_img: pg.Surface, ground_hitbox: tuple, bullet_hitbox: tuple, foot: int):
		self.pos, self.default_img, self.foot = pos, default_img, foot
		self.ground_hitbox, self.bullet_hitbox = ground_hitbox, bullet_hitbox


	def __str__(self) -> str:
		"""String representation of entity."""
		x, y = self.intPos()
		return f'E({x}, {y})'


	def intPos(self) -> list:
		"""Return entity position with integers."""
		return [int(v) for v in self.pos]


	def getFoot(self) -> int:
		"""Return relative foot y position."""
		return int(self.pos[1] + self.foot)


	def getRelative(self, hitbox: tuple) -> tuple:
		"""Return hitbox relative to entity position."""
		(px, py), (hx, hy, hw, hh) = self.pos, hitbox
		return px+hx, py+hy, hw, hh


	def getRect(self, hitbox: tuple) -> pg.Rect:
		"""Return a pygame Rect object relative to entity position and given hitbox."""
		return pg.Rect(*self.getRelative(hitbox))


	def getCenter(self, hitbox: tuple, to_int = False) -> tuple:
		"""Return the center of the given hitbox relative to entity position."""
		hx, hy, hw, hh = self.getRelative(hitbox)
		x, y = (hx+hw)/2, (hy+hh)/2
		if to_int:
			return int(x), int(y)
		else:
			return  x, y


	def collide(self, other) -> tuple:
		"""Return correction (dx, dy) if colision with given entity else None."""
		self_rect = self.getRect(self.ground_hitbox)
		other_rect = other.getRect(other.ground_hitbox)

		if self_rect.colliderect(other_rect):
			self_center = self.getCenter(self.ground_hitbox)
			other_center = other.getCenter(other.ground_hitbox)

			dcx, dcy = vecSub(other_center, self_center)

			px, py, pw, ph = self.getRelative(self.ground_hitbox)
			ox, oy, ow, oh = other.getRelative(other.ground_hitbox)

			if dcx > 0: dx = px + pw - ox
			else: dx = px - ox - ow

			if dcy > 0: dy = py + ph - oy
			else: dy = py - oy - oh

			return dx, dy


	def show(self, s: pg.Surface):
		"""Blit the default image on given surface."""
		s.blit(self.default_img, self.pos)



class Animated(Entity):
	"""Class for animated entities."""

	def __init__(self, pos: list, img_bank: dict, ground_hitbox: tuple, bullet_hitbox: tuple, foot: int, health: int = 10, anim_len: int = 1, anim_rate: int = 1):
		super(Animated, self).__init__(pos, None, ground_hitbox, bullet_hitbox, foot)

		self.img_bank = img_bank
		self.health = health
		self.anim_len, self.anim_rate = anim_len, anim_rate

		self.movement = 'stay'
		self.orientation = 0
		self.hit_frame = 0


	def move(self, dx: int, dy: int):
		"""Move the entity by adding dx, dy to self.pos and changes entity orientation and movement."""
		if dx == dy == 0:
			self.movement = 'stay'
		else:
			self.pos[0] += dx
			self.pos[1] += dy

			self.orientation = int((atan2(dx, dy)/pi*4) % 8)
			self.movement = 'run'


	def show(self, s: pg.Surface, frame: int, blood: bool = False):
		"""Blit entity on given pygame Surface."""
		o, m = self.orientation, self.movement
		l, r = self.anim_len, self.anim_rate

		n = 0 if m == 'stay' or l == 1 else (frame*r//48) % l
		img = self.img_bank[m][f'{o}_{n}'].copy()

		if blood:
			r = range(30)
			for y in r:
				for x in r:
					if img.get_at([x, y])[3] > 200:
						img.set_at([x, y], [randint(192, 255), 0, 0, randint(128, 255)])
					else:
						img.set_at([x, y], [0]*4)

		s.blit(img, self.pos)


	def shoot(self, sight: tuple, frame: int, no_latence: bool = False):
		"""Return a new Bullet in the direction the entity looks at if 20 frames passed since last hit or shot."""
		hit = frame - self.hit_frame >= 15
		if hit or no_latence:
			if not no_latence: self.hit_frame = frame
			x, y = self.pos
			vx, vy = sight
			m = mag(vx, vy)
			return Particle([x+16, y+16], [vx/m*8, vy/m*8], slow = .9, dead_vel = 1)


	def hit(self, other, frame: int) -> bool:
		"""Hit another Humman if 5 frames passed since last hit or shot. Return True if hit, else False"""
		if frame - self.hit_frame >= 5:
			self.hit_frame = frame
			other.health -= 1
			return True



class Particle:
	"""Class for the particles of bloob and bullets."""

	def __init__(self, pos: list, vel: list, trace: int = 2, slow: float = .99, dead_vel: float = 1):
		self.pos, self.vel = pos, vel
		self.trace = [self.intPos() for i in range(trace)]
		self.slow, self.dead_vel = slow, dead_vel


	def __str__(self):
		"""String representation of entity."""
		return f'Particle({self.pos}, {self.vel})'


	def move(self, borders: tuple):
		"""Move and bounce the particle."""
		for i in [0, 1]:
			self.pos[i] += self.vel[i]
			self.vel[i] *= self.slow

		x, y = self.pos
		W, H = borders

		if x < 0: self.vel[0] = abs(self.vel[0])
		if y < 0: self.vel[1] = abs(self.vel[1])
		if x > W: self.vel[0] = -abs(self.vel[0])
		if y > H: self.vel[1] = -abs(self.vel[1])

		self.pos = [between(0, v, s) for v, s in zip(self.pos, borders)]
		
		self.trace.pop(0)
		self.trace.append(self.intPos())


	def dead(self):
		return mag(*self.vel) <= self.dead_vel


	def getTraject(self, borders: tuple):
		while not self.dead():
			self.move(borders)
			yield self.intPos()


	def intPos(self) -> list:
		"""Return particle position with integers."""
		return [int(v) for v in self.pos]


	def collide(self, entity: Entity) -> bool:
		"""return True if particle collides entity."""
		return entity.getRect(entity.bullet_hitbox).collidepoint(*self.intPos())


	def show(self, s: pg.Surface, size: int = 1, color = [255, 255, 255]):
		"""Draw particle on a given pygame Surface."""
		pg.draw.lines(s, color, False, self.trace, size)



def mag(x: int, y: int) -> float:
	"""Return magnitude of the vector (x, y)."""
	return (x**2 + y**2)**.5


def vecSub(v1: list, v2: list) -> tuple:
	"""Return v1 - v2"""
	(x1, y1), (x2, y2) = v1, v2
	return x1-x2, y1-y2


def between(a: int, b: int, c: int, /) -> int:
	"""Return b such as a <= b <= c."""
	return max(a, min(b, c))