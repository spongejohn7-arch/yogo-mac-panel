"""Data-driven 6×6 themes matching their approved previews."""
import json
from pathlib import Path
from yogo.frame import Frame

THEMES={}
for filename,step in (('world_sprites.json',.65),('companion_sprites.json',.6)):
    data=json.loads(Path(__file__).with_name(filename).read_text())
    palette={key:tuple(int(value[i:i+2],16) for i in (1,3,5))
             for key,value in data['palette'].items()}
    for name,states in data['themes'].items():
        THEMES[name]=(states,palette,step)


def world_frame(theme,state,elapsed):
    states,palette,step=THEMES[theme]
    frames=states.get(state,states['idle'])['frames']
    index=int(max(0,elapsed)/step)
    # Completion and error play once; ongoing states, including idle, repeat.
    index=min(index,len(frames)-1) if state in ('done','error') else index%len(frames)
    return Frame.from_pixels([palette[pixel] for row in frames[index] for pixel in row])
