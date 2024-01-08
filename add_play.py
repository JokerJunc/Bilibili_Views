import subprocess
from PyQt5.QtCore import QThread
from functools import reduce
import hashlib
import time
import urllib.parse
import requests
from fake_useragent import UserAgent
import os

ua = UserAgent()

class RedisProxy(QThread):
    def __init__(self):
        super(RedisProxy,self).__init__()
        self.index = ''
    def openRedis(self):
        # print("你好")
        os.chdir("E:\\developer\\environment\\Redis-x64-3.2.100")
        subprocess.Popen("redis-server.exe redis.windows.conf")
class Bilibili_User_Videos(QThread):
    def __init__(self):
        super(Bilibili_User_Videos,self).__init__()
        # self.MID=MID
        self.SESSDATA = 'd8b01d70%2C1720023170%2C3b8d4%2A11CjBCI2qZfY7M9uB-6Os0X412JvYfAz9vFSKVdHAArG7hbMYNjjjMyQ1thrZ_80l0oI8SVlFLR19RUE1GdEJVNkZzZWZvdWNkSHZwYjBfTUpLN2VFS2ZOU00tNE1kZEVLNWJtZmJ1aEpnRUJKNzg4b0ptX25paGI1NWh6dWVtNjdBTnFLdVY3MVlnIIEC'
        self.headers = {
            'User-Agent': ua.random,
            'Cookie': 'SESSDATA=' + self.SESSDATA,
        }
        self.play=0
        self.needPlay = 0



    def getjson(self,url, headers=None):
        response = requests.get(url, headers=headers)
        # print(self.headers)
        # print(headers)
        if response.status_code == 200:
            json_data = response.json()
            return json_data
        else:
            return None


    def getMixinKey(self,ae):
        oe = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12,
              38, 41,
              13, 37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36,
              20, 34, 44, 52]
        le = reduce(lambda s, i: s + ae[i], oe, "")
        return le[:32]


    def encWbi(self,params_in: dict):
        params = params_in.copy()  # 加上防止改变传入字典的原值?
        resp = self.getjson("https://api.bilibili.com/x/web-interface/nav",headers=self.headers)
        # print(self.headers)
        wbi_img: dict = resp["data"]["wbi_img"]
        me = self.getMixinKey(wbi_img['img_url'].split("/")[-1].split(".")[0] + wbi_img['sub_url'].split("/")[-1].split(".")[0])
        wts = int(time.time())
        # wts = 1684940606
        params["wts"] = wts
        params = dict(sorted(params.items()))
        Ae = "&".join([f'{key}={value}' for key, value in params.items()])
        w_rid = hashlib.md5((Ae + me).encode(encoding='utf-8')).hexdigest()
        return w_rid, wts


    # 输入uid 返回投稿视频的字典列表
    def getUpVideos(self,up_uid, startpage=1, endpage=10, tid=0, keyword=''):
        up_videos = []
        for space_video_page in range(startpage, endpage + 1):  # 最多下载10页 300个视频
            time.sleep(3)  # 频率不宜过快
            space_video_search_params_dict = {'mid': up_uid,  # UP主UID
                                              'ps': 30,  # 每页的视频个数
                                              'tid': tid,  # 分区筛选号 0为不筛选
                                              'special_type': '',
                                              'pn': space_video_page,  # 页码
                                              'keyword': keyword,  # 搜索关键词
                                              'order': 'pubdate',  # 降序排序 click(播放)/stow(收藏)
                                              'platform': 'web',
                                              'web_location': 1550101,
                                              'order_avoided': 'true'
                                              }
            w_rid, wts = self.encWbi(space_video_search_params_dict)
            space_video_search_params_urlcoded = urllib.parse.urlencode(space_video_search_params_dict)
            up_videos_api = 'https://api.bilibili.com/x/space/wbi/arc/search?%s&w_rid=%s&wts=%s' % (
            space_video_search_params_urlcoded, w_rid, wts)

            space_video_search_json = self.getjson(up_videos_api, headers=self.headers)
            # print(space_video_search_json)
            if space_video_page == startpage:
                # 获取分类表 如果该页无视频则返回None
                # tlist = space_video_search_json['data']['list']['tlist']
                # for each in tlist :
                #     print('tid:',tlist[each]['tid'],'类名:',tlist[each]['name'],'数目:',tlist[each]['count'])

                # 获取视频总数 如果该页无视频则返回0
                space_video_num = space_video_search_json['data']['page']['count']

            if space_video_search_json['data']['list']['vlist']:  # 如果不存在视频则为空列表[]
                thisPageVideos = space_video_search_json['data']['list']['vlist']
                thisPageVideos.reverse()
                thisPageVideos_num = len(thisPageVideos)
                for each_video_id in range(thisPageVideos_num):
                    each_video_info = thisPageVideos[thisPageVideos_num - each_video_id - 1]
                    play = each_video_info['play']
                    if(play < 300):
                        self.needPlay += 1
                    # up_videos格式
                        up_videos.append({'title': each_video_info['title'],
                                          'bvid': each_video_info['bvid'],
                                          'play':each_video_info['play'],
                                          'author': each_video_info['author'],
                                          'mid': each_video_info['mid'],
                                          'created': each_video_info['created'],
                                          })
                if self.needPlay ==0:
                    return None
                if space_video_page == endpage:
                    print('[√] 已获取 [%d/%d] 个视频' % (len(up_videos), space_video_num))
                    return up_videos
            else:  # 这页不存在视频
                print('[√] 已获取 [%d/%d] 个视频' % (len(up_videos), space_video_num))
                return up_videos


    def dic2bvid(self,data):
        bvid_list = [item['bvid'] for item in data] or ''
        return bvid_list


    def getBvidList(self,uid):
        data = self.getUpVideos(uid)
        if data is None:
            return None
        else:
            return self.dic2bvid(data)

