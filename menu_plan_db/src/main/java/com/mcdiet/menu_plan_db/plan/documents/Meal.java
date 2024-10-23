package com.mcdiet.menu_plan_db.plan.documents;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
public class Meal {

    private List<Item> items;
    private Integer totalCaloriesMeal;

    public Meal(List<Item> items, Integer totalCaloriesMeal) {
        this.items = items;
        this.totalCaloriesMeal = totalCaloriesMeal;
    }
}