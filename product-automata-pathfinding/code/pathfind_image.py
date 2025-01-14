import numpy as np
import cv2
import matplotlib.pyplot as plt
import math
import bisect
# import spot
# from cairosvg import svg2png
# from PIL import Image
# from io import BytesIO

# spot.setup()
# automata_refuel = "G(XXXr) && Fa && Fb" # XXXXXXXXXXXXXXXXXXX
# a = spot.translate(automata_refuel)

# # https://stackoverflow.com/a/70007704
# # https://stackoverflow.com/a/46135174
# img_png = svg2png(a.show().data, scale=5.0)
# img = Image.open(BytesIO(img_png))
# plt.imshow(img)
# plt.show()

# exit()

# spot.setup()
# automata_refuel = "G(XXXr) && Fa && Fb" # XXXXXXXXXXXXXXXXXXX
# a = spot.translate(automata_refuel)

# # https://stackoverflow.com/a/70007704
# # https://stackoverflow.com/a/46135174
# img_png = svg2png(a.show().data, scale=5.0)
# img = Image.open(BytesIO(img_png))
# plt.imshow(img)
# plt.show()

# exit()

# GLOBAL VARS
CELLS_SIZE = 32 # 32 pixels
MAX_WEIGHT = 999

map_h = 640
map_w = 576

# Read image and show it
img = cv2.imread('./sample.jpg')
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
plt.show()

# These 4 points are used to perspective correct the image
# they represent the 4 corners of the map
# used code from here as reference: https://stackoverflow.com/questions/22656698
src = np.float32([[1025, 132], [855, 2702], [3337, 2722], [2974, 165]])
dest = np.float32([[0, 0], [0, map_h], [map_w, map_h], [map_w, 0]])

# Use those corners to create the transformation matrix
# then apply that matrix to the image
transmtx = cv2.getPerspectiveTransform(src, dest)
wpcc_img = cv2.warpPerspective(img, transmtx, (map_w, map_h)) # processed

# Show the perspective corrected image
plt.imshow(cv2.cvtColor(wpcc_img, cv2.COLOR_BGR2RGB))
plt.show()

# Split the image into the seperate HSV vhannels
wpcc_img = cv2.cvtColor(wpcc_img, cv2.COLOR_BGR2HSV)
hue_channel, sat_channel, _ = cv2.split(wpcc_img)

# plt.imshow(hue_channel)
# plt.show()
# plt.imshow(sat_channel)
# plt.show()

# Extract the bright colors from the image
# the useful values are in the Hue and Saturation channel
# hue will allow us to pinpoint the color shade and the saturation channel will allow us
# to choose the bright colored spots (remove the gray areas and keep the bright colored areas)

# EXAMPLE: for the red channel, the hue values are around zero (the hue channel loops back around to 180)
# so for the hue channel we get the values in range of 175 and 180 and the values in range of 0 to 5
# this will create a mask of all values that are 175-180 and 0-5. This mask will also include gray colors
# that are slightly red, we then use the saturation channel to remove the slightly red gray values and only
# keep the deep red colors
# red = (hue_red_low or hue_red_high) and sat_high
# the and distributes and creates
# red = (hue_red_low and sat_high) or (hue_red_high and sat_high)
# This same can be used for all the colors that we want to extract
red_low_channel = cv2.bitwise_and(cv2.inRange(hue_channel, 0, 5), cv2.inRange(sat_channel, 100, 255))
red_high_channel = cv2.bitwise_and(cv2.inRange(hue_channel, 175, 180), cv2.inRange(sat_channel, 100, 255))
red_channel = cv2.bitwise_or(red_low_channel, red_high_channel)
green_channel = cv2.bitwise_and(cv2.inRange(hue_channel, 40, 50), cv2.inRange(sat_channel, 100, 255))
blue_channel = cv2.bitwise_and(cv2.inRange(hue_channel, 100, 110), cv2.inRange(sat_channel, 100, 255))
yellow_channel = cv2.bitwise_and(cv2.inRange(hue_channel, 20, 30), cv2.inRange(sat_channel, 100, 255))

