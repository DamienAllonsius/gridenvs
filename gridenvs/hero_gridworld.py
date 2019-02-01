#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gridenvs.gridworld import GridworldEnv
from gridenvs.gridworld_map import GridworldMap, GameObject
from gridenvs.utils import Direction, Point
import numpy as np
from copy import deepcopy

class HeroGridEnv(GridworldEnv):
    """
    Abstract class for environments with a hero that can be moved around the grid
    """
    ACTION_MAP = [None, ] + Direction.cardinal() # Default actions: Noop, north, east, south west.
    STATE_MAP = dict()       # Description of the state machine. TODO: describe
    BLOCKS = set()           # Names of objects that cannot be trespassed by the hero

    def __init__(self, max_moves=None, obs_type="image"):
        self.game_state = {'done': True}
        self.max_moves = max_moves
        assert self.max_moves is None or self.max_moves > 0
        GridworldEnv.__init__(self, len(self.ACTION_MAP), obs_type=obs_type)

    def _clone(self):
        return (self.world, self.game_state)

    def _restore(self, internal_state):
        self.world = internal_state[0]
        self.game_state = internal_state[1]

    def _reset(self):
        self.game_state['hero'] = self.reset_world()
        assert self.game_state['hero'] is not None, "Reset world should return hero object."
        self.game_state['state_id'] = 0
        self.game_state['moves'] = 0
        self.game_state['done'] = False
        return self.generate_observation(self.world)

    def move(self, obj, direction):
        if direction:
            dx, dy = direction.value
            bb = obj.bounding_box
            if bb[0].x + dx >= 0 and bb[1].x + dx <= self.world.grid_size.x and bb[0].y + dy >= 0 and bb[1].y + dy <= self.world.grid_size.y:
                others = self.world.collisions(obj, direction)
                if dx != 0 and dy != 0:
                    # diagonal move, also check cardinal positions before trying to move diagonally
                    others.extend(self.world.collisions(obj, Direction(Point(dx, 0))))
                    others.extend(self.world.collisions(obj, Direction(Point(0, dy)))) #we may have repeated objects

                for other in others:
                    if other.name in self.BLOCKS:
                        return False
                obj.pos += (dx, dy)
            else:
                return False
        return True

    def move_hero(self, direction):
        return self.move(self.game_state['hero'], direction)

    def update_environment(self, action):
        assert not self.game_state['done'], "The environment needs to be reset."
        if np.issubdtype(type(action), np.integer):
            if action >= len(self.ACTION_MAP):
                raise Exception("Action index %s not in ACTION_MAP." % action)
            else:
                action = self.ACTION_MAP[action]
        else:
            if action not in self.ACTION_MAP:
                raise Exception("Action %s not in ACTION_MAP. ACTION_MAP: %s" % (action, str(self.ACTION_MAP)))

        self.move_hero(action)
        self.game_state['moves'] += 1
        r, self.game_state['done'], info_dict = self.update_world()
        return r, self.game_state['done'], info_dict

    def update_world(self):
        reward = 0.
        end_episode = False
        collisions = self.world.collisions(self.game_state['hero'])
        for collision in collisions:
            try:
                # state, collision_name -> new_state, reward, end_of_episode, collision_fn
                self.game_state['state_id'], reward, end_episode, state_change_fn = self.STATE_MAP[(self.game_state['state_id'], collision.name)]
                if state_change_fn: state_change_fn(self.world, collision)
            except KeyError:
                # if the pair (state, collision_name) does not exist -> new_state = state, reward = 0, end_of_episode = False, fn world, collision_obj = lambda:None
                pass

        if self.max_moves is not None and self.game_state['moves'] >= self.max_moves:
            end_episode = True
        info = {
            'state_id': self.game_state['state_id']
        }
        return reward, end_episode, info

    def create_world(self):
        """
        Called at init.
        :return: the world (GridworldMap object)
        """
        raise NotImplementedError()

    def reset_world(self):
        """
        Called at every reset().
        :return: the hero (GameObject).
        """
        raise NotImplementedError

