import scrapy
from scrapy.selector import Selector
from scrapy.crawler import CrawlerProcess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from shutil import which
from time import sleep

with open("USA Location URLs.txt") as f:
    URLs = f.readlines()


class AmazonJobSpider(scrapy.Spider):
    name = "Amazon Job Spider"

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': 'Data Extracted.csv',
    }

    def __init__(self):
        chromeOptions = Options()
        chromeOptions.add_argument("--headless")
        chromePath = which("chromedriver")
        self.driver = webdriver.Chrome(executable_path=chromePath, options=chromeOptions)
        self.driver.maximize_window()

    def start_requests(self):
        for url in URLs:
            offset = 0
            offsetLimit = 0
            while offset <= offsetLimit:
                self.driver.get(url.strip() + "?offset=" + str(offset))
                sleep(5)
                html = self.driver.page_source
                response = Selector(text=html)
                jobs = response.css("div.job-tile > a::attr(href)").extract()

                if offset == 0:
                    if response.css("div.pagination-control > button"):
                        pagination = response.css("div.pagination-control > button::text").extract()
                        pagination = pagination[-1]
                        offsetLimit = (int(pagination) * 10) + 10
                offset += 10

                for job in jobs:
                    yield scrapy.Request(url="https://amazon.jobs" + job,
                                         callback=self.parse, dont_filter=True,
                                         headers={
                                             'USER-AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                                                           "Chrome/81.0.4044.138 Safari/537.36",
                                         },
                                         )

    def parse(self, response):
        title = response.css("h1.title::text").extract_first()

        jobID = response.css("div.details-line > p::text").extract_first()
        jobID = jobID.split(":")[-1]
        jobID = jobID.split("|")[0]

        loc = response.css("div.association.location-icon > div > a::text").extract_first()
        if not loc:
            loc = response.css("div.association.location-icon > div > p::text").extract_first()

        desc = response.css("div.section.description > p::text").extract()
        desc = "\n\n".join(desc)

        basicQ = response.css("div.section:nth-of-type(1) > p::text").extract()
        basicQ = "\n".join(basicQ)

        prefQ = response.css("div.section:nth-of-type(2) > p::text").extract()
        prefQ = "\n".join(prefQ)

        yield {
            "Title": title.strip(),
            "Job ID": jobID.strip(),
            "Location": loc.strip(),
            "Description": desc.strip(),
            "Basic Qualifications": basicQ,
            "Preferred Qualifications": prefQ,
            "Job URL": response.url,
        }


process = CrawlerProcess()
process.crawl(AmazonJobSpider)
process.start()
