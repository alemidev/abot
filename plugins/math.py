import asyncio
import traceback

from pyrogram import filters

from bot import alemiBot

from util import batchify
from util.globals import PREFIX
from util.permission import is_allowed
from util.message import edit_or_reply

import sympy
from sympy.solvers import solve
from sympy.plotting import plot3d, plot3d_parametric_line
from sympy.parsing.sympy_parser import parse_expr
from sympy import preview, plot
from plugins.help import HelpCategory

HELP = HelpCategory("MATH")

HELP.add_help(["expr", "math"], "convert to LaTeX formula",
                "this command accepts sympy syntax and will spit out a LaTeX formula as image. " +
                "You can add the `-latex` argument and pass LaTeX directly.", args="[-latex] <expr>", public=True)
@alemiBot.on_message(is_allowed & filters.command(["expr", "math"], list(alemiBot.prefixes)) & filters.regex(
    pattern=r"^.(?:expr|math)(?: |)(?P<opt>-latex|)(?: |)(?P<query>.*)"
))
async def expr(client, message):
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

HELP.add_help(["plot", "graph"], "plot provided function",
                "this command will run sympy `plot` and return result as image. Foruma passing is wonky. " +
                "You can add the `-3d` argument to plot in 3d.", args="[-3d] <expr>", public=True)
@alemiBot.on_message(is_allowed & filters.command(["plot", "graph"], list(alemiBot.prefixes)) & filters.regex(
    pattern=r"^.(?:plot|graph)(?: |)(?P<opt>-3d|-par|)(?: |)(?P<query>.*)"
))
async def graph(client, message):
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

HELP.add_help("solve", "attempt to solve equation",
                "this command will run sympy `solve` and attempt to find roots of the " +
                "equation. You can pass systems too!", args="<expr>", public=True)
@alemiBot.on_message(is_allowed & filters.command("solve", list(alemiBot.prefixes)) & filters.regex(
    pattern=r"^.solve(?: |)(?P<query>.*)"
))
async def solve_cmd(_, message):
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
