import pygame as pg, os, platform
from entites import Entity, Player, Zombie, Sheep, Particle, mag, vecSub, between
from random import randint, random, choice
from math import sin


def getImgBank(path: str) -> dict:
	"""Return a dict containing all images in a folder with recursion."""
	d = {}
	for f in os.listdir(path):
		if len(f) > 4 and f[-4:] in ('.png', '.jpg'):
			d[f[:-4]] = pg.image.load(f'{path}/{f}').convert_alpha()
		else:
			d[f] = getImgBank(f'{path}/{f}')
	return d


def gradiant(s: pg.surface, color: list, rand: float, player: Player, fog: bool = None):
	"""Set random pixels of given surface to given RGBA color."""
	w, h = s.get_size()
	sx, sy = surface_pos

	if player is not None:
		px, py = player.intPos()
	else:
		px, py = 0, 0
	
	border = 20
	rx = max(0, int(-sx//SCALE) - border), min(int((-sx+SCREEN_W)//SCALE) + border, SURFACE_W)
	ry = max(0, int(-sy//SCALE) - border), min(int((-sy+SCREEN_H)//SCALE) + border, SURFACE_H)

	for y in range(*ry):
		for x in range(*rx):
			if random() > rand:
				if fog:
					fx, fy = vecSub((x-16, y-16), (px, py))
					intensity = int(fx*fx + fy*fy)
					color[-1] = randint(between(0, intensity - 64, 255), between(0, intensity, 255))
				s.set_at([x, y], color)
	return s


def getSurfacePos(player: Player, mouse: tuple) -> tuple:
	"""Return position of surface so that the view is aligned with player."""
	if player is None: return 0, 0
	px, py = player.pos
	mx, my = mouse
	x = between(-SURFACE_W*SCALE + SCREEN_W, (-px-16)*SCALE + SCREEN_W//2 - mx//10, 0)
	y = between(-SURFACE_H*SCALE + SCREEN_H, (-py-16)*SCALE + SCREEN_H//2 - my//10, 0)
	return x, y


def explosion(pos: list, entity_from: Entity, frame: int):
	if len(bullets) < 256:
		d = {mag(*vecSub(e.getCenter(e.bullet_hitbox), pos)): e for e in [*zombies, *sheeps] if e is not entity_from}
		v, n = min(d), d[min(d)]
		dx, dy = vecSub(n.getCenter(n.bullet_hitbox), pos)
		speed = 3
		part = Particle(bullet.pos, [dx/v*speed, dy/v*speed], slow = .94, dead_vel = 1, entity_from = entity_from, creation_frame = frame)
		part.explosive = True
		bullets.append(part)


if __name__ == "__main__":
	if 'Windows' in platform.platform():  # car pb de dpi sur windows
		from ctypes import windll
		windll.shcore.SetProcessDpiAwareness(1)

	pg.init()

	SCREEN_SIZE = SCREEN_W, SCREEN_H = 1200, 720
	SCREEN = pg.display.set_mode(SCREEN_SIZE)
	img_bank = getImgBank('img')
	SURFACE_SIZE = SURFACE_W, SURFACE_H = img_bank['ground'].get_size()
	SURFACE = pg.Surface(SURFACE_SIZE).convert_alpha()
	SEFFECT = SURFACE.copy()
	SCALE = 8

	clock = pg.time.Clock()
	bold_font = pg.font.Font(f"Consolas.ttf", 24)
	bold_font.set_bold(True)
	mouse_drag = None
	explosive = False
	fog_frame = 0
	score = 0
	traj = None

	player = None
	bullets, blood_particles = [], []
	zombies = []
	sheeps = []
	ammo = []

	static_entities = [
		Entity([23, 86], img_bank['house1'], [0, 28, 59, 23], [0, 21, 59, 23], 51),
		Entity([199, 81], img_bank['house2'], [0, 20, 50, 24], [0, 13, 50, 24], 44),
		Entity([249, 132], img_bank['house3'], [0, 27, 42, 24], [0, 20, 42, 24], 51),
		Entity([362, 41], img_bank['pine1'], [29, 108, 5, 5], [29, 94, 5, 11], 112),
		Entity([0, 0], img_bank['pine2'], [5, 43, 5, 5], [5, 33, 5, 8], 48)
	]

	os.system('cls')

	frame = 0
	game_state = 'menu'
	while game_state != 'end':
		frame += 1
		clock.tick(48)

		if any(e.type == pg.QUIT for e in pg.event.get()):
			game_state = 'end'
			continue

		keys = pg.key.get_pressed()
		mouse_data = pg.mouse.get_pressed()
		click = 0
		if mouse_data[0]:
			click = 1
		elif mouse_data[2]:
			click = 2
		mouse_pos = pg.mouse.get_pos()
		mouse_from_center = vecSub(mouse_pos, [SCREEN_W//2, SCREEN_H//2])

		surface_pos = getSurfacePos(player, mouse_from_center)

		if game_state == 'menu':
			SEFFECT = gradiant(SEFFECT, [0, 0, 0, 255], .8, player)
			SURFACE.blit(SEFFECT, [0, 0])
			SCREEN.blit(pg.transform.scale(SURFACE, [SURFACE_W*SCALE, SURFACE_H*SCALE]), surface_pos)
			
			if keys[pg.K_RETURN]:
				game_state = 'play'
				player = Player([randint(0, SURFACE_W), randint(0, SURFACE_H)], img_bank['player'])
				bullets, blood_particles = [], []
				zombies = []
				sheeps = []
				ammo = []
				score = 0
				fog_frame = 64
				SEFFECT.fill([0, 0, 0, 255])


		if game_state == 'play':
			SEFFECT = gradiant(SEFFECT, [0]*4, .8, player, fog = False if frame > fog_frame else True)
			
			print(int(clock.get_fps()), player.health, score, end = ' \r')
			

			if player.health <= 0:
				game_state = 'menu'
				
			
			if random() > .98 and len(zombies) < 32:
				zombies.append(Zombie([randint(0, SURFACE_W), randint(0, SURFACE_H)], img_bank['zombie']))

			if random() > .98 and len(sheeps) < 16:
				sheeps.append(Sheep([randint(0, SURFACE_W), randint(0, SURFACE_H)], img_bank['sheep']))


			for zombie in zombies:
				dx, dy = vecSub(player.pos, zombie.pos)
				if dx**2 + dy**2 > 144:
					m = mag(dx, dy)
					zombie.move(dx/m/2, dy/m/2, frame, to_avoid = static_entities, borders = SURFACE_SIZE)
				else:
					zombie.move(0, 0, frame, to_avoid = static_entities, borders = SURFACE_SIZE)
					if random() > .9 and zombie.hit(player, frame):
						fog_frame = frame + randint(96, 128)
						player.show(SEFFECT, frame, blood = True)

				if zombie.health <= 0:
					zombie.show(SEFFECT, frame, blood = True)
					zombies.remove(zombie)
					score += 1


			for sheep in sheeps:
				dx, dy = vecSub(player.getCenter(player.ground_hitbox), sheep.getCenter(sheep.ground_hitbox))
				if dx**2 + dy**2 < 2000:
					m = mag(dx, dy)
					sheep.move(-dx/m/2, -dy/m/2, frame, to_avoid = static_entities, borders = SURFACE_SIZE)
				else:
					sheep.move(0, 0, frame, to_avoid = static_entities, borders = SURFACE_SIZE)

				if sheep.health <= 0:
					sheep.show(SEFFECT, frame, blood = True)
					sheeps.remove(sheep)
					for i in range(randint(3, 6)):
						shpx, shpy = sheep.intPos()
						ammo.append(Entity([shpx + random()*16, shpy + random()*16], img_bank[f'ammo{randint(1, 3)}'], None, None, 4))


			for a in ammo:
				dx, dy = vecSub(player.getCenter(player.ground_hitbox), a.pos)
				if dx**2 + dy**2 < 144:
					ammo.remove(a)
					player.ammo[0] += randint(1, 4)
					if random() > .9:
						player.ammo[1] += 1


			direction = [0, 0]
			if keys[pg.K_w]: direction[1] -= 1
			if keys[pg.K_s]: direction[1] += 1
			if keys[pg.K_a]: direction[0] -= 1
			if keys[pg.K_d]: direction[0] += 1

			dx, dy = direction
			if abs(dx) != abs(dy):
				dx *= 1.4
				dy *= 1.4
			
			player.move(dx, dy, frame, to_avoid = static_entities, borders = SURFACE_SIZE)


			if click:
				if click == 2:
					explosive = True
				if mouse_drag is None:
					mouse_drag = mouse_pos
				else:
					fake_bullet = player.shoot(vecSub(mouse_pos, mouse_drag), frame, no_latence = True)
					if fake_bullet is not None:
						traj = fake_bullet.getTraject(SURFACE_SIZE)
			else:
				traj = None
				if mouse_drag not in (None, (0, 0)) and (b:=player.shoot(vecSub(mouse_pos, mouse_drag), frame)) is not None:
					if explosive and player.ammo[1]:
						b.explosive = True
						player.ammo[1] -= 1
						player.ammo[0] += 1

					if player.ammo[0]:
						bullets.append(b)
						player.ammo[0] -= 1
					else:
						px, py = player.getCenter(player.bullet_hitbox, to_int = True)
						mx, my = vecSub(mouse_pos, mouse_drag)
						pg.draw.line(SEFFECT, [255]*4, [px, py], [px+mx//SCALE, py+my//SCALE])
						
				mouse_drag = None
				explosive = False
				

			for bullet in bullets:
				bullet.move(SURFACE_SIZE)
				if bullet.explosive:
					bullet.show(SEFFECT, color = [192, 255, 255])
				else:
					bullet.show(SEFFECT, color = [255, 255, 192])

				for zombie in zombies:
					if bullet.collide(zombie):
						zombie.health -= sum(v**2/10 for v in bullet.vel)
						if bullet.explosive:
							explosion(bullet.pos, zombie, frame)
							zombie.health = 0
							bullet.vel = [0, 0]
						else:
							bullet.vel = [v*.8 for v in bullet.vel]
						for i in range(randint(2, 5)):
							blood_particles.append(Particle(bullet.intPos(), [v+random()*2-1 for v in bullet.vel], slow = .85, dead_vel = .4))

				for sheep in sheeps:
					if bullet.collide(sheep):
						sheep.health -= sum(v**2/10 for v in bullet.vel)
						if bullet.explosive:
							explosion(bullet.pos, sheep, frame)
							sheep.health = 0
							bullet.vel = [0, 0]
						else:
							bullet.vel = [v*.8 for v in bullet.vel]
						for i in range(randint(2, 5)):
							blood_particles.append(Particle(bullet.intPos(), [v+random()*2-1 for v in bullet.vel], slow = .85, dead_vel = .4))

				for entity in static_entities:
					if bullet.collide(entity):
						bullet.vel = [0, 0]

				if bullet.dead():
					bullets.remove(bullet)


			for part in blood_particles:
				part.move(SURFACE_SIZE)
				part.show(SEFFECT, color = [randint(192, 255), 0, 0, randint(64, 255)])
				
				if part.dead():
					blood_particles.remove(part)

			# graphics
			SURFACE.blit(img_bank['ground'], [0, 0])

			for entity in Entity.order([*zombies, player, *static_entities, *sheeps, *ammo]):
				if type(entity) is Entity:
					entity.show(SURFACE)
				else:
					entity.show(SURFACE, frame)

			if traj is not None:
				for x, y in traj:
					x, y = between(0, x, SURFACE_W-1), between(0, y, SURFACE_H-1)
					SURFACE.set_at([x, y], [int(c*.5) for c in SURFACE.get_at([x, y])])

			SURFACE.blit(img_bank['tree_fg'], [12, 0])
			SURFACE.blit(SEFFECT, [0, 0])
			SCREEN.blit(pg.transform.scale(SURFACE, [SURFACE_W*SCALE, SURFACE_H*SCALE]), surface_pos)
			if mouse_drag is not None:
				pg.draw.line(SCREEN, [255]*4, mouse_pos, mouse_drag, 3)
			SCREEN.blit(bold_font.render(f"Zombies: {len(zombies)}", False, [255]*4), [10, 16*3])
			SCREEN.blit(bold_font.render(f"Arrows: {player.ammo[0]}", False, [255, 255, 192]), [10, 16*5])
			SCREEN.blit(bold_font.render(f"Magic arrows: {player.ammo[1]}", False, [192, 255, 255]), [10, 16*7])

		SCREEN.blit(bold_font.render(f"Score: {score}", False, [255]*4), [10, 16])
		pg.display.update()