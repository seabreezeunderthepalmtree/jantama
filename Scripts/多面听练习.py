#!/usr/bin/env python3
"""随机生成7张形的多面听练习，仅使用 Python 标准库。

运行：python3 多面听练习.py
限制题数：python3 多面听练习.py -n 10
复现：python3 多面听练习.py --seed 42
"""

import argparse
from functools import lru_cache
import random
import re

# 导入后，终端中的 input() 支持方向键移动、删除和历史记录。
try:
    import readline
except ImportError:
    pass


SHAPES = (
    "1234567", "4566789", "3334556", "7888899", "1112234",
    "2223456", "2233344", "2233444", "23444m11z",
    "3334555", "3335777", "2333456", "6777888",
) # 你记住的形状就可以删除了
SUITS = "mpsz"


def format_tiles(tiles):
    """将牌的编号转换为如 23444p11z 的简写。"""
    parts = []
    for suit_index, suit in enumerate(SUITS):
        digits = "".join(
            str(tile % 9 + 1)
            for tile in sorted(tiles)
            if tile // 9 == suit_index
        )
        if digits:
            parts.append(digits + suit)
    return "".join(parts)


def transform(shape, rng):
    # 字牌对子保留原样，只对数牌做镜像、平移和换花色。
    mixed = shape == "23444m11z"
    digits = [int(n) for n in ("23444" if mixed else shape)]
    if rng.choice((False, True)):
        digits = [10 - n for n in digits]
    shift = rng.randint(1 - min(digits), 9 - max(digits))
    suit_offset = rng.randrange(3) * 9
    tiles = [suit_offset + n + shift - 1 for n in digits]
    if mixed:
        tiles.extend((27, 27))  # 11z，即东风对子。
    return tuple(sorted(tiles))


@lru_cache(maxsize=None)
def all_melds(counts):
    """判断剩余牌能否全部拆成刻子或顺子。"""
    first = next((i for i, count in enumerate(counts) if count), None)
    if first is None:
        return True
    rest = list(counts)
    if rest[first] >= 3:
        rest[first] -= 3
        if all_melds(tuple(rest)):
            return True
        rest[first] += 3
    if (
        first < 27 and first % 9 <= 6
        and rest[first + 1] and rest[first + 2]
    ):
        for tile in (first, first + 1, first + 2):
            rest[tile] -= 1
        if all_melds(tuple(rest)):
            return True
    return False


def winning_shape(counts):
    for pair, count in enumerate(counts):
        if count >= 2:
            rest = list(counts)
            rest[pair] -= 2
            if all_melds(tuple(rest)):
                return True
    return False


def find_waits(tiles):
    counts = [0] * 34
    for tile in tiles:
        counts[tile] += 1
    waits = []
    for tile in range(34):
        if counts[tile] == 4:
            continue
        counts[tile] += 1
        if winning_shape(counts):
            waits.append(tile)
        counts[tile] -= 1
    return waits


def generate_question(rng):
    tiles = transform(rng.choice(SHAPES), rng)
    return format_tiles(tiles), format_tiles(find_waits(tiles))


def parse_answer(value, hand):
    value = re.sub(r"[\s,，、/]+", "", value.lower())
    if re.fullmatch(r"[1-9]+", value):
        suits = set(re.findall(r"[mpsz]", hand))
        if len(suits) != 1:
            raise ValueError("这题有不同花色，请写明花色，例如14m1z。")
        value += next(iter(suits))
    if not re.fullmatch(r"(?:[1-9]+[mpsz])+", value):
        raise ValueError("请输入待牌，例如147m；单一花色的题也可以只输入147。")
    tiles = set()
    for digits, suit in re.findall(r"([1-9]+)([mpsz])", value):
        if suit == "z" and any(int(n) > 7 for n in digits):
            raise ValueError("字牌只能使用1z至7z。")
        tiles.update(SUITS.index(suit) * 9 + int(n) - 1 for n in digits)
    return tiles


def read_input(prompt):
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\n练习结束。")
        return None


def main():
    parser = argparse.ArgumentParser(description="7张形多面听：随机镜像、平移、换花色。")
    parser.add_argument("-n", "--count", type=int, help="最多练习的题数，默认不限")
    parser.add_argument("--seed", type=int, help="随机种子，用于复现同一组题目")
    args = parser.parse_args()
    if args.count is not None and args.count < 1:
        parser.error("题数必须大于0")

    rng = random.Random(args.seed)
    print("假设另外两个面子已完成，且不与这7张牌重叠。请找出全部待牌。")
    print("只判断普通和牌结构，不考虑役、振听或场上已见牌。m=万，p=筒，s=索，z=字牌。\n")
    print("输入答案后才会公布结果；输入q退出。")
    index = 1
    while args.count is None or index <= args.count:
        hand, answer = generate_question(rng)
        print(f"第{index}题：{hand}，听什么？")
        while True:
            value = read_input("你的答案：")
            if value is None or value.lower() in ("q", "quit", "exit", "退出"):
                return
            try:
                submitted = parse_answer(value, hand)
            except ValueError as error:
                print(error)
                continue
            if submitted == parse_answer(answer, hand):
                print("答对了！")
            else:
                print(f"答错了，正确答案是：{answer}")
            break
        if args.count is not None and index == args.count:
            print("本轮练习完成。")
            return
        while True:
            choice = read_input("要不要下一道？[y/n]：")
            if choice is None or choice.lower() in ("n", "no", "q", "退出", "否", "不要"):
                return
            if choice.lower() in ("y", "yes", "是", "要", "好", "继续"):
                break
            print("请输入y继续，或n结束。")
        index += 1
        print()


if __name__ == "__main__":
    main()
