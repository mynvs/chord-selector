import subprocess
from settings import *

CHARACTERS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
CHAR_TO_VALUE = {char: index for index, char in enumerate(CHARACTERS)}

def int_to_base62(num):
    if num == 0:
        return CHARACTERS[0]
    result = ''
    while num:
        result = CHARACTERS[num % 62] + result
        num //= 62
    return result

def smallest_rotation(s):  # booth's algorithm
    s = s + s
    n = len(s) // 2
    f = [-1] * len(s)
    k = 0
    for j in range(1, len(s)):
        i = f[j - k - 1]
        while i != -1 and s[j] != s[k + i + 1]:
            if s[j] < s[k + i + 1]:
                k = j - i - 1
            i = f[i]
        if i == -1 and s[j] != s[k + i + 1]:
            if s[j] < s[k + i + 1]:
                k = j
            f[j - k] = -1
        else:
            f[j - k] = i + 1
    rotation_count = (n-k) % n
    return s[k:k + n], CHARACTERS[rotation_count]

def read_binary_strings(binary_filename, n, density):
    with open(binary_filename, 'rb') as f:
        data = f.read()
    binary_strings = []
    bits_read = 0
    current_value = 0
    mask = (1 << n) - 1
    for byte in data:
        current_value = (current_value << 8) | byte
        bits_read += 8
        while bits_read >= n:
            bits_read -= n
            binary_strings.append(format((current_value >> bits_read) & mask, f'0{n}b'))
    if density != 0:
        while binary_strings and all(bit == '0' for bit in binary_strings[-1]):
            binary_strings.pop()
    else:
        while len(binary_strings) > 1 and all(bit == '0' for bit in binary_strings[-1]):
            binary_strings.pop()
    return binary_strings

def run_necklaces_exe(type, edo, density=None, forbidden_sequence=None):
    command = ['./necklaces.exe', str(type), str(edo)]
    if type == 2 and density is not None:
        command.append(str(density))
    elif type == 3 and forbidden_sequence is not None:
        command.append(forbidden_sequence)
    subprocess.run(command)

def unique_binaries(edo, chord_sizes=None):
    if isinstance(chord_sizes, int):
        chord_sizes = [chord_sizes]
    result = set()
    if chord_sizes is None:
        run_necklaces_exe(1, edo)
        binary_strings = read_binary_strings('binaries.bin', edo, 0)
        result.update(binary_strings)
    else:
        for size in chord_sizes:
            run_necklaces_exe(2, edo, size)
            binary_strings = read_binary_strings('binaries.bin', edo, size)
            result.update(binary_strings)
    return sorted(result, key=lambda x: int(x, 2))

def binary_to_positions(binary):
    return ''.join([CHARACTERS[11-i] for i, bit in enumerate(binary) if bit == '1'])

def binary_to_gap_lengths(binary, simplify=False):
    gaps = []
    gap_count = 0 if simplify else 1
    binary += binary[0]
    for bit in binary:
        if bit == '0':
            gap_count += 1
        else:
            gaps.append(gap_count)
            gap_count = 0 if simplify else 1

    if binary[0] != '0':
        gaps = gaps[1:]
    return ''.join(CHARACTERS[gap] for gap in gaps)

def generate_interval_variations(binary, step_size, do_both_directions=False):
    length = len(binary)
    variations = set()
    one_positions = [i for i, bit in enumerate(binary) if bit == '1']
    if type(step_size) == int:
        step_size = [step_size]
    for step in step_size:
        for pos in one_positions:
            new_binary = list(binary)
            new_binary[pos] = '0'
            new_pos = (pos + step) % length
            if new_binary[new_pos] == '0':
                new_binary[new_pos] = '1'
                new_binary_str = ''.join(new_binary)
                variations.add(new_binary_str)
            if do_both_directions:
                new_binary = list(binary)
                new_binary[pos] = '0'
                new_pos = (pos - step) % length
                if new_binary[new_pos] == '0':
                    new_binary[new_pos] = '1'
                    new_binary_str = ''.join(new_binary)
                    variations.add(new_binary_str)
    return sorted(variations)

