import re
import argparse
import os

alpha = "abcdefghijklmnopqrstuvwxyz"
ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Argparse
parser = argparse.ArgumentParser(description='Convert script file to .cs')
parser.add_argument('input', type=str)
args = parser.parse_args()

file_name, ext = os.path.splitext(args.input)
output = [
    "using System;",
    "using WvsBeta.Game;",
    "using WvsBeta.Game.Scripting;",
    "",
    "namespace WvsBeta.Scripts.Scripts",
    "{",
    "    public class " + file_name,
    "    {",
    "    }"
]
with open(args.input) as f:
    lines = f.read().splitlines()
    nLine=0
    script_name = None
    vars = set()
    var_idx = 0
    func_name = None
    func_idx = 0
    func_vars = set()
    for line in lines:
        line = line.replace("\t", "    ")
        line = line.replace("registerTransferField", "target.ChangeMap")
        line = line.replace(" = random(", " = Rand32.NextBetween(")
        line = line.replace(".n", ".")
        line = line.replace(" = currentTime;", " = MasterThread.CurrentDate;")
        line = line.replace("integer( substring( cTime, 13, 1 ) )", "cTime.Minute")
        line = line.replace("end;", "return;")
        if re.match(r'\s+(else )?if\s+\(.*( and | or ).*\)\s+\{?', line):
            line = line.replace(" or ", " || ").replace(" and ", " && ")
        # if (target.Level > 29 and target.Level < 40 ) {
        for idx, x in enumerate(alpha):
            a = alpha[idx]
            A = ALPHA[idx]
            line = line.replace("." + a, "." + A)
        fcall_m = re.search(r'\s+(?!return)([a-z][a-z\d_]+);', line)
        if fcall_m is not None: # Func call
            fname = fcall_m.group(1)
            print('Call ' + fname)
            line = line.replace(fname, file_name + "." + fname + "(self, target)")
        if re.match(r'\}\s*', line):
            if script_name is not None: # Close script
                output.insert(var_idx, "        dynamic " + ", ".join(vars) + ";") # Insert vars
                print("Close " + script_name)
                vars.clear()
                script_name = None
                output.append("        }")
                output.append("    }")
            elif func_name is not None: # Close func
                print("Close func ", func_name)
                output.insert(8 + func_idx, "        }")
                func_idx = 0
                func_name = None
        if script_name is not None or func_name is not None:
            var_m = re.search(r'\s+([a-zA-Z\d]+) = ', line)
            if var_m is not None: # Var init
                var_name = var_m.group(1)
                if (var_name in vars) == False:
                    vars.add(var_name)
                    if func_name is not None: func_vars.add(var_name)
                    print(var_name)
            if script_name is not None:
                output.append("        " + line)
            else:
                output.insert(8 + func_idx, "        " + line)
                func_idx += 1
        func_m = re.match(r'function(\([a-z,]+\))?\s+([A-Za-z_\d]+)(\([a-z, ]+\))?\s*\{?', line)
        if func_m is not None: # Open func
            func_idx = 1
            func_name = func_m.group(2)
            print("Open func ", func_name)
            output.insert(8, "        public static void " + func_name + "(INpcHost self, GameCharacter target)\n        {")
        cmt_m = re.match(r'^\/\/.+', line) # Script comment
        if cmt_m is not None:
            scr_cmt = cmt_m.group(0)
            cmt_line = nLine
        scr_m = re.match(r'script "([a-z_\d]+)"', line)
        if scr_m: # Open script
            script_name = scr_m.group(1)
            print("\r\nOpen " + script_name + "")
            if cmt_line == nLine - 1:
                output.append("    " + scr_cmt)
            output.append("    [Script(\"" + script_name + "\")]")
            output.append("    class " + script_name + " : INpcScript\n    {")
            var_idx = len(output)
            output.append("        public void Run(INpcHost self, GameCharacter target)\n        {")
        nLine+=1
    output.insert(8, "        static dynamic " + ", ".join(func_vars) + ";") # Insert func vars

output.append("}")
output_s = "\n".join(output)
# print(output_s)

file_name_out = file_name + ".cs"
f_out = open(file_name_out, "w")
f_out.write(output_s)
f_out.close()

print("Output saved to " + file_name_out)