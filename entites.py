import pygame as pg
from math import atan2, pi
from random import random, randint, choice


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
		self.pos = pos
		self.default_img, self.foot = default_img, foot
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
		x, y = hx+hw/2, hy+hh/2
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
		s.blit(self.default_img, self.intPos())



class Moving(Entity):
	"""Class for moving entities."""
	
	def __init__(self, pos: list, health: int, default_img: pg.Surface, ground_hitbox: tuple, bullet_hitbox: tuple, foot: int):
		super(Moving, self).__init__(pos, default_img, ground_hitbox, bullet_hitbox, foot)

		self.health = health
		self.movement = 'stay'
		self.move_frame = None
		self.look = [choice([-1, 1]), choice([-1, 1])]
		self.true_look = [0, 0]


	def move(self, dx: int, dy: int, frame: int, to_avoid: list = [], borders: list = None):
		"""Move the entity by adding dx, dy to self.pos and changes entity look and movement."""
		self.true_look = [dx, dy]
		
		if dx == dy == 0:
			self.movement = 'stay'
			self.move_frame = None
		else:
			self.movement = 'run'

			if self.move_frame is None:
				self.move_frame = frame

			self.pos[0] += dx
			self.pos[1] += dy

			if dx > 0: self.look[0] = 1
			if dy > 0: self.look[1] = 1
			if dx < 0: self.look[0] = -1
			if dy < 0: self.look[1] = -1

			for entity in to_avoid:
				collision = self.collide(entity)
				if collision is not None:
					dx, dy = collision

					if dx < dy:
						self.pos[0] -= dx
					else:
						self.pos[1] -= dy

		if borders is not None:
			W, H = borders
			x, y = self.pos
			hx, hy, hw, hh = self.bullet_hitbox
			self.pos = [between(-hx, x, W-hx-hw), between(-hy, y, H-hy-hh)]



	def getBlood(self, img: pg.Surface) -> pg.Surface:
		"""Return bloody version of given surface."""
		w, h = img.get_size()
		for y in range(h):
			for x in range(w):
				if img.get_at([x, y])[3] > 200:
					img.set_at([x, y], [randint(192, 255), 0, 0, randint(128, 255)])
				else:
					img.set_at([x, y], [0]*4)
		return img



class Sheep(Moving):
	"""Class for sheeps."""
	
	def __init__(self, pos: list, img_bank: dict):
		super(Sheep, self).__init__(pos, 5, None, [3, 15, 10, 1], [3, 8, 10, 6], 16)
		self.img_bank = img_bank


	def getCardinal(self):
		"""Return cardinal point the sheep looks at."""
		h, v = self.look
		return {-1: 'N', 1: 'S'}[v] + {-1: 'W', 1: 'E'}[h]


	def show(self, s: pg.Surface, frame: int, blood: bool = False):
		"""Blit sheep on given pygame Surface."""
		img = self.img_bank[self.getCardinal()].copy()
		
		if blood:
			img = self.getBlood(img)

		if self.movement == 'run':
			n = ((frame-self.move_frame)//5)%6
			h = [0, 3, 5, 6, 5, 3][n]
			x, y = self.pos
			s.blit(img, [x, y])
		else:
			s.blit(img, self.pos)



class Human(Moving):
	"""Class for Human entities."""

	def __init__(self, pos: list, health: int, img_bank: dict, anim_rate: int = 1):
		super(Human, self).__init__(pos, health, None, [12, 22, 6, 3], [11, 9, 8, 13], 24)

		self.img_bank = img_bank
		self.anim_rate = anim_rate

		self.hit_frame = 0
		self.anim_len = 6


	def getOrientation(self) -> int:
		"""Return an integer between 0 and 7 which represents the orientation of the entity."""
		return int((atan2(*self.true_look)/pi*4) % 8)


	def show(self, s: pg.Surface, frame: int, blood: bool = False):
		"""Blit Human on given pygame Surface."""
		o, m = self.getOrientation(), self.movement
		l, r = self.anim_len, self.anim_rate

		n = 0 if m == 'stay' or l == 1 else (frame*r//48) % l
		n = min(n, 7)
		img = self.img_bank[m][f'{o}_{n}'].copy()

		if blood:
			img = self.getBlood(img)

		s.blit(img, self.pos)



class Zombie(Human):
	def __init__(self, pos: list, img_bank: dict):
		super(Zombie, self).__init__(pos, 10, img_bank, anim_rate = 12)


	def hit(self, other: Human, frame: int) -> bool:
		"""Hit another Humman if 5 frames passed since last hit. Return True if hit, else False"""
		if frame - self.hit_frame >= 5:
			self.hit_frame = frame
			other.health -= 1
			return True



class Player(Human):
	def __init__(self, pos: list, img_bank: dict):
		super(Player, self).__init__(pos, 10, img_bank, anim_rate = 16)
		self.ammo = [8, 0]


	def shoot(self, sight: tuple, frame: int, no_latence: bool = False):
		"""Return a new Bullet in the direction the entity looks at if 20 frames passed since last hit or shot."""
		hit = frame - self.hit_frame >= 15
		if (hit or no_latence) and sight != (0, 0):
			if not no_latence: self.hit_frame = frame
			x, y = self.pos
			vx, vy = sight
			m = mag(vx, vy)
			return Particle([x+16, y+16], [vx/m*8, vy/m*8], slow = .9, dead_vel = 1)



class Particle:
	"""Class for the particles of bloob and bullets."""

	def __init__(self, pos: list, vel: list, trace: int = 2, slow: float = .99, dead_vel: float = 1, entity_from: Entity = None, creation_frame: int = 0):
		self.pos, self.vel = pos, vel
		self.trace = [self.intPos() for i in range(trace)]
		self.slow, self.dead_vel = slow, dead_vel
		self.explosive = False
		self.entity_from = entity_from
		self.creation_frame = creation_frame


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


	def collide(self, entity: Entity, frame: int = None) -> bool:
		"""return True if particle collides entity."""
		return entity is not self.entity_from and (frame is None or frame > self.creation_frame + 5) and entity.getRect(entity.bullet_hitbox).collidepoint(*self.intPos())


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