from pydub import AudioSegment
import os
import time


def x_to_pan(x):
    x -= 0.5
    pan_boundary = 0.9
    x = min(x, pan_boundary)
    x = max(x, -pan_boundary)
    return x / pan_boundary

def pan_stereo(sound, pos):
    """
    將音效調整到指定的立體聲位置。
    -1 = 完全左聲道
     0 = 中間
     1 = 完全右聲道
    """
    return sound.pan(pos)


# 計時開始
start_time = time.time()

# 載入敲擊音檔
hit_sounds = [
    None,
    AudioSegment.from_wav("hit1.wav"),
    AudioSegment.from_wav("hit2.wav"),
    AudioSegment.from_wav("hit3.wav"),
]

# 讀取 chart.txt，並解析敲擊時間與立體聲位置
with open("hits.txt", "r") as chart_file:
    lines = chart_file.readlines()
    hits = [(int(line.split()[0]), float(line.split()[1]), line.split()[2]) for line in lines]

# 計算節奏檔的總長度
total_duration = max(hit[0] for hit in hits) + len(hit_sounds[1]) * 2

# 建立一個空白的立體聲音檔，長度為總時長
rhythm_track = AudioSegment.silent(duration=total_duration).set_channels(2)

# 將敲擊音疊加到對應的時間點，並調整立體聲位置
for hit_time, xcoord, hit_sound in hits:
    panned_hit = pan_stereo(hit_sounds[int(hit_sound[-1])], x_to_pan(xcoord))  # 根據 xcoord 調整立體聲位置
    rhythm_track = rhythm_track.overlay(panned_hit, position=hit_time)

# 將合成的節奏檔輸出為 rhythm.wav
output_file = "rhythm.wav"
rhythm_track.export(output_file, format="wav")

end_time = time.time()
execution_time = end_time - start_time

print(f"立體聲節奏檔已成功輸出為 {output_file}")
print(f"程式執行時間: {execution_time:.2f} 秒")

