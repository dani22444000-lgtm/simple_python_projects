import math
import os
import sys
import time
filename="deomed player (2).obj"

ASCII_CHARS = "kgwxaeri. "


def load_obj(path):
    vertices = []
    faces = []
    with open(path, "r") as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            if parts[0] == "v":
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif parts[0] == "f":
                face = []
                for token in parts[1:]:
                    idx = int(token.split("/")[0])
                    face.append(idx - 1)
                for i in range(1, len(face) - 1):
                    faces.append([face[0], face[i], face[i + 1]])
    return vertices, faces


def rotation_matrix(rx, ry, rz):
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)

    Rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    Ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    Rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]

    def matmul(A, B):
        return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

    return matmul(matmul(Rx, Ry), Rz)

def apply_matrix(v, M):
    return [
        M[0][0]*v[0] + M[0][1]*v[1] + M[0][2]*v[2],
        M[1][0]*v[0] + M[1][1]*v[1] + M[1][2]*v[2],
        M[2][0]*v[0] + M[2][1]*v[1] + M[2][2]*v[2],
    ]


def project(vertex, width, height, fov=1.5, camera_z=4.0):
    x, y, z = vertex
    z += camera_z
    if z <= 0.1:
        return None
    factor = fov / z
    px = int(x * factor * width / 2 + width / 2)
    py = int(-y * factor * height / 2 + height / 2)
    return px, py, z


def fill_triangle(pts, char, screen, zbuffer, width, height):
    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = pts

    min_x = max(0, min(x0, x1, x2))
    max_x = min(width - 1, max(x0, x1, x2))
    min_y = max(0, min(y0, y1, y2))
    max_y = min(height - 1, max(y0, y1, y2))

    area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    if abs(area) < 1e-6:
        return

    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            w0 = ((x1 - x0) * (y - y0) - (x - x0) * (y1 - y0)) / area
            w1 = ((x - x0) * (y2 - y0) - (x2 - x0) * (y - y0)) / area
            w2 = 1 - w0 - w1

            if w0 >= 0 and w1 >= 0 and w2 >= 0:
                z = w1 * z0 + w2 * z1 + w0 * z2
                if z < zbuffer[y][x]:
                    zbuffer[y][x] = z
                    screen[y][x] = char


def render(vertices, faces, width=80, height=40, rx=0.3, ry=0.5, rz=0.0):
    M = rotation_matrix(rx, ry, rz)
    rotated = [apply_matrix(v, M) for v in vertices]

    screen = [[" " for _ in range(width)] for _ in range(height)]
    zbuffer = [[float("inf") for _ in range(width)] for _ in range(height)]

    for face in faces:
        pts = []
        for idx in face:
            p = project(rotated[idx], width, height)
            if p is None:
                break
            pts.append(p)
        if len(pts) < 3:
            continue

        v0 = rotated[face[0]]
        v1 = rotated[face[1]]
        v2 = rotated[face[2]]
        edge1 = [v1[i] - v0[i] for i in range(3)]
        edge2 = [v2[i] - v0[i] for i in range(3)]
        normal = [
            edge1[1]*edge2[2] - edge1[2]*edge2[1],
            edge1[2]*edge2[0] - edge1[0]*edge2[2],
            edge1[0]*edge2[1] - edge1[1]*edge2[0],
        ]
        length = math.sqrt(sum(n*n for n in normal)) or 1
        normal = [n / length for n in normal]

        light = [0, 0, -1]
        dot = sum(normal[i] * light[i] for i in range(3))
        intensity = max(0.0, dot)

        char_index = int(intensity * (len(ASCII_CHARS) - 1))
        char = ASCII_CHARS[char_index]
        if char == " ":
            continue

        fill_triangle(pts, char, screen, zbuffer, width, height)

    return screen


def clear_screen():
    
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()

def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def main():
    OBJ_PATH = filename
    if not os.path.exists(OBJ_PATH):
        print("no OBJ file exist with name",filename)
        return

    vertices, faces = load_obj(OBJ_PATH)
    print(f"object vertices: {len(vertices)} |object faces: {len(faces)}")
    time.sleep(1.5)

    hide_cursor()

    rx, ry, rz = 0.0, 0.0, 0.0
    speed_ry = math.radians(5)
    speed_rx = math.radians(0)
    frame_delay = 1.0 / 15

    try:
        while True:
            screen = render(vertices, faces, width=80, height=40,
                            rx=rx, ry=ry, rz=rz)

            
            lines = ["\033[H\033[J"]  
            lines.extend("".join(row) for row in screen)
            lines.append(f"rx={math.degrees(rx):6.1f}°  ry={math.degrees(ry):6.1f}°  |  Ctrl+C to exit")
            sys.stdout.write("\n".join(lines))
            sys.stdout.flush()

            rx += speed_rx
            ry += speed_ry
            time.sleep(frame_delay)

    except KeyboardInterrupt:
        show_cursor()
        print("exit")

if __name__ == "__main__":
    main()