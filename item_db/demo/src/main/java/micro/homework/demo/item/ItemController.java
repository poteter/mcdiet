package micro.homework.demo.item;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.TimeoutException;

@RestController
@RequestMapping("/api/item")
public class ItemController {
    private final ItemService itemService;

    @Autowired
    public ItemController(final ItemService itemService) {
        this.itemService = itemService;
    }

    /* GET mappings */

    @GetMapping("/{id}")
    public Item getItem(@PathVariable Long id) {
        return itemService.getItemById(id);
    }

    @GetMapping("/page/{pageNumber}")
    public List<Item> getItems(@PathVariable int pageNumber) {
        return itemService.getAllItems(pageNumber);
    }

    @GetMapping("/codes")
    public List<Long> getCodes() {
        return itemService.getItemCodes();
    }

    @GetMapping
    public List<Item> getItems() {
        return itemService.getAll();
    }

    @GetMapping("/codecal")
    public List<ItemIdFoodTypeAndEnergyKcal> getCodeFoodTypeAndCal() {
        return itemService.fetchFoodTypeItemIdsAndEnergy();
    }

    /* POST mappings */

    @PostMapping
    public Item createItem(@RequestBody Item item) throws IOException, TimeoutException {
        return itemService.saveItem(item);
    }

    /* DELETE mappings */

    @DeleteMapping("/codes/{code}")
    public void deleteItem(@PathVariable Long code) {
        itemService.deleteItemByCode(code);
    }
}
