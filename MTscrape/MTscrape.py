import multiprocessing, requests
from bs4 import BeautifulSoup
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse

URL_base = "https://www.tevetron.hr/hr/webshop/ic/16/"

class MTWebCrawler:

    def __init__(self, URL_base) -> None:
        self.URL_base = URL_base
        self.rootURL = '{}://{}/{}'.format(urlparse(self.URL_base).scheme,
                                        urlparse(self.URL_base).netloc,
                                        urlparse(self.URL_base).path)
        self.pool = ThreadPoolExecutor(max_workers=8)
        self.scrapedPages = set([])
        self.crawlQueue = Queue()
        self.crawlQueue.put(self.URL_base)
        print(f'Root URL initialized to {self.rootURL}')

    def scrapePage(self, url):
        try:
            res = requests.get(url, timeout=(3, 30))
            return res
        except requests.RequestException:
            return

    def runWebCrawler(self):
        while True:
            try:
                targetURL = self.crawlQueue.get(timeout=60)

                if targetURL not in self.scrapedPages:
                    print("Scraping URL: {}".format(targetURL))
                    self.scrapedPages.add(targetURL)
                    job = self.pool.submit(self.scrapePage, targetURL)
                    job.add_done_callback(self.postScrapeCallback)
            except Empty:
                return
            except Exception as e:
                print(e)
                continue
    
    def scrapeInfo(self, html):
        # multiple parser options: html5lib, html.parser, lxml
        soup = BeautifulSoup(html, "lxml")
        products = soup.find_all("div", class_="product-inner")
        
        for item in products:
            productNumber = item.find("h3").text.strip()
            productPrice = item.find("span", class_ = "cprice1").text.strip()
            productPackage = item.find("h4").text.strip()
            productAvailability = item.find("span", class_="raspolozivost_2 da").text.strip() if item.find("span", class_="raspolozivost_2 da") != None else item.find("span", class_="raspolozivost_2 ne").text.strip()
            
        print(f'PN: {productNumber} Price: {productPrice}')
        return
    
    def parseLinks(self, html):
        soup = BeautifulSoup(html, 'lxml')
        Anchor_Tags = soup.find_all('a', href=True)
        
        for link in Anchor_Tags:
            url = link['href']

            if self.URL_base in url:

                url = urljoin(self.rootURL, url)
                
                if url not in self.scrapedPages:
                    self.crawlQueue.put(url)

            # if url.startswith('/') or url.startswith(self.rootURL):
            #     url = urljoin(self.rootURL, url)
                
            #     if url not in self.scrapedPages:
            #         self.crawlQueue.put(url)

    def postScrapeCallback(self, res):
        result = res.result()
        
        if result and result.status_code == 200:
            self.parseLinks(result.text)
            self.scrapeInfo(result.text)

    def info(self):
        print('\n Seed URL is: ', self.URL_base, '\n')
        print('Scraped pages are: ', self.scrapedPages, '\n')

if __name__ == '__main__':
    cc = MTWebCrawler(URL_base)
    cc.runWebCrawler()
    cc.info()