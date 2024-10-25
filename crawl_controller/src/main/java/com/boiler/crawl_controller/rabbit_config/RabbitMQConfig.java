package com.boiler.crawl_controller.rabbit_config;

import org.springframework.amqp.core.Queue;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {

    public static final String QUEUE_NAME = "runTrigger";

    @Bean
    public Queue userParamsQueue() {
        return new Queue(QUEUE_NAME, true); // durable queue
    }
}
