package com.eletrojun.eletrojun_project.model;

import java.time.LocalDateTime;

import org.springframework.format.annotation.DateTimeFormat;

public class Message {

    private Float temperature;
    private Float humidity;

    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime dateAndTime;

    public Message() {
    }

    public Message(Float temperature, Float humidity, LocalDateTime dateAndTime) {
        this.temperature = temperature;
        this.humidity = temperature;
        this.dateAndTime = dateAndTime;
    }

    public Float getTemperature() {
        return temperature;
    }

    public void setTemperature(Float temperature) {
        this.temperature = temperature;
    }

    public Float getHumidity() {
        return humidity;
    }

    public void setHumidity(Float humidity) {
        this.humidity = humidity;
    }

    public LocalDateTime getDateAndTime() {
        return dateAndTime;
    }

    public void setDateAndTime(LocalDateTime dateAndTime) {
        this.dateAndTime = dateAndTime;
    }

}
