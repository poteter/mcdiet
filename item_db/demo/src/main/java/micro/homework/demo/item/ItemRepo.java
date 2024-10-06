package micro.homework.demo.item;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ItemRepo extends JpaRepository<Item, Long>{

    @Query("SELECT i.item_id from Item as i")
    public List<Long> getItemIds();

    @Query("SELECT i.item_id AS itemId, i.energy_Kcal AS energyKcal, i.food_type AS foodType FROM Item i")
    List<ItemIdFoodTypeAndEnergyKcal> getItemIdFoodTypeAndEnergyKcal();
}
