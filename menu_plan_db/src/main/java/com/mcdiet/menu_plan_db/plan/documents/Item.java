package com.mcdiet.menu_plan_db.plan.documents;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class Item {

    private Integer energyKcal;
    private String foodType;
    private String itemId;

    public Item(Integer energyKcal, String foodType, String itemId) {
        this.energyKcal = energyKcal;
        this.foodType = foodType;
        this.itemId = itemId;
    }
}