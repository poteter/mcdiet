package com.boiler.user_parameters.parameters;

import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/user")
public class ParameterController {

    private final ParameterService parameterService;

    @Autowired
    public ParameterController(final ParameterService parameterService) {
        this.parameterService = parameterService;
    }

    @GetMapping("/test")
    public String test() {
        return "test";
    }

    @PostMapping
    public void sendParamsToRabbit(@Valid @RequestBody ParameterDTO parameterDTO) {
        parameterService.sendToRabbit(parameterDTO);
    }
}
