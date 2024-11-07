package com.mcdiet.menu_plan_db.plan;

import com.mcdiet.menu_plan_db.plan.documents.DietPlan;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/plan")
public class PlanController {

    private final PlanService planService;

    @Autowired
    public PlanController(final PlanService planService) {
        this.planService = planService;
    }

    @PostMapping
    public DietPlan createPlan(@RequestBody DietPlan plan) {
        return planService.saveDietPlan(plan);
    }

    @GetMapping("/user")
    public DietPlan getPlanById(@RequestParam String userId) {
        return planService.getDietPlanById(userId);
    }

    @GetMapping("/test")
    public String getPlanById() {
        return "wololo";
    }
}
