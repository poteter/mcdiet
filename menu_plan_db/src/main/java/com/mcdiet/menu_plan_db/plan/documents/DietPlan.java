package com.mcdiet.menu_plan_db.plan.documents;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@Document(collection = "dietplans") // Specify the collection name
public class DietPlan {

    @Id
    private String id; // MongoDB's ObjectId

    private String user;
    private Integer calories;
    private Integer range;
    private Integer days;
    private Integer mealsPerDay; // Adjusted to camelCase

    private List<Plan> plan;

    public DietPlan(String user, Integer calories, Integer range, Integer days, Integer mealsPerDay, List<Plan> plan) {
        this.user = user;
        this.calories = calories;
        this.range = range;
        this.days = days;
        this.mealsPerDay = mealsPerDay;
        this.plan = plan;
    }
}