def all_rotations(input_data):
    list_of_chords = []
    if isinstance(input_data, str):
        rotations = [input_data[i:] + input_data[:i] for i in range(len(input_data))]
        list_of_chords.extend(rotations)
    elif isinstance(input_data, list):
        for binary in input_data:
            rotations = [binary[i:] + binary[:i] for i in range(len(binary))]
            list_of_chords.extend(rotations)
    else:
        raise ValueError("input must be a string or a list of strings")
    return list_of_chords

def generate_symbols(list_of_chords, reduce_relative=False, truncate_relative=False, absolute_smallest=False, style='actual'):
    list_of_chords = sorted(list_of_chords, key=lambda x: int(x, 2))
    output_list = []
    for i in list_of_chords:
        if style == 'relative':
            binary, key = smallest_rotation(i)
            gaps = binary_to_gap_lengths(binary, reduce_relative)
            relative = (gaps[::-1][:-1] if truncate_relative else gaps[::-1]) + '.'+key
            output_list.append(relative)
        elif style == 'absolute':
            if absolute_smallest:
                binary, key = smallest_rotation(i)
                positions = binary_to_positions(binary)
                absolute = positions[::-1] + '.'+key
            else:
                positions = binary_to_positions(i)
                absolute = positions[::-1]
            output_list.append(absolute)
        elif style == 'actual':
            if absolute_smallest:
                binary, key = smallest_rotation(i)
                smallest = binary[::-1] + '.'+key
                output_list.append(smallest)
            else:
                actual = i[::-1]
                output_list.append(actual)

    return output_list

def add_all_rotations_to_set(set):
    for i in [all_rotations(e) for e in set]:
        if isinstance(i, list):
            for e in i:
                set.add(e)
        else:
            set.add(i)

def add_all_interval_variations_to_set(input_set, intervals, both_directions=False):
    if intervals == None:
        return input_set
    elif intervals == []:
        return input_set
    new_set = set()
    for i in [generate_interval_variations(e, intervals, both_directions) for e in input_set]:
        if isinstance(i, list):
            for e in i:
                new_set.add(e)
        else:
            new_set.add(i)
    return new_set

def filter_chords(set_of_chords, anti_set_of_chords, MODE = True, ALL=False):
    if MODE:
        def is_subset(subset, superset):
            return (int(subset, 2) & int(superset, 2)) == int(superset, 2)
        filtered_chords = set()
        for chord in set_of_chords:
            A = [is_subset(anti_chord, chord) for anti_chord in anti_set_of_chords]
            if (all(A) if ALL else any(A)):
                filtered_chords.add(chord)    
        return filtered_chords
    else:
        def is_subset(subset, superset):
            return (int(subset, 2) | int(superset, 2)) == int(superset, 2)
        filtered_chords = set()
        for chord in set_of_chords:
            A = [is_subset(anti_chord, chord) for anti_chord in anti_set_of_chords]
            if (all(A) if ALL else not any(A)):
                filtered_chords.add(chord)
        return filtered_chords

def rotate_by_step(binary_set, step_size):
    rotated_set = set()
    for binary in binary_set:
        effective_step = step_size % len(binary)
        rotated = binary[effective_step:] + binary[:effective_step]
        rotated_set.add(rotated)
    return rotated_set

def prepare_set_of_chords(set_of_chords, edo, all_unique_binaries, specific_chords, rotations, interval_variations):
    set_of_chords.update(unique_binaries(edo, all_unique_binaries))
    for size, index in specific_chords:
        set_of_chords.add(unique_binaries(edo, size)[index])
    if isinstance(rotations, int):
        if rotations == 0:
            pass
        set_of_chords = rotate_by_step(set_of_chords, rotations)
    elif rotations == [0]:
        pass
    elif rotations == []:
        set_of_chords = set()
    elif len(rotations) == 1:
        set_of_chords = rotate_by_step(set_of_chords, rotations[0])
    elif rotations == None:
        add_all_rotations_to_set(set_of_chords)
    elif rotations:
        set_of_chords2 = set()
        for i in rotations:
            set_of_chords2.update(rotate_by_step(set_of_chords, i))
        set_of_chords = set_of_chords2
    set_of_chords = add_all_interval_variations_to_set(set_of_chords, interval_variations, True)

    return(set_of_chords)