# plt.imshow(red_channel, cmap='gray')
# plt.show()
# plt.imshow(green_channel, cmap='gray')
# plt.show()
# plt.imshow(blue_channel, cmap='gray')
# plt.show()
# plt.imshow(yellow_channel, cmap='gray')
# plt.show()

# We want to convert the different color channels into an RGB image and since yellow is Red and Green
# we want add the yellow channel into the red and green channels
red_channel = cv2.bitwise_or(red_channel, yellow_channel)
green_channel = cv2.bitwise_or(green_channel, yellow_channel)

# plt.imshow(red_channel, cmap='gray')
# plt.show()
# plt.imshow(green_channel, cmap='gray')
# plt.show()

# Merge the channels into one RGB image
processed_img = cv2.merge([red_channel,green_channel,blue_channel])
plt.imshow(processed_img)
plt.show()

# Get the dimensions of the image
dim = wpcc_img.shape
print(dim)

# Calculate the number of cells
cells_height = math.floor(dim[0] / CELLS_SIZE)
cells_width  = math.floor(dim[1] / CELLS_SIZE)

print((cells_height, cells_width))

# Variable to store the unique colors in the image
colors = []

# Go through each cell and each pixel of the cell to decide what type of cell it is
# use this info to construct a cell type map of the area
cell_type = []
cell_num_height = 0
cell_num_width = 0
for y in range(0, dim[0], CELLS_SIZE):
    cell_type.append([])
    cell_num_height = 0

    for x in range(0, dim[1], CELLS_SIZE):
        cell_type[cell_num_width].append('C')

        # draw rectangles
        img_cells = cv2.rectangle(processed_img, (x+1,y+1), (x + CELLS_SIZE,y + CELLS_SIZE), (255,255,255), 1)

        # determine what the cell is
        cell_known = False
        for u in range(y, y + CELLS_SIZE, 1):
            if u >= dim[0]:
                break

            for v in range(x, x + CELLS_SIZE, 1):
                if v >= dim[1]:
                    break

                # keep a record of all the different colors
                if tuple(processed_img[u,v]) not in colors:
                    colors.append(tuple(processed_img[u,v]))

                # mark the cells if its corosponding color exists in the cell
                if tuple(processed_img[u,v]) == (0,255,0): # Hazard Cells
                    cell_known = True
                    img_cells = cv2.putText(img_cells, 'H',(x+3, y+CELLS_SIZE-3), 2, 1, (255,255,255),1)
                    cell_type[cell_num_width][cell_num_height] = 'H'
                if tuple(processed_img[u,v]) == (255, 0, 0): # Goal Cells
                    cell_known = True
                    img_cells = cv2.putText(img_cells, 'G',(x+3, y+CELLS_SIZE-3), 2, 1, (255,255,255),1)
                    cell_type[cell_num_width][cell_num_height] = 'G'
                if tuple(processed_img[u,v]) == (255, 255, 0): # Objective Cells
                    cell_known = True
                    img_cells = cv2.putText(img_cells, 'O',(x+3, y+CELLS_SIZE-3), 2, 1, (255,255,255),1)
                    cell_type[cell_num_width][cell_num_height] = 'O'
                if tuple(processed_img[u,v]) == (0, 0, 255): # Refuel Cells
                    cell_known = True
                    img_cells = cv2.putText(img_cells, 'R',(x+3, y+CELLS_SIZE-3), 2, 1, (255,255,255),1)
                    cell_type[cell_num_width][cell_num_height] = 'R'

            # Exit loop if we know the cell type
            if cell_known:
                break

        # if we dont know the cell type (its all white), mark it as a clean cell
        if not cell_known:
            img_cells = cv2.putText(img_cells, 'C',(x+3, y+CELLS_SIZE-3), 2, 1, (255,255,255),1)
        cell_num_height += 1
    cell_num_width += 1

# Print the different colors in the image
print(colors)
print()
print()

# Print the cell type map for debugging
for y in cell_type:
    print(y)
print()
print()

