package com.mcdiet.item_db.item;

import jakarta.transaction.Transactional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ItemRepo extends JpaRepository<Item, Long>{

    @Query("SELECT i.item_id from Item as i")
    public List<Long> getItemIds();

    @Query("SELECT i.item_id AS itemId, i.energy_Kcal AS energyKcal, i.food_type AS foodType FROM Item i")
    List<ItemIdFoodTypeAndEnergyKcal> getItemIdFoodTypeAndEnergyKcal();

    @Modifying
    @Transactional
    @Query("DELETE FROM Item i WHERE i.item_id = :itemId")
    void deleteByItemId(@Param("itemId") String itemId);
}