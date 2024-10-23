package com.mcdiet.menu_plan_db.plan.documents;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
public class Plan {

    private String date;
    private List<Meal> meals;
    private Integer totalCaloriesDay;

    public Plan(String date, List<Meal> meals, Integer totalCaloriesDay) {
        this.date = date;
        this.meals = meals;
        this.totalCaloriesDay = totalCaloriesDay;
    }
}