package com.boiler.user_parameters.parameters;

import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.util.concurrent.TimeoutException;

@Service
public class ParameterService {
    private final static String QUEUE_NAME = "userParams";

    public void sendToRabbit(ParameterDTO parameterDTO) {
        String message = convertDtoToMessage(parameterDTO);
        sendMessage(message);
    }

    private void sendMessage(String message) {
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        try (Connection connection = factory.newConnection();
             Channel channel = connection.createChannel()) {
            channel.queueDeclare(QUEUE_NAME, true, false, false, null);
            channel.basicPublish("", QUEUE_NAME, null, message.getBytes());
        } catch (IOException | TimeoutException e) {
            throw new RuntimeException(e);
        }
    }

    private String convertDtoToMessage(ParameterDTO parameterDTO) {
        ObjectMapper objectMapper = new ObjectMapper();
        try {
            return objectMapper.writeValueAsString(parameterDTO);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Error converting ParameterDTO to JSON", e);
        }
    }
}
