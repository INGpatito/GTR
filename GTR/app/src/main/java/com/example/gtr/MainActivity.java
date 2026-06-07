package com.example.gtr;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import org.json.JSONObject;

import java.io.IOException;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

/**
 * ═══════════════════════════════════════════════════
 * Parking GTR — Welcome Display
 * ═══════════════════════════════════════════════════
 *
 * Pantalla de bienvenida en modo landscape:
 * - IDLE:    Muestra el logo GTR
 * - WELCOME: Muestra "Bienvenido, [Nombre]" por 5 segundos
 *
 * Hace polling al backend cada 3 segundos en:
 *   GET /api/scan-event
 *
 * Cuando el scanner Python verifica un socio, el backend
 * almacena el evento y esta app lo recoge.
 */
public class MainActivity extends AppCompatActivity {

    private static final String TAG = "GTR_Display";

    // ── Polling config ──
    // Candidate API hosts to try (same logic as admin-panel settings.py)
    private static final String[] CANDIDATE_HOSTS = {
            "10.0.2.2",            // Android Emulator Loopback
            "192.168.100.47",      // Host Local WiFi
            "10.42.0.1",           // Hotspot GTR
            "192.168.100.16",      // LAN (MiWiFi)
            "100.89.43.30",        // Tailscale VPN
            "192.168.100.61",      // LAN antigua
    };
    private static final int API_PORT = 3001;
    private static final long POLL_INTERVAL_MS = 3000;     // 3 seconds
    private static final long WELCOME_DURATION_MS = 5000;  // 5 seconds

    // ── State ──
    private volatile String apiBaseUrl = null;
    private volatile boolean isShowingWelcome = false;
    private long lastEventTimestamp = 0;
    private volatile boolean isResolvingHost = false;

    // ── UI ──
    private LinearLayout logoContainer;
    private LinearLayout welcomeContainer;
    private TextView memberNameText;

    // ── Polling ──
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final OkHttpClient httpClient = new OkHttpClient.Builder()
            .connectTimeout(2, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(2, java.util.concurrent.TimeUnit.SECONDS)
            .build();

    private final Runnable pollRunnable = new Runnable() {
        @Override
        public void run() {
            if (apiBaseUrl != null) {
                pollScanEvent();
            } else {
                resolveApiHost();
            }
            handler.postDelayed(this, POLL_INTERVAL_MS);
        }
    };

    // ═══════════════════════════════════════════════════
    //  LIFECYCLE
    // ═══════════════════════════════════════════════════

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Get UI references
        logoContainer = findViewById(R.id.logoContainer);
        welcomeContainer = findViewById(R.id.welcomeContainer);
        memberNameText = findViewById(R.id.memberNameText);

        // Enter immersive fullscreen
        hideSystemUI();

        // Show logo state
        showLogo();

        Log.i(TAG, "Parking GTR Display started — resolving API host...");
    }

    @Override
    protected void onResume() {
        super.onResume();
        hideSystemUI();
        // Start polling
        handler.post(pollRunnable);
    }

    @Override
    protected void onPause() {
        super.onPause();
        // Stop polling when not visible
        handler.removeCallbacks(pollRunnable);
    }

    // ═══════════════════════════════════════════════════
    //  FULLSCREEN / IMMERSIVE
    // ═══════════════════════════════════════════════════