def calculate_chord_counts(edo):
    chord_counts = {}
    for size in range(1, edo + 1):
        chord_counts[size] = len(unique_binaries(edo, size))
    return chord_counts

def main():
    set_of_chords = set()
    set_of_chords = prepare_set_of_chords(set_of_chords, EDO, ALL_UNIQUE_BINARIES1, SPECIFIC_CHORDS1, ROTATIONS1, INTERVAL_VARIATIONS1)

    anti_set_of_chords = set()
    anti_set_of_chords = prepare_set_of_chords(anti_set_of_chords, EDO, ALL_UNIQUE_BINARIES2, SPECIFIC_CHORDS2, ROTATIONS2, INTERVAL_VARIATIONS2)

    if anti_set_of_chords != set():
        if FILTER_INVERTED:
            A = set_of_chords
            B = filter_chords(set_of_chords, anti_set_of_chords, FILTER_GATE_AND, FILTER_ALL)
            if FILTER_GATE_AND:
                final_set_of_chords = A - B
            else:
                final_set_of_chords = A if A == B else A - B

        else:
            final_set_of_chords = filter_chords(set_of_chords, anti_set_of_chords, FILTER_GATE_AND, FILTER_ALL)
    else:
        final_set_of_chords = set_of_chords

    if REDUCE_FINAL_SET:
        final_chords = set()
        for i in final_set_of_chords:
            binary, _ = smallest_rotation(i)
            final_chords.add(binary)
    else:
        final_chords = final_set_of_chords

    try:
        symbols = generate_symbols(final_chords, style='actual')
        with open("symbols.py", "w") as f:
            f.write(f"SYMBOLS = {symbols}\n")
    except:
        print('None')
        # with open("symbols.py", "w") as f:
        #     f.write(f"SYMBOLS = None\n")

if __name__ == '__main__':
    main()

r'''
TODO:
chord transformations
multiinterval transformations
rotate all transformations to all keys
filter chord transformations
  
turn the sorting into a function

sorting method based on number of ones instead of binary value
sorting method based on gray code
sorting method based on converting to fifths representation first
sorting method based on converting to fifths representation first, then gray code
sorting method based on shape in binary value, but rotations immediately following others of the same shape.

'''


r'''

make EDO selector slidable


drag and drop chords into include and filter buckets


display count of how many binaries are in the list

add row on top of binary display to show note names


clicking should toggle the rows, not releasing the click.

make selecting high edos not lag and generate all lists of lists
very important to cache the lists of lists **

store the boolean states for each unique binaries in the program while its running instead of updating a file every time.
only update the file when clicking "generate"

add a reset to default button
add presets for learning and becoming acclimatized to the program


ability to use vertical dragging to invert the state of a swath of binaries at a time in the binary display region 

attempt to refactor based on intended purpose, consolidating things that work together often, without making any compromises.


convert settings to C array, do math on C array, convert back to numpy array. as a temporary bridge until the ui is in C.

display edo in integer form
make edo selector have multiple rows

better telling apart when the display is controllable vs not controllable and 
better control for when display is controllable

display chord transformations in the binary display region somehow.

the pyagme window's horizontal position should always move leftward exactly countering the window width adjustment moving the window's right edge to the right, so that instead,
after the edo display is clicked it stays exactly in the same position relative to the mouse along with the rest of the right half of the app, and the left region binary display
appears to expand out to the left.  

auto click the "generate" button after certain actions

add buttons for the remaining boolean static variables


button that sets all toggle row states to be either all false or all true.

binaries get played as sine waves when clicked

ability to go beyond neckalces and do all voices


make base62 labels for the binary number column, or have the selectors line up vertically with the binary display.



put the NOT rows directly below their corresponding upper rows, eliminating the need for doubled labels.

ability to see which binaries got reduced to the smallest rotation, as well as show a count next to the reduced ones.


Instead of throwing the error below, make the code work for 1 edo and 0 edo.
for 1 edo:
   - delete the "interval varitions", and "NOT interval variations" rows
for 0 edo:
   - delete the interval variations rows as well just like for 1 edo
   - also delete the "rotations" or "NOT rotations" rows, now.:

Traceback (most recent call last):
  File "C:\Users\15082\Desktop\portfolio\music theory\new mtheory\new_musicthery\edo_graphs2\src\chord_size_selector.py", line 489, in <module>
    ChordSizeSelector().run()
  File "C:\Users\15082\Desktop\portfolio\music theory\new mtheory\new_musicthery\edo_graphs2\src\chord_size_selector.py", line 485, in run
    while self.handle_events():
          ^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\15082\Desktop\portfolio\music theory\new mtheory\new_musicthery\edo_graphs2\src\chord_size_selector.py", line 335, in handle_events
    self.update_layout()
  File "C:\Users\15082\Desktop\portfolio\music theory\new mtheory\new_musicthery\edo_graphs2\src\chord_size_selector.py", line 469, in update_layout
    self.create_regions()
  File "C:\Users\15082\Desktop\portfolio\music theory\new mtheory\new_musicthery\edo_graphs2\src\chord_size_selector.py", line 118, in create_regions
    region = self.create_region(adjusted_x, y, adjusted_width, self.region_height, label, i in [1, 4], i in [2, 5])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\15082\Desktop\portfolio\music theory\new mtheory\new_musicthery\edo_graphs2\src\chord_size_selector.py", line 130, in create_region
    button_width = width // len(button_labels)
                   ~~~~~~^^~~~~~~~~~~~~~~~~~~~
ZeroDivisionError: integer division or modulo by zero

'''



