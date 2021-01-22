import requests
import yaml
import urllib3
import logging
import logging.config
import os
from bs4 import BeautifulSoup
import math

def setup_logging(default_path= "logging.yaml",default_level=logging.INFO,env_key='LOG_CFG'):
    path = default_path
    value = os.getenv(env_key,None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path,'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',filename='example.log',level=default_level)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
setup_logging()

comment_base_url = 'https://api.bilibili.com/x/v2/reply'
base_video_url = 'https://www.bilibili.com/video'
video_id = 'BV1EA411p7Jx'
url = base_video_url + '/' + video_id

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:79.0) Gecko/20100101 Firefox/79.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': 'www.bilibili.com',
    'Cookie': "finger=-1486130818; _uuid=F5FAF7E1-C8C8-F472-E2C6-AC83A892242C40223infoc; buvid3=E5AFB9D6-9B8D-442C-87CA-5F4BC7565CCF155830infoc; LIVE_BUVID=AUTO1915931692335610; PVID=1; sid=c3rbjvad; CURRENT_FNVAL=80; rpdid=|(umY))kulm|0J'ulmJuYmmY|; bp_video_offset_343639121=482743170045599079; bp_t_offset_343639121=482743170045599079; blackside_state=1; CURRENT_QUALITY=80; LIVE_PLAYER_TYPE=2; fingerprint3=e2f310c53fbf9bc6f4733d1d1d187782; fingerprint=2796c2e05867f8bd7e4bc5ed1e18eabe; fingerprint_s=babde9c0ac0f0bdc066059f33197d910; buivd_fp=E5AFB9D6-9B8D-442C-87CA-5F4BC7565CCF155830infoc; buvid_fp_plain=BA66943F-BB62-457E-2458-168ED0F916AC40082infoc; buvid_fp=E5AFB9D6-9B8D-442C-87CA-5F4BC7565CCF155830infoc; DedeUserID=343639121; DedeUserID__ckMd5=8c3479ebe92326b9; SESSDATA=0830a3f9%2C1625114780%2C9453b*11; bili_jct=fdf24ae6bec8dafa95a047982f87328e; finger=-1486130818"
}


def start():
    crawl_video(url,video_id)


def get_video_av_id(html_text):
    '''获取视频av号
    :param html_text: raw html text

    :return: video av id.

    :rtype: int.
    '''
    soup = BeautifulSoup(html_text,'lxml')
    # 评论接口地址：https://api.bilibili.com/x/v2/reply?pn=1&type=1&oid=416272888&sort=2&_=1611238129455
    # 上面接口中，416272888 是视频av号 查看网页源码即可看到如下标签：
    #  <meta data-vue-meta="true" itemprop="url" content="https://www.bilibili.com/video/av416272888/">
    # 需要从此标签中提取视频av号
    return soup.select('meta[data-vue-meta="true"][itemprop="url"]')[0]['content'].rstrip('/').split('/')[-1].replace('av','')

def get_comment_url(av_id,pn = 1):
    '''获取视频评论地址
    :param av_id: av id of video

    :param pn: comments page number of video

    :return: video comment url.
    
    :rtype: string.
    '''
    return '{}?pn={page}&type=1&oid={av_id}'.format(comment_base_url,av_id=av_id,pn = pn)

def get_comment_pages_count(response):
    '''获取评论页数
    根据接口返回的数据进行计算：
        code	0
        message	"0"
        ttl	1
        data	
            page	
                num	1
                size	20
                count	1278
                acount	1532
    
    计算公式：page = math.floor(count /  size)
    :param res: response of comment api interface

    count可能会不断变化，因为可能会不断有人评论

    :return: pages count of video comments.

    :rtype: int.
    '''
    return math.floor(response['data']['page']['count'] / response['data']['page']['size'])

def crawl_video(video_url,video_id):
    r = requests.get(video_url,verify=False, headers=headers)
    if r.status_code != 200:
        logging.error(r)
    with open('{}.html'.format(video_id),'w',encoding='utf-8') as f:
        f.write(r.text)
    av = get_video_av_id(r.text)
    print(av)

def crawl_video_comment():
    '''爬取视频评论'''
    
    comment_url = 'https://api.bilibili.com/x/v2/reply?pn={page}&type=1&oid=331340884&sort=2&_=1611237114129'.format(page = 1)
    
def crawl_video_barrage():
    '''爬取视频弹幕'''
    pass

if __name__ == '__main__':
    start()