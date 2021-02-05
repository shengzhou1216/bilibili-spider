import requests
import yaml
import urllib3
import logging
import logging.config
import os
from bs4 import BeautifulSoup
import math
import json
import re
import base64
from db import insert_video
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def setup_logging(default_path="logging.yaml", default_level=logging.INFO, env_key='LOG_CFG'):
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(format='%(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p', filename='example.log', level=default_level)


setup_logging()

logging = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_video_url = 'https://www.bilibili.com/video'
replay_base_url = 'https://api.bilibili.com/x/v2/reply'
dm_base_url = 'http://api.bilibili.com/x/v2/dm/web/seg.so'
video_id = 'BV1EA411p7Jx'
url = base_video_url + '/' + video_id

video_headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:79.0) Gecko/20100101 Firefox/79.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': 'www.bilibili.com',
    'Cookie': "finger=-1486130818; _uuid=F5FAF7E1-C8C8-F472-E2C6-AC83A892242C40223infoc; buvid3=E5AFB9D6-9B8D-442C-87CA-5F4BC7565CCF155830infoc; LIVE_BUVID=AUTO1915931692335610; PVID=1; sid=c3rbjvad; CURRENT_FNVAL=80; rpdid=|(umY))kulm|0J'ulmJuYmmY|; bp_video_offset_343639121=482743170045599079; bp_t_offset_343639121=482743170045599079; blackside_state=1; CURRENT_QUALITY=80; LIVE_PLAYER_TYPE=2; fingerprint3=e2f310c53fbf9bc6f4733d1d1d187782; fingerprint=2796c2e05867f8bd7e4bc5ed1e18eabe; fingerprint_s=babde9c0ac0f0bdc066059f33197d910; buivd_fp=E5AFB9D6-9B8D-442C-87CA-5F4BC7565CCF155830infoc; buvid_fp_plain=BA66943F-BB62-457E-2458-168ED0F916AC40082infoc; buvid_fp=E5AFB9D6-9B8D-442C-87CA-5F4BC7565CCF155830infoc; DedeUserID=343639121; DedeUserID__ckMd5=8c3479ebe92326b9; SESSDATA=0830a3f9%2C1625114780%2C9453b*11; bili_jct=fdf24ae6bec8dafa95a047982f87328e; finger=-1486130818"
}

reply_headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:79.0) Gecko/20100101 Firefox/79.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
}


def start():
    crawl_video(url)


def get_video_info(html_text):
    '''获取视频基本信息
    :param html_text: raw html text

    :return: video base info

    :rtype: dict. containes video's aid id,title,description and so on.
    '''
    soup = BeautifulSoup(html_text, 'lxml')
    # 评论接口地址：https://api.bilibili.com/x/v2/reply?pn=1&type=1&oid=416272888&sort=2&_=1611238129455
    # 上面接口中，416272888 是视频av号 查看网页源码即可看到如下标签：
    #  <meta data-vue-meta="true" itemprop="url" content="https://www.bilibili.com/video/av416272888/">
    # 需要从此标签中提取视频av号
    aid = soup.select('meta[data-vue-meta="true"][itemprop="url"]')[
        0]['content'].rstrip('/').split('/')[-1].replace('av', '')
    title = soup.select('meta[data-vue-meta="true"][itemprop="name"]')[
        0]['content'].replace('_哔哩哔哩 (゜-゜)つロ 干杯~-bilibili', '')
    description = soup.select(
        'meta[data-vue-meta="true"][itemprop="description"]')[0]['content']
    keywords = soup.select(
        'meta[data-vue-meta="true"][itemprop="keywords"]')[0]['content']
    author = soup.select(
        'meta[data-vue-meta="true"][itemprop="author"]')[0]['content']
    image = soup.select(
        'meta[data-vue-meta="true"][itemprop="image"]')[0]['content']
    url = soup.select(
        'meta[data-vue-meta="true"][itemprop="url"]')[0]['content']
    m = re.search('cid=(\w+)',html_text)
    cid = m.groups()[0]
    return {
        'aid': aid,
        'cid': cid,
        'title': title,
        'description': description,
        'keywords': keywords,
        'author': author,
        'image': image,
        'url': url,
    }


def get_reply_url(aid, pn=1):
    '''获取视频评论地址
    :param aid: aid id of video

    :param pn: replies page number of video

    :return: video reply url.

    :rtype: string.
    '''
    return '{}?pn={page}&type=1&oid={aid}'.format(replay_base_url, aid=aid, page=pn)


def get_dm_url(aid,cid,segment_index = 1):
    '''获取弹幕地址
    :param: aid of video

    :param cid: cid of video
    
    :return: dm url 

    :rtype: string.
    '''
    # "?type=1&oid=" + a.cid + "&pid=" + a.aid + "&segment_index=" + i;
    return '{}?type=1&oid={oid}&pid={pid}&segment_index={segment_index}'.format(dm_base_url,oid=cid,pid=aid,segment_index=segment_index)


def get_reply_pages_count(response):
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
    :param res: response of reply api interface

    count可能会不断变化，因为可能会不断有人评论

    :return: pages count of video replies.

    :rtype: int.
    '''
    return math.floor(response['data']['page']['count'] / response['data']['page']['size'])


def crawl_video(video_url):
    '''爬取视频
    :param video_url: url of video 
    '''
    r = requests.get(video_url, verify=False, headers=video_headers)
    video_id = video_url.split('/')[-1]
    if r.status_code != 200:
        logging.exception(r)
    with open('{}.html'.format(video_id), 'w', encoding='utf-8') as f:
        f.write(r.text)
    video = get_video_info(r.text)
    # video['replies'] = get_video_reply(video['aid'])
    video['dm'] = get_video_dm(video['aid'],video['cid'])
    # insert_video(video)


def get_video_reply(aid):
    '''爬取视频评论
    :param aid: aid id of video (aid id is not video id)
    '''
    reply_url = get_reply_url(aid)
    logging.info("reply_url: %s", reply_url)
    r = requests.get(reply_url, verify=False, headers=reply_headers)
    res = json.loads(r.text)
    pages = get_reply_pages_count(res)
    logging.info("replies pages count: %d", pages)
    video = res['data']
    # from page 2 to get replies
    for page in range(2, pages+1):
        reply_url = get_reply_url(aid, page)
        logging.info("reply_url: %s", reply_url)
        r = requests.get(reply_url, verify=False, headers=reply_headers)
        res = json.loads(r.text)
        video['replies'] += res['data']['replies']
    return video


def get_video_dm(aid,cid):
    '''爬取视频弹幕
    '''
    driver = webdriver.Firefox()
    driver.get("https://www.bilibili.com/video/BV1EA411p7Jx")
    zhankai = WebDriverWait(driver,10).until(
        EC.presence_of_element_located(By.CSS_SELECTOR,'span.bui-collapse-arrow-test')
    )
    zhankai.click()

if __name__ == '__main__':
    start()
