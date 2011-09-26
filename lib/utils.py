#!/usr/bin/env python
# -*- coding: utf-8  -*-
'''
A small library with useful functions for ATC-NG.
'''

from math import cos, sin, radians, degrees, atan2

import pygame.surface
from pygame.locals import *

from engine.settings import settings as S
from lib.euclid import Vector2, Vector3

__author__ = "Mac Ryan"
__copyright__ = "Copyright 2011, Mac Ryan"
__license__ = "GPL v3"
#__version__ = "<dev>"
#__date__ = "<unknown>"
__maintainer__ = "Mac Ryan"
__email__ = "quasipedia@gmail.com"
__status__ = "Development"

def rint(float_):
    '''
    Return the rounded integer of the float_.
    '''
    return int(round(float_))

def sc(vector):
    '''
    Return a version of a 2-elements iterable (coordinates) suitable for
    screen representation. That means:
    - Scaled (to window resolution)
    - Translated (to below x axis)
    - With the y sign reversed (y are positive under x, on screen)
    '''
    x, y = [int(round(c / S.METRES_PER_PIXEL)) for c in vector]
    return (x, -(y - S.RADAR_RECT.height))

def render_lines(fontobj, lines, colour):
    '''
    Return the image of the rendered multiline text.
    '''
    new_lines = [(l, colour) for l in lines]
    return render_colour_lines(fontobj, new_lines)

def render_colour_lines(fontobj, lines):
    '''
    Return the image of the rendered multiline text. Each enty in ``lines``
    is a tuple in the form (text, colour).
    '''
    font_height = fontobj.get_height()
    surfaces = [fontobj.render(ln, True, col) for ln, col in lines]
    maxwidth = max([s.get_width() for s in surfaces])
    result = pygame.surface.Surface((maxwidth, len(lines)*font_height),
                                    SRCALPHA)
    for i in range(len(lines)):
        result.blit(surfaces[i], (0,i*font_height))
    return result

def get_fontobj_by_text_width(font, text, max_size):
    '''
    Return a font object calibrated for the ``text`` to fit within the box
    defined by ``max_size``, a (width, height) tuple.
    '''
    size = 1
    max_w, max_h = max_size
    while True:
        fontobj = pygame.font.Font(font, size)
        if isinstance(text, list):
            img = render_lines(fontobj, text, S.WHITE)
        else:
            img = fontobj.render(text, True, S.WHITE)
        w,h = img.get_size()
        if w > max_w or h > max_h:
            break
        last_ok = fontobj
        size += 1
    return last_ok

def blur_image(surface, amt):
    '''
    Return a blurred copy of ``surface`` by the given ``amount`` (that must be
    1 or greater).
    [Adapted from: http://www.akeric.com/blog/?p=720]
    '''
    # 'amt' must be greater than 1.0
    assert amt > 1
    scale = 1.0/amt
    surf_size = surface.get_size()
    scale_size = (int(surf_size[0]*scale), int(surf_size[1]*scale))
    surf = pygame.transform.smoothscale(surface, scale_size)
    surf = pygame.transform.smoothscale(surf, surf_size)
    return surf

def blit_dead_centre(dest, source, pos=None):
    '''
    Blit ``source`` onto ``dest`` by using ``dest`` centre (instead of its
    upper-left corner as reference. The ``pos`` parameter defaults to
    ``dest.center``.
    '''
    if pos == None:
        pos = dest.get_rect().center
    target_pos = (pos[0] - source.get_width()/2,
                  pos[1] - source.get_height()/2)
    dest.blit(source, target_pos)

def in_between(boundaries, value):
    '''
    Return True if value is between boundaries.
    Boundaries : any two values (tuple, list)
    Value: the value to be tested
    '''
    PRECISION = 7
    tmp = list(boundaries)
    tmp.append(value)
    tmp = [round(el, PRECISION) for el in tmp]
    tmp.sort()
    return tmp[1] == round(value, PRECISION)

def heading_in_between(boundaries, value):
    '''
    This is a heading-specific implementation of `test_in_between`.
    From a geometrical point of view, an angle is always between other two.
    This method return True, if the tested value is between the *smallest*
    angle between the other two.
    '''
    # special case for 180°: angles is always in-between
    if (boundaries[0]-boundaries[1])%360 == 180:
        return True
    # early return: if the tested value is == to a limit, is always in-between
    if value in boundaries:
        return True
    sort_a = lambda a,b : [a,b] if (a-b)%360 > (b-a)%360 else [b,a]
    tmp = sort_a(*boundaries)
    a, b = [heading_to_v3(el) for el in tmp]
    v = heading_to_v3(value)
    if cmp(a.cross(v).z, 0) == cmp(a.cross(b).z, 0) == cmp(v.cross(b).z, 0):
        return True
    return False

def v3_to_heading(vector):
    '''
    Return the heading of a vector (CW degrees from North).
    '''
    return (90-degrees(atan2(vector.y, vector.x)))%360

