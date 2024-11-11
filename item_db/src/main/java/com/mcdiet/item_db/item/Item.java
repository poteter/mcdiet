package com.mcdiet.item_db.item;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Getter
@Setter
@NoArgsConstructor
@Table(name = "item")
public class Item {

    @Id
    @Column(name = "itemId")
    private String item_id = "";

    @Column(name = "itemName")
    private String item_name;

    @Column(name = "energyKcal")
    private int energy_Kcal;

    @Column(name = "foodType")
    private String food_type;

    public Item(String itemName, int kcal, String item_id, String food_type) {
        this.food_type = food_type;
        this.item_name = itemName;
        this.energy_Kcal = kcal;
        this.item_id = item_id;
    }
}