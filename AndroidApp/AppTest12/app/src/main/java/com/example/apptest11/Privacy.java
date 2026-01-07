package com.example.apptest11;

import android.os.Bundle;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;


public class Privacy extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_privacy);

        TextView text = findViewById(R.id.privacy_text);

        text.setText(
                "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"+
                "Datenschutz-Information\n\n" +
                        "Diese App sendet in regelmäßigen Abständen ein Bluetooth-Low-Energy-Signal.\n\n" +
                        "Dabei wird ausschließlich ein anonymisierter Hash übertragen.\n\n" +
                        "Es werden keine personenbezogenen Daten wie Name, Standort oder Kontakte gespeichert oder versendet.\n\n" +
                        "Der Hash wird lokal auf dem Gerät gespeichert und kann jederzeit neu registriert werden.\n\n" +
                        "Die App dient ausschließlich zu Lern- und Testzwecken."
        ); //Text von Gemini
    }
}