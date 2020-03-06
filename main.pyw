import pygame as pg, os, platform
from entites import Player, Bullet
from random import randint, random
from math import sin
	

def between(a: int, b: int, c: int, /):
	"""Return b such as a < b < c."""
	return max(a, min(b, c))


def getImgBank(path: str) -> dict:
	"""Return a dict containing all images in a folder with recursion."""
	d = {}
	for f in os.listdir(path):
		if len(f) > 4 and f[-4:] in ('.png', 'jpg'):
			d[f[:-4]] = pg.image.load(f'{path}/{f}')
		else:
			d[f] = getImgBank(f'{path}/{f}')
	return d


if __name__ == "__main__":
	if 'Windows' in platform.platform(): # car pb de dpi sur windows
		from ctypes import windll
		windll.shcore.SetProcessDpiAwareness(1)

	pg.init()
	os.system('cls')

	img_bank = getImgBank('img')
	player = Player([randint(20, 60) for i in range(2)], img_bank['player'])
	bullets = []

	SIZE = 960, 576

	SCREEN = pg.display.set_mode(SIZE)
	SURFACE = pg.Surface([120, 120])
	SEFFECT = pg.Surface([120, 120])
	SEFFECT.set_colorkey([0]*3)
 
	clock = pg.time.Clock()

	bold_font = pg.font.Font(f"Consolas.ttf", 24)
	bold_font.set_bold(True)

	frame = 0
	game_state = 'menu'
	while game_state != 'end':
		frame += 1
		clock.tick(48)

		if any(e.type == pg.QUIT for e in pg.event.get()):
			game_state = 'end'
			continue

		keys = pg.key.get_pressed()

		SCREEN.fill([0]*3)

		if game_state == 'menu':
			SCREEN.blit(bold_font.render("> press [Enter] to start.", False, [abs(int(sin(frame/5)*255))]*3), [10, 16])
			if keys[pg.K_RETURN]:
				game_state = 'play'

		if game_state == 'play':
			# logic
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
					if random() >= 0.9:
						SEFFECT.set_at([x, y], [0]*3)


			for b in bullets:
				b.move()
				x, y = b.pos

				if x < 0: b.vel[0] = abs(b.vel[0])
				if y < 0: b.vel[1] = abs(b.vel[1])
				if x > 120: b.vel[0] = -abs(b.vel[0])
				if y > 120: b.vel[1] = -abs(b.vel[1])

				b.pos = [between(0, v, 120) for v in b.pos]

				b.show(SEFFECT)

				if Bullet.mag(*b.vel) <= 0.5:
					bullets.remove(b)

			# graphics
			h = int(SIZE[1]//16 - player.getCenter()[1])
			h = between(-48, h, 0)

			SURFACE.blit(img_bank['bg'], [0, 0])
			player.show(SURFACE, frame)
			SURFACE.blit(img_bank['bg_tree'], [0, 0])
			SURFACE.blit(SEFFECT, [0, 0])

			SCREEN.blit(pg.transform.scale(SURFACE, [SIZE[0]]*2), [0, h*8])

		pg.display.update()