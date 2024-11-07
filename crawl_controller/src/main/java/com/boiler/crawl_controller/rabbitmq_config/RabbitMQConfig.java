package com.boiler.crawl_controller.rabbitmq_config;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.FanoutExchange;
import org.springframework.amqp.core.Queue;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {

    public static final String QUEUE_NAME = "runTrigger";
    public static final String FANOUT_EXCHANGE_NAME = "runTriggerFanoutExchange";

    // Declare a durable queue
    @Bean
    public Queue userParamsQueue() {
        return new Queue(QUEUE_NAME, true);
    }

    // Declare a fanout exchange
    @Bean
    public FanoutExchange fanoutExchange() {
        return new FanoutExchange(FANOUT_EXCHANGE_NAME, true, false); // durable, non-auto-delete
    }

    // Bind the queue to the fanout exchange
    @Bean
    public Binding binding(Queue userParamsQueue, FanoutExchange fanoutExchange) {
        return BindingBuilder.bind(userParamsQueue).to(fanoutExchange);
    }
}
