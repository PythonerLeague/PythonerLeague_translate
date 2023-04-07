import whisper
import warnings
import os
import hashlib
import time
import subprocess
import pyaudio
import wave
from whisper import tokenizer
import zhconv
# from multiprocessing import Queue
import queue
from langconv import Converter
import sys
import chardet
import codecs
import shutil
import traceback
sys.stdout = open(os.devnull, 'w')
def catch_exception(func):
    """
    不带参数的装饰器
    :param func:
    :return:
    """

    def warp(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e)
            #traceback.print_exc()
    return warp

class WhisperTranslate(object):
    def __init__(self,model_name='large',language='Chinese',compute_engine='cpu',model_path_root=os.path.dirname(os.path.abspath(__file__)),mes_q=queue.Queue()):
        self.model_name = model_name
        self.language = language
        self.mes_q = mes_q
        self.compute_engine = compute_engine
        self.model_path_root = model_path_root
        # self.result_q = result_q
        if self.model_name != 'large':
            warnings.warn("警告，选择的模型不是large，如果文件语言跟要生成的语言不一致，large模型效果最好，但是速度会最慢，建议选择large模型，如果一致，选择小模型即可")
            self.mes_q.put("警告，选择的模型不是large，如果文件语言跟要生成的语言不一致，large模型效果最好，但是速度会最慢，建议选择large模型，如果一致，选择小模型即可")

    def get_model_name(self):
        return whisper._MODELS

    def get_language_list(self):
        return [i for i in tokenizer.LANGUAGES.values()]

    def get_language_dict(self):
        return tokenizer.LANGUAGES

    def change_file_encode(self,file_path):
        if sys.getdefaultencoding() == 'utf-8':
            return
        with codecs.open(filename=file_path, mode='r', encoding='utf-8') as fi:
            data = fi.read()
            with open('temp.srt', mode='w', encoding=sys.getdefaultencoding()) as fo:
                fo.write(data)
                fo.close()
        os.remove(file_path)
        shutil.copy('temp.srt', file_path)
        os.remove('temp.srt')
        return

    def model_exist_judge(self):
        download_root = os.getenv(
            "XDG_CACHE_HOME",
            os.path.join(os.path.expanduser("~"), ".cache", "whisper")
        )
        # whisper._download(whisper._MODELS[self.model_name],download_root,False)
        download_target = os.path.join(download_root, os.path.basename(whisper._MODELS[self.model_name]))
        expected_sha256 = whisper._MODELS[self.model_name].split("/")[-2]
        if os.path.isfile(download_target):
            with open(download_target, "rb") as f:
                model_bytes = f.read()
            if hashlib.sha256(model_bytes).hexdigest() == expected_sha256:
                return '模型已存在电脑里可以直接使用'
            else:
                return '模型需要下载，请等待'

    def translate_file(self,translate_file,save_path):
        # mes = self.model_exist_judge()
        try:
            download_target = os.path.join(self.model_path_root, os.path.basename(whisper._MODELS[self.model_name]))
            if not os.path.exists(download_target) and not os.path.isfile(download_target):
                self.mes_q.put('模型保存路径不存在选取的模型，所以需要先下载模型，模型下载中，请等待！')
                model = whisper.load_model(self.model_name,device=self.compute_engine,download_root=self.model_path_root)
                self.mes_q.put('模型下载完毕')
            else:
                model = whisper.load_model(self.model_name,device=self.compute_engine,download_root=self.model_path_root)
            self.mes_q.put('开始翻译,请等待处理结束')
            result = model.transcribe(translate_file, language=self.language)
            # print(result["segment"])
            file_name = os.path.splitext(os.path.basename(translate_file))[0]
            srt_str = ''
            with open(save_path + '/{}.srt'.format(file_name), 'w',encoding='utf-8') as f:
                for i in result["segments"]:
                    f.write('{}\n'.format(i['id']))
                    f.write('{} --> {}\n'.format(time.strftime('%H:%M:%S,%d', time.gmtime(i['start'])),
                                                 time.strftime('%H:%M:%S,%d', time.gmtime(i['end']))))
                    if self.language == 'chinese':
                        f.write('{}\n\n'.format(Converter('zh-hans').convert(i['text'])))
                        srt_str += '{} --> {}:{}\n'.format(time.strftime('%H:%M:%S,%d', time.gmtime(i['start'])),
                                                     time.strftime('%H:%M:%S,%d', time.gmtime(i['end'])),Converter('zh-hans').convert(i['text']))
                    else:
                        f.write('{}\n\n'.format(i['text']))
                        srt_str += '{} --> {}:{}\n'.format(time.strftime('%H:%M:%S,%d', time.gmtime(i['start'])),
                                                           time.strftime('%H:%M:%S,%d', time.gmtime(i['end'])),
                                                           i['text'])
            # self.result_q.put([srt_str,save_path + '/{}.srt'.format(file_name)])
            self.change_file_encode(save_path + '/{}.srt'.format(file_name))
            self.mes_q.put(srt_str)
            self.mes_q.put('文件保存路径：'+save_path + '/{}.srt'.format(file_name))
            self.mes_q.put('操作完成')
        except Exception as e:
            self.mes_q.put(traceback.format_exc())
            self.mes_q.put('操作完成')

    def add_subtitle(self, translate_file,save_path):
        try:
            download_target = os.path.join(self.model_path_root, os.path.basename(whisper._MODELS[self.model_name]))
            if not os.path.exists(download_target) and not os.path.isfile(download_target):
                self.mes_q.put('模型保存路径不存在选取的模型，所以需要先下载模型，模型下载中，请等待！')
                model = whisper.load_model(self.model_name,device=self.compute_engine,download_root=self.model_path_root)
                self.mes_q.put('模型下载完毕')
            else:
                model = whisper.load_model(self.model_name, device=self.compute_engine,
                                           download_root=self.model_path_root)
            self.mes_q.put('开始添加字幕, 请等待处理结束')
            result = model.transcribe(translate_file, language=self.language)
            file_name =os.path.splitext(os.path.basename(translate_file))[0]
            if len(os.path.basename(translate_file).split('.')) == 1:
                file_type = 'mp4'
            else:
                file_type = os.path.splitext(os.path.basename(translate_file))[-1].replace('.','')
            with open(save_path+'/{}.srt'.format(file_name),'w',encoding='utf-8') as f:
                for i in result["segments"]:
                    f.write('{}\n'.format(i['id']))
                    f.write('{} --> {}\n'.format(time.strftime('%H:%M:%S,%d',time.gmtime(i['start'])),time.strftime('%H:%M:%S,%d',time.gmtime(i['end']))))
                    if self.language == 'chinese':
                        f.write('{}\n\n'.format(Converter('zh-hans').convert(i['text'])))
                    else:
                        f.write('{}\n\n'.format(i['text']))
            self.change_file_encode(save_path + '/{}.srt'.format(file_name))
            # if file_type != 'mp4':
            #     cmd = 'ffmpeg -i {} -i {} -c copy -c:s mov_text -y {}_add_subtitle.{}'.format(translate_file,save_path+'/{}.srt'.format(file_name),save_path+'/{}'.format(file_name),file_type)
            # else:
            #     cmd = 'ffmpeg -i {} -i {} -c copy -c:s srt -y {}_add_subtitle.{}'.format(translate_file,save_path+'/{}.srt'.format(file_name),save_path+'/{}'.format(file_name),file_type)
            cmd = "ffmpeg -i {} -vf subtitles=\\'{}\\' -y {}_add_subtitle.{}".format(translate_file,save_path+'/{}.srt'.format(file_name),save_path+'/{}'.format(file_name),file_type)
            result = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = result.communicate()
            if result.returncode != 0:
                for line in out.splitlines():
                    self.mes_q.put(line.decode('utf-8', 'ignore'))
                for line in err.splitlines():
                    self.mes_q.put(line.decode('utf-8', 'ignore'))
            else:
                self.mes_q.put('添加字幕成功')
            self.mes_q.put('文件保存路径：' + save_path + '/{}_add_subtitle.{}'.format(file_name,file_type))
            self.mes_q.put('操作完成')
        except Exception as e:
            self.mes_q.put(traceback.format_exc())
            self.mes_q.put('操作完成')

    def Ddiscriminate_language(self,LanguageCategoryEdit,input_file):
        try:
            self.mes_q.put('开始识别文件的语言种类，请等待处理结束')
            model = whisper.load_model(self.model_name)
            audio = whisper.load_audio(input_file)
            audio = whisper.pad_or_trim(audio)
            # make log-Mel spectrogram and move to the same device as the model
            mel = whisper.log_mel_spectrogram(audio).to(model.device)

            # detect the spoken language
            _, probs = model.detect_language(mel)
            LanguageCategoryEdit.setText(self.get_language_dict()[max(probs, key=probs.get)])
            self.mes_q.put('操作完成')
        except Exception as e:
            self.mes_q.put(traceback.format_exc())
            self.mes_q.put('操作完成')

    def monitor_voice(self):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        RECORD_SECONDS = 5
        WAVE_OUTPUT_FILENAME = "output.wav"

        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        print("* recording")

        frames = []

        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        print("* done recording")

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

