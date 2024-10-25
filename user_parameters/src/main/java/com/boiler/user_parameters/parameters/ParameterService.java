package com.boiler.user_parameters.parameters;

import com.boiler.user_parameters.rabbit_config.RabbitMQConfig;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class ParameterService {

    private final RabbitTemplate rabbitTemplate;
    private final ObjectMapper objectMapper;

    @Autowired
    public ParameterService(RabbitTemplate rabbitTemplate, ObjectMapper objectMapper) {
        this.rabbitTemplate = rabbitTemplate;
        this.objectMapper = objectMapper;
    }

    public void sendToRabbit(ParameterDTO parameterDTO) {
        String message = convertDtoToMessage(parameterDTO);
        rabbitTemplate.convertAndSend(RabbitMQConfig.QUEUE_NAME, message);
    }

    private String convertDtoToMessage(ParameterDTO parameterDTO) {
        try {
            return objectMapper.writeValueAsString(parameterDTO);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Error converting ParameterDTO to JSON", e);
        }
    }
}
