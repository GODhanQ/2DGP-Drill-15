from pico2d import *

import random
import math
import game_framework
import game_world
from Lecture16_AI import common
from behavior_tree import BehaviorTree, Action, Sequence, Condition, Selector


# zombie Run Speed
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 10.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

# zombie Action Speed
TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 10.0

animation_names = ['Walk', 'Idle']


class Zombie:
    images = None

    def load_images(self):
        if Zombie.images == None:
            Zombie.images = {}
            for name in animation_names:
                Zombie.images[name] = [load_image("./zombie/" + name + " (%d)" % i + ".png") for i in range(1, 11)]
            Zombie.font = load_font('ENCR10B.TTF', 40)
            Zombie.marker_image = load_image('hand_arrow.png')


    def __init__(self, x=None, y=None):
        self.x = x if x else random.randint(100, 1180)
        self.y = y if y else random.randint(100, 924)
        self.load_images()
        self.dir = 0.0      # radian 값으로 방향을 표시
        self.speed = 0.0
        self.frame = random.randint(0, 9)
        self.state = 'Idle'
        self.ball_count = 0

        self.patrol_locations = [(43, 274), (1118, 274), (1050, 494), (575, 804),
                                 (235, 991), (575, 804), (1050, 494), (1118, 274)]
        self.loc_no = 0
        self.tx, self.ty = 1000, 1000
        # 여기를 채우시오.

        self.build_behavior_tree()


    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50


    def update(self):
        self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION
        # fill here
        self.BT.run()


    def draw(self):
        if math.cos(self.dir) < 0:
            Zombie.images[self.state][int(self.frame)].composite_draw(0, 'h', self.x, self.y, 100, 100)
        else:
            Zombie.images[self.state][int(self.frame)].draw(self.x, self.y, 100, 100)
        self.font.draw(self.x - 10, self.y + 60, f'{self.ball_count}', (0, 0, 255))
        Zombie.marker_image.draw(self.tx+25, self.ty-25)

        draw_rectangle(*self.get_bb())

        draw_circle(self.x, self.y, int(PIXEL_PER_METER * 7), 255, 255, 0)

    def handle_event(self, event):
        pass

    def handle_collision(self, group, other):
        if group == 'zombie:ball':
            self.ball_count += 1


    def set_target_location(self, x=None, y=None):
        self.tx, self.ty = x, y
        return BehaviorTree.SUCCESS
        pass



    def distance_less_than(self, x1, y1, x2, y2, r):
        distance2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
        return distance2 < (PIXEL_PER_METER * r) ** 2
        pass



    def move_little_to(self, tx, ty):
        # 각도 theta 구하고
        self.dir = math.atan2(ty - self.y, tx - self.x)
        # 거리 구하기
        distance = RUN_SPEED_PPS * game_framework.frame_time
        self.x += distance * math.cos(self.dir)
        self.y += distance * math.sin(self.dir)
        pass



    def move_to(self, r=0.5):
        # 목표 지점으로 조금 이동
        self.state = 'Walk'
        self.move_little_to(self.tx, self.ty)

        # 목표 지점에 거의 도착했으면 SUCCESS 리턴
        if self.distance_less_than(self.x, self.y, self.tx, self.ty, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING

        pass

    def set_random_location(self):
        self.tx = random.randint(100, 1180)
        self.ty = random.randint(100, 924)
        return BehaviorTree.SUCCESS
        pass


    def if_boy_nearby(self, distance):
        if self.distance_less_than(common.boy.x, common.boy.y, self.x, self.y, distance):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL
        pass

    def run_from_boy(self):
        self.state = 'Walk'

        dx = self.x - common.boy.x
        dy = self.y - common.boy.y

        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance == 0:
            return BehaviorTree.FAIL

        target_x = self.x + (dx / distance) * PIXEL_PER_METER * 7
        target_y = self.y + (dy / distance) * PIXEL_PER_METER * 7

        self.move_little_to(target_x, target_y)

        # 목표 지점에 도달하지 않았으면 RUNNING 반환
        if not self.distance_less_than(self.x, self.y, target_x, target_y, 0.5):
            return BehaviorTree.RUNNING
        else:
            return BehaviorTree.SUCCESS

    def move_to_boy(self, r=0.5):
        if common.boy.ball_count >= self.ball_count:
            return BehaviorTree.FAIL

        self.state = 'Walk'
        self.move_little_to(common.boy.x, common.boy.y)

        if self.distance_less_than(common.boy.x, common.boy.y, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING
        pass


    def get_patrol_location(self):
        self.tx, self.ty = self.patrol_locations[self.loc_no]
        self.loc_no = (self.loc_no + 1) % len(self.patrol_locations)
        return BehaviorTree.SUCCESS
        pass

    def build_behavior_tree(self):
        boy_nearby_condition = Condition('소년이 근처에 있는가?', self.if_boy_nearby, 7)
        ball_count_condition = Condition('공 개수가 더 많은가?',
                                         lambda: BehaviorTree.SUCCESS if common.boy.ball_count < self.ball_count else BehaviorTree.FAIL)

        move_to_boy_action = Action('소년에게 접근', self.move_to_boy)
        run_from_boy_action = Action('소년에게서 도망', self.run_from_boy)

        # 공 개수 비교 후 행동 선택
        move_to_boy_sequence = Sequence('공 비교 후 접근', ball_count_condition, move_to_boy_action)
        run_from_boy_sequence = Sequence('공 비교 후 도망', Selector('공 비교 실패', ball_count_condition), run_from_boy_action)

        boy_interaction_selector = Selector('소년과의 상호작용', move_to_boy_sequence, run_from_boy_sequence)
        chase_boy_sequence = Sequence('소년 근처에서 행동', boy_nearby_condition, boy_interaction_selector)

        a1 = Action('목적지 설정', self.set_random_location)
        a2 = Action('목적지로 이동', self.move_to)
        wander = Selector('배회', a2, a1)

        root = Selector('Behavior_Tree', chase_boy_sequence, wander)

        self.BT = BehaviorTree(root)