# Show the images with the cell type and cell boundries
plt.imshow(img_cells)
plt.show()

# Convert connected cells with the \p orig_value to \p new_value
# this allows us to mark areas from Goals to Start and Finish Cells
def convert_cells(cell_type, y, x, orig_value, new_value):
    cell_type[y][x] = new_value
    if y > 0 and cell_type[y - 1][x] == orig_value:
        convert_cells(cell_type, y - 1, x, orig_value, new_value)
    if x > 0 and cell_type[y][x - 1] == orig_value:
        convert_cells(cell_type, y, x - 1, orig_value, new_value)
    if y < (len(cell_type)-1) and cell_type[y + 1][x] == orig_value:
        convert_cells(cell_type, y + 1, x, orig_value, new_value)
    if x < (len(cell_type[y])-1) and cell_type[y][x + 1] == orig_value:
        convert_cells(cell_type, y, x + 1, orig_value, new_value)

objectives = ["A", "B"]
objectives_idx = 0
goals = ["S", "F"]
goals_idx = 0
# Convert Goal Cells into start and finish cells
for y in range(len(cell_type)):
    for x in range(len(cell_type[y])):
        if cell_type[y][x] == "O":
            convert_cells(cell_type, y, x, "O", objectives[objectives_idx])
            objectives_idx += 1
        if cell_type[y][x] == "G":
            convert_cells(cell_type, y, x, "G", goals[goals_idx])
            goals_idx += 1

# Print the converted cell types
for y in cell_type:
    print(y)
print()
print()

# Can the vehicle travel into this cell?
def is_valid_travel_cell(c):
    if c in ["A", "B", "C", "S", "F", "R"]:
        return True
    return False

# Convert the cell type map into a state diagram
# the algo pretty much checks the 4 sides (North, South, Eeast, West) to see
# if the block is a travelable block and creates a valid edge with weight of 1.0
# if it is
state_diagram = []
state_dict = {}
for y in range(len(cell_type)):
    state_diagram.append([])
    for x in range(len(cell_type[0])):
        state_diagram[y].append([MAX_WEIGHT, MAX_WEIGHT, MAX_WEIGHT, MAX_WEIGHT, cell_type[y][x], f"{x}-{y}"])
        state_dict[f"{x}-{y}"] = []
        if cell_type[y][x] == 'H':
            continue
        # check up left
        # NOT IMPL

        # check up
        if y > 0 and is_valid_travel_cell(cell_type[y - 1][x]):
            state_diagram[y][x][0] = 1
            state_dict[f"{x}-{y}"].append(('u', f"{x}-{y-1}"))
        # check up right
        # NOT IMPL

        # check left
        if x > 0 and is_valid_travel_cell(cell_type[y][x - 1]):
            state_diagram[y][x][1] = 1
            state_dict[f"{x}-{y}"].append(('l', f"{x-1}-{y}"))

        # check right
        if x < (len(cell_type[0]) - 1) and is_valid_travel_cell(cell_type[y][x + 1]):
            state_diagram[y][x][2] = 1
            state_dict[f"{x}-{y}"].append(('r', f"{x+1}-{y}"))

        # check down left
        # NOT IMPL

        # check down
        if y < (len(cell_type) - 1) and is_valid_travel_cell(cell_type[y + 1][x]):
            state_diagram[y][x][3] = 1
            state_dict[f"{x}-{y}"].append(('d', f"{x}-{y+1}"))
        # check down right
        # NOT IMPL

# pretty print state diagram
for row in state_diagram:
    # Up arrows
    for col in row:
        print(" ", end="") # space for the left arrow
        if col[0] != MAX_WEIGHT:
            print("↑", end="")
        else:
            print(" ", end="")
        print(" ", end="") # space for the right arrow
    print()
    # left/right and center char
    for col in row:
        if col[1] != MAX_WEIGHT:
            print("←", end="")
        else:
            print(" ", end="")
        print(col[4], end="")
        if col[2] != MAX_WEIGHT:
            print("→", end="")
        else:
            print(" ", end="")
    print()
    # Down arrows
    for col in row:
        print(" ", end="") # space for the left arrow
        if col[3] != MAX_WEIGHT:
            print("↓", end="")
        else:
            print(" ", end="")
        print(" ", end="") # space for the right arrow
    print()

