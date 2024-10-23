package com.mcdiet.menu_plan_db.plan;

import com.mcdiet.menu_plan_db.plan.documents.DietPlan;
import com.mcdiet.menu_plan_db.plan.documents.Plan;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PlanRepo extends MongoRepository<DietPlan, String> {
    // Find diet plans by user
    DietPlan findByUser(String user);
}