    private void hideSystemUI() {
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.R) {
            getWindow().setDecorFitsSystemWindows(false);
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.hide(WindowInsets.Type.systemBars());
                controller.setSystemBarsBehavior(
                        WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
                );
            }
        } else {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                            | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_FULLSCREEN
            );
        }
    }

    // ═══════════════════════════════════════════════════
    //  API HOST RESOLUTION
    // ═══════════════════════════════════════════════════

    /**
     * Tries each candidate host until one responds to /api/health.
     * Runs on a background thread to avoid NetworkOnMainThreadException.
     */
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

                        String url = "http://" + host;
                        if (port != 80) {
                            url += ":" + port;
                        }
                        url += "/api/health";

                        Request request = new Request.Builder().url(url).build();

                        try (Response response = httpClient.newCall(request).execute()) {
                            if (response.isSuccessful()) {
                                String resolvedUrl = "http://" + host;
                                if (port != 80) {
                                    resolvedUrl += ":" + port;
                                }
                                apiBaseUrl = resolvedUrl;
                                Log.i(TAG, "✓ API host resolved: " + apiBaseUrl);
                                return;
                            }
                        } catch (IOException e) {
                            Log.v(TAG, "Host " + host + " on port " + port + " unreachable");
                        }
                    }
                }
                if (apiBaseUrl == null) {
                    Log.w(TAG, "No API host available yet, will retry...");
                }
            } finally {
                isResolvingHost = false;
            }
        }).start();
    }

    // ═══════════════════════════════════════════════════
    //  POLLING
    // ═══════════════════════════════════════════════════

    private void pollScanEvent() {
        if (isShowingWelcome) return; // Don't poll while showing welcome

        String url = apiBaseUrl + "/api/scan-event";
        Request request = new Request.Builder().url(url).build();

        httpClient.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                // Silent — will retry on next poll
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                try {
                    if (!response.isSuccessful()) return;

                    String body = response.body() != null ? response.body().string() : "";
                    JSONObject json = new JSONObject(body);

                    if (!json.optBoolean("success", false)) return;
                    if (json.isNull("event")) return;

                    JSONObject event = json.getJSONObject("event");
                    String memberName = event.optString("member_name", "");
                    long timestamp = event.optLong("timestamp", 0);

                    // Only show if this is a NEW event (different timestamp)
                    if (memberName.isEmpty() || timestamp == lastEventTimestamp) return;
                    lastEventTimestamp = timestamp;

                    Log.i(TAG, "Scan event received: " + memberName);

                    // Show welcome on UI thread
                    runOnUiThread(() -> showWelcome(memberName));

                    // Clear the event on the server so it doesn't re-trigger
                    clearScanEvent();

                } catch (Exception e) {
                    Log.e(TAG, "Error parsing scan event", e);
                } finally {
                    response.close();
                }
            }
        });
    }

    /**
     * DELETE /api/scan-event — clears the event so repeated polls don't re-trigger.
     */
    private void clearScanEvent() {
        String url = apiBaseUrl + "/api/scan-event";
        Request request = new Request.Builder().url(url).delete().build();
        httpClient.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) { /* ignore */ }

            @Override
            public void onResponse(Call call, Response response) {
                response.close();
            }
        });
    }

    // ═══════════════════════════════════════════════════
    //  UI STATE TRANSITIONS
    // ═══════════════════════════════════════════════════

    /**
     * Shows the GTR logo (idle state) — no animation, instant.
     */
    private void showLogo() {
        isShowingWelcome = false;
        logoContainer.clearAnimation();
        welcomeContainer.clearAnimation();
        logoContainer.setAlpha(1f);
        logoContainer.setVisibility(View.VISIBLE);
        welcomeContainer.setAlpha(0f);
        welcomeContainer.setVisibility(View.GONE);
    }

    private void showWelcome(String memberName) {
        isShowingWelcome = true;

        // Set the member name
        memberNameText.setText(memberName);

        // Cancel any running animations to prevent glitches
        logoContainer.animate().cancel();
        welcomeContainer.animate().cancel();

        // 1. Fade out logo
        logoContainer.animate()
                .alpha(0f)
                .setDuration(400)
                .withEndAction(() -> logoContainer.setVisibility(View.GONE))
                .start();

        // 2. Fade in welcome container simultaneously
        welcomeContainer.setAlpha(0f);
        welcomeContainer.setVisibility(View.VISIBLE);
        welcomeContainer.animate()
                .alpha(1f)
                .setDuration(500)
                .start();

        // Schedule return to logo after duration
        handler.postDelayed(() -> {
            logoContainer.animate().cancel();
            welcomeContainer.animate().cancel();

            // 1. Fade out welcome container
            welcomeContainer.animate()
                    .alpha(0f)
                    .setDuration(400)
                    .withEndAction(() -> welcomeContainer.setVisibility(View.GONE))
                    .start();

            // 2. Fade in logo simultaneously
            logoContainer.setAlpha(0f);
            logoContainer.setVisibility(View.VISIBLE);
            logoContainer.animate()
                    .alpha(1f)
                    .setDuration(500)
                    .start();

            isShowingWelcome = false;
        }, WELCOME_DURATION_MS);
    }
}