# def print_symbols(list_of_chords, reduce_relative=False, truncate_relative=False, absolute_smallest=True):
#     list_of_chords = sorted(list_of_chords, key=lambda x: int(x, 2))
#     A = len(list_of_chords[0])+2, 14
#     s = [' '*len(str(len(list_of_chords))), ' '*(A[0]-len('actual')),' '*(A[0]-len('smallest')),' '*(A[1]-len('absol')),' '*(A[1]-len('rel'))]
#     print(f'i{s[0]}actual{s[1]}smallest{s[2]}absol{s[3]}rel')
#     for e, i in enumerate(list_of_chords):
#         # e += 1
#         binary, key = smallest_rotation(i)
#         if absolute_smallest:
#             positions = binary_to_positions(binary)
#             absolute = positions[::-1] + '.'+key
#         else:
#             positions = binary_to_positions(i)
#             absolute = positions[::-1]
#         gaps = binary_to_gap_lengths(binary, reduce_relative)

#         actual = i[::-1]
#         smallest = binary[::-1]
        
#         realtive = (gaps[::-1][:-1] if truncate_relative else gaps[::-1]) + '.'+key
#         key = key

#         s = [' '*(len(str(len(list_of_chords)))-len(str(e))),' '*(A[0]-len(actual)),' '*(A[0]-len(smallest)),' '*(A[1]-len(absolute)),' '*(A[1]-len(realtive))]
#         print(f"{e} {s[0]}{actual}{s[1]}{smallest}{s[2]}{absolute}{s[3]}{realtive}{s[4]}")





    # # REDUCE_RELATIVE = False
    # # TRUNCATE_RELATIVE = False
    # # ABSOLUTE_SMALLEST = False

    # # try:
    # #     print('include')
    # #     print_symbols(set_of_chords,
    # #                 reduce_relative=REDUCE_RELATIVE,
    # #                 truncate_relative=TRUNCATE_RELATIVE,
    # #                 absolute_smallest=ABSOLUTE_SMALLEST)
    # # except:
    # #     print('\tNone')
    # # try:
    # #     print('exclude')
    # #     print_symbols(anti_set_of_chords,
    # #                 reduce_relative=REDUCE_RELATIVE,
    # #                 truncate_relative=TRUNCATE_RELATIVE,
    # #                 absolute_smallest=ABSOLUTE_SMALLEST)
    # # except:
    # #     print('\tNone')
    # try:
    #     # print('final')
    #     # print_symbols(final_set_of_chords,
    #     #             reduce_relative=REDUCE_RELATIVE,
    #     #             truncate_relative=TRUNCATE_RELATIVE,
    #     #             absolute_smallest=ABSOLUTE_SMALLEST)
    #     # print()
    #     symbols = generate_symbols(final_chords, style='actual')
    #     with open("symbols.py", "w") as f:
    #         f.write(f"SYMBOLS = {symbols}\n")
    # except:
    #     print('None')