print(state_dict)

# find the start node
start = ()
finish = ()
for y in range(len(cell_type)):
    for x in range(len(cell_type[0])):
        if cell_type[y][x] == 'S':
            start = (x, y)
        if cell_type[y][x] == 'F':
            finish = (x, y)

print(start)
print(finish)

# Start creating a video of the D's algo in working
visited_image = cv2.cvtColor(img_cells.copy(), cv2.COLOR_BGR2RGB)
video_out = cv2.VideoWriter('project_phys_only.mkv',cv2.VideoWriter_fourcc('M','P','4','V'), 15, (visited_image.shape[1], visited_image.shape[0]))

# Dijkstras algo
# When I wrote this code, only god and I knew how it works. Now, only god knows
queue = [] # queue is an array of (weight, (x, y))
visited_nodes = [ [False] * len(cell_type[0]) for _ in range(len(cell_type))] # create bool false array same size as state_diagram
distances = [ [MAX_WEIGHT] * len(cell_type[0]) for _ in range(len(cell_type))]
prev = [ [(0,0)] * len(cell_type[0]) for _ in range(len(cell_type))]

queue.append((0,start))
distances[start[1]][start[0]] = 0

while len(queue) != 0:
    # get first element
    current = queue[0]
    queue = queue[1:]

    # unpack element
    x = current[1][0]
    y = current[1][1]
    dist = current[0]

    # if weve already been to this node, skip it
    if (visited_nodes[y][x]): continue
    # mark node as visited
    visited_nodes[y][x] = True
    # get directions we can travel
    valid_paths = state_diagram[y][x]

    half_cell = math.ceil((CELLS_SIZE/2))
    center = (x*CELLS_SIZE+half_cell, y*CELLS_SIZE+half_cell)
    visited_image = cv2.circle(visited_image, center, 4, (0, 255, 255), 5)
    # plt.imshow(visited_image)
    # plt.show()

    # write the current state as an image into the video
    video_out.write(visited_image)
    visited_image = cv2.circle(visited_image, center, 4, (100 + (dist*10), 0, 100 + (dist*10)), 5)

    # check each direction we can travel
    if valid_paths[0] == 1: # UP
        old_distance = distances[y - 1][x]
        new_distance = dist + state_diagram[y][x][0]
        if new_distance <= old_distance:
            distances[y - 1][x] = new_distance
            prev[y - 1][x] = (x,y)
        bisect.insort(queue, (distances[y - 1][x], (x,y-1)), key=lambda a: a[0])
    if valid_paths[1] == 1: # LEFT
        old_distance = distances[y][x - 1]
        new_distance = dist + state_diagram[y][x][1]
        if new_distance <= old_distance:
            distances[y][x - 1] = new_distance
            prev[y][x - 1] = (x,y)
        bisect.insort(queue, (distances[y][x - 1], (x-1,y)), key=lambda a: a[0])
    if valid_paths[2] == 1: # RIGHT
        old_distance = distances[y][x + 1]
        new_distance = dist + state_diagram[y][x][2]
        if new_distance <= old_distance:
            distances[y][x + 1] = new_distance
            prev[y][x + 1] = (x,y)
        bisect.insort(queue, (distances[y][x + 1], (x+1,y)), key=lambda a: a[0])
    if valid_paths[3] == 1: # DOWN
        old_distance = distances[y + 1][x]
        new_distance = dist + state_diagram[y][x][3]
        if new_distance <= old_distance:
            distances[y + 1][x] = new_distance
            prev[y + 1][x] = (x,y)
        bisect.insort(queue, (distances[y + 1][x], (x,y+1)), key=lambda a: a[0])

# Print the distances map
for y in distances:
    print(y)

# Print the previous cell map
for y in prev:
    print(y)

