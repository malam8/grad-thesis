import numpy as np
import cv2
import matplotlib.pyplot as plt
import math
import bisect
# import spot
# from cairosvg import svg2png
# from PIL import Image
# from io import BytesIO

import img_process
import cell_process
import ltl_process

# spot.setup()
# automata_refuel = "G(XXXr) && Fa && Fb" # XXXXXXXXXXXXXXXXXXX
# a = spot.translate(automata_refuel)

# # https://stackoverflow.com/a/70007704
# # https://stackoverflow.com/a/46135174
# img_png = svg2png(a.show().data, scale=5.0)
# img = Image.open(BytesIO(img_png))
# plt.imshow(img); plt.show()

# exit()

# GLOBAL VARS
CELLS_SIZE = 4 # 32 pixels
MAX_WEIGHT = 1.0

map_h = 640
map_w = 576

# Read image and show it
img = cv2.imread('./sample.jpg')
# plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)); plt.show()

points = [[1025, 132], [855, 2702], [3337, 2722], [2974, 165]]
wpcc_img = img_process.perspective_warp(img, points, map_w, map_h)

(red_channel, green_channel, blue_channel, yellow_channel) = img_process.color_segment_image(wpcc_img)

processed_img = img_process.merge_colors(red_channel, green_channel, blue_channel, yellow_channel)

orig_goal_reward_image = cv2.add(cv2.add(red_channel, blue_channel), yellow_channel)
goal_reward_image = img_process.apply_edge_blur(orig_goal_reward_image, 128)

risk_image = img_process.create_risk_img(green_channel, 16)

img_cells, cell_type, cell_cost = cell_process.create_cells(processed_img, risk_image, CELLS_SIZE)

cell_type = cell_process.convert_cells(cell_type, objectives=["A", "B"], goals=["S", "F"])

ltl_state_diag, start_state, final_state = ltl_process.parse_ltl_hoa("ltl.hoa.txt")

reward_graphs = img_process.get_reward_images(cell_type, orig_goal_reward_image, CELLS_SIZE)

current_state_reward_graph = ltl_process.get_reward_img_state(ltl_state_diag, start_state, reward_graphs, (map_h, map_w))
reward_current = img_process.apply_edge_blur(current_state_reward_graph, 128)
plt.imshow(reward_current, cmap="gray"); plt.show()

exit()
##################################### Convert Cells To Seperate Goals ##############################################





##################################### LTL Input ##############################################

# Go through each cell and see which ones 

# current_state = start_state
# for key in ltl_state_diag[current_state].keys():
#     ap = ltl_state_diag[current_state][key]
#     ap_nomial = ap.split("&")
#     print(ap_nomial)
#     for col in cell_type:
#         for element in col:
#             value = True
#             for nomial in ap_nomial:
#                 state = nomial[-1]
#                 if state == element:
                    
# create individual reward images







##################################### LTL Dj's Algo





exit()
##################################### State Diagram Conversion ##############################################


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
        if y > 0:
            state_diagram[y][x][0] = cell_cost[y][x]
            state_dict[f"{x}-{y}"].append(('u', f"{x}-{y-1}"))
        # check up right
        # NOT IMPL
        
        # check left
        if x > 0:
            state_diagram[y][x][1] = cell_cost[y][x]
            state_dict[f"{x}-{y}"].append(('l', f"{x-1}-{y}"))

        # check right
        if x < (len(cell_type[0]) - 1):
            state_diagram[y][x][2] = cell_cost[y][x]
            state_dict[f"{x}-{y}"].append(('r', f"{x+1}-{y}"))

        # check down left
        # NOT IMPL

        # check down
        if y < (len(cell_type) - 1):
            state_diagram[y][x][3] = cell_cost[y][x]
            state_dict[f"{x}-{y}"].append(('d', f"{x}-{y+1}"))
        # check down right
        # NOT IMPL

