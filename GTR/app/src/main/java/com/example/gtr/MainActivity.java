package com.example.gtr;

import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.util.Log;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;

import com.journeyapps.barcodescanner.ScanContract;
import com.journeyapps.barcodescanner.ScanIntentResult;
import com.journeyapps.barcodescanner.ScanOptions;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "GTR_Display";
    private static final String[] CANDIDATE_HOSTS = {
            "10.0.2.2", "192.168.100.47", "10.42.0.1",
            "192.168.100.16", "100.89.43.30", "192.168.100.61",
    };
    // API_PORT removed — host resolution tests 3001, 3000, 80 automatically
    private static final long POLL_INTERVAL_MS = 3000;
    private static final long WELCOME_DURATION_MS = 5000;
    private static final long REQUEST_POLL_MS = 4000;

    // State
    private volatile String apiBaseUrl = null;
    private volatile boolean isShowingWelcome = false;
    private volatile boolean isShowingParking = false;
    private long lastEventTimestamp = 0;
    private volatile boolean isResolvingHost = false;
    private final StringBuilder keyAccumulator = new StringBuilder();

    // ZXing camera scanner launcher
    private ActivityResultLauncher<ScanOptions> barcodeLauncher;

    // Current user data for parking
    private int currentUserId = -1;
    private String currentUserName = "";
    private List<VehicleInfo> currentVehicles = new ArrayList<>();
    private int selectedVehicleIndex = -1;
    private String lastRequestType = "";

    // UI
    private LinearLayout logoContainer;
    private LinearLayout welcomeContainer;
    private ScrollView parkingContainer;
    private LinearLayout parkingIdleView;
    private LinearLayout parkingActiveView;
    private TextView memberNameText;
    private TextView parkingUserName;
    private TextView parkingUserInfo;
    private LinearLayout parkingVehiclesList;
    private TextView parkingNoVehicles;
    private LinearLayout parkingRequestStatus;
    private TextView parkingStatusText;
    private LinearLayout spotSelectorContainer;
    private TextView btnHeliport;

    // Polling
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final OkHttpClient httpClient = new OkHttpClient.Builder()
            .connectTimeout(2, TimeUnit.SECONDS)
            .readTimeout(2, TimeUnit.SECONDS)
            .build();

    private final Runnable pollRunnable = new Runnable() {
        @Override
        public void run() {
            if (apiBaseUrl != null) {
                if (!isShowingParking) pollScanEvent();
            } else {
                resolveApiHost();
            }
            handler.postDelayed(this, POLL_INTERVAL_MS);
        }
    };

    private Runnable requestPollRunnable;

    // ═══ VEHICLE INFO ═══
    static class VehicleInfo {
        String nickname, vehicleType, brand, model, plate, color;
        int year;
        boolean isPrimary;
        int vehicleId;
    }

    // ═══ LIFECYCLE ═══
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Register ZXing barcode scanner launcher BEFORE any UI interaction
        barcodeLauncher = registerForActivityResult(new ScanContract(), this::onScanResult);

        logoContainer = findViewById(R.id.logoContainer);
        welcomeContainer = findViewById(R.id.welcomeContainer);
        parkingContainer = findViewById(R.id.parkingContainer);
        parkingIdleView = findViewById(R.id.parkingIdleView);
        parkingActiveView = findViewById(R.id.parkingActiveView);
        memberNameText = findViewById(R.id.memberNameText);
        parkingUserName = findViewById(R.id.parkingUserName);
        parkingUserInfo = findViewById(R.id.parkingUserInfo);
        parkingVehiclesList = findViewById(R.id.parkingVehiclesList);
        parkingNoVehicles = findViewById(R.id.parkingNoVehicles);
        parkingRequestStatus = findViewById(R.id.parkingRequestStatus);
        parkingStatusText = findViewById(R.id.parkingStatusText);
        spotSelectorContainer = findViewById(R.id.spotSelectorContainer);
        btnHeliport = findViewById(R.id.btnHeliport);

        hideSystemUI();
        showLogo();

        // Parking buttons
        findViewById(R.id.btnParkingEnter).setOnClickListener(v -> sendParkingRequest("check_in"));
        findViewById(R.id.btnParkingWithdraw).setOnClickListener(v -> sendParkingRequest("check_out"));
        findViewById(R.id.parkingCloseBtn).setOnClickListener(v -> resetParkingToIdle());
        btnHeliport.setOnClickListener(v -> sendParkingRequest("heliport"));

        // Parking Idle buttons
        findViewById(R.id.btnParkingManualInput).setOnClickListener(v -> showManualInputDialog());
        findViewById(R.id.btnParkingScanCamera).setOnClickListener(v -> launchCameraScanner());
        findViewById(R.id.btnParkingExitMode).setOnClickListener(v -> closeParkingInterface());

        // Root click for manual input (only when in logo state)
        findViewById(R.id.rootLayout).setOnClickListener(v -> {
            if (!isShowingParking && !isShowingWelcome) showManualInputDialog();
        });

        Log.i(TAG, "Parking GTR Display started — resolving API host...");
    }

    @Override
    protected void onResume() {
        super.onResume();
        hideSystemUI();
        handler.post(pollRunnable);
    }

    @Override
    protected void onPause() {
        super.onPause();
        handler.removeCallbacks(pollRunnable);
        stopRequestPolling();
    }

    // ═══ FULLSCREEN ═══
    private void hideSystemUI() {
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.R) {
            getWindow().setDecorFitsSystemWindows(false);
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.hide(WindowInsets.Type.systemBars());
                controller.setSystemBarsBehavior(WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
            }
        } else {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_FULLSCREEN);
        }
    }

    // ═══ API HOST RESOLUTION ═══
    private void resolveApiHost() {
        if (isResolvingHost) return;
        isResolvingHost = true;
        new Thread(() -> {
            try {
                for (String host : CANDIDATE_HOSTS) {
                    if (apiBaseUrl != null) break;
                    int[] ports = {3001, 3000, 80};
                    for (int port : ports) {
                        if (apiBaseUrl != null) break;
                        String url = "http://" + host + (port != 80 ? ":" + port : "") + "/api/health";
                        Request request = new Request.Builder().url(url).build();
                        try (Response response = httpClient.newCall(request).execute()) {
                            if (response.isSuccessful()) {
                                apiBaseUrl = "http://" + host + (port != 80 ? ":" + port : "");
                                Log.i(TAG, "✓ API host resolved: " + apiBaseUrl);
                                return;
                            }
                        } catch (IOException ignored) {}
                    }
                }
                if (apiBaseUrl == null) Log.w(TAG, "No API host available yet, will retry...");
            } finally {
                isResolvingHost = false;
            }
        }).start();
    }

    // ═══ POLLING SCAN EVENTS ═══
    private void pollScanEvent() {
        if (isShowingWelcome || isShowingParking) return;
        String url = apiBaseUrl + "/api/scan-event";
        httpClient.newCall(new Request.Builder().url(url).build()).enqueue(new Callback() {
            @Override public void onFailure(Call call, IOException e) {}
            @Override public void onResponse(Call call, Response response) throws IOException {
                try {
                    if (!response.isSuccessful()) return;
                    String body = response.body() != null ? response.body().string() : "";
                    JSONObject json = new JSONObject(body);
                    if (!json.optBoolean("success", false) || json.isNull("event")) return;
                    JSONObject event = json.getJSONObject("event");
                    String memberName = event.optString("member_name", "");
                    long timestamp = event.optLong("timestamp", 0);
                    if (memberName.isEmpty() || timestamp == lastEventTimestamp) return;
                    lastEventTimestamp = timestamp;
                    Log.i(TAG, "Scan event received: " + memberName);
                    runOnUiThread(() -> showWelcome(memberName));
                    clearScanEvent();
                } catch (Exception e) {
                    Log.e(TAG, "Error parsing scan event", e);
                } finally {
                    response.close();
                }
            }
        });
    }

    private void clearScanEvent() {
        String url = apiBaseUrl + "/api/scan-event";
        httpClient.newCall(new Request.Builder().url(url).delete().build()).enqueue(new Callback() {
            @Override public void onFailure(Call call, IOException e) {}
            @Override public void onResponse(Call call, Response response) { response.close(); }
        });
    }

    // ═══ UI STATE TRANSITIONS ═══
    private void showLogo() {
        isShowingWelcome = false;
        isShowingParking = false;
        logoContainer.clearAnimation();
        welcomeContainer.clearAnimation();
        logoContainer.setAlpha(1f);
        logoContainer.setVisibility(View.VISIBLE);
        welcomeContainer.setAlpha(0f);
        welcomeContainer.setVisibility(View.GONE);
        parkingContainer.setAlpha(0f);
        parkingContainer.setVisibility(View.GONE);
    }

    private void showWelcome(String memberName) {
        isShowingWelcome = true;
        isShowingParking = false;
        memberNameText.setText(memberName);
        logoContainer.animate().cancel();
        welcomeContainer.animate().cancel();

        logoContainer.animate().alpha(0f).setDuration(400)
                .withEndAction(() -> logoContainer.setVisibility(View.GONE)).start();

        parkingContainer.setVisibility(View.GONE);
        parkingContainer.setAlpha(0f);

        welcomeContainer.setAlpha(0f);
        welcomeContainer.setVisibility(View.VISIBLE);
        welcomeContainer.animate().alpha(1f).setDuration(500).start();

        handler.postDelayed(() -> {
            welcomeContainer.animate().alpha(0f).setDuration(400)
                    .withEndAction(() -> welcomeContainer.setVisibility(View.GONE)).start();
            logoContainer.setAlpha(0f);
            logoContainer.setVisibility(View.VISIBLE);
            logoContainer.animate().alpha(1f).setDuration(500).start();
            isShowingWelcome = false;
        }, WELCOME_DURATION_MS);
    }

    // ═══ PARKING INTERFACE ═══
    private void showParkingInterface() {
        isShowingParking = true;
        isShowingWelcome = false;

        logoContainer.animate().alpha(0f).setDuration(300)
                .withEndAction(() -> logoContainer.setVisibility(View.GONE)).start();
        welcomeContainer.setVisibility(View.GONE);

        parkingContainer.setAlpha(0f);
        parkingContainer.setVisibility(View.VISIBLE);
        parkingContainer.animate().alpha(1f).setDuration(400).start();

        if (currentUserId > 0) {
            parkingIdleView.setVisibility(View.GONE);
            parkingActiveView.setVisibility(View.VISIBLE);
            parkingUserName.setText(currentUserName);
            parkingUserInfo.setText("MEMBER  •  GTR-" + String.format("%04d", currentUserId));
            renderVehiclesList();
        } else {
            parkingActiveView.setVisibility(View.GONE);
            parkingIdleView.setVisibility(View.VISIBLE);
        }
        parkingRequestStatus.setVisibility(View.GONE);
        spotSelectorContainer.setVisibility(View.GONE);
        if (currentUserId > 0) loadHeliportStatus();
    }

    private void closeParkingInterface() {
        isShowingParking = false;
        currentUserId = -1;
        currentUserName = "";
        currentVehicles.clear();
        selectedVehicleIndex = -1;
        lastRequestType = "";
        stopRequestPolling();

        parkingContainer.animate().alpha(0f).setDuration(300)
                .withEndAction(() -> parkingContainer.setVisibility(View.GONE)).start();

        logoContainer.setAlpha(0f);
        logoContainer.setVisibility(View.VISIBLE);
        logoContainer.animate().alpha(1f).setDuration(400).start();
    }

    private void resetParkingToIdle() {
        currentUserId = -1;
        currentUserName = "";
        currentVehicles.clear();
        selectedVehicleIndex = -1;
        lastRequestType = "";
        stopRequestPolling();

        parkingActiveView.setVisibility(View.GONE);
        parkingIdleView.setVisibility(View.VISIBLE);
        parkingRequestStatus.setVisibility(View.GONE);
        spotSelectorContainer.setVisibility(View.GONE);
    }

    private void renderVehiclesList() {
        parkingVehiclesList.removeAllViews();

        if (currentVehicles.isEmpty()) {
            parkingNoVehicles.setVisibility(View.VISIBLE);
            return;
        }
        parkingNoVehicles.setVisibility(View.GONE);

        for (int i = 0; i < currentVehicles.size(); i++) {
            VehicleInfo v = currentVehicles.get(i);
            final int index = i;

            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.HORIZONTAL);
            card.setPadding(dp(16), dp(12), dp(16), dp(12));
            card.setGravity(android.view.Gravity.CENTER_VERTICAL);

            GradientDrawable bg = new GradientDrawable();
            bg.setCornerRadius(dp(8));
            bg.setColor(selectedVehicleIndex == i ? Color.parseColor("#2a2a1a") : Color.parseColor("#161616"));
            bg.setStroke(dp(1), selectedVehicleIndex == i ? Color.parseColor("#d4af37") : Color.parseColor("#333333"));
            card.setBackground(bg);

            LinearLayout.LayoutParams cardParams = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            cardParams.bottomMargin = dp(8);
            card.setLayoutParams(cardParams);

            // Vehicle emoji
            String emoji = getVehicleEmoji(v.vehicleType);
            TextView emojiView = new TextView(this);
            emojiView.setText(emoji);
            emojiView.setTextSize(24);
            emojiView.setPadding(0, 0, dp(12), 0);
            card.addView(emojiView);

            // Info column
            LinearLayout infoCol = new LinearLayout(this);
            infoCol.setOrientation(LinearLayout.VERTICAL);
            infoCol.setLayoutParams(new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

            TextView nameView = new TextView(this);
            nameView.setText(v.nickname != null ? v.nickname : "Vehículo");
            nameView.setTextColor(Color.WHITE);
            nameView.setTextSize(14);
            nameView.setTypeface(null, android.graphics.Typeface.BOLD);
            infoCol.addView(nameView);

            String meta = joinNonNull(" · ", v.brand, v.model, v.year > 0 ? String.valueOf(v.year) : null);
            if (!meta.isEmpty()) {
                TextView metaView = new TextView(this);
                metaView.setText(meta);
                metaView.setTextColor(Color.parseColor("#666666"));
                metaView.setTextSize(12);
                infoCol.addView(metaView);
            }

            if (v.plate != null && !v.plate.isEmpty()) {
                TextView plateView = new TextView(this);
                plateView.setText("🪪 " + v.plate);
                plateView.setTextColor(Color.parseColor("#c8bc98"));
                plateView.setTextSize(11);
                infoCol.addView(plateView);
            }

            card.addView(infoCol);

            // Selection indicator
            if (selectedVehicleIndex == i) {
                TextView check = new TextView(this);
                check.setText("✓");
                check.setTextColor(Color.parseColor("#d4af37"));
                check.setTextSize(20);
                card.addView(check);
            } else if (v.isPrimary) {
                TextView star = new TextView(this);
                star.setText("★");
                star.setTextColor(Color.parseColor("#d4af37"));
                star.setTextSize(14);
                card.addView(star);
            }

            card.setOnClickListener(view -> {
                selectedVehicleIndex = index;
                renderVehiclesList();
            });

            parkingVehiclesList.addView(card);
        }
    }

    // ═══ PARKING REQUESTS ═══
    private void sendParkingRequest(String requestType) {
        if (currentUserId <= 0) return;
        // Heliport doesn't require vehicle selection
        if (!requestType.equals("heliport")) {
            if (currentVehicles.isEmpty()) {
                Toast.makeText(this, "No hay vehículos registrados", Toast.LENGTH_SHORT).show();
                return;
            }
            if (selectedVehicleIndex < 0) {
                Toast.makeText(this, "Selecciona un vehículo primero", Toast.LENGTH_SHORT).show();
                return;
            }
        }
        if (apiBaseUrl == null) {
            Toast.makeText(this, "API no disponible", Toast.LENGTH_SHORT).show();
            resolveApiHost();
            return;
        }

        lastRequestType = requestType;
        int vehicleId = 0;
        if (selectedVehicleIndex >= 0 && selectedVehicleIndex < currentVehicles.size()) {
            vehicleId = currentVehicles.get(selectedVehicleIndex).vehicleId;
        }

        JSONObject body = new JSONObject();
        try {
            body.put("user_id", currentUserId);
            body.put("vehicle_id", vehicleId);
            body.put("request_type", requestType);
        } catch (Exception e) { return; }

        parkingRequestStatus.setVisibility(View.VISIBLE);
        spotSelectorContainer.setVisibility(View.GONE);
        parkingStatusText.setText("⏳ Enviando solicitud...");
        parkingStatusText.setTextColor(ContextCompat.getColor(this, R.color.amber_pending));

        String url = apiBaseUrl + "/api/parking/request";
        RequestBody reqBody = RequestBody.create(body.toString(), MediaType.parse("application/json"));

        httpClient.newCall(new Request.Builder().url(url).post(reqBody).build()).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                runOnUiThread(() -> {
                    parkingStatusText.setText("❌ Error de red");
                    parkingStatusText.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.red_occupied));
                });
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                try {
                    String respBody = response.body() != null ? response.body().string() : "";
                    JSONObject json = new JSONObject(respBody);
                    if (json.optBoolean("success")) {
                        runOnUiThread(() -> {
                            String label;
                            switch (requestType) {
                                case "check_in": label = "INGRESAR"; break;
                                case "check_out": label = "RETIRAR"; break;
                                case "heliport": label = "HELIPUERTO"; break;
                                default: label = requestType.toUpperCase(); break;
                            }
                            parkingStatusText.setText("⏳ Solicitud de " + label + " enviada.\nEsperando aprobación del administrador...");
                            parkingStatusText.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.amber_pending));
                            startRequestPolling();
                        });
                    } else {
                        runOnUiThread(() -> {
                            parkingStatusText.setText("❌ Error al enviar solicitud");
                            parkingStatusText.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.red_occupied));
                        });
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Error parsing parking response", e);
                } finally {
                    response.close();
                }
            }
        });
    }

    private void startRequestPolling() {
        stopRequestPolling();
        requestPollRunnable = new Runnable() {
            @Override
            public void run() {
                if (!isShowingParking || currentUserId <= 0 || apiBaseUrl == null) return;
                pollRequestStatus();
                handler.postDelayed(this, REQUEST_POLL_MS);
            }
        };
        handler.postDelayed(requestPollRunnable, REQUEST_POLL_MS);
    }

    private void stopRequestPolling() {
        if (requestPollRunnable != null) {
            handler.removeCallbacks(requestPollRunnable);
            requestPollRunnable = null;
        }
    }

    private void pollRequestStatus() {
        String url = apiBaseUrl + "/api/parking/request/" + currentUserId + "/status";
        httpClient.newCall(new Request.Builder().url(url).build()).enqueue(new Callback() {
            @Override public void onFailure(Call call, IOException e) {}
            @Override
            public void onResponse(Call call, Response response) throws IOException {
                try {
                    if (!response.isSuccessful()) return;
                    String body = response.body() != null ? response.body().string() : "";
                    JSONObject json = new JSONObject(body);
                    if (!json.optBoolean("success") || json.isNull("request")) return;

                    JSONObject req = json.getJSONObject("request");
                    String status = req.optString("status", "");

                    if ("approved".equals(status)) {
                        String reqType = req.optString("request_type", lastRequestType);
                        runOnUiThread(() -> {
                            stopRequestPolling();
                            if ("check_in".equals(reqType)) {
                                parkingStatusText.setText("✅ ¡Ingreso aprobado! Selecciona tu espacio:");
                                parkingStatusText.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.green_available));
                                loadAndShowSpotSelector();
                            } else {
                                String msg = "heliport".equals(reqType)
                                    ? "✅ ¡Helipuerto reservado!"
                                    : "✅ ¡Retiro aprobado!";
                                parkingStatusText.setText(msg);
                                parkingStatusText.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.green_available));
                                handler.postDelayed(() -> resetParkingToIdle(), 3000);
                            }
                        });
                    } else if ("rejected".equals(status)) {
                        runOnUiThread(() -> {
                            parkingStatusText.setText("❌ Solicitud rechazada por el administrador");
                            parkingStatusText.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.red_occupied));
                            stopRequestPolling();
                            handler.postDelayed(() -> resetParkingToIdle(), 4000);
                        });
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Error polling request status", e);
                } finally {
                    response.close();
                }
            }
        });
    }
    // ═══ SPOT SELECTOR & HELIPORT ═══
    private void loadAndShowSpotSelector() {
        if (apiBaseUrl == null) return;
        String url = apiBaseUrl + "/api/parking/spots";
        httpClient.newCall(new Request.Builder().url(url).build()).enqueue(new Callback() {
            @Override public void onFailure(Call call, IOException e) {}
            @Override
            public void onResponse(Call call, Response response) throws IOException {
                try {
                    String body = response.body() != null ? response.body().string() : "";
                    JSONObject json = new JSONObject(body);
                    if (!json.optBoolean("success")) return;
                    
                    JSONArray spots = json.getJSONArray("spots");
                    runOnUiThread(() -> {
                        spotSelectorContainer.removeAllViews();
                        spotSelectorContainer.setVisibility(View.VISIBLE);
                        
                        // Group spots by floor
                        for (int floor = 1; floor <= 3; floor++) {
                            TextView floorTitle = new TextView(MainActivity.this);
                            floorTitle.setText("PISO " + floor);
                            floorTitle.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.gold));
                            floorTitle.setTypeface(null, android.graphics.Typeface.BOLD);
                            floorTitle.setPadding(0, 16, 0, 8);
                            spotSelectorContainer.addView(floorTitle);

                            LinearLayout row = new LinearLayout(MainActivity.this);
                            row.setOrientation(LinearLayout.HORIZONTAL);
                            
                            for (int i = 0; i < spots.length(); i++) {
                                JSONObject spot = spots.optJSONObject(i);
                                if (spot != null && spot.optInt("floor") == floor) {
                                    int spotId = spot.optInt("id");
                                    String label = spot.optString("spot_label");
                                    String status = spot.optString("status");
                                    
                                    TextView btn = new TextView(MainActivity.this);
                                    LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, 120, 1f);
                                    params.setMargins(4, 4, 4, 4);
                                    btn.setLayoutParams(params);
                                    btn.setText(label);
                                    btn.setGravity(android.view.Gravity.CENTER);
                                    btn.setTextSize(12);
                                    btn.setTypeface(null, android.graphics.Typeface.BOLD);
                                    
                                    if ("available".equals(status)) {
                                        btn.setBackgroundColor(ContextCompat.getColor(MainActivity.this, R.color.green_available));
                                        btn.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.black));
                                        btn.setOnClickListener(v -> selectSpot(spotId, label));
                                    } else {
                                        btn.setBackgroundColor(ContextCompat.getColor(MainActivity.this, R.color.red_occupied));
                                        btn.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.white));
                                    }
                                    row.addView(btn);
                                    
                                    // 4 spots per row visually
                                    if (row.getChildCount() == 4) {
                                        spotSelectorContainer.addView(row);
                                        row = new LinearLayout(MainActivity.this);
                                        row.setOrientation(LinearLayout.HORIZONTAL);
                                    }
                                }
                            }
                            if (row.getChildCount() > 0) {
                                spotSelectorContainer.addView(row);
                            }
                        }
                    });
                } catch (Exception e) {
                    Log.e(TAG, "Error parsing spots", e);
                } finally {
                    response.close();
                }
            }
        });
    }

    private void selectSpot(int spotId, String spotLabel) {
        if (apiBaseUrl == null || currentUserId <= 0) return;
        
        int vehicleId = 0;
        if (selectedVehicleIndex >= 0 && selectedVehicleIndex < currentVehicles.size()) {
            vehicleId = currentVehicles.get(selectedVehicleIndex).vehicleId;
        }

        JSONObject body = new JSONObject();
        try {
            body.put("user_id", currentUserId);
            body.put("vehicle_id", vehicleId);
            body.put("spot_id", spotId);
        } catch (Exception e) { return; }

        parkingStatusText.setText("⏳ Confirmando espacio " + spotLabel + "...");
        parkingStatusText.setTextColor(ContextCompat.getColor(this, R.color.amber_pending));
        
        // Hide spots while submitting
        for (int i = 0; i < spotSelectorContainer.getChildCount(); i++) {
            spotSelectorContainer.getChildAt(i).setEnabled(false);
        }

        String url = apiBaseUrl + "/api/parking/spot/select";
        RequestBody reqBody = RequestBody.create(body.toString(), MediaType.parse("application/json"));

        httpClient.newCall(new Request.Builder().url(url).post(reqBody).build()).enqueue(new Callback() {
            @Override public void onFailure(Call call, IOException e) {
                runOnUiThread(() -> {
                    parkingStatusText.setText("❌ Error de red al seleccionar espacio");
                    parkingStatusText.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.red_occupied));
                });
            }
            @Override
            public void onResponse(Call call, Response response) throws IOException {
                try {
                    String respBody = response.body() != null ? response.body().string() : "";
                    JSONObject json = new JSONObject(respBody);
                    if (json.optBoolean("success")) {
                        runOnUiThread(() -> {
                            parkingStatusText.setText("✅ ¡Estacionado en " + spotLabel + "!");
                            parkingStatusText.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.green_available));
                            handler.postDelayed(() -> resetParkingToIdle(), 3000);
                        });
                    } else {
                        runOnUiThread(() -> {
                            parkingStatusText.setText("❌ Error: " + json.optJSONArray("errors").optString(0, ""));
                            parkingStatusText.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.red_occupied));
                            loadAndShowSpotSelector(); // reload
                        });
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Error selecting spot", e);
                } finally {
                    response.close();
                }
            }
        });
    }

    private void loadHeliportStatus() {
        if (apiBaseUrl == null) return;
        String url = apiBaseUrl + "/api/parking/heliport";
        httpClient.newCall(new Request.Builder().url(url).build()).enqueue(new Callback() {
            @Override public void onFailure(Call call, IOException e) {}
            @Override
            public void onResponse(Call call, Response response) throws IOException {
                try {
                    String body = response.body() != null ? response.body().string() : "";
                    JSONObject json = new JSONObject(body);
                    if (!json.optBoolean("success")) return;
                    
                    JSONObject heliport = json.getJSONObject("heliport");
                    String status = heliport.optString("status");
                    
                    runOnUiThread(() -> {
                        if ("available".equals(status)) {
                            btnHeliport.setText("🚁  RESERVAR HELIPUERTO (DISPONIBLE)");
                            btnHeliport.setBackgroundColor(ContextCompat.getColor(MainActivity.this, R.color.green_available));
                            btnHeliport.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.black));
                            btnHeliport.setEnabled(true);
                        } else {
                            btnHeliport.setText("🚁  HELIPUERTO OCUPADO");
                            btnHeliport.setBackgroundColor(ContextCompat.getColor(MainActivity.this, R.color.red_occupied));
                            btnHeliport.setTextColor(ContextCompat.getColor(MainActivity.this, R.color.white));
                            btnHeliport.setEnabled(false);
                        }
                    });
                } catch (Exception e) {
                    Log.e(TAG, "Error loading heliport status", e);
                } finally {
                    response.close();
                }
            }
        });
    }
    // ═══ MANUAL ENTRY & KEYBOARD SCANNER ═══
    @Override
    public boolean dispatchKeyEvent(KeyEvent event) {
        if (event.getAction() == KeyEvent.ACTION_DOWN) {
            int keyCode = event.getKeyCode();
            if (keyCode >= KeyEvent.KEYCODE_0 && keyCode <= KeyEvent.KEYCODE_9) {
                keyAccumulator.append((char) ('0' + (keyCode - KeyEvent.KEYCODE_0)));
                if (keyAccumulator.length() > 32) keyAccumulator.setLength(0);
                return true;
            }
            if (keyCode >= KeyEvent.KEYCODE_NUMPAD_0 && keyCode <= KeyEvent.KEYCODE_NUMPAD_9) {
                keyAccumulator.append((char) ('0' + (keyCode - KeyEvent.KEYCODE_NUMPAD_0)));
                if (keyAccumulator.length() > 32) keyAccumulator.setLength(0);
                return true;
            }
            if (keyCode == KeyEvent.KEYCODE_ENTER || keyCode == KeyEvent.KEYCODE_NUMPAD_ENTER) {
                String cardNumber = keyAccumulator.toString().trim();
                keyAccumulator.setLength(0);
                if (cardNumber.length() == 16) submitCardNumber(cardNumber);
                return true;
            }
        }
        return super.dispatchKeyEvent(event);
    }

    // ═══ CAMERA SCANNER (ZXing) ═══
    private void launchCameraScanner() {
        ScanOptions options = new ScanOptions();
        options.setDesiredBarcodeFormats(ScanOptions.QR_CODE, ScanOptions.CODE_128, ScanOptions.CODE_39);
        options.setPrompt("Escanea el código QR o el código de barras de la tarjeta GTR");
        options.setCameraId(0);
        options.setBeepEnabled(true);
        options.setBarcodeImageEnabled(false);
        options.setOrientationLocked(false);
        barcodeLauncher.launch(options);
    }

    private void onScanResult(ScanIntentResult result) {
        hideSystemUI(); // Restore fullscreen after camera activity
        if (result.getContents() == null) {
            Toast.makeText(this, "Escaneo cancelado", Toast.LENGTH_SHORT).show();
            return;
        }

        String scanned = result.getContents().trim().replace(" ", "").replace("-", "");
        Log.i(TAG, "Scanned: " + scanned + " (length=" + scanned.length() + ")");

        // Extract 16 digits from the scanned content
        String cardNumber = extractCardNumber(scanned);
        if (cardNumber != null) {
            Toast.makeText(this, "Tarjeta detectada: " + formatCard(cardNumber), Toast.LENGTH_SHORT).show();
            submitCardNumber(cardNumber);
        } else {
            Toast.makeText(this, "Código no reconocido. Se esperan 16 dígitos.", Toast.LENGTH_LONG).show();
        }
    }

    private String extractCardNumber(String raw) {
        // If it's exactly 16 digits, use it directly
        if (raw.length() == 16 && raw.matches("\\d{16}")) return raw;
        // Try to find 16 consecutive digits in the scanned text
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("(\\d{16})").matcher(raw);
        if (m.find()) return m.group(1);
        // If it's all digits but not 16, still reject
        return null;
    }

    private String formatCard(String digits) {
        if (digits.length() != 16) return digits;
        return digits.substring(0, 4) + " " + digits.substring(4, 8) + " "
                + digits.substring(8, 12) + " " + digits.substring(12, 16);
    }

    private void showManualInputDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Escanear Tarjeta");
        builder.setMessage("Ingresa el número de tarjeta (16 dígitos):");

        final EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_NUMBER);
        FrameLayout container = new FrameLayout(this);
        int pad = (int) (24 * getResources().getDisplayMetrics().density);
        container.setPadding(pad, pad / 2, pad, pad / 2);
        input.setLayoutParams(new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        container.addView(input);
        builder.setView(container);

        builder.setPositiveButton("Enviar", (dialog, which) -> {
            String cardNumber = input.getText().toString().trim().replace(" ", "").replace("-", "");
            if (cardNumber.length() == 16) submitCardNumber(cardNumber);
            else Toast.makeText(this, "El número debe tener 16 dígitos", Toast.LENGTH_SHORT).show();
        });
        builder.setNegativeButton("Cancelar", (dialog, which) -> dialog.cancel());
        if (!isShowingParking) {
            builder.setNeutralButton("Parking", (dialog, which) -> showParkingInterface());
        }
        builder.show();
    }

    private void submitCardNumber(String cardNumber) {
        if (apiBaseUrl == null) {
            Toast.makeText(this, "API no resuelta. Intentando reconectar...", Toast.LENGTH_SHORT).show();
            resolveApiHost();
            return;
        }

        String url = apiBaseUrl + "/api/scan-event/card";
        JSONObject json = new JSONObject();
        try { json.put("card_number", cardNumber); } catch (Exception e) { return; }

        RequestBody body = RequestBody.create(json.toString(), MediaType.parse("application/json; charset=utf-8"));
        httpClient.newCall(new Request.Builder().url(url).post(body).build()).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "Error de red", Toast.LENGTH_SHORT).show());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                try {
                    String responseBody = response.body().string();
                    if (response.isSuccessful()) {
                        JSONObject respJson = new JSONObject(responseBody);
                        String memberName = respJson.optString("member_name", "");
                        int memberId = respJson.optInt("member_id", -1);

                        // Parse vehicles if available
                        List<VehicleInfo> vehicles = new ArrayList<>();
                        JSONArray vArr = respJson.optJSONArray("vehicles");
                        if (vArr != null) {
                            for (int i = 0; i < vArr.length(); i++) {
                                JSONObject vj = vArr.getJSONObject(i);
                                VehicleInfo vi = new VehicleInfo();
                                vi.nickname = vj.optString("nickname", "Vehículo");
                                vi.vehicleType = vj.optString("vehicle_type", "sedan");
                                vi.brand = vj.optString("brand", "");
                                vi.model = vj.optString("model", "");
                                vi.year = vj.optInt("year", 0);
                                vi.color = vj.optString("color", "");
                                vi.plate = vj.optString("plate", "");
                                vi.isPrimary = vj.optBoolean("is_primary", false);
                                vi.vehicleId = vj.optInt("id", 0);
                                vehicles.add(vi);
                            }
                        }

                        runOnUiThread(() -> {
                            currentUserId = memberId;
                            currentUserName = memberName;
                            currentVehicles = vehicles;
                            selectedVehicleIndex = vehicles.isEmpty() ? -1 : 0;
                            if (isShowingParking) {
                                showParkingInterface();
                            } else {
                                showWelcome(memberName);
                            }
                        });
                    } else {
                        runOnUiThread(() -> Toast.makeText(MainActivity.this, "Tarjeta no reconocida", Toast.LENGTH_LONG).show());
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Error parsing response: " + e.getMessage());
                } finally {
                    response.close();
                }
            }
        });
    }

    // ═══ HELPERS ═══
    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density);
    }

    private String getVehicleEmoji(String type) {
        if (type == null) return "🚗";
        switch (type) {
            case "sports": return "🏎";
            case "suv": return "🚙";
            case "convertible": return "🚘";
            case "exotic": return "🏆";
            default: return "🚗";
        }
    }

    private String joinNonNull(String sep, String... parts) {
        StringBuilder sb = new StringBuilder();
        for (String p : parts) {
            if (p != null && !p.isEmpty()) {
                if (sb.length() > 0) sb.append(sep);
                sb.append(p);
            }
        }
        return sb.toString();
    }
}
