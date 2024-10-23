package com.mcdiet.menu_plan_db.plan;

import com.mcdiet.menu_plan_db.plan.documents.DietPlan;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
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
}
