import terminal
import sys
from enum import Enum, auto
import re
from math import pi as PI
from math import sin

DEBUG = False

RADIUS = 5
AUDIO_OFFSET = 0
EPS = 1e-7

class Timing:
    def __init__(self):
        pass

class NoteType(Enum):
    TAP = auto()
    HOLD = auto()
    ARC = auto()
    ARCTAP = auto()
    BLACKCURVE = auto()

class ArcEasing(Enum):
    b = auto()
    s = auto()
    si = auto()
    so = auto()
    sisi = auto()
    siso = auto()
    sosi = auto()
    soso = auto()

class ArcColor(Enum):
    BLUE = auto()
    RED = auto()
    GREEN = auto()


class __Note:
    def __init__(self, TYPE: NoteType, time: int, endTime: int):
        self.TYPE = TYPE
        self.time = time
        self.endTime = endTime if endTime else time


class __NoteARC(__Note):
    def __init__(self, TYPE: NoteType, time: int, endTime: int,
                 startX: float, endX: float,
                 easing: ArcEasing,
                 startY: float, endY: float):
        super().__init__(TYPE, time, endTime)
        self.startX = startX
        self.endX = endX
        self.easing = easing
        self.startY = startY
        self.endY = endY

    def _bezier_find_by_x(self, x, y, given_x):
        target_y = y[0]

        if y[0] == y[3]:
            return target_y
        if given_x == x[0]:
            return y[0]
        if given_x == x[3]:
            return y[3]
        
        # Do binary-search over t (0 <= t <= 1)
        bezier = lambda t : ((1-t)*((1-t)*((1-t)*x[0]+t*x[1])+t*((1-t)*x[1]+t*x[2]))+t*((1-t)*((1-t)*x[1]+t*x[2])+t*((1-t)*x[2]+t*x[3])),
         (1-t)*((1-t)*((1-t)*y[0]+t*y[1])+t*((1-t)*y[1]+t*y[2]))+t*((1-t)*((1-t)*y[1]+t*y[2])+t*((1-t)*y[2]+t*y[3])))
        
        L, R = 0, 1
        for iter in range(500):
            mid = (L + R) / 2
            point = bezier(mid)
            target_y = point[1]
            if abs(point[0] - given_x) < EPS:
                return round(target_y, 2)
            if point[0] <= given_x:
                L = mid
            else:
                R = mid

        return round(target_y, 2)

    def _interpolate_bezier(self, currentTime: int) -> list:
        point = [0, 0]
        b = 0.35
        x, y = [None] * 4, [None] * 4

        # (time, X)
        x[0], y[0] = (self.time, self.startX)
        x[3], y[3] = (self.endTime, self.endX)
        x[1], y[1] = (((1 - b) * x[0] + b * x[3]), y[0])
        x[2], y[2] = (x[3] - (x[1] - x[0]), y[3])
        point[0] = self._bezier_find_by_x(x, y, currentTime)

        # (time, Y)
        x[0], y[0] = (self.time, self.startY)
        x[3], y[3] = (self.endTime, self.endY)
        x[1], y[1] = (((1 - b) * x[0] + b * x[3]), y[0])
        x[2], y[2] = (x[3] - (x[1] - x[0]), y[3])
        point[1] = self._bezier_find_by_x(x, y, currentTime)

        return point
    
    def _interpolate_straight(self, currentTime: int, startCoord: float, endCoord: float) -> float:
        tx = (currentTime - self.time) / (self.endTime - self.time)
        return round(startCoord + (endCoord - startCoord) * tx, 2)
    
    def _transform(self, sa, s, sb, ta, tb):  # return t
        ratio = (s - sa) / (sb - sa)
        return ta + ratio * (tb - ta)

    def _interpolate_sine_in(self, currentTime: int, startCoord: float, endCoord: float) -> float:
        tX = self._transform(self.time, currentTime, self.endTime, 0, PI / 2)
        tY = sin(tX)
        return self._transform(0, tY, 1, startCoord, endCoord)

    def _interpolate_sine_out(self, currentTime: int, startCoord: float, endCoord: float) -> float:
        tX = self._transform(self.time, currentTime, self.endTime, -PI / 2, 0)
        tY = sin(tX)
        return self._transform(-1, tY, 0, startCoord, endCoord)

    def interpolate(self, currentTime: int) -> list:
        if self.easing == ArcEasing.b:
            return self._interpolate_bezier(currentTime)
        elif self.easing == ArcEasing.s:
            return [
                self._interpolate_straight(currentTime, self.startX, self.endX),
                self._interpolate_straight(currentTime, self.startY, self.endY)
            ]
        else:
            point = [0, 0]

            if (self.easing == ArcEasing.si or
                    self.easing == ArcEasing.sisi or
                    self.easing == ArcEasing.siso):
                point[0] = self._interpolate_sine_in(currentTime, self.startX, self.endX)
            elif (self.easing == ArcEasing.so or
                    self.easing == ArcEasing.sosi or
                    self.easing == ArcEasing.soso):
                point[0] = self._interpolate_sine_out(currentTime, self.startX, self.endX)

            if (self.easing == ArcEasing.sisi or
                    self.easing == ArcEasing.sosi):
                point[1] = self._interpolate_sine_in(currentTime, self.startY, self.endY)
            elif (self.easing == ArcEasing.siso or
                    self.easing == ArcEasing.soso):
                point[1] = self._interpolate_sine_out(currentTime, self.startY, self.endY)
            else:
                point[1] = self._interpolate_straight(currentTime, self.startY, self.endY)

            return point