# pretty print state diagram
for row in state_diagram:
    # Up arrows
    for col in row:
        print(" ", end="") # space for the left arrow
        weight_single = 9 if col[0] == 1.0 else int(col[0] * 10)
        print(weight_single, end="")
        print(" ", end="") # space for the right arrow
    print()
    # left/right and center char
    for col in row:
        weight_single = 9 if col[1] == 1.0 else int(col[1] * 10)
        print(weight_single, end="")
        print(col[4], end="")
        weight_single = 9 if col[2] == 1.0 else int(col[2] * 10)
        print(weight_single, end="")
    print()
    # Down arrows
    for col in row:
        print(" ", end="") # space for the left arrow
        weight_single = 9 if col[3] == 1.0 else int(col[3] * 10)
        print(weight_single, end="")
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

##################################### D's Algo base ##############################################

# Start creating a video of the D's algo in working
visited_image = cv2.cvtColor(img_cells.copy(), cv2.COLOR_BGR2RGB)
video_out = cv2.VideoWriter('project_phys_only.mkv',cv2.VideoWriter_fourcc('M','P','4','V'), 15, (visited_image.shape[1], visited_image.shape[0]))

# Dijkstras algo
# When I wrote this code, only god and I knew how it works. Now, only god knows
queue = [] # queue is an array of (weight, (x, y))
visited_nodes = [ [False] * len(cell_type[0]) for _ in range(len(cell_type))] # create bool false array same size as state_diagram
distances = [ [float("inf")] * len(cell_type[0]) for _ in range(len(cell_type))]
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

    half_cell = math.ceil((CELLS_SIZE/2))
    center = (x*CELLS_SIZE+half_cell, y*CELLS_SIZE+half_cell)
    visited_image = cv2.circle(visited_image, center, 4, (0, 255, 255), 1)
    # plt.imshow(visited_image)
    # plt.show()

    # write the current state as an image into the video
    video_out.write(visited_image)
    visited_image = cv2.circle(visited_image, center, 4, (100 + (dist*10), 0, 100 + (dist*10)), 1)

    # check each direction we can travel
    if y > 0: # UP
        old_distance = distances[y - 1][x]
        new_distance = dist + state_diagram[y][x][0]
        if new_distance < old_distance:
            distances[y - 1][x] = new_distance
            prev[y - 1][x] = (x,y)
            bisect.insort(queue, (distances[y - 1][x], (x,y-1)), key=lambda a: a[0])
    if x > 0: # LEFT
        old_distance = distances[y][x - 1]
        new_distance = dist + state_diagram[y][x][1]
        if new_distance < old_distance:
            distances[y][x - 1] = new_distance
            prev[y][x - 1] = (x,y)
            bisect.insort(queue, (distances[y][x - 1], (x-1,y)), key=lambda a: a[0])
    if x < (len(cell_type[0]) - 1): # RIGHT
        old_distance = distances[y][x + 1]
        new_distance = dist + state_diagram[y][x][2]
        if new_distance < old_distance:
            distances[y][x + 1] = new_distance
            prev[y][x + 1] = (x,y)
            bisect.insort(queue, (distances[y][x + 1], (x+1,y)), key=lambda a: a[0])
    if y < (len(cell_type) - 1): # DOWN
        old_distance = distances[y + 1][x]
        new_distance = dist + state_diagram[y][x][3]
        if new_distance < old_distance:
            distances[y + 1][x] = new_distance
            prev[y + 1][x] = (x,y)
            bisect.insort(queue, (distances[y + 1][x], (x,y+1)), key=lambda a: a[0])

# Print the distances map
for y in distances:
    for dist in y:
        print("{:.2f}".format(dist), end=", ")
    print()

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
    visited_image = cv2.circle(visited_image, center, 4, (255, 255, 255), 1)
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
    
    img_plain_djk = cv2.line(img_plain_djk, center, next_center, (0,255,255), 1)

# Show the path found image from D's algo
plt.imshow(img_plain_djk)
plt.show()

exit()

##################################### LTL Formula Conversion ##############################################


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


##################################### Product Automata Construction ##############################################


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

##################################### D's Algo on Product Automata ##############################################


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

# plt.imshow(img_final_djk); plt.show()

print(len(key_f))