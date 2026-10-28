#!/usr/bin/env python3
"""Offline material-identity audit, not an experiment or automated interpretation.
Reads the supplied PNG headers/CRCs and all text input anew. The only inference
is whether dimensions are consistent with the crop described in the packet.
"""
import argparse
import hashlib
import json
import re
import struct
import zlib
from fractions import Fraction
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def png_metadata(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Invalid PNG signature')
    p = 8
    chunks = []
    info = None
    while p < len(data):
        if p + 12 > len(data):
            raise ValueError('Truncated PNG')
        n = struct.unpack('>I', data[p:p+4])[0]
        kind = data[p+4:p+8]
        payload = data[p+8:p+8+n]
        if len(payload) != n or p + 12 + n > len(data):
            raise ValueError('Truncated PNG chunk')
        crc = struct.unpack('>I', data[p+8+n:p+12+n])[0]
        if zlib.crc32(kind+payload) & 0xffffffff != crc:
            raise ValueError('PNG CRC mismatch')
        chunks.append(kind.decode('ascii'))
        if kind == b'IHDR':
            if n != 13:
                raise ValueError('Invalid IHDR')
            w,h,depth,color,compression,filtering,interlace = struct.unpack('>IIBBBBB',payload)
            info = {'width':w,'height':h,'bit_depth':depth,'color_type':color,'interlace':interlace}
        p += n + 12
        if kind == b'IEND':
            break
    if info is None or not chunks or chunks[-1] != 'IEND' or p != len(data):
        raise ValueError('Incomplete PNG')
    return dict(info,chunk_types=chunks,all_chunk_crcs_valid=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    if args.output_dir.exists():
        parser.error('output directory must not exist')
    names=['task.md','source-packet.md','draft.md','original.png','reproduction.png']
    data={name:(args.input_dir/name).read_bytes() for name in names}
    images={name:png_metadata(data[name]) for name in names if name.endswith('.png')}
    text={name:data[name].decode('utf-8').splitlines() for name in names if name.endswith('.md')}
    packet=text['source-packet.md']
    matches=[re.search(r'底部(\d+)像素',line) for line in packet]
    crops=[int(m.group(1)) for m in matches if m]
    if len(crops)!=1:
        raise ValueError('Packet must state one bottom-crop amount')
    original=images['original.png'];reproduction=images['reproduction.png']
    scale=Fraction(reproduction['width'],original['width'])
    retained=original['height']-crops[0]
    expected_height=retained*scale
    result={
        'scope':'Material identity, PNG dimensions and packet locators; does not prove pixel transformation, symbolism or artist intent.',
        'input_sha256':{name:sha(content) for name,content in data.items()},
        'images':images,
        'crop_dimension_check':{
            'packet_bottom_crop_pixels':crops[0],
            'inferred_width_scale_ratio':str(scale),
            'retained_original_height':retained,
            'predicted_reproduction_height':str(expected_height),
            'observed_reproduction_height':reproduction['height'],
            'dimensions_consistent':expected_height==reproduction['height']
        },
        'packet_locators':[
            {'line':i,'source_id':line.split()[0],'text':line}
            for i,line in enumerate(packet,1) if re.match(r'^(A1|C1|E1)\s',line)
        ],
        'text_line_counts':{name:len(lines) for name,lines in text.items()}
    }
    args.output_dir.mkdir(parents=True,exist_ok=False)
    (args.output_dir/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':'results.json','dimensions_consistent':result['crop_dimension_check']['dimensions_consistent']},ensure_ascii=False))

if __name__=='__main__':
    main()
