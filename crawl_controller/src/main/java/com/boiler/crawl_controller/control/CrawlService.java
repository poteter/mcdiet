package com.boiler.crawl_controller.control;

import com.boiler.crawl_controller.rabbitmq_config.RabbitMQConfig;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class CrawlService {

    private final RabbitTemplate rabbitTemplate;

    @Autowired
    public CrawlService(RabbitTemplate rabbitTemplate) {
        this.rabbitTemplate = rabbitTemplate;
    }

    public void runCrawl() {
        rabbitTemplate.convertAndSend(RabbitMQConfig.FANOUT_EXCHANGE_NAME, "run");
    }
}
