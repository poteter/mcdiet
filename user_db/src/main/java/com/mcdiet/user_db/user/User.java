package com.mcdiet.user_db.user;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Getter
@Setter
@NoArgsConstructor
@Table(name = "userName")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "userId")
    private long user_id;

    @Column(name = "userName")
    private String user_name;

    public User(String userName) {
        user_name = userName;
    }
}
