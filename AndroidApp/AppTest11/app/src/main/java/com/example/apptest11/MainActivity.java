package com.example.apptest11;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.graphics.Color;
import android.os.Handler;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.le.AdvertiseCallback;
import android.bluetooth.le.AdvertiseData;
import android.bluetooth.le.AdvertiseSettings;
import android.bluetooth.le.BluetoothLeAdvertiser;
import java.nio.charset.StandardCharsets;

import android.graphics.drawable.Drawable;
import androidx.core.content.ContextCompat;
import androidx.core.graphics.drawable.DrawableCompat;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "BLE_ADVERTISER_APP";
    private static final int REQUEST_BLUETOOTH_PERMISSIONS = 100;
    private static final long ADVERTISING_INTERVAL_MS = 1000;
    private static final int ADVERTISING_DURATION_MS = 100;
    private static final int MANUFACTURER_ID = 0x1100;

    private EditText nameInput;
    private Button actionButton;
    private TextView statusText;
    private BluetoothAdapter bluetoothAdapter;
    private BluetoothLeAdvertiser advertiser;
    private AdvertiseCallback advertiseCallback;
    private Handler handler = new Handler();
    private Runnable advertisingRunnable;
    private boolean isAdvertisingScheduled = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        nameInput = findViewById(R.id.name_input);
        actionButton = findViewById(R.id.action_button);
        statusText = findViewById(R.id.status_text);

        checkAndRequestPermissions();
        initBLE();

        actionButton.setOnClickListener(v -> {
            String name = nameInput.getText().toString().trim();

            if (isAdvertisingScheduled) {
                stopPeriodicAdvertising();
            } else if (name.isEmpty()) {
                statusText.setText("Status: Bitte einen Namen eingeben!");
                statusText.setTextColor(Color.RED);
            } else {
                startPeriodicAdvertising(name);
                actionButton.setText("Advertising stoppen");
            }
        });
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        stopPeriodicAdvertising();
    }

    private void startPeriodicAdvertising(String name) {
        if (isAdvertisingScheduled) return;

        advertisingRunnable = () -> {
            startAdvertising(name);
            handler.postDelayed(advertisingRunnable, ADVERTISING_INTERVAL_MS);
        };

        handler.post(advertisingRunnable);
        isAdvertisingScheduled = true;
        Log.d(TAG, "Periodisches Advertising gestartet.");
        statusText.setText("aktiv");
        statusText.setTextColor(Color.parseColor("#9abc85"));


        Drawable activeIcon = ContextCompat.getDrawable(this, R.drawable.send);
        statusText.setCompoundDrawablesRelativeWithIntrinsicBounds(activeIcon, null, null, null);
    }

    private void stopPeriodicAdvertising() {
        if (isAdvertisingScheduled) {
            handler.removeCallbacks(advertisingRunnable);
            isAdvertisingScheduled = false;
            Log.d(TAG, "Status: Bereit zum Senden");
        }
        stopAdvertisingInternal();
        statusText.setText("inaktiv");
        statusText.setTextColor(Color.BLACK);
        actionButton.setText("Advertising starten");


        Drawable readyIcon = ContextCompat.getDrawable(this, R.drawable.notsend);
        statusText.setCompoundDrawablesRelativeWithIntrinsicBounds(readyIcon, null, null, null);
    }

    private void stopAdvertisingInternal() {
        if (advertiser != null && advertiseCallback != null) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
                    ActivityCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_ADVERTISE) != PackageManager.PERMISSION_GRANTED) {
                Log.e(TAG, "Fehlende BLUETOOTH_ADVERTISE-Berechtigung beim Stoppen.");
                return;
            }
            advertiser.stopAdvertising(advertiseCallback);
            Log.d(TAG, "Advertising gestoppt.");
        }
    }

    private void initBLE() {
        bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (bluetoothAdapter != null) {
            advertiser = bluetoothAdapter.getBluetoothLeAdvertiser();
            setupAdvertiseCallback();
        }
    }

    private void startAdvertising(String name) {
        if (advertiser == null) {
            return;
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
                ActivityCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_ADVERTISE) != PackageManager.PERMISSION_GRANTED) {
            statusText.setText("Status: Berechtigung zum Senden fehlt!");
            statusText.setTextColor(Color.RED);
            checkAndRequestPermissions();
            return;
        }

        byte[] nameBytes = name.getBytes(StandardCharsets.UTF_8);

        AdvertiseSettings settings = new AdvertiseSettings.Builder()
                .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
                .setConnectable(true)
                .setTimeout(ADVERTISING_DURATION_MS)
                .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
                .build();

        AdvertiseData advertiseData = new AdvertiseData.Builder()
                .setIncludeDeviceName(false)
                .addManufacturerData(MANUFACTURER_ID, nameBytes)
                .build();

        advertiser.startAdvertising(settings, advertiseData, advertiseCallback);
    }

    private void setupAdvertiseCallback() {
        advertiseCallback = new AdvertiseCallback() {
            @Override
            public void onStartSuccess(AdvertiseSettings settingsInEffect) {
                super.onStartSuccess(settingsInEffect);
                Log.d(TAG, "Advertising erfolgreich gestartet (Dauer: " + settingsInEffect.getTimeout() + "ms).");
                if (isAdvertisingScheduled) return;
                statusText.setText("Status: BLE Advertising gestartet!");
                statusText.setTextColor(Color.GREEN);
            }

            @Override
            public void onStartFailure(int errorCode) {
                super.onStartFailure(errorCode);
                String errorMsg = "Fehler beim Start des Advertisings: " + errorCode;
                Log.e(TAG, errorMsg);
                stopPeriodicAdvertising();
                statusText.setText("Status: " + errorMsg + " (Senden gestoppt)");
                statusText.setTextColor(Color.RED);


                Drawable errorIcon = ContextCompat.getDrawable(MainActivity.this, R.drawable.senderror);
                statusText.setCompoundDrawablesRelativeWithIntrinsicBounds(errorIcon, null, null, null);
            }
        };
    }

    private void checkAndRequestPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (checkSelfPermission(Manifest.permission.BLUETOOTH_ADVERTISE) != PackageManager.PERMISSION_GRANTED ||
                    checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {

                ActivityCompat.requestPermissions(this, new String[]{
                        Manifest.permission.BLUETOOTH_ADVERTISE,
                        Manifest.permission.BLUETOOTH_CONNECT
                }, REQUEST_BLUETOOTH_PERMISSIONS);
            }
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_BLUETOOTH_PERMISSIONS) {
            boolean allGranted = true;
            for (int result : grantResults) {
                if (result != PackageManager.PERMISSION_GRANTED) {
                    allGranted = false;
                    break;
                }
            }
            if (allGranted) {
                initBLE();
            } else {
                statusText.setText("Status: BLE-Berechtigungen verweigert!");
                statusText.setTextColor(Color.RED);
            }
        }
    }
}