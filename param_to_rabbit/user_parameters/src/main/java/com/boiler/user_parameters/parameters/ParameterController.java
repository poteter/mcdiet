package com.boiler.user_parameters.parameters;

import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/user")
public class ParameterController {

    private final ParameterService parameterService;

    @Autowired
    public ParameterController(final ParameterService parameterService) {
        this.parameterService = parameterService;
    }

    @PostMapping
    public void sendParamsToRabbit(@Valid @RequestBody ParameterDTO parameterDTO) {
        parameterService.sendToRabbit(parameterDTO);
    }
}
