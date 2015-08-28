# ***************************************
# *     Author  Sadat Anwar 2015		*
# ***************************************

from __future__ import print_function
import os

project_folder = ""
try:
    project_folder = os.environ["BENCH_DEBUGGER"]
    # patch to make it work on my windows dev machine.
except KeyError:
    if "windows" in os.environ["OS"].lower():
        os.environ["BENCH_DEBUGGER"] = "C:" + os.sep + "Repo" + os.sep + "TestBench Project"
        project_folder = os.environ["BENCH_DEBUGGER"]

tempDirectory = os.path.join(project_folder,"temp")
assemblerDirectory = os.path.join(tempDirectory, 'assembler')
ext = ".p"
includePattern = "#include"
lineCount = 0
numberFormat = '{0:04d}'
headerFile = os.path.join(project_folder,"src", "headers_4W","header.hp")
footerFile = os.path.join(project_folder,"src", "headers_4W","footer.hp")
output_folder = os.path.join(tempDirectory, 'msp_out')
assembler_files = []

verbose = True

# ATP file signal sequence
TEST = 0
TCK = 1
TMS = 2
TDI = 3
TDO = 4
RST = 5

# lines in file
def file_len(fileName):
    with open(fileName) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


# Write the header to the file
def create_file_with_header(file_name):
    file_name = os.path.join(assemblerDirectory, file_name + ext)
    if os.path.isfile(file_name):
        if verbose:
            print("WARN:\t" + file_name + " already exists, will now be deleted.")
        os.remove(file_name)
    with open(file_name, "ab+") as out:
        out.writelines("#include \"" + headerFile + "\"\n")
        out.close()


# Write the footer to the file
def end_file_with_footer(file_name):
    file_name = os.path.join(assemblerDirectory, file_name + ext)
    # check if the file has any relevant lines
    if file_len(file_name) > 2:
        if verbose:
            print("LOG: \t" + file_name + " created.")
        with open(file_name, "ab+") as out:
            out.writelines("#include \"" + footerFile + "\"\n")
            out.close()
        assembler_files.append(file_name)
    else:
        if verbose:
            print("LOG: \t" + file_name + " is empty, will be deleted.")
        os.remove(file_name)


# Add lines to file
def add_line_to_file(file_name, line):
    file_name = os.path.join(assemblerDirectory, file_name + ext)
    with open(file_name, "ab+") as out:
        out.writelines(line)
        out.close()


def parse_atp_file(atp_file):
    if not os.path.exists(assemblerDirectory):
        os.makedirs(assemblerDirectory)
    if not os.path.isfile(atp_file):
        print("Provide valid ATP filename with complete path. Exiting")
        return
    macro = "Unknown"
    file_index = 0
    compare_pattern = ""
    create_file_with_header(numberFormat.format(file_index) + macro)
    # Read and parse the ATP file
    with open(atp_file) as f:
        lines = f.readlines()
    for x in range(0, len(lines)):
        line = lines[x]
        # Handle lines starting with "/" (Comments and #include statements)
        if line.startswith("/"):
            # if the line has an include message :
            if includePattern in line:
                line = line.replace(includePattern, "")
                macro_prev = macro
                # get the edt macro name ''.join(e for e in string if e.isalnum())
                macro = ''.join(e for e in line if e.isalnum()).replace("edt", "")
                # end the old file, add a footer include
                end_file_with_footer(numberFormat.format(file_index) + macro_prev)
                # increment the index counter
                file_index += 1
                # start new file with the header include
                create_file_with_header(numberFormat.format(file_index) + macro)
                continue
        if len(line) < 5:
            continue
        if ">" in line and ("FIX1US" in line or "JTAG" in line or "TCLK" in line):
            line = line.replace(" ", "")
            if line.startswith("repeat"):
                if "FIX1US" in line:
                    line = line.replace("repeat", "")
                    repeatLength = line.index(">")
                    repeat = line[:repeatLength]
                    line = line[repeatLength + 1:]
                    line = line[:line.index(";")]
                    bits = line[-6:]
                    bit_seq = bits[RST] + bits[TEST] + bits[TDI] + bits[TMS] + bits[TCK]
                    output_line = "FIX1US \t 0b000" + bit_seq + ", " + str(repeat) + "00\n"
                    # add the line to file
                    add_line_to_file(numberFormat.format(file_index) + macro, output_line)
                    continue
                else:
                    line = line.replace("repeat", "")
                    repeatLength = line.index(">")
                    repeat = line[:repeatLength]
                    line = line[repeatLength + 1:]
                    line = line[:line.index(";")]
                    bits = line[-6:]
                    signal = line[:-6]
                    if signal == "TCLK":
                        if bits[TDI] == "0":
                            signal = "TCLK_CLR_TDI"
                        else:
                            signal = "TCLK_SET_TDI"
                    for rep in range(0, int(repeat)):
                        bit_seq = bits[RST] + bits[TEST] + bits[TDI] + bits[TMS] + bits[TCK]
                        output_line = signal + " \t 0b000" + bit_seq + "\n"
                        # add the line to file
                        add_line_to_file(numberFormat.format(file_index) + macro, output_line)
                    continue
            else:
                comment = ""
                line = line.replace(">", "")
                line = line[:line.index(";")]
                bits = line[-6:]
                signal = line[:-6]
                if signal == "TCLK":
                    if bits[3] == "0":
                        signal = "TCLK_CLR_TDI"
                    else:
                        signal = "TCLK_SET_TDI"
                if signal == "haltJTAG":
                    signal = "JTAG_END   //"
                if signal == "ignJTAG":
                    continue
                if bits[TDO] == "H" or bits[TDO] == "L":
                    signal = "JTAG_IN"
                    comment = "// " + bits[TDO]
                    if bits[4] == "H":
                        compare_pattern += "1"
                    else:
                        compare_pattern += "0"
                bit_seq = bits[RST] + bits[TEST] + bits[TDI] + bits[TMS] + bits[TCK]
                output_line = signal + " \t 0b000" + bit_seq + "\t" + comment + "\n"
                # add the line to file
                add_line_to_file(numberFormat.format(file_index) + macro, output_line)

    # Add footer to last file
    end_file_with_footer(numberFormat.format(file_index) + macro)

    # Write the compare file
    length = len(compare_pattern)
    dWords = length / 32
    remainder = length % 32
    zeros = 32 - remainder
    output_file = os.path.join(output_folder, 'inputPattern.txt')
    if os.path.isfile(output_file):
        if verbose:
            print("WARN:\t" + output_file + " already exists, will now be deleted")
        os.remove(output_file)
    with open(output_file, "ab+") as out:
        for x in range(0, dWords):
            for y in range(0, 32):
                bit = y + (32 * x)
                out.writelines(compare_pattern[bit] + "\n")
        for x in range(0, zeros):
            out.writelines("0\n")
        for x in range(0, remainder):
            bit = x + (32 * dWords)
            out.writelines(compare_pattern[bit] + "\n")
    if verbose:
        print("LOG: \t" + output_file + " Created")
    return assembler_files
