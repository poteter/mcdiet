package com.boiler.crawl_controller.control;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RequestMapping("/api/crawl")
@RestController
public class CrawlController {
    private final CrawlService crawlService;

    @Autowired
    public CrawlController(final CrawlService crawlService) {
        this.crawlService = crawlService;
    }

    @PostMapping("/run")
    public void run() {
        crawlService.runCrawl();
    }
}
