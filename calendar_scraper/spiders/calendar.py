import scrapy
from scrapy.crawler import CrawlerProcess
import json
import os
import re

class CalendarSpider(scrapy.Spider):
    name = 'calendar'
    allowed_domains = ['wku.ac.kr']
    custom_settings = {
        'DOWNLOAD_DELAY': 3.0,  # 3초 지연
    }

    def start_requests(self):
        base_url = 'https://www.wku.ac.kr/calendar/page/{}/?cal_year=2024&cal_month={}#038;cal_month={}'
        months_with_multiple_pages = [1, 2, 5, 6]

        for month in range(1, 13):
            if month in months_with_multiple_pages:
                for page in range(1, 3):
                    yield scrapy.Request(url=base_url.format(page, month, month), callback=self.parse, meta={'month': month, 'page': page})
            else:
                yield scrapy.Request(url=base_url.format(1, month, month), callback=self.parse, meta={'month': month, 'page': 1})

    def parse(self, response):
        month = response.meta['month']
        page = response.meta['page']
        
        wrap = response.xpath('//div[@id="wrap"]')
        container = wrap.xpath('.//section[@id="container"]')
        content = container.xpath('.//article[@id="content"]')
        calendar_table = content.xpath('.//table[contains(@class, "calendarTable")]')

        # Extract and clean thead elements
        thead = calendar_table.xpath('.//thead/tr/th/text()').getall()
        thead = [re.sub(r'\s+', ' ', th).strip() for th in thead]

        # Extract and clean tbody elements
        tbody = calendar_table.xpath('.//tbody/tr')
        rows = []
        for tr in tbody:
            row = {
                'td_texts': [re.sub(r'\s+', ' ', td).strip() for td in tr.xpath('.//td/text()').getall()],
                'td_a_texts': [re.sub(r'\s+', ' ', td).strip() for td in tr.xpath('.//td/a/text()').getall()],
                'td_p_texts': [re.sub(r'\s+', ' ', td).strip() for td in tr.xpath('.//td/p/text()').getall()]
            }
            rows.append(row)

        # Structure data in dictionary
        data = {
            'month': month,
            'page': page,
            'thead': thead,
            'tbody': rows,
        }

        # Save data as json file in the corresponding month's file
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save file path for all months, including single-page months
        filepath = os.path.join(output_dir, f'calendar_2024_month_{month}_page_{page}.json')

        # Overwrite the file with new data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([data], f, ensure_ascii=False, indent=4)

        self.log(f'Saved data to {filepath}')

# To run the spider
process = CrawlerProcess()
process.crawl(CalendarSpider)
process.start()
