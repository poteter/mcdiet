package com.mcdiet.menu_plan_db.plan;

import com.mcdiet.menu_plan_db.plan.documents.DietPlan;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class PlanService {
    private final PlanRepo planRepo;

    @Autowired
    public PlanService(final PlanRepo planRepo) {
        this.planRepo = planRepo;
    }

    public DietPlan saveDietPlan(DietPlan plan) {
        return planRepo.save(plan);
    }

    public DietPlan getDietPlanById(String user) {
        return planRepo.findByUser(user);
    }

}
