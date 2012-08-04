'''
This module contains functions for handling an abstract asteroid.

Testing has determined the graphics card is the performance bottleneck.
Python classes Asteroid, Level, TileGroup are designed for ease of use.
Performance is not a concern here.

The main interface is the Asteroid class.
'''
import random

from pandac.PandaModules import PandaNode
from pandac.PandaModules import NodePath
from pandac.PandaModules import CardMaker

import resource

LEVEL_SPACING = 50
TILE_SIZE  = 10
TILE_GRP_SIZE = 5 #length and width of each tile group (grouped for performance)
LEVEL_SIZE = 7 #length and width of each asteroid level, in tile groups

NUM_LEVELS = 12

CARD_MAKER = CardMaker('tile_generator')
CARD_MAKER.setFrame(0, TILE_SIZE, 0, TILE_SIZE)

#need to figure out how to do pathfinding -- what kind of data structures required here?

class TileType(object):
	texture = None

class Empty(TileType):
	def __init__(self):
		self.passable = True

class Natural(TileType):
	def __init__(self):
		self.passable = False

	def tunnel(self, direction):
		self.passable = True # TODO: figure out how to draw the tunnel

class Rock(Natural):
	texture = resource.TEXTURES.rocks


class Asteroid(object):
	def __init__(self, name="Asteroid"):
		self.name = name
		#root nodepath for asteroid
		self.nodepath = NodePath(PandaNode("Asteroid"+name))
		#initialize with empty contents
		self._width  = TILE_GRP_SIZE * LEVEL_SIZE
		self._height = TILE_GRP_SIZE * LEVEL_SIZE
		self._depth  = NUM_LEVELS
		self.contents = [[[Empty() for i in range(self.width)] 
							       for j in range(self.height)]
							       for k in range(self.depth)]
		self.levels = [Level(self, i) for i in range(NUM_LEVELS)]
		for i in range(NUM_LEVELS):
			self.levels[i].nodepath.setPos(0, i*LEVEL_SPACING, 0)

	@classmethod
	def make_spheroid(cls, tile_type, name="Asteroid"):
		self = cls(name)
		z_scale = NUM_LEVELS+1
		y_scale = x_scale = TILE_GRP_SIZE * LEVEL_SIZE
		for i in range(NUM_LEVELS):
			for x in range(x_scale):
				for y in range(y_scale):
					distance = ((0.5 - 1.0*(i+1)/z_scale)**2 + 
								(0.5-1.0*x/x_scale)**2 + 
								(0.5-1.0*y/y_scale)**2)**0.5
					if distance < 0.5:
						self.update(x, y, i, tile_type)
		self.redraw()
		return self

	def update(self, x, y, level, tile_type):
		self.contents[level][y][x] = tile_type
		self.levels[level].update(x, y, tile_type.texture)

	def redraw(self):
		for level in self.levels:
			level.redraw()

	def get_pos(self, x, y, level):
		'convert asteroid coordinates to position'
		pos_x, pos_y, pos_z = self.nodepath.getPos()
		return (pos_x + TILE_SIZE*(x+0.5), 
			    pos_y + level * LEVEL_SPACING, 
			    pos_z + TILE_SIZE*(y+0.5))

	@property
	def width(self): return self._width

	@property
	def height(self): return self._height

	@property
	def depth(self): return self._depth

	def get(self, x, y, level):
		try:
			return self.contents[level][y][x]
		except IndexError:
			return None


class Level(object):
	'''
	Represents one level of the asteroid.
	Internal to Asteroid mostly.
	'''
	def __init__(self, parent, num):
		self.parent = parent
		self.name = "{0}-Level#{1}".format(parent.name, num)
		#create one root nodepath for the overall level
		self.nodepath = NodePath(PandaNode(self.name))
		self.tile_groups = [[TileGroup(self, i, j) 
							for i in range(LEVEL_SIZE)] 
							for j in range(LEVEL_SIZE)]
		step = TILE_GRP_SIZE * TILE_SIZE
		for i in range(LEVEL_SIZE):
			for j in range(LEVEL_SIZE):
				self.tile_groups[i][j].nodepath.setPos(i*step, 0, j*step)
		self.nodepath.reparentTo(self.parent.nodepath)
		
	def update(self, x, y, texture):
		tgs = TILE_GRP_SIZE
		self.tile_groups[x/tgs][y/tgs].update(x%tgs, y%tgs, texture)

	def redraw(self):
		for row in self.tile_groups:
			for tile_group in row:
				tile_group.redraw()
		

class TileGroup(object):
	def __init__(self, parent, tile_x, tile_y):
		self.parent = parent
		self.name = "{0}:TileGroup({1},{2})".format(parent.name,tile_x, tile_y)
		self.nodepath = NodePath(PandaNode(self.name))
		self.textures = [[None]*TILE_GRP_SIZE for i in range(TILE_GRP_SIZE)]
		self.nodepath.reparentTo(self.parent.nodepath)
		self.dirty = False

	def update(self, x, y, texture):
		if self.textures[x][y] != texture:
			self.textures[x][y] = texture
			self.dirty = True

	def redraw(self):
		if not self.dirty:
			return #nothing has changed, no need to redraw
		container = NodePath(PandaNode(self.name+"container"))
		for i in range(TILE_GRP_SIZE):
			for j in range(TILE_GRP_SIZE):
				cur = self.textures[i][j]
				if cur:
					node = container.attachNewNode(CARD_MAKER.generate())
					node.setTexture(cur)
					node.setTwoSided(True)
					node.setPos(i*TILE_SIZE, 0, j*TILE_SIZE)
		container.flattenStrong()
		for child in self.nodepath.getChildren():
			child.removeNode()
		container.reparentTo(self.nodepath)
		self.dirty = False


def tunnel(asteroid):
	'cut out pieces of the asteroid; allow for pathing tests'
	#dig the initial tunnel through center of mass
	for z in range(asteroid.depth):
		asteroid.update(asteroid.width/2, asteroid.height/2, z, Empty())
	for i in range(20):
		#make a bunch of random cuts that intersect the tunnel
		if random.random() > 0.5:
			ys = range(0, asteroid.height/2)
			xs = [asteroid.width/2]*len(ys)
		else:
			xs = range(0, asteroid.width/2)
			ys = [asteroid.height/2]*len(xs)
		zs = [random.randint(0, asteroid.depth-1)]*len(ys)
		for x, y, z in zip(xs, ys, zs):
			asteroid.update(x,y,z,Empty())
	asteroid.redraw()