class Tap(__Note):
    def __init__(self, time: int, lane: int):
        super().__init__(NoteType.TAP, time, None)
        self.lane = lane


class Hold(__Note):
    def __init__(self, time: int, endTime: int, lane: int):
        super().__init__(NoteType.HOLD, time, endTime)
        self.lane = lane


class Arc(__NoteARC):
    def __init__(self, time: int, endTime: int,
                 startX: float, endX: float,
                 easing: ArcEasing,
                 startY: float, endY: float,
                 color: ArcColor):
        super().__init__(NoteType.ARC, time, endTime,
                         startX, endX,
                         easing,
                         startY, endY)
        self.color = color


class ArcTap(__Note):
    def __init__(self, time: int, X: float, Y: float):
        super().__init__(NoteType.ARCTAP, time, None)
        self.X = X
        self.Y = Y


class BlackCurve(__NoteARC):
    def __init__(self, time: int, endTime: int,
                 startX: float, endX: float,
                 easing: ArcEasing,
                 startY: float, endY: float,
                 sfx: str, arctaps: list):
        super().__init__(NoteType.BLACKCURVE, time, endTime,
                         startX, endX,
                         easing,
                         startY, endY)
        self.sfx = sfx
        self.arctaps = arctaps if arctaps else list()

    def genArcTaps(self):
        pass



def outputProperties(obj):
    if not DEBUG:
        return
    print("\n".join("%s: %s" % item for item in vars(obj).items()))
    print()

# testTap = Tap(152485,4)
# testHold = Hold(7624, 8950, 1)
# testArc = Arc(662,1325,1.00,0.50,ArcEasing.so,1.00,1.00,ArcColor.RED)
# testBlackCurve = BlackCurve(5966,6629,0.50,0.50,ArcEasing.s,1.00,1.00,[6298])