def is_behind(velocity, position, target):
    '''
    Return True if target is behind a point at ``position`` travelling with
    ``velocity``. The function operates on a 2D projection. Behind is defined
    as over 90° from the velocity vector. from the
    '''
    tuple_ = (velocity, position, target)
    velocity, position, target = [Vector3(*el.xy) for el in tuple_]
    if position == target:
        return False
    return velocity.angle(target-position) >= 1.5708  #90° in radians

def heading_to_v3(heading):
    '''
    Return a normalised vector pointing in the heading direction.
    '''
    heading = radians(90-heading)
    return Vector3(cos(heading), sin(heading)).normalized()

def get_rect_at_centered_pos(img, pos):
    '''
    Return the rect based on where 'img' should be blit if 'pos' needs to be
    its centre.
    '''
    rect = img.get_rect()
    pos = [a - b for a, b in zip(pos, img.get_rect().center)]
    rect.x, rect.y = pos
    return rect

def rectangle_intersection(c1, c2, c3, c4):
    '''
    Return True if the rectangle defined by c1-c2 and the one defined by c3-c4
    intersect. Even one single point of intersection (shared corner) count!
    '''
    x = lambda corner : corner[0]
    y = lambda corner : corner[1]
    right  = lambda corners : max([x(corner) for corner in corners])
    left   = lambda corners : min([x(corner) for corner in corners])
    top    = lambda corners : max([y(corner) for corner in corners])
    bottom = lambda corners : min([y(corner) for corner in corners])
    r1 = (c1, c2)
    r2 = (c3, c4)
    if right(r1) < left(r2) or left(r1) > right(r2) or \
       top(r1) < bottom(r2) or bottom(r1) > top(r2):
        return False
    return True

def __intersect_values(p1, p2, p3, p4):
    '''
    Return the intermediate values used by the line-intersection formula at:
    http://paulbourke.net/geometry/lineline2d/
    These values can be processed differently according to what is needed (for
    example for line, segment and ray intersection (see other utility
    functions)
    '''
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    num_ua = (x4-x3)*(y1-y3)-(y4-y3)*(x1-x3)
    num_ub = (x2-x1)*(y1-y3)-(y2-y1)*(x1-x3)
    den = (y4-y3)*(x2-x1)-(x4-x3)*(y2-y1)
    return num_ua, num_ub, den

def line_intersection(p1, p2, p3, p4):
    '''
    Calculate the intersection point between lines (infinite length) defined as
    passing for points p1-p2 and p3-p4 respectively.
       Returns a tuple (value, comment)
    '''
    num_ua, num_ub, den = __intersect_values(p1, p2, p3, p4)
    if num_ua == num_ub == den == 0:
        return None, 'overlapping'
    if den == 0:
        return None, 'parallelism'
    ua = 1.0*num_ua/den
    ub = 1.0*num_ub/den
    x1, y1 = p1
    x2, y2 = p2
    x = x1 + ua*(x2-x1)
    y = y1 + ua*(y2-y1)
    return (x, y), 'intersection'

def segment_intersection(p1, p2, p3, p4):
    '''
    Calculate the intersection point between segments (finite length) defined
    as lines between p1-p2 and p3-p4 respectively.
       Returns a tuple (value, comment)
    '''
    num_ua, num_ub, den = __intersect_values(p1, p2, p3, p4)
    if num_ua == num_ub == den == 0:
        # Note that two aligned but disjointed segments (0,0-1,1 and 3,3-4,4)
        # would still result in an overlapping message. To prevent this
        # behaviour, we check the bounding rectangles instead.
        if not rectangle_intersection(p1, p2, p3, p4):
            return None, 'separation'
        return None, 'overlapping'
    if den == 0:
        return None, 'parallelism'
    ua = 1.0*num_ua/den
    ub = 1.0*num_ub/den
    if 0 > ua or 0 > ub or 1 < ua or 1 < ub:
        return None, 'separation'
    x1, y1 = p1
    x2, y2 = p2
    x = x1 + ua*(x2-x1)
    y = y1 + ua*(y2-y1)
    return (x, y), 'intersection'

def ground_distance(v1, v2):
    '''
    Return the ground distance between two points indicated by 2D or 3D
    vectors.
    '''
    v1 = Vector2(*v1.xy)
    v2 = Vector2(*v2.xy)
    return abs(v1-v2)

def distance_point_line(point, origin, vector):
    '''
    Return the distance between ``point`` and the line passing from ``origin``
    and being parallel to ``vector``.
    See: http://members.tripod.com/vector_applications/distance_point_line
    and: http://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
    '''
    ap = point - origin
    unit = vector.normalized()
    return abs(ap - (ap.dot(unit) * unit))

def logical_xor(a, b):
    '''
    Perform logical XOR.
    '''
    return bool(a) ^ bool(b)

def only_one(list_):
    '''
    Return True if one, and only one in the list has boolean value == True.
    '''
    return len(filter(bool, list_)) == 1