# calculate the shortest path and create a video while
shortest_path = []
current_node = finish
while current_node != start:
    # write the current back trace state into the video
    half_cell = math.ceil((CELLS_SIZE/2))
    center = (current_node[0]*CELLS_SIZE+half_cell, current_node[1]*CELLS_SIZE+half_cell)
    visited_image = cv2.circle(visited_image, center, 4, (255, 255, 255), 5)
    for i in range(3):
        video_out.write(visited_image)

    shortest_path.append(current_node)
    current_node = prev[current_node[1]][current_node[0]]
shortest_path.append(start)

# pause for two seconds on the final frame
for i in range(60):
    video_out.write(visited_image)
video_out and video_out.release()

print(shortest_path)

# draw the shortest path
img_plain_djk = img_cells.copy()
for i in range(len(shortest_path)):
    half_cell = math.ceil((CELLS_SIZE/2))

    if shortest_path[i] == start: break

    node = shortest_path[i]
    next_node = shortest_path[i+1]

    center = (node[0]*CELLS_SIZE+half_cell, node[1]*CELLS_SIZE+half_cell)
    next_center = (next_node[0]*CELLS_SIZE+half_cell, next_node[1]*CELLS_SIZE+half_cell)

    img_plain_djk = cv2.line(img_plain_djk, center, next_center, (255,255,255), 8)

# Show the path found image from D's algo
plt.imshow(img_plain_djk)
plt.show()

# This the LTL ormula converted to a buchii automata
ltl_auto = ["0", "1", "2", "3"]
def ltl_auto_valid(src, dest, ops):
    if src == "0": return True

    if src == "1" and dest =="0": return True if "B" in ops else False
    if src == "1" and dest =="1": return True if "B" not in ops else False

    if src == "2" and dest =="0": return True if "A" in ops and "B" in ops else False
    if src == "2" and dest =="1": return True if "A" in ops and "B" not in ops else False
    if src == "2" and dest =="2": return True if "A" not in ops and "B" not in ops and "R" not in ops else False
    if src == "2" and dest =="3": return True if "A" not in ops and "B" in ops and "R" not in ops else False

    if src == "3" and dest =="3": return True if "A" not in ops and "R" not in ops else False
    if src == "3" and dest =="0": return True if "A" in ops else False

    return False

# This is the map FSM wrapper func, allows us to write the algoithm easier
def phys_map_fsm_valid(src, dest, ops):
    valid_paths = state_dict[src]
    for direction in valid_paths:
        if dest == direction[1]:
            return True
    return False

# PRODUCT AUTOMATA Code
# see the other folders on how this works
# waws copied from there
auto_final = {}
key_f = []

for key_1 in state_dict.keys():
    for key_2 in ltl_auto:
        key_f.append((key_1, key_2))

print(key_f)
print(len(key_f))

for src_1, src_2 in key_f:
    for dest_1, dest_2 in key_f:
        state_diagram_cord = dest_1.split("-")
        state_diagram_cord_x = int(state_diagram_cord[0])
        state_diagram_cord_y = int(state_diagram_cord[1])
        state_at_cord = state_diagram[state_diagram_cord_y][state_diagram_cord_x][4]
        if phys_map_fsm_valid(src_1, dest_1, []) and ltl_auto_valid(src_2, dest_2, [state_at_cord]):
            key_f_src_str = src_1 + ',' + src_2
            key_f_dest_str = dest_1 + ',' + dest_2
            if key_f_src_str not in auto_final.keys(): auto_final[key_f_src_str] = []
            auto_final[key_f_src_str].append(key_f_dest_str)

for key in auto_final:
    print(key, end=" : ")
    print(auto_final[key])

auto_final_start = f"{start[0]}-{start[1]},2"
auto_final_end = f"{finish[0]}-{finish[1]},0"

print()
print(auto_final_start)
print(auto_final_end)

## MOST OF THE CODE BELOW IS COPIED FROM ABOVE and does the same thing so Im not going to detail
## comment it.
# pretty much its just D's algo, video making, and making the images

# Dijkstras algo
# When I wrote this code, only god and I knew how it works. Now, only god knows
queue = [] # queue is an array of (weight, (x, y))
visited_nodes = [] # create bool false array same size as state_diagram
distances = {}
prev = {}

