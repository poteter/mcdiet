package com.mcdiet.item_db.item;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.TimeoutException;

@Service
public class ItemService {
    private final ItemRepo itemRepo;

    @Autowired
    public ItemService(ItemRepo itemRepo) {
        this.itemRepo = itemRepo;
    }

    public List<Item> getAll(){
        return itemRepo.findAll();
    }

    public List<ItemIdFoodTypeAndEnergyKcal> fetchFoodTypeItemIdsAndEnergy() {
        return itemRepo.getItemIdFoodTypeAndEnergyKcal();
    }

    public void deleteItemByCode(String code) {
        itemRepo.deleteByItemId(code);
    }

    public List<Long> getItemCodes(){
        return itemRepo.getItemIds();
    }

    public Item getItemById(Long id) {
        return itemRepo.findById(id).orElse(null);
    }

    public List<Item> getAllItems(int pageNumber) {
        return itemRepo.findAll(PageRequest.of(pageNumber, 10)).stream().toList();
    }

    public Item saveItem(Item item) throws IOException, TimeoutException {
        return itemRepo.save(item);
    }
}