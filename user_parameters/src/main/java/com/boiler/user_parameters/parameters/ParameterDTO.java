package com.boiler.user_parameters.parameters;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
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

    @Positive(message = "NumberValue must be a positive number.")
    private Integer mealsPerDay;

    @Positive(message = "NumberValue must be a positive number.")
    private Integer days;

    @Pattern(regexp = "^[0-9a-zA-ZåÅøØæÆ]+$", message = "User must contain only numbers 0-9 and letters aA-åÅ.")
    private String user;
}