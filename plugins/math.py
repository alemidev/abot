import asyncio
import traceback

from pyrogram import filters

from bot import alemiBot

from util import set_offline, batchify
from util.globals import PREFIX
from util.permission import is_allowed
from util.message import edit_or_reply

import sympy
from sympy.solvers import solve
from sympy.plotting import plot3d, plot3d_parametric_line
from sympy.parsing.sympy_parser import parse_expr

# Print LaTeX formatted expression from either sympy or latex
@alemiBot.on_message(is_allowed & filters.command(["expr", "math"], prefixes=".") & filters.regex(
    pattern=r"^.(?:expr|math)(?: |)(?P<opt>-latex|)(?: |)(?P<query>.*)"
))
async def expr(_, message):
    try:
        arg = message.matches[0]["query"]
        opt = message.matches[0]["opt"]
        print(f" [ mathifying {arg} ]")
        if opt == "-latex":
            preview(arg, viewer='file', filename='expr.png', dvioptions=["-T", "bbox", "-D 300", "--truecolor", "-bg", "Transparent"])
        else:
            res = parse_expr(arg)
            preview(res, viewer='file', filename='expr.png', dvioptions=["-T", "bbox", "-D 300", "--truecolor", "-bg", "Transparent"])
        await client.send_photo(message.chat.id, "expr.png", reply_to_message_id=message.message_id,
                                        caption=f"` → {arg} `")
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))

# Plot a matplotlib graph
@alemiBot.on_message(is_allowed & filters.command(["plot", "graph"], prefixes=".") & filters.regex(
    pattern=r"^.(?:plot|graph)(?: |)(?P<opt>-3d|-par|)(?: |)(?P<query>.*)"
))
async def graph(_, message):
    try:
        arg = message.matches[0]["query"]
        opt = message.matches[0]["opt"]
        print(f" [ plotting {arg} ]")
        eq = []
        for a in arg.split(", "):
            eq.append(parse_expr(a))
        if opt == "-3d":
            plot3d(*eq, show=False).save("graph.png")
        # elif opt == "-par":
        #     plot3d_parametric_line(res, show=False).save("graph.png")
        else:
            plot(*eq, show=False).save("graph.png")
        await client.send_photo(message.chat.id, "graph.png", reply_to_message_id=message.message_id,
                                        caption=f"` → {arg} `")
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))

# Solve equation
@alemiBot.on_message(is_allowed & filters.command("solve", prefixes=".") & filters.regex(
    pattern=r"^.solve(?: |)(?P<query>.*)"
))
async def solve_cmd(event):
    try:
        arg = message.matches[0]["query"]
        print(f" [ mathifying {arg} ]")
        in_expr = parse_expr(arg).simplify()
        res = solve(in_expr)
        out = f"` → {str(in_expr)}`\n```" + str(res) + "```"
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))

# class MathModules:
#     def __init__(self, client):
#         self.helptext = "`━━┫ MATH`\n"
# 
#         client.add_event_handler(expr)
#         self.helptext += "`→ .expr [-latex] <expr> ` print math expr formatted *\n"
# 
#         client.add_event_handler(graph)
#         self.helptext += "`→ .plot [-3d] <expr> ` print graph of expression *\n"
# 
#         client.add_event_handler(solve_cmd)
#         self.helptext += "`→ .solve <expr> ` find roots of algebric equation *\n"
# 
#         print(" [ Registered Math Modules ]")

