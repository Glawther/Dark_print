import subprocess
import os
import shutil

ffmpeg = shutil.which('ffmpeg') or r'C:\Users\SAMSUNG\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin\ffmpeg.EXE'
out_dir = r'storage\local_videos'
os.makedirs(out_dir, exist_ok=True)

clips = [
    (
        os.path.join(out_dir, 'minimal_gradient_flow.mp4'),
        'testsrc2=size=1080x1920:rate=30,format=gbrp,curves=all=0/0 0.5/0.2 1/0.6,colorchannelmixer=rr=0.15:gg=0.2:bb=0.3,boxblur=12:6',
        15
    ),
    (
        os.path.join(out_dir, 'digital_matrix_grid.mp4'),
        'mandelbrot=size=1080x1920:rate=30:maxiter=120,colorchannelmixer=rr=0.08:gg=0.35:bb=0.25,format=yuv420p',
        15
    ),
    (
        os.path.join(out_dir, 'particle_stars_ambient.mp4'),
        'sierpinski=size=1080x1920:rate=30:seed=1337,colorchannelmixer=rr=0.15:gg=0.2:bb=0.45,format=yuv420p,boxblur=8:4',
        15
    ),
    (
        os.path.join(out_dir, 'financial_abstract_waves.mp4'),
        'testsrc=size=1080x1920:rate=30:decimals=0,colorchannelmixer=rr=0.12:gg=0.18:bb=0.28,format=yuv420p,boxblur=20:10',
        15
    )
]

for out_path, filter_complex, duration in clips:
    if os.path.exists(out_path):
        print(f'Already exists: {out_path}')
        continue
    cmd = [
        ffmpeg, '-y',
        '-f', 'lavfi', '-i', filter_complex,
        '-t', str(duration),
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'ultrafast',
        out_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f'Created: {out_path} ({os.path.getsize(out_path)} bytes)')
    else:
        print(f'Failed: {out_path}: {res.stderr[-200:]}')
