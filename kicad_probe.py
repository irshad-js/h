"""Run with KiCad's bundled Python. Creates a disposable QR coupon only."""
import argparse
import json
import pcbnew

parser = argparse.ArgumentParser()
parser.add_argument('matrix')
parser.add_argument('output')
args = parser.parse_args()
matrix = json.load(open(args.matrix, encoding='utf-8'))
board = pcbnew.BOARD()
pitch = .35
offset = (20 - len(matrix) * pitch) / 2


def point(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


for layer in [pcbnew.F_SilkS, pcbnew.B_SilkS]:
    for y, row in enumerate(matrix):
        for x, ink in enumerate(row):
            if not ink:
                continue
            # Backside artwork mirrors board coordinates, reads normally from back.
            xx = x if layer == pcbnew.F_SilkS else len(matrix) - 1 - x
            rect = pcbnew.PCB_SHAPE(board)
            rect.SetShape(pcbnew.SHAPE_T_RECT)
            rect.SetStart(point(offset + xx * pitch, offset + y * pitch))
            rect.SetEnd(point(offset + (xx + 1) * pitch, offset + (y + 1) * pitch))
            rect.SetLayer(layer); rect.SetWidth(0); rect.SetFilled(True)
            board.Add(rect)

for a, b in [((0, 0), (20, 0)), ((20, 0), (20, 20)), ((20, 20), (0, 20)), ((0, 20), (0, 0))]:
    line = pcbnew.PCB_SHAPE(board)
    line.SetShape(pcbnew.SHAPE_T_SEGMENT)
    line.SetStart(point(*a)); line.SetEnd(point(*b))
    line.SetLayer(pcbnew.Edge_Cuts); line.SetWidth(pcbnew.FromMM(.05))
    board.Add(line)
pcbnew.SaveBoard(args.output, board)
print('Disposable front/back QR coupon:', args.output)
