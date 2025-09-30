package com.mcdiet.user_db.user;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class UserService {
    private final UserRepo userRepo;

    @Autowired
    public UserService(UserRepo userRepo) {
        this.userRepo = userRepo;
    }

    public void addUser(User user) {
        userRepo.save(user);
    }

    public void removeUser(long id) {
        userRepo.deleteById(id);
    }

    public User getUserById(long id) {
        return userRepo.findById(id).orElse(null);
    }
}
