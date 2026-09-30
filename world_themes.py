"""Garden and space animations matching the approved 6×6 preview."""
import json
from pathlib import Path
from yogo.frame import Frame

DATA=json.loads(Path(__file__).with_name('world_sprites.json').read_text())
PALETTE={key:tuple(int(value[i:i+2],16) for i in (1,3,5)) for key,value in DATA['palette'].items()}

def world_frame(theme,state,elapsed):
    states=DATA['themes'][theme]
    frames=states.get(state,states['idle'])['frames']
    index=int(max(0,elapsed)/.65)
    # Show completion/error once, then hold until the real status changes.
    index=min(index,len(frames)-1) if state in ('done','error') else index%len(frames)
    return Frame.from_pixels([PALETTE[pixel] for row in frames[index] for pixel in row])
