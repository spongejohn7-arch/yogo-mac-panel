"""Original 6×6 robot sprites. Dark space keeps tiny expressions legible."""
from yogo.frame import Frame

BLACK=(0,0,0)
WHITE=(225,245,255)
PINK=(255,60,120)
COLORS={
    'idle':(40,105,225),'thinking':(0,175,195),'tool':(145,65,225),
    'waiting':(220,125,15),'done':(25,195,95),'error':(220,40,45),
}

def robot_frame(state,t):
    state=state if state in COLORS else 'idle'
    t=max(0,t)
    color=COLORS[state]
    accent=WHITE
    rows=['..A...','.BBBB.','BWBBWB','BBBBBB','.BWWB.','.B..B.']
    # Each design has exactly six columns; eyes and feet move on different beats.
    if state=='idle':
        if t%4.5>=4.15:rows[2]='BBBBBB';rows[3]='BWBBWB'
    elif state=='thinking':
        accent=(255,205,45)
        rows[0]='...A..' if int(t*2)%2 else '..A...'
        rows[2]='BBWBWB' if int(t/1.1)%2 else 'BWBWBB'
        rows[4]='.BBBB.'
    elif state=='tool':
        accent=(255,190,70)
        rows[0]='.A....' if int(t*3)%2 else '....A.'
        rows[4]='.BWWB.'
        rows[5]='..B.B.' if int(t*2)%2 else '.B.B..'
    elif state=='waiting':
        rows=['..A...','.BBBB.','BWBBWB','BBBBBB','.BWWB.','..AA..']
        # Alternate an unmistakable exclamation with the orange face.
        if int(t*2)%2:rows=['..AA..','..AA..','..AA..','......','..AA..','.BBBB.']
    elif state=='done':
        if t<1.6:rows=['.A..A.','.BBBB.','BWBBWB','BBBBBB','.BWWB.','..BB..'];accent=(255,215,60)
        else:
            color=PINK;accent=WHITE
            rows=['.BB.B.','BBBBBB','BWBBBB','.BBBB.','..BB..','......']
            if int(t*3)%2:rows[0]='.BA.B.'
            else:rows[0]='.AB.B.'
    elif state=='error':
        accent=(255,190,55)
        # Two X-shaped eyes, followed by a steady sad face (no continuous flashing).
        rows=['......','B.BB.B','.B..B.','B.BB.B','..AA..','.A..A.']
        if t<.8 and int(t*5)%2:rows=['..A...','.BBBB.','BWBBWB','BBBBBB','..WW..','.B..B.']
    palette={'.':BLACK,'B':color,'W':WHITE,'A':accent}
    return Frame.from_pixels([palette[ch] for row in rows for ch in row])
