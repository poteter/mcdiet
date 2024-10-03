package com.boiler.user_parameters.parameters;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class ParameterDTO {

    @NotNull(message = "NumberValue cannot be null.")
    @Positive(message = "NumberValue must be a positive number.")
    private Integer calories;

    @Positive(message = "NumberValue must be a positive number.")
    private Integer range;
}