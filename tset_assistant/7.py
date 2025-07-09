# -*- coding: utf-8 -*-

import queue
import json
import asyncio
import os
import uuid
import glob
import platform
import subprocess
from vosk import Model, KaldiRecognizer
import sounddevice as sd
from openai import OpenAI
from edge_tts import Communicate

# ====== 配置区域 ======
DEEPSEEK_API_KEY = "sk-88257db5a9364043afd664b0931c5fe2"  #  DeepSeek API Key
MODEL_PATH = "/root/vosk-model-small-cn-0.22"  # Vosk 模型路径
SAMPLERATE = 16000
INPUT_DEVICE_INDEX = 1  # 根据 `sounddevice.query_devices()` 得到 USB 麦克风对应索引
USB_AUDIO_CARD = "plughw:1,0"  # USB 音响输出设备
EXIT_KEYWORDS = ["退出", "结束", "关闭", "拜拜"]

# ====== 初始化 ======
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
q = queue.Queue()
model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, SAMPLERATE)

conversation_history = [
    {"role": "system", "content": "你是一个中文语音助手，回答简洁有帮助。"}
]

# ====== 清理旧音频文件 ======
def cleanup_audio_files():
    for file in glob.glob("output_*.mp3") + glob.glob("output_*.wav"):
        try:
            os.remove(file)
        except Exception as e:
            print(f"⚠️ 无法删除 {file}: {e}")

# ====== 音频输入回调 ======
def callback(indata, frames, time, status):
    if status:
        print("⚠️ 音频输入状态:", status)
    q.put(bytes(indata))

# ====== 合成语音并播放到 USB 音响 ======
async def speak(text):
    cleanup_audio_files()
    mp3_file = f"output_{uuid.uuid4().hex[:8]}.mp3"
    wav_file = mp3_file.replace(".mp3", ".wav")

    communicate = Communicate(text, voice="zh-CN-XiaoxiaoNeural")
    await communicate.save(mp3_file)

    # mp3 转 wav
    subprocess.run(["ffmpeg", "-y", "-i", mp3_file, wav_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 播放 wav 到指定设备
    subprocess.run(["aplay", "-D", USB_AUDIO_CARD, wav_file])

# ====== 获取 DeepSeek 回复并维护上下文 ======
def get_deepseek_reply(text):
    conversation_history.append({"role": "user", "content": text})
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=conversation_history,
            stream=False
        )
        reply = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        print("❌ DeepSeek 请求失败:", e)
        return "对不起，我暂时无法连接服务器。"

# ====== 主逻辑入口 ======
def main():
    sd.default.device = (INPUT_DEVICE_INDEX, None)

    print("🟢 语音助手已启动（Ubuntu 终端）")
    with sd.RawInputStream(samplerate=SAMPLERATE, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("\n🎙️ 现在请讲话（说“退出”可关闭）")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                text = json.loads(result)["text"]
                if text.strip() == "":
                    continue

                print("🗣️ 你说的是：", text)

                if any(kw in text for kw in EXIT_KEYWORDS):
                    print("👋 检测到退出指令，语音助手结束运行。")
                    break

                reply = get_deepseek_reply(text)
                print("🤖 助手回复：", reply)
                asyncio.run(speak(reply))
                print("\n🎙️ 继续讲话（等待中...）")

# ====== 启动程序 ======
if __name__ == "__main__":
    main()
