package com.gamers;
import jade.core.Agent;

public class HelloWorld extends Agent {
    @Override
    protected void setup() {
        super.setup();
        System.out.println("Hello world from "+ getAID().getName() + "!");
    }
}