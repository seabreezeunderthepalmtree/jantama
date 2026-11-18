#!/usr/bin/env python3
"""符数计算练习，仅使用 Python 标准库。

python3 Scripts/符数计算练习.py -n 10
python3 Scripts/符数计算练习.py --seed 42
题目总番数1—4番，最终符数不超过60；按雀魂四麻规则计算连风雀头4符。
"""

import argparse
from collections import Counter
from dataclasses import dataclass
import random
import re

try:
    import readline
except ImportError:
    pass


最大符数 = 60
练习番数 = (1, 2, 3, 4)
SUITS = 'mpsz'
WINDS = ('东', '南', '西', '北')


def fmt(tiles):
    return ''.join(''.join(str(t % 9 + 1) for t in sorted(tiles)
                           if t // 9 == s) + suit
                   for s, suit in enumerate(SUITS)
                   if any(t // 9 == s for t in tiles))


def terminal(t):
    return t >= 27 or t % 9 in (0, 8)


@dataclass(frozen=True)
class Meld:
    tiles: tuple
    kind: str = '暗'  # 暗：手中面子；吃、碰、明杠、暗杠：固定面子

    @property
    def sequence(self):
        return self.tiles[0] != self.tiles[1]

    @property
    def opened(self):
        return self.kind in ('吃', '碰', '明杠')


@dataclass
class Question:
    concealed: tuple  # 和牌前的手牌，不含固定面子
    fixed: tuple
    win: int
    tsumo: bool
    seat: int
    round_wind: int
    riichi: bool
    dora: int

    @property
    def closed(self):
        return not any(m.opened for m in self.fixed)


@dataclass
class Result:
    han: int
    fu: int
    yaku: list
    steps: list
    groups: str


def decompositions(tiles, needed):
    """枚举普通形的雀头和面子；不同拆法均保留。"""
    counts = Counter(tiles)

    def visit(left, groups):
        if not left:
            if len(groups) == needed:
                yield tuple(groups)
            return
        if len(groups) >= needed:
            return
        t = min(left)
        choices = []
        if left[t] >= 3:
            choices.append((t, t, t))
        if t < 27 and t % 9 <= 6 and left[t + 1] and left[t + 2]:
            choices.append((t, t + 1, t + 2))
        for group in choices:
            rest = left.copy()
            rest.subtract(group)
            rest = +rest
            yield from visit(rest, groups + [Meld(group)])

    for pair in sorted(counts):
        if counts[pair] >= 2:
            rest = counts.copy()
            rest[pair] -= 2
            for melds in visit(+rest, []):
                yield pair, melds


def evaluate(q):
    """按高点法选取解释；返回None表示无役或含役满，不用于本练习。"""
    concealed = q.concealed + (q.win,)
    all_tiles = concealed + tuple(t for m in q.fixed for t in m.tiles)
    if any(n > 4 for n in Counter(all_tiles).values()):
        return None
    results = []
    base_yaku = []
    if q.riichi:
        if not q.closed:
            return None
        base_yaku.append(('立直', 1))
    if q.closed and q.tsumo:
        base_yaku.append(('门前清自摸和', 1))
    if all(not terminal(t) for t in all_tiles):
        base_yaku.append(('断幺九', 1))
    suits = {t // 9 for t in all_tiles if t < 27}
    honors = any(t >= 27 for t in all_tiles)
    if len(suits) == 1:
        base_yaku.append(('混一色' if honors else '清一色',
                          (3 if honors else 6) - (not q.closed)))
    # 字一色、绿一色、清老头、九莲宝灯属于役满，不出题。
    if not suits or all(t in (19, 20, 21, 23, 25, 32) for t in all_tiles):
        return None
    if all(t < 27 and terminal(t) for t in all_tiles):
        return None
    if q.closed and not q.fixed and len(suits) == 1 and not honors:
        counts = Counter(t % 9 for t in all_tiles)
        if counts[0] >= 3 and counts[8] >= 3 and all(counts[i] for i in range(1, 8)):
            return None

    counts = Counter(concealed)
    if not q.fixed and len(counts) == 7 and set(counts.values()) == {2}:
        yaku = base_yaku + [('七对子', 2)]
        if all(terminal(t) for t in all_tiles):
            yaku.append(('混老头', 2))
        results.append(Result(sum(h for _, h in yaku) + q.dora, 25, yaku,
                              ['七对子固定25符，不另加雀头、待牌或自摸符。'],
                              ' / '.join(fmt((t, t)) for t in sorted(counts))))

    for pair, hidden in decompositions(concealed, 4 - len(q.fixed)):
        # 和牌张可归属于雀头或任何包含它的暗面子。
        targets = ([-1] if pair == q.win else []) + [
            i for i, m in enumerate(hidden) if q.win in m.tiles]
        for target in targets:
            melds = hidden + q.fixed
            if target == -1:
                wait, wait_fu = '单骑', 2
            elif not hidden[target].sequence:
                wait, wait_fu = '双碰', 0
            else:
                seq = hidden[target].tiles
                if q.win == seq[1]:
                    wait, wait_fu = '坎张', 2
                elif (seq[0] % 9 == 0 and q.win == seq[2]
                      or seq[0] % 9 == 6 and q.win == seq[0]):
                    wait, wait_fu = '边张', 2
                else:
                    wait, wait_fu = '两面', 0
            trips = [m for m in melds if not m.sequence]
            seqs = [m.tiles[0] for m in melds if m.sequence]
            concealed_trips = sum(
                not m.sequence and not m.opened
                and not (not q.tsumo and i == target)
                for i, m in enumerate(melds))
            trip_tiles = {m.tiles[0] for m in trips}
            kans = sum(len(m.tiles) == 4 for m in melds)
            if ({31, 32, 33} <= trip_tiles or len(trip_tiles & set(range(27, 31))) == 4
                    or (len(trip_tiles & set(range(27, 31))) == 3 and pair in range(27, 31))
                    or concealed_trips == 4 or kans == 4):
                return None
            yaku = base_yaku.copy()
            pair_fu = 2 * ((pair >= 31) + (pair == q.seat) + (pair == q.round_wind))
            pinfu = q.closed and len(seqs) == 4 and not pair_fu and wait == '两面'
            if pinfu:
                yaku.append(('平和', 1))
            for t in sorted(trip_tiles):
                if t >= 31:
                    yaku.append(('役牌·' + ('白', '发', '中')[t - 31], 1))
                if t == q.seat:
                    yaku.append(('役牌·自风' + WINDS[t - 27], 1))
                if t == q.round_wind:
                    yaku.append(('役牌·场风' + WINDS[t - 27], 1))
            if q.closed:
                doubles = sum(n // 2 for n in Counter(seqs).values())
                if doubles:
                    yaku.append(('二杯口' if doubles == 2 else '一杯口', 3 if doubles == 2 else 1))
            if len(trips) == 4:
                yaku.append(('对对和', 2))
            if concealed_trips == 3:
                yaku.append(('三暗刻', 2))
            if kans == 3:
                yaku.append(('三杠子', 2))
            if len(trip_tiles & {31, 32, 33}) == 2 and pair >= 31:
                yaku.append(('小三元', 2))
            if all(terminal(t) for t in all_tiles):
                yaku.append(('混老头', 2))
            if seqs and terminal(pair) and all(any(terminal(t) for t in m.tiles) for m in melds):
                yaku.append(('混全带幺九' if honors else '纯全带幺九',
                              (2 if honors else 3) - (not q.closed)))
            for rank in range(7):
                if all(s * 9 + rank in seqs for s in range(3)):
                    yaku.append(('三色同顺', 2 if q.closed else 1))
            for rank in range(9):
                if all(s * 9 + rank in trip_tiles for s in range(3)):
                    yaku.append(('三色同刻', 2))
            for suit in range(3):
                if all(suit * 9 + r in seqs for r in (0, 3, 6)):
                    yaku.append(('一气通贯', 2 if q.closed else 1))
            if not yaku:
                continue  # 宝牌不能充当役。
            steps = ['底符：20符。']
            raw_fu = 20
            for i, m in enumerate(melds):
                if m.sequence:
                    continue
                opened = m.opened or (not q.tsumo and i == target)
                value = (2 if opened else 4) * (2 if terminal(m.tiles[0]) else 1)
                if len(m.tiles) == 4:
                    value *= 4
                label = ('明' if opened else '暗') + ('杠' if len(m.tiles) == 4 else '刻')
                note = '（荣和完成的刻子按明刻计符）' if not q.tsumo and i == target else ''
                steps.append(f'{fmt(m.tiles)}：{label}，+{value}符{note}。')
                raw_fu += value
            steps.append(f'雀头{fmt((pair, pair))}：+{pair_fu}符'
                         + ('（连风雀头）' if pair_fu == 4 else '') + '。')
            raw_fu += pair_fu
            steps.append(f'和牌张{fmt((q.win,))}归入{wait}听牌：+{wait_fu}符。')
            raw_fu += wait_fu
            if pinfu and q.tsumo:
                fu = 20
                steps = ['平和自摸固定20符，不加自摸的2符。']
            else:
                if q.tsumo:
                    raw_fu += 2
                    steps.append('自摸：+2符。')
                elif q.closed:
                    raw_fu += 10
                    steps.append('门前清荣和：+10符。')
                if raw_fu == 20:
                    fu = 30
                    steps.append('副露平和形荣和按30符计算。')
                else:
                    fu = (raw_fu + 9) // 10 * 10
                    steps.append(f'合计{raw_fu}符，向上取整到十位：{fu}符。')
            groups = ' / '.join([fmt((pair, pair)) + '（雀头）'] +
                                [fmt(m.tiles) + ('（' + m.kind + '）' if m.kind != '暗' else '')
                                 for m in melds])
            results.append(Result(sum(h for _, h in yaku) + q.dora, fu, yaku, steps, groups))
    if not results:
        return None
    # 以实际支付总额比较高点法，点数相同时优先高番，再高符。
    def value(r):
        basic = min(r.fu * 2 ** (r.han + 2), 2000)
        up = lambda n: (n + 99) // 100 * 100
        if not q.tsumo:
            points = up(basic * (6 if q.seat == 27 else 4))
        elif q.seat == 27:
            points = 3 * up(basic * 2)
        else:
            points = up(basic * 2) + 2 * up(basic)
        return points, r.han, r.fu
    return max(results, key=value)


def generate_question(rng):
    for _ in range(10000):
        fixed, hidden = [], []
        if rng.random() < 0.12:
            pairs = rng.sample(range(34), 7)
            tiles = [t for t in pairs for _ in range(2)]
        else:
            for _ in range(4):
                if rng.random() < 0.55:
                    t = rng.randrange(3) * 9 + rng.randrange(7)
                    m = Meld((t, t + 1, t + 2), '吃' if rng.random() < 0.25 else '暗')
                else:
                    t = rng.randrange(34)
                    kind = rng.choices(('暗', '碰', '明杠', '暗杠'), (6, 2, 1, 1))[0]
                    m = Meld((t,) * (4 if '杠' in kind else 3), kind)
                (hidden if m.kind == '暗' else fixed).append(m)
            if not hidden:
                continue
            pair = rng.randrange(34)
            tiles = [t for m in hidden for t in m.tiles] + [pair, pair]
        full = tiles + [t for m in fixed for t in m.tiles]
        if max(Counter(full).values()) > 4:
            continue
        win = rng.choice(tiles)
        tiles.remove(win)
        closed = not any(m.opened for m in fixed)
        q = Question(tuple(sorted(tiles)), tuple(fixed), win, rng.choice((True, False)),
                     27 + rng.randrange(4), 27 + rng.randrange(2),
                     closed and rng.random() < 0.65, 0)
        initial = evaluate(q)
        if initial is None or initial.han > max(练习番数):
            continue
        targets = [h for h in 练习番数 if h >= initial.han]
        if not targets:
            continue
        q.dora = rng.choice(targets) - initial.han
        result = evaluate(q)
        if result and result.han in 练习番数 and result.fu <= 最大符数:
            return q, result
    raise ValueError('未能生成题目，请检查番数和符数配置。')


def show_question(q, number):
    fixed = ''.join('/' + fmt(m.tiles) + '（' + m.kind + '）' for m in q.fixed)
    print(f'\n第{number}题：{fmt(q.concealed)}{fixed}')
    print(f'场风：{WINDS[q.round_wind - 27]}；自风：{WINDS[q.seat - 27]}；'
          f'{"已立直" if q.riichi else "未立直"}。')
    print(f'和牌张：{fmt((q.win,))}，{"自摸" if q.tsumo else "荣和"}。')
    result = evaluate(q)
    print('符合的役：' + '、'.join(name for name, _ in result.yaku) + '。')
    print(f'宝牌：{q.dora}张。')


def parse_answer(value):
    match = re.fullmatch(r'\s*(\d+)(?:\s*番\s*|[\s,，/]+)(\d+)\s*符?\s*', value)
    if not match:
        raise ValueError('请输入“番 符”，例如：3 40，或3番40符。')
    return tuple(map(int, match.groups()))


def show_answer(q, r):
    print(f'正确答案：{r.han}番{r.fu}符。')
    terms = [f'{name}{han}番' for name, han in r.yaku]
    if q.dora:
        terms.append(f'宝牌{q.dora}番')
    print('番数：' + ' + '.join(terms) + f' = {r.han}番。')
    print('和牌拆解：' + r.groups)
    for step in r.steps:
        print('  ' + step)


def main():
    parser = argparse.ArgumentParser(description='随机生成1—4番、60符以内的符数计算题。')
    parser.add_argument('-n', '--count', type=int, help='题数，默认不限')
    parser.add_argument('--seed', type=int, help='随机种子，复现同一组题目')
    args = parser.parse_args()
    if args.count is not None and args.count < 1:
        parser.error('题数必须大于0')
    if not 练习番数 or any(type(h) is not int or not 1 <= h <= 4 for h in 练习番数):
        parser.error('练习番数须为1—4之间的整数')
    if not 20 <= 最大符数 <= 60:
        parser.error('最大符数须在20—60之间')
    rng = random.Random(args.seed)
    total = correct = 0
    print('四麻符数练习：1—4番，最终符数最多60符，连风雀头4符。')
    print('显示和牌前理好的手牌；斜杠后为固定面子，暗杠也在斜杠后注明。')
    print('和牌前合计13张加杠数；和牌张另列。m=万，p=筒，s=索，z=东南西北白发中。')
    print('均为普通巡目和牌，无一发、岭上、抢杠、海底等偶然役；有杠也不是刚开杠。')
    print('同一和牌有多种拆法时按实际得点最高者计分；题面役种采用该拆法。')
    print('输入“番 符”（如3 40），回车直接看答案，q退出。')
    try:
        while args.count is None or total < args.count:
            q, r = generate_question(rng)
            show_question(q, total + 1)
            while True:
                value = input('你的答案：').strip()
                if value.lower() in ('q', 'quit', 'exit', '退出'):
                    return
                if not value:
                    submitted = None
                    break
                try:
                    submitted = parse_answer(value)
                    break
                except ValueError as error:
                    print(error)
            total += 1
            if submitted == (r.han, r.fu):
                correct += 1
                print('答对了！')
            else:
                if submitted is not None:
                    print('答错了。')
                show_answer(q, r)
            if args.count is None or total < args.count:
                if input('\n回车下一题，q退出：').strip().lower() in ('q', 'quit', 'exit', '退出'):
                    return
    except (EOFError, KeyboardInterrupt):
        print()
    finally:
        print(f'练习结束：答对{correct}/{total}题（直接查看答案也计入题数）。')


if __name__ == '__main__':
    main()
