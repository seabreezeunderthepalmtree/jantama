#!/usr/bin/env python3
"""点数记忆练习，仅使用 Python 标准库。

修改下面的配置后运行：python3 Scripts/点数记忆练习.py
限制题数：python3 Scripts/点数记忆练习.py -n 10
复现题目：python3 Scripts/点数记忆练习.py --seed 42
"""

import argparse
import random
import re

try:
    import readline
except ImportError:
    pass


# ===== 练习配置：True 开启，False 关闭 =====
包括亲家 = True
包括子家 = True
包括荣和 = True
包括自摸 = True
包括25符 = True
包括30符 = True
包括40符 = True
包括其他符 = False  # 20、50、60、70、80、90、100、110符
练习番数 = (1, 2, 3, 4)  # 可加入5至13番，练习满贯至累计役满
# =========================================


def round_up_100(points):
    return (points + 99) // 100 * 100


def score(dealer, tsumo, fu, han):
    """返回支付点数元组；子家自摸按（子，亲）排列。"""
    if han >= 13:
        basic = 8000
    elif han >= 11:
        basic = 6000
    elif han >= 8:
        basic = 4000
    elif han >= 6:
        basic = 3000
    elif han >= 5:
        basic = 2000
    else:
        basic = min(fu * 2 ** (han + 2), 2000)
    if not tsumo:
        return (round_up_100(basic * (6 if dealer else 4)),)
    if dealer:
        return (round_up_100(basic * 2),)
    return (round_up_100(basic), round_up_100(basic * 2))


def build_questions():
    fus = []
    for enabled, values in (
        (包括25符, (25,)),
        (包括30符, (30,)),
        (包括40符, (40,)),
        (包括其他符, (20, 50, 60, 70, 80, 90, 100, 110)),
    ):
        if enabled:
            fus.extend(values)
    if not 练习番数 or any(type(han) is not int or not 1 <= han <= 13 for han in 练习番数):
        raise ValueError("练习番数必须是1至13之间的整数，且至少选择一种番数。")
    questions = []
    for dealer, enabled in ((True, 包括亲家), (False, 包括子家)):
        if not enabled:
            continue
        for tsumo, enabled in ((False, 包括荣和), (True, 包括自摸)):
            if not enabled:
                continue
            for fu in fus:
                for han in sorted(set(练习番数)):
                    # 排除不成立的番符组合。
                    if fu == 20 and (not tsumo or han < 2):
                        continue  # 20符仅平和自摸，至少2番
                    if fu == 25 and han < (3 if tsumo else 2):
                        continue  # 七对子2番，自摸还要加1番
                    if fu == 110 and tsumo and han < 2:
                        continue
                    questions.append((dealer, tsumo, fu, han))
    if not questions:
        raise ValueError("当前配置没有可练习的题目，请开启身份、和牌方式和符数，并检查番数。")
    return questions


def parse_answer(value, expected_length):
    parts = re.split(r"[\s,，、/]+", value.strip())
    if len(parts) != expected_length or any(not re.fullmatch(r"[0-9]+", p) for p in parts):
        if expected_length == 2:
            raise ValueError("请输入两个整数，按子、亲排列，例如：1000 2000。")
        raise ValueError("请输入一个整数，例如：3900。亲家自摸只需输入每家支付的点数。")
    return tuple(int(p) for p in parts)


def format_answer(answer, dealer, tsumo):
    if not tsumo:
        return f"{answer[0]}点"
    if dealer:
        return f"{answer[0]}点（每家支付）"
    return f"{answer[0]} {answer[1]}（子 亲）"


def main():
    parser = argparse.ArgumentParser(description="随机练习日麻番符点数，配置在文件开头。")
    parser.add_argument("-n", "--count", type=int, help="题数，默认不限")
    parser.add_argument("--seed", type=int, help="随机种子")
    args = parser.parse_args()
    if args.count is not None and args.count < 1:
        parser.error("题数必须大于0")
    try:
        questions = build_questions()
    except ValueError as error:
        parser.error(str(error))
    rng = random.Random(args.seed)
    deck = []
    total = correct = 0
    print("四人麻将点数练习，不计本场、立直棒，不采用切上满贯。")
    print("荣和：输入总点数。子家自摸：按‘子 亲’输入，例如1000 2000。")
    print("亲家自摸：输入每家支付的点数，例如2000。输入q退出。\n")
    try:
        while args.count is None or total < args.count:
            if not deck:
                deck = questions.copy()
                rng.shuffle(deck)
            dealer, tsumo, fu, han = deck.pop()
            answer = score(dealer, tsumo, fu, han)
            print(f"第{total + 1}题：{'亲家' if dealer else '子家'}，"
                  f"{han}番{fu}符，{'自摸' if tsumo else '荣和'}")
            while True:
                value = input("你的答案：").strip()
                if value.lower() in ("q", "quit", "exit", "退出"):
                    return
                try:
                    submitted = parse_answer(value, len(answer))
                except ValueError as error:
                    print(error)
                    continue
                break
            total += 1
            if submitted == answer:
                correct += 1
                print("答对了！\n")
            else:
                print(f"答错了，正确答案：{format_answer(answer, dealer, tsumo)}\n")
    except (EOFError, KeyboardInterrupt):
        print()
    finally:
        print(f"练习结束：答对{correct}/{total}题。")


if __name__ == "__main__":
    main()
