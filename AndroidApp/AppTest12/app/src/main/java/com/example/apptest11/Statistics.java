package com.example.apptest11;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;


public class Statistics extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_statistics);

        TextView text = findViewById(R.id.stats_text);

        SharedPreferences prefs =
                getSharedPreferences("stats", MODE_PRIVATE);

        int count = prefs.getInt("count", 0);
        long timeMs = prefs.getLong("time", 0);

        long seconds = timeMs / 1000;

        text.setText(
                "\n\n\n\n\n\n\n\n\n\n\n\n\n\n" +
                "Statistik\n\n" +
                        "Gesendete BLE-Pakete: " + count + "\n\n" +
                        "Gesamte Sendezeit: " + seconds + " Sekunden"
        );
    }

}