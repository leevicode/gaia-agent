package com.gamers;

import jade.core.Agent;

public class SecondaryAgent extends Agent {
    @Override
    protected void setup() {
        super.setup();
        System.out.println("Secondary working!"+getLocalName());
    }
}
