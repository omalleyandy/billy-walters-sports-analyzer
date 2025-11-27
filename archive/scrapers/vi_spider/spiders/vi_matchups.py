import scrapy


class VIMatchupsSpider(scrapy.Spider):
    name = "vi_matchups"
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1.0,
    }
    start_urls = ["https://www.vegasinsider.com/college-football/matchups/"]

    def parse(self, response):
        # TODO: refine selectors to current DOM
        for href in response.css("a.viGameCard::attr(href)").getall():
            yield response.follow(href, callback=self.parse_matchup)

    def parse_matchup(self, response):
        title = response.css("h1::text").get(default="").strip()
        yield {"title": title, "url": response.url}
