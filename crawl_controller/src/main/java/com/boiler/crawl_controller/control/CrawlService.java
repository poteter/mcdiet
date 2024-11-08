package com.boiler.crawl_controller.control;

import com.boiler.crawl_controller.rabbitmq_config.RabbitMQConfig;
import org.springframework.amqp.core.FanoutExchange;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class CrawlService {

    private final RabbitTemplate rabbitTemplate;
    private final FanoutExchange fanoutExchange;

    @Autowired
    public CrawlService(RabbitTemplate rabbitTemplate, FanoutExchange fanoutExchange) {
        this.rabbitTemplate = rabbitTemplate;
        this.fanoutExchange = fanoutExchange;
    }

    public void runCrawl() {
        rabbitTemplate.convertAndSend(fanoutExchange.getName(), "", "run");
    }
}