queue.append((0,auto_final_start))
distances[auto_final_start] = 0

visited_image = cv2.cvtColor(img_cells.copy(), cv2.COLOR_BGR2RGB)
video_out = cv2.VideoWriter('project_final.mkv',cv2.VideoWriter_fourcc('M','P','4','V'), 15, (visited_image.shape[1], visited_image.shape[0]))

while len(queue) != 0:
    # get first element
    current = queue[0]
    queue = queue[1:]

    # unpack element
    dist = current[0]
    node = current[1]

    # if weve already been to this node, skip it
    if (node in visited_nodes): continue
    # mark node as visited
    visited_nodes.append(node)
    # get directions we can travel
    valid_paths = auto_final[node]

    node_x = int(node.split(',')[0].split('-')[0])
    node_y = int(node.split(',')[0].split('-')[1])
    half_cell = math.ceil((CELLS_SIZE/2))
    center = (node_x*CELLS_SIZE+half_cell, node_y*CELLS_SIZE+half_cell)
    visited_image = cv2.circle(visited_image, center, 4, (0, 255, 255), 5)
    # plt.imshow(visited_image)
    # plt.show()
    video_out.write(visited_image)
    visited_image = cv2.circle(visited_image, center, 4, (100 + (dist*10), 0, 100 + (dist*10)), 5)

    for path in valid_paths:
        if path not in distances.keys(): distances[path] = MAX_WEIGHT

        old_distance = distances[path]
        new_distance = dist + 1

        if new_distance <= old_distance:
            distances[path] = new_distance
            prev[path] = node

        bisect.insort(queue, (distances[path], path), key=lambda a: a[0])

for key in distances.keys():
    print(key, end=" : ")
    print(distances[key])

print()
print()
for key in prev.keys():
    print(key, end=" : ")
    print(prev[key])

# calculate the shortest path
shortest_path = []
current_node = auto_final_end
visited_image_b4_backtrace = visited_image.copy()
while current_node != auto_final_start:
    node_x = int(current_node.split(',')[0].split('-')[0])
    node_y = int(current_node.split(',')[0].split('-')[1])
    half_cell = math.ceil((CELLS_SIZE/2))
    center = (node_x*CELLS_SIZE+half_cell, node_y*CELLS_SIZE+half_cell)
    visited_image = cv2.circle(visited_image, center, 4, (255, 255, 255), 5)
    if state_diagram[node_y][node_x][4] == "A" or state_diagram[node_y][node_x][4] == "B":
        visited_image = visited_image_b4_backtrace.copy()
    for i in range(3):
        video_out.write(visited_image)

    shortest_path.append(current_node)
    current_node = prev[current_node]
shortest_path.append(auto_final_start)

print(shortest_path)

shortest_path_phys = []
for path in shortest_path:
    sp = path.split(",")
    shortest_path_phys.append(sp[0])

print(shortest_path_phys)


# draw the shortest path
img_final_djk = cv2.cvtColor(img_cells.copy(), cv2.COLOR_BGR2RGB)
for i in range(len(shortest_path_phys) - 1):
    half_cell = math.ceil((CELLS_SIZE/2))

    if shortest_path_phys[i] == start: break

    node_str = shortest_path_phys[i]
    next_node_str = shortest_path_phys[i+1]

    node = (int(node_str.split("-")[0]), int(node_str.split("-")[1]))
    next_node = (int(next_node_str.split("-")[0]), int(next_node_str.split("-")[1]))

    center = (node[0]*CELLS_SIZE+half_cell, node[1]*CELLS_SIZE+half_cell)
    next_center = (next_node[0]*CELLS_SIZE+half_cell, next_node[1]*CELLS_SIZE+half_cell)

    img_final_djk = cv2.line(img_final_djk, center, next_center, (255,255,255), 8)

for i in range(60):
    video_out.write(img_final_djk)
video_out and video_out.release()

plt.imshow(img_final_djk)
plt.show()

print(len(key_f))
