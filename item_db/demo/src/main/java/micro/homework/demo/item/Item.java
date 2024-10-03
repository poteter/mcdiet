package micro.homework.demo.item;

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
    private Long item_id = 0L;

    @Column(name = "itemName")
    private String item_name;

    @Column(name = "energyKcal")
    private int energy_Kcal;

    public Item(String itemName, int kcal, Long item_id) {
        this.item_name = itemName;
        this.energy_Kcal = kcal;
        this.item_id = item_id;
    }
}
