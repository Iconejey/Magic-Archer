import pygame as pg, os, platform
from entites import Human, Particle
from random import randint, random, choice
from math import sin


def between(a: int, b: int, c: int, /) -> int:
	"""Return b such as a <= b <= c."""
	return max(a, min(b, c))


def getImgBank(path: str) -> dict:
	"""Return a dict containing all images in a folder with recursion."""
	d = {}
	for f in os.listdir(path):
		if len(f) > 4 and f[-4:] in ('.png', 'jpg'):
			d[f[:-4]] = pg.image.load(f'{path}/{f}').convert_alpha()
		else:
			d[f] = getImgBank(f'{path}/{f}')
	return d


if __name__ == "__main__":
	if 'Windows' in platform.platform():  # car pb de dpi sur windows
		from ctypes import windll
		windll.shcore.SetProcessDpiAwareness(1)

	pg.init()
	os.system('cls')

	SIZE = 960, 576
	SCREEN = pg.display.set_mode(SIZE)

	img_bank = getImgBank('img')
	player = Human([randint(20, 60) for i in range(2)], img_bank['player'])
	zombies = []
	bullets, blood = [], []

	SURFACE = pg.Surface([120, 120])
	SEFFECT = pg.Surface([120, 120])
	SEFFECT.set_colorkey([0]*3)

	clock = pg.time.Clock()

	bold_font = pg.font.Font(f"Consolas.ttf", 24)
	bold_font.set_bold(True)

	frame = 0
	game_state = 'menu'
	while game_state != 'end':
		print(player.health, end = ' \r')
		frame += 1
		clock.tick(48)

		if any(e.type == pg.QUIT for e in pg.event.get()):
			game_state = 'end'
			continue

		keys = pg.key.get_pressed()

		SCREEN.fill([0]*3)

		blink = abs(int(sin(frame/5)*255))

		if game_state == 'menu':
			SCREEN.blit(bold_font.render("> press [Enter] to start.", False, [blink]*3), [10, 16])
			if keys[pg.K_RETURN]:
				game_state = 'play'

		if game_state == 'play':
			# logic
			if frame == 0 or frame%48 == 0 and random() >= 0.75:
				zombies.append(Human([randint(0, 120) for i in range(2)], img_bank['zombie'], 10))

			for zom in zombies:
				dx, dy = [b-a for a, b in zip(zom.pos, player.pos)]
				mag = 4*(dx**2 + dy**2)**.5
				if mag > 32:
					dx /= mag
					dy /= mag
					zom.move(dx, dy)
				else:
					zom.move(0, 0)
					if random() > .9:
						zom.hit(player, frame)
						player.show(SEFFECT, frame, blood = True)

				if zom.health <= 0:
					zom.show(SEFFECT, frame, blood = True)
					zombies.remove(zom)

			direction = [0, 0]
			if keys[pg.K_w]: direction[1] -= 1
			if keys[pg.K_s]: direction[1] += 1
			if keys[pg.K_a]: direction[0] -= 1
			if keys[pg.K_d]: direction[0] += 1
			player.move(*direction)
			x, y = player.pos
			player.pos = [between(-11, x, 101), between(-8, y, 96)]

			if keys[pg.K_SPACE]:
				if (b:=player.shoot(frame)) is not None:
					bullets.append(b)

			for y in range(120):
				for x in range(120):
					if random() >= .8:
						SEFFECT.set_at([x, y], [0]*3)

			for bul in bullets:
				bul.move()
				x, y = bul.pos

				if x < 0: bul.vel[0] = abs(bul.vel[0])
				if y < 0: bul.vel[1] = abs(bul.vel[1])
				if x > 120: bul.vel[0] = -abs(bul.vel[0])
				if y > 120: bul.vel[1] = -abs(bul.vel[1])

				bul.pos = [between(0, v, 120) for v in bul.pos]

				bul.show(SEFFECT, color = [255, 255, 192])

				rem = False

				for zom in zombies:
					if zom.getRect().collidepoint(*bul.intPos()):
						zom.health -= 2
						rem = True
						for i in range(randint(2, 5)):
							blood.append(Particle(bul.intPos(), [v+random()*2-1 for v in bul.vel], slow = .85))

				if Particle.mag(*bul.vel) <= 0.5:
					rem = True
					
				if rem: bullets.remove(bul)

			for blo in blood:
				blo.move()
				blo.show(SEFFECT, color = [randint(192, 255), 0, 0, randint(64, 255)])
				
				if Particle.mag(*blo.vel) <= 0.5:
					blood.remove(blo)

			# graphics
			h = int(SIZE[1]//16 - player.getCenter()[1])
			h = between(-48, h, 0)

			SURFACE.blit(img_bank['bg'], [0, 0])

			dist_dict = {tuple(reversed(h.pos)): h for h in zombies + [player]}
			for k in sorted(dist_dict):
				dist_dict[k].show(SURFACE, frame)

			SURFACE.blit(img_bank['bg_tree'], [0, 0])
			SURFACE.blit(SEFFECT, [0, 0])

			SCREEN.blit(pg.transform.scale(SURFACE, [SIZE[0]]*2), [0, h*8])

		pg.display.update()