def parseAff(affFileName: str):
    patterns = {
        "AUDIO_OFFSET": r"AudioOffset:(\d+)",
        NoteType.TAP: r"\((\d+),\s*(\d+)\);",
        NoteType.HOLD: r"hold\((\d+),\s*(\d+),\s*(\d+)\);",
        NoteType.ARC: r"arc\((\d+),\s*(\d+),\s*(-?\d+\.\d{2}),\s*(-?\d+\.\d{2}),\s*([a-z]+),\s*(-?\d+\.\d{2}),\s*(-?\d+\.\d{2}),\s*(\d+),\s*(.+?),\s*false\);",
        NoteType.BLACKCURVE: r"arc\((\d+),\s*(\d+),\s*(-?\d+\.\d{2}),\s*(-?\d+\.\d{2}),\s*([a-z]+),\s*(-?\d+\.\d{2}),\s*(-?\d+\.\d{2}),\s*(\d+),\s*(.+?),\s*true\)",
    }

    easings = {
        "b": ArcEasing.b,
        "s": ArcEasing.s,
        "si": ArcEasing.si,
        "so": ArcEasing.so,
        "sisi": ArcEasing.sisi,
        "siso": ArcEasing.siso,
        "sosi": ArcEasing.sosi,
        "soso": ArcEasing.soso,
    }
    
    colors = {
        "0": ArcColor.BLUE,
        "1": ArcColor.RED,
        "2": ArcColor.GREEN,
    }

    affFile = open(affFileName, "r")
    
    for _clause in affFile.readlines():
        note = None
        flag_matched = False

        clause = _clause.strip()

        for notetype, pattern in patterns.items():
            match = re.match(pattern, clause)
            if not match:
                continue
            
            flag_matched = True
            
            if notetype == "AUDIO_OFFSET":
                if DEBUG:
                    terminal.coloredEcho("YELLOW", " Offset| {}".format(clause))
                AUDIO_OFFSET = int(match.group(1))

            elif notetype == NoteType.TAP:
                if DEBUG:
                    terminal.coloredEcho("GREEN", "  Match| {}: {}".format(notetype, clause))
                time, lane = map(int, match.groups())
                note = Tap(time, lane)

            elif notetype == NoteType.HOLD:
                if DEBUG:
                    terminal.coloredEcho("GREEN", "  Match| {}: {}".format(notetype, clause))
                time, endTime, lane = map(int, match.groups())
                note = Hold(time, endTime, lane)

            elif notetype == NoteType.ARC:
                if DEBUG:
                    terminal.coloredEcho("GREEN", "  Match| {}: {}".format(notetype, clause))
                time, endTime, startX, endX, easing, startY, endY, color, sfx = match.groups()
                note = Arc(int(time), int(endTime),
                           float(startX), float(endX),
                           easings[easing],
                           float(startY), float(endY),
                           colors[color])
            
            elif notetype == NoteType.BLACKCURVE:
                if DEBUG:
                    terminal.coloredEcho("GREEN", "  Match| {}: {}".format(notetype, clause))
                time, endTime, startX, endX, easing, startY, endY, color, sfx = match.groups()
                arctaps = list()
                _tmp = re.search(r"\[.*\]", clause)
                if _tmp:
                    arctaps = [int(arctap) for arctap in re.findall(r"arctap\((\d+)\)", _tmp.group())]
                    if DEBUG:
                        print("arctaps: {}".format(arctaps))
                note = BlackCurve(int(time), int(endTime),
                                  float(startX), float(endX),
                                  easings[easing],
                                  float(startY), float(endY),
                                  sfx, arctaps)
            
            break

        if DEBUG and not flag_matched:
            terminal.coloredEcho("RED", "Unmatch| {}".format(clause))
        
        yield note

    affFile.close()



if __name__ == "__main__":
    terminal.sysInit()
    
    notes = list()
    for note in parseAff(sys.argv[1]):
        if note:
            notes.append(note)
    
    lane_to_coord = [
        (0, 0),
        (-0.25, 0),
        (0.25, 0),
        (0.75, 0),
        (1.25, 0),
    ]
    
    indeg = set()
    for note in notes:
        if note.TYPE == NoteType.ARC:
            indeg.add((note.endTime, note.endX, note.endY, note.color))
        elif note.TYPE == NoteType.HOLD or note.TYPE == NoteType.TAP:
            indeg.add((note.endTime, lane_to_coord[note.lane][0], lane_to_coord[note.lane][1], ArcColor.BLUE))
            indeg.add((note.endTime, lane_to_coord[note.lane][0], lane_to_coord[note.lane][1], ArcColor.RED))
        elif note.TYPE == NoteType.BLACKCURVE:
            for t in note.arctaps:
                indeg.add((t, note.interpolate(t)[0], ArcColor.BLUE))
                indeg.add((t, note.interpolate(t)[0], ArcColor.RED))
            pass
    
    hits = set()  # (time, x-coord, sfx)
    for note in notes:
        if note.TYPE == NoteType.TAP:
            hits.add((note.time, lane_to_coord[note.lane][0], "hit1"))
        elif note.TYPE == NoteType.HOLD:
            hits.add((note.time, lane_to_coord[note.lane][0], "hit1"))
        elif note.TYPE == NoteType.ARCTAP:
            hits.add((note.time, note.X, "hit2"))
        elif note.TYPE == NoteType.ARC:
            no_hitsound = False
            for t in range(note.time - RADIUS, note.time + RADIUS + 1):
                for x in range(int(100 * note.startX) - RADIUS, int(100 * note.startX) + RADIUS + 1):
                    for y in range(int(100 * note.startY) - RADIUS, int (100 * note.startY) + RADIUS + 1):
                        if (t, round(x / 100, 2), round(y / 100, 2), note.color) in indeg:
                            no_hitsound = True
                            break
            if not no_hitsound:
                hits.add((note.time, note.startX, "hit3"))
        elif note.TYPE == NoteType.BLACKCURVE:
            for t in note.arctaps:
                hits.add((t, note.interpolate(t)[0], "hit2"))


    hitsFile = open("hits.txt", "w")
    for hit in sorted(hits):
        hitsFile.write(str(hit[0]) + " " + str(hit[1]) + " " + str(hit[2]) + "\n")
    hitsFile.close()

    
    
