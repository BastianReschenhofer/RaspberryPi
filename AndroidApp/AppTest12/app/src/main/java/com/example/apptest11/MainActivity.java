package com.example.apptest11;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import android.Manifest;
import android.app.AlertDialog;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.le.AdvertiseCallback;
import android.bluetooth.le.AdvertiseData;
import android.bluetooth.le.AdvertiseSettings;
import android.bluetooth.le.BluetoothLeAdvertiser;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.drawable.Drawable;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.util.Log;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import com.journeyapps.barcodescanner.ScanContract;
import com.journeyapps.barcodescanner.ScanOptions;
import java.nio.charset.StandardCharsets;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "BLE_ADVERTISER";
    private static final long ADVERTISING_INTERVAL_MS = 1000;
    private static final int ADVERTISING_DURATION_MS = 120;
    private static final int MANUFACTURER_ID = 0x1100;
    private static final int REQUEST_BLUETOOTH_PERMISSIONS = 100;

    private EditText nameInput;
    private Button startStopButton;
    private Button registerButton;
    private TextView statusText;
    private Button privacyButton;
    private Button statsButton;

    // BLE
    private BluetoothAdapter bluetoothAdapter;
    private BluetoothLeAdvertiser advertiser;
    private AdvertiseCallback advertiseCallback;

    // Steuerung Advertising
    private final Handler handler = new Handler();
    private Runnable advertisingRunnable;
    private boolean isAdvertisingActive = false;

    // Speicherung Hashes
    private static final String PREFS_NAME = "name";
    private static final String KEY_USER_NAME = "key_name";
    private String userHash = "TestTest";

    // QR-Code-Scanner
    private final ScanOptions scanOptions = new ScanOptions();

    //Stats
    private int advertisingCount = 0;
    private long advertisingStartTime = 0;
    private long totalAdvertisingTime = 0;

    private final androidx.activity.result.ActivityResultLauncher<ScanOptions> barcodeLauncher =
            registerForActivityResult(new ScanContract(), result -> {

                if (result.getContents() == null) {
                    statusText.setText("Scan abgebrochen");
                    return;
                }

                String scannedHash = result.getContents();
                saveHash(scannedHash);

                nameInput.setText(scannedHash);
                statusText.setText("Hash registriert");
                statusText.setTextColor(Color.BLUE);

                Log.d(TAG, "QR-Code erfolgreich gescannt");
            });

    @Override
    protected void onCreate(Bundle savedInstanceState) { //saveInstanceState -> speichert Daten des vorherigen Zustand falls App im Hintergrund lief
        SharedPreferences prefsDaS = getSharedPreferences("app_prefs", MODE_PRIVATE); //kleiner Speicher für Speichern des Hashes

        boolean privacyAccepted = prefsDaS.getBoolean("privacy_accepted", false);

        if (!privacyAccepted) {
            showPrivacyDialog();
        }

        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Buttons initialisieren
        nameInput = findViewById(R.id.name_input);
        startStopButton = findViewById(R.id.action_button);
        registerButton = findViewById(R.id.action_button1);
        statusText = findViewById(R.id.status_text);
        privacyButton = findViewById(R.id.privacy_button);
        statsButton = findViewById(R.id.statistics_button);

        // gespeicherten Hash laden
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        userHash = prefs.getString(KEY_USER_NAME, "TestTest");

        nameInput.setText(userHash);
        nameInput.setEnabled(false);

        checkAndRequestPermissions();
        initBluetooth();

        startStopButton.setOnClickListener(v -> {
            Log.d(TAG, "Start/Stop Button gedrückt");

            if (isAdvertisingActive) {
                stopPeriodicAdvertising();
            } else {
                startPeriodicAdvertising(userHash);
            }
        });


        privacyButton.setOnClickListener(v -> {
            startActivity(new Intent(this, Privacy.class));
        });

        statsButton.setOnClickListener(v -> {
            startActivity(new Intent(this, Statistics.class));
        });



        registerButton.setOnClickListener(v -> {
            scanOptions.setPrompt("Scanne QR-Code");
            scanOptions.setBeepEnabled(true);
            scanOptions.setOrientationLocked(false);
            scanOptions.setTimeout(3000);

            barcodeLauncher.launch(scanOptions);
        });
    }



    // BLE Advertising Logik
    private void startPeriodicAdvertising(String hash) {

        advertisingStartTime = System.currentTimeMillis();

        vibrateShort();

        if (isAdvertisingActive) return;

        advertisingRunnable = new Runnable() {
            @Override
            public void run() {
                startSingleAdvertising(hash);
                handler.postDelayed(this, ADVERTISING_INTERVAL_MS);
            }
        };

        handler.post(advertisingRunnable);
        isAdvertisingActive = true;

        startStopButton.setText("Stoppen");
        statusText.setText("BLE Advertising aktiv");
        statusText.setTextColor(Color.parseColor("#9abc85"));

        Drawable icon = ContextCompat.getDrawable(this, R.drawable.send);
        statusText.setCompoundDrawablesRelativeWithIntrinsicBounds(icon, null, null, null);
    }

    private void stopPeriodicAdvertising() {

        if (advertisingStartTime != 0) {
            totalAdvertisingTime +=
                    System.currentTimeMillis() - advertisingStartTime;
        }

        vibrateShort();

        if (!isAdvertisingActive) return;

        handler.removeCallbacks(advertisingRunnable);
        isAdvertisingActive = false;

        stopAdvertisingInternal();

        startStopButton.setText("Advertising starten");
        statusText.setText("Bereit zum Senden");
        statusText.setTextColor(Color.BLACK);

        Drawable icon = ContextCompat.getDrawable(this, R.drawable.notsend);
        statusText.setCompoundDrawablesRelativeWithIntrinsicBounds(icon, null, null, null);

        Log.d(TAG, "Advertising gestoppt");

        SharedPreferences prefs = getSharedPreferences("stats", MODE_PRIVATE);
        prefs.edit().putInt("count", advertisingCount).putLong("time", totalAdvertisingTime).apply();
    }

    private void startSingleAdvertising(String hash) {

        blinkStatusOnce();
        advertisingCount++;

        if (advertiser == null) return;

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
                ActivityCompat.checkSelfPermission(this,
                        Manifest.permission.BLUETOOTH_ADVERTISE)
                        != PackageManager.PERMISSION_GRANTED) {

            statusText.setText("Bluetooth-Berechtigung fehlt");
            statusText.setTextColor(Color.RED);
            checkAndRequestPermissions();
            return;
        }

        byte[] data = hash.getBytes(StandardCharsets.UTF_8);

        AdvertiseSettings settings = new AdvertiseSettings.Builder()
                .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
                .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
                .setTimeout(ADVERTISING_DURATION_MS)
                .setConnectable(true)
                .build();

        AdvertiseData advertiseData = new AdvertiseData.Builder()
                .setIncludeDeviceName(false)
                .addManufacturerData(MANUFACTURER_ID, data)
                .build();

        advertiser.startAdvertising(settings, advertiseData, advertiseCallback);
    }

    private void stopAdvertisingInternal() {
        if (advertiser != null && advertiseCallback != null) {
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_ADVERTISE) != PackageManager.PERMISSION_GRANTED) {
                return;
            }
            advertiser.stopAdvertising(advertiseCallback);
        }
    }

    private void initBluetooth() {
        bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();

        if (bluetoothAdapter == null) {
            statusText.setText("Bluetooth nicht verfügbar");
            statusText.setTextColor(Color.RED);
            return;
        }

        advertiser = bluetoothAdapter.getBluetoothLeAdvertiser();
        setupAdvertiseCallback();
    }

    private void setupAdvertiseCallback() {
        advertiseCallback = new AdvertiseCallback() {

            @Override
            public void onStartSuccess(AdvertiseSettings settingsInEffect) {
                Log.d(TAG, "Advertising gestartet (" +
                        settingsInEffect.getTimeout() + "ms)");
            }

            @Override
            public void onStartFailure(int errorCode) {
                Log.e(TAG, "Advertising Fehler: " + errorCode);

                stopPeriodicAdvertising();

                statusText.setText("Fehler beim Senden");
                statusText.setTextColor(Color.RED);

                Drawable icon = ContextCompat.getDrawable(
                        MainActivity.this, R.drawable.senderror);
                statusText.setCompoundDrawablesRelativeWithIntrinsicBounds(
                        icon, null, null, null);
            }
        };
    }
  
    // Berechtigungen
    private void checkAndRequestPermissions() {
        // Bluetooth-Permissions sind erst ab Android 12 notwendig
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return;

        if (checkSelfPermission(Manifest.permission.BLUETOOTH_ADVERTISE)
                != PackageManager.PERMISSION_GRANTED ||
                checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)
                        != PackageManager.PERMISSION_GRANTED) {

            ActivityCompat.requestPermissions(
                    this,
                    new String[]{
                            Manifest.permission.BLUETOOTH_ADVERTISE,
                            Manifest.permission.BLUETOOTH_CONNECT
                    },
                    REQUEST_BLUETOOTH_PERMISSIONS
            );
        }
    }

    //Datenschutz
    private void showPrivacyDialog() {
        new AlertDialog.Builder(this)
                .setTitle("Datenschutz")
                .setMessage(
                        "Diese App verwendet Bluetooth.\n" +
                                "Es werden keine personenbezogenen Daten gespeichert oder weitergegeben."
                )
                .setCancelable(false)
                .setPositiveButton("Ich stimme zu", (dialog, which) -> {
                    SharedPreferences prefs =
                            getSharedPreferences("app_prefs", MODE_PRIVATE);
                    prefs.edit()
                            .putBoolean("privacy_accepted", true)
                            .apply();
                })
                .setNegativeButton("App schließen", (dialog, which) -> {
                    finish();
                })
                .show();
    }

    @Override
    public void onRequestPermissionsResult(
            int requestCode,
            @NonNull String[] permissions,
            @NonNull int[] grantResults) {

        super.onRequestPermissionsResult(
                requestCode, permissions, grantResults);

        if (requestCode != REQUEST_BLUETOOTH_PERMISSIONS) return;

        for (int result : grantResults) {
            if (result != PackageManager.PERMISSION_GRANTED) {
                statusText.setText("Bluetooth-Berechtigung verweigert");
                statusText.setTextColor(Color.RED);
                return;
            }
        }

        initBluetooth();
    }
    
    // Speicherung
    private void saveHash(String hash) {
        SharedPreferences prefs =
                getSharedPreferences(PREFS_NAME, MODE_PRIVATE);

        prefs.edit()
                .putString(KEY_USER_NAME, hash)
                .apply();

        userHash = hash;
        Log.d(TAG, "Neuer Hash gespeichert");
    }

    private void vibrateShort() {
        Vibrator vibrator = (Vibrator) getSystemService(VIBRATOR_SERVICE);
        if (vibrator == null) return;

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(
                    VibrationEffect.createOneShot(
                            100,
                            VibrationEffect.DEFAULT_AMPLITUDE
                    )
            );
        } else {
            vibrator.vibrate(100);
        }
    }

    private void blinkStatusOnce() {
        int normalColor = Color.parseColor("#9abc85");

        statusText.setTextColor(Color.GREEN);

        handler.postDelayed(() -> {
            statusText.setTextColor(normalColor);
        }, 200);
    }
}