class playback_quantity(QThread):
    def __init__(self,bvid):
        super(playback_quantity,self).__init__()
        # 视频bv号放这里，格式如下
        self.bvid = bvid

        # 代理池地址，项目可见https://github.com/jhao104/proxy_pool

        self.getproxy = "http://127.0.0.1:5010/get/"
        self.deleteproxy = "http://127.0.0.1:5010/delete/?proxy={}"
        self.proxynum = "http://127.0.0.1:5010/count"

        self.url = "http://api.bilibili.com/x/click-interface/click/web/h5"

        self.headers = {
            # 'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.bilibili.com',
            'Connection': 'keep-alive'
        }
        self.reqdata = []


    def forBvid(self):
        for bv in self.bvid:
            stime = str(int(time.time()))

            resp = requests.get("https://api.bilibili.com/x/web-interface/view?bvid={}".format(bv), headers=self.headers)
            # print(resp.text)
            getdata = resp.json()["data"]
            # print(getdata)
            data = {
                'aid': getdata["aid"],
                'cid': getdata["cid"],
                "bvid": bv,
                'part': '1',
                'mid': getdata["owner"]["mid"],
                'lv': '6',
                "stime": stime,
                'jsonp': 'jsonp',
                'type': '3',
                'sub_type': '0',
                'title': getdata["title"]
            }
            self.reqdata.append(data)

    def run(self):
        num = 0
        while int(requests.get(self.proxynum).json().get("count")) != 0:

            resp = requests.get(self.getproxy).json().get("proxy")
            for data in self.reqdata:
                try:
                    stime = str(int(time.time()))
                    data["stime"] = stime
                    self.headers['User-Agent'] = ua.random
                    self.headers["referer"] = "http://www.bilibili.com/video/{}/".format(data.get("bvid"))

                    proxy = {
                        "http": "http://{}".format(resp)
                    }

                    requests.post(self.url, headers=self.headers, data=data, proxies=proxy, timeout=5)
                    # print(headers)
                except Exception as e:
                    print("")
            # requests.get(deleteproxy.format(resp))
            num += 1
            print("当前已刷播放量{}".format(num))

        print("无可用代理")

if __name__ == '__main__':
# test get BvidList
    bilibili_user_video_parse = Bilibili_User_Videos()
    table_list = bilibili_user_video_parse.getBvidList('485111228')

    if table_list is None:
        print('没有需要播放的视频')
    else:
        print('以下视频播放量未超过100', table_list)
        bilibili_play = playback_quantity(table_list)
        bilibili_play.forBvid()
        bilibili_play.run()

