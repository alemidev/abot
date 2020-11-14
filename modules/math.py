import asyncio
import traceback

from telethon import events

from util import can_react, set_offline, batchify
from util.globals import PREFIX

from sympy import *
from sympy.solvers import solve
from sympy.plotting import plot3d, plot3d_parametric_line
from sympy.parsing.sympy_parser import parse_expr

# Print LaTeX formatted expression from either sympy or latex
@events.register(events.NewMessage(pattern=r"{p}(?:expr|math)(?: |)(?P<opt>-latex|)(?: |)(?P<query>.*)".format(p=PREFIX)))
async def expr(event):
    if not can_react(event.chat_id):
        return
    try:
        arg = event.pattern_match.group("query")
        opt = event.pattern_match.group("opt")
        print(f" [ mathifying {arg} ]")
        if opt == "-latex":
            preview(arg, viewer='file', filename='expr.png', dvioptions=["-T", "bbox", "-D 300", "--truecolor", "-bg", "Transparent"])
        else:
            res = parse_expr(arg)
            preview(res, viewer='file', filename='expr.png', dvioptions=["-T", "bbox", "-D 300", "--truecolor", "-bg", "Transparent"])
        await event.message.reply("` → `", file="expr.png")
    except Exception as e:
        traceback.print_exc()
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Plot a matplotlib graph
@events.register(events.NewMessage(pattern=r"{p}(?:plot|graph)(?: |)(?P<opt>-3d|-par|)(?: |)(?P<query>.*)".format(p=PREFIX)))
async def graph(event):
    if not can_react(event.chat_id):
        return
    try:
        arg = event.pattern_match.group("query")
        opt = event.pattern_match.group("opt")
        print(f" [ plotting {arg} ]")
        res = parse_expr(arg)
        if opt == "-3d":
            plot3d(res, show=False).save("graph.png")
        # elif opt == "-par":
        #     plot3d_parametric_line(res, show=False).save("graph.png")
        else:
            plot(res, show=False).save("graph.png")
        await event.message.reply("` → `", file="graph.png")
    except Exception as e:
        traceback.print_exc()
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Solve equation
@events.register(events.NewMessage(pattern=r"{p}solve(?: |)(?P<query>.*)".format(p=PREFIX)))
async def solve_cmd(event):
    if not can_react(event.chat_id):
        return
    try:
        arg = event.pattern_match.group("query")
        print(f" [ mathifying {arg} ]")
        in_expr = parse_expr(arg)
        res = solve(in_expr)
        out = f"` → ` {res}"
        for m in batchify(out, 4090):
            await event.message.reply(m)
    except Exception as e:
        traceback.print_exc()
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)


class MathModules:
    def __init__(self, client):
        self.helptext = "`━━┫ MATH`\n"

        client.add_event_handler(expr)
        self.helptext += "`→ .expr [-latex] <expr> ` print math expr formatted\n"

        client.add_event_handler(graph)
        self.helptext += "`→ .plot [-3d] <expr> ` print graph of expression\n"

        client.add_event_handler(solve_cmd)
        self.helptext += "`→ .solve <expr> ` find roots of algebric equation\n"

        print(" [ Registered Math Modules ]")
