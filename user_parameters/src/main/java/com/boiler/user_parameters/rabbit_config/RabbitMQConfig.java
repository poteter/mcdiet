package com.boiler.user_parameters.rabbit_config;

import org.springframework.amqp.core.Queue;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {

    public static final String QUEUE_NAME = "userParams";

    @Bean
    public Queue userParamsQueue() {
        return new Queue(QUEUE_NAME, true); // durable queue
    }
}
