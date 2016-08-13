# -*- coding: utf-8 -*-
import scrapy
import json
import os
import sys  
reload(sys)  
sys.setdefaultencoding('utf8')  

class MMSpider(scrapy.Spider):
    name = "mm_crawler"
    #allowed_domains = ["mm.taobao.com"]
    url_fmt = "https://mm.taobao.com/tstar/search/tstar_model.do?_input_charset=utf-8&q=&viewFlag=A&sortType=default&searchStyle=&searchRegion=city%%3A&searchFansNum=&currentPage=%s&pageSize=100"
    start_urls = [
        url_fmt%(1),
    ]
    mm_crawled = set()
    ouput_root = 'data/mm_crawled/'

    def parse(self, response):
        data = json.loads(response.body.decode('gbk').encode('utf-8'))
        if data.get('message', '') == 'search success!' and data.get('data', None):
            data = data['data']
            total_page = data['totalPage']
            
            for idx in xrange(1, total_page+1):
                print('crawling list page ' + MMSpider.url_fmt%(idx)) 
                yield scrapy.Request(MMSpider.url_fmt%(idx), callback=self.parse_list_page)

    def parse_list_page(self, response):
        data = json.loads(response.body.decode('gbk').encode('utf-8'))
        
        if data.get('message', '') == 'search success!' and data.get('data', None):
            data = data['data']
            l = data.get('searchDOList', [])
            for avt in l:
                if avt['userId'] in self.mm_crawled:
                    return
                self.mm_crawled.add(avt['userId'])
                output_dir = self.ouput_root + str(avt['userId']) + '/'
                try:
                    os.makedirs(output_dir)
                except OSError:
                    pass
                with open(output_dir + 'info.json', 'w+') as fp:
                    fp.write(json.dumps(avt, ensure_ascii=False))
                yield scrapy.Request('http:'+avt['avatarUrl'], callback=lambda response, output_dir=output_dir:self.save_img(response, output_dir))
                yield scrapy.Request('http:'+avt['cardUrl'], callback=lambda response, output_dir=output_dir:self.save_img(response, output_dir))
                yield scrapy.Request('https://mm.taobao.com/self/aiShow.htm?userId=%s'%(avt['userId']), callback=lambda response, output_dir=output_dir:self.parse_detail_page(response, output_dir))

    def save_img(self, response, output_dir, img_name=None):
        print('save_img %s %s %s %s'%(response, output_dir, img_name, response.url.split("/")[-1]))
        if not img_name:
            img_name = response.url.split("/")[-1]
        with open(output_dir + img_name, 'wb+') as fp:
            fp.write(response.body)

    def parse_detail_page(self, response, output_dir):
        for each in response.xpath('//*[@id="J_ScaleImg"]/*/img/@src').extract():
            print('http:'+each)
            yield scrapy.Request('http:'+each, callback=lambda response, output_dir=output_dir:self.save_img(response, output_dir))