class ZonesEnv(HeroGridEnv):
    def __init__(self, zone_size_x = 1, zone_size_y = 1, blurred = False, number_gray_colors = 0):
        HeroGridEnv.__init__(self, max_moves = None, obs_type = "image")
        HeroGridEnv._reset()
        # The zone is a region of the state space. For the moment we take squares of size zone_size.
        # The location of the zones are given by a Point, which contains its coordinates.
        self.update_zone(self.game_state['hero'].pos)
        # Is the world blurred ?
        self.blurred = blurred
        self.number_gray_colors = number_gray_colors
        # The grid is cut into several zones of size zone_size_x X zone_size_y
        self.set_zone_size(zone_size_x, zone_size_y)
        
    def set_zone_size(self, x,y):
        self.zone_size = Point(x, y)

    def get_hero_position(self):
        return self.game_state['hero'].pos

    def get_hero_zone(self):
        self.update_zone(self.get_hero_position())
        return self.game_state['zone']
    
    def render_scaled(self, size=(512, 512), mode='human', close=False):
        img = self.render_env_low_quality(size, self.world)
        self.render_gym(img, mode, close)


    def render_env(self, size, grid_state):
        """
        here we are making an average of the colors in the grid
        TODO : make sure that if zone_size_x = zone_size_y = 1 then the environement is not blurred
        """
        # a is a matrix which each entry is an array of 3 integers (RGB)
        # it is just the translation in terms of color of the grid writen in examples.
        grid_colors = grid_state.render()
        # a = self.average_colors(a)
        if (len(grid_colors[0]) % self.zone_size.x == 0) and (len(grid_colors) % self.zone_size.y == 0):
            size_x_image_blurred = int(len(grid_colors[0]) // self.zone_size.x)
            size_y_image_blurred = int(len(grid_colors) // self.zone_size.y)
            image_blurred = cv2.resize(grid_colors, (size_x_image_blurred, size_y_image_blurred), interpolation=cv2.INTER_AREA)
            # gray scale ?
            if self.number_gray_colors:
                for j in range(size_x_image_blurred):
                    for i in range(size_y_image_blurred):
                        rgb = image_blurred[i][j]
                        gray_level = (255 * 3) // self.number_gray_colors
                        sum_rgb = (sum(rgb) // gray_level) * gray_level 
                        image_blurred[i][j] = [sum_rgb]*3

            image_blurred_resized = cv2.resize(image_blurred, size, interpolation=cv2.INTER_NEAREST)
            return image_blurred_resized
        else:
            raise Exception("The gridworld can not be fragmented into zones")

    def update_world(self):
        reward, end_episode, info = HeroGridEnv.update_world()
        info.update({'zone' : self.game_state['zone']})
        info.update({'position' : self.game_state['hero'].pos})
        self.update_zone(self.game_state['hero'].pos)
        return reward, end_episode, info

    def update_zone(self, position):
        """
        gives the current zone for the position
        """
        self.game_state['zone'] =  position // self.zone_size


class StrMapHeroGridEnv(HeroGridEnv):
    MAP = None                  # String array representation of the world
    MAP_DESC = {                # You are able to redefine just a part of this map
        'COLORS': dict(),       # Object name -> color
        'HERO_MARK': 'H',       # Hero object name in the MAP
    }

    def __init__(self, max_moves=None, obs_type="image"):
        self.MAP_DESC = {**StrMapHeroGridEnv.MAP_DESC, **self.MAP_DESC}  # Complete not given parameters
        HeroGridEnv.__init__(self, max_moves=max_moves, obs_type=obs_type)

    def reset_world(self):
        self.world = deepcopy(self.fresh_world)
        res = self.world.get_objects_by_names(self.MAP_DESC['HERO_MARK'])
        assert len(res) == 1 is not None, "Hero not found in world objects (or more than one found?!)."
        return res[0]

    def create_world(self):
        assert self.MAP is not None
        self.world = GridworldMap((len(self.MAP[0]), len(self.MAP)))

        hero_mark = self.MAP_DESC['HERO_MARK']
        hero = None
        for y, string in enumerate(self.MAP):
            for x, point in enumerate(string):
                if point == '.':
                    continue
                else:
                    obj_name = self.MAP[y][x]
                    # print((obj_name, start_x, start_y, end_x, end_y))
                    assert obj_name in self.MAP_DESC["COLORS"], "Please define a color for object %s"%obj_name
                    color = self.MAP_DESC["COLORS"][obj_name]

                    o = GameObject(name=point, pos=(x, y), rgb=color)
                    if point == hero_mark:
                        o.render_preference = 1
                        hero = o
                    self.world.add_object(o)

        assert hero is not None, "Hero could not be loaded."
        self.fresh_world = deepcopy(self.world)
        return self.world
