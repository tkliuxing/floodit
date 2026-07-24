"""按时间推进的粒子特效。

和 anim.py 一样，所有运动都由 dt 驱动，与帧率无关。
粒子只负责表现，不影响任何游戏逻辑。
"""

import math
import random
from dataclasses import dataclass, field

import pygame as pg

# 重力加速度（像素/秒²）
GRAVITY = 900.0
# 空气阻力，每秒保留的速度比例
DRAG = 0.86


@dataclass
class Particle:
    """单个粒子。位置和速度都以像素/秒为单位。"""

    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple
    size: float
    max_life: float = field(default=0.0)
    gravity: float = GRAVITY
    drag: float = DRAG
    spin: float = 0.0
    angle: float = 0.0

    def __post_init__(self):
        if not self.max_life:
            self.max_life = self.life

    @property
    def alive(self) -> bool:
        return self.life > 0

    @property
    def fade(self) -> float:
        """剩余寿命比例，1 为刚生成，0 为消失。"""
        return max(0.0, self.life / self.max_life) if self.max_life else 0.0

    def update(self, dt: float):
        self.life -= dt
        vx0, vy0 = self.vx, self.vy
        self.vy += self.gravity * dt
        # 阻力按 dt 指数衰减，保证不同帧率下衰减量一致
        damping = self.drag**dt
        self.vx *= damping
        self.vy *= damping
        # 位置用步内平均速度积分（梯形法）。若直接用步末速度，
        # dt 越大重力被累积得越多，轨迹会随帧率明显漂移。
        self.x += (vx0 + self.vx) * 0.5 * dt
        self.y += (vy0 + self.vy) * 0.5 * dt
        self.angle += self.spin * dt


class ParticleSystem:
    """粒子容器。负责推进、绘制和自动回收。"""

    def __init__(self, max_particles: int = 400):
        self.particles: list[Particle] = []
        self.max_particles = max_particles

    def __len__(self) -> int:
        return len(self.particles)

    @property
    def active(self) -> bool:
        return bool(self.particles)

    def clear(self):
        self.particles.clear()

    def emit(self, particles):
        """加入一批粒子，超出上限时丢弃最旧的。"""
        self.particles.extend(particles)
        if len(self.particles) > self.max_particles:
            del self.particles[: len(self.particles) - self.max_particles]

    def update(self, dt: float):
        """推进所有粒子并回收死亡的。"""
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, screen: pg.Surface):
        """绘制所有粒子，返回被弄脏的矩形列表以便局部擦除。"""
        dirty = []
        for p in self.particles:
            size = max(1, round(p.size * p.fade))
            rect = pg.Rect(round(p.x) - size, round(p.y) - size, size * 2, size * 2)
            pg.draw.rect(screen, p.color, rect)
            dirty.append(rect)
        return dirty


def burst(
    pos: tuple,
    color: tuple,
    count: int = 6,
    speed: tuple = (60.0, 200.0),
    life: tuple = (0.25, 0.5),
    size: tuple = (1.5, 3.0),
    rng: random.Random = random,
) -> list:
    """向四周迸发的小碎屑，用于格子变色。"""
    out = []
    for _ in range(count):
        angle = rng.uniform(0, math.tau)
        v = rng.uniform(*speed)
        out.append(
            Particle(
                x=pos[0],
                y=pos[1],
                vx=math.cos(angle) * v,
                vy=math.sin(angle) * v,
                life=rng.uniform(*life),
                color=color,
                size=rng.uniform(*size),
            )
        )
    return out


def confetti(
    area: pg.Rect,
    colors: list,
    count: int = 90,
    rng: random.Random = random,
) -> list:
    """从区域顶部撒落的彩带，用于胜利。"""
    out = []
    for _ in range(count):
        out.append(
            Particle(
                x=rng.uniform(area.left, area.right),
                y=rng.uniform(area.top - area.height * 0.3, area.top),
                vx=rng.uniform(-70, 70),
                vy=rng.uniform(0, 120),
                life=rng.uniform(0.9, 1.8),
                color=rng.choice(colors),
                size=rng.uniform(2.0, 4.0),
                gravity=GRAVITY * 0.35,
                drag=0.95,
                spin=rng.uniform(-8, 8),
            )
        )
    return out


class Ripple:
    """从点击处扩散的渐隐圆环。"""

    def __init__(
        self,
        pos: tuple,
        color: tuple,
        radius: float = 34.0,
        duration: float = 0.4,
    ):
        self.x, self.y = pos
        self.color = color
        self.radius = radius
        self.duration = duration
        self.elapsed = 0.0

    @property
    def alive(self) -> bool:
        return self.elapsed < self.duration

    @property
    def progress(self) -> float:
        if self.duration <= 0:
            return 1.0
        return min(1.0, self.elapsed / self.duration)

    def update(self, dt: float):
        self.elapsed += dt

    def draw(self, screen: pg.Surface) -> pg.Rect:
        """绘制圆环，返回脏矩形。"""
        t = self.progress
        r = max(1, round(self.radius * (1 - (1 - t) ** 2)))
        width = max(1, round(3 * (1 - t)))
        rect = pg.Rect(round(self.x) - r, round(self.y) - r, r * 2, r * 2)
        pg.draw.circle(screen, self.color, (round(self.x), round(self.y)), r, width)
        return rect


class ScreenShake:
    """屏幕震动，返回每帧的绘制偏移。"""

    def __init__(
        self, amplitude: float = 6.0, duration: float = 0.35, freq: float = 32.0
    ):
        self.amplitude = amplitude
        self.duration = duration
        self.freq = freq
        self.elapsed = 0.0

    @property
    def alive(self) -> bool:
        return self.elapsed < self.duration

    def update(self, dt: float):
        self.elapsed += dt

    def offset(self) -> tuple:
        """当前帧的 (dx, dy)，振幅随时间线性衰减到 0。"""
        if not self.alive:
            return (0, 0)
        decay = 1 - self.elapsed / self.duration
        a = self.amplitude * decay
        return (
            round(math.sin(self.elapsed * self.freq) * a),
            round(math.cos(self.elapsed * self.freq * 1.3) * a * 0.6),
        )
