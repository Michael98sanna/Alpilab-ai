package ai.alpilab.alpilab_mobile

import android.content.Context
import android.net.wifi.WifiManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.net.Inet4Address
import java.net.NetworkInterface

class MainActivity : FlutterActivity() {
    private var multicastLock: WifiManager.MulticastLock? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "ai.alpilab/multicast")
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "acquire" -> {
                        try {
                            if (multicastLock == null) {
                                val wifi = applicationContext
                                    .getSystemService(Context.WIFI_SERVICE) as WifiManager
                                multicastLock = wifi.createMulticastLock("alpilab_mdns").apply {
                                    setReferenceCounted(true)
                                    acquire()
                                }
                            }
                            result.success(true)
                        } catch (e: Exception) {
                            result.error("LOCK_ERROR", e.message, null)
                        }
                    }
                    "release" -> {
                        try {
                            multicastLock?.let {
                                if (it.isHeld) it.release()
                            }
                            multicastLock = null
                            result.success(true)
                        } catch (e: Exception) {
                            result.error("LOCK_ERROR", e.message, null)
                        }
                    }
                    else -> result.notImplemented()
                }
            }

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "ai.alpilab/network")
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "getWifiGateway" -> {
                        try {
                            val wifi = applicationContext
                                .getSystemService(Context.WIFI_SERVICE) as WifiManager
                            val dhcp = wifi.dhcpInfo
                            if (dhcp != null && dhcp.gateway != 0) {
                                val gw = intToIp(dhcp.gateway)
                                result.success(gw)
                            } else {
                                result.success(null)
                            }
                        } catch (e: Exception) {
                            result.error("NETWORK_ERROR", e.message, null)
                        }
                    }
                    else -> result.notImplemented()
                }
            }
    }

    private fun intToIp(ip: Int): String {
        return "${ip and 0xFF}.${(ip shr 8) and 0xFF}.${(ip shr 16) and 0xFF}.${(ip shr 24) and 0xFF}"
    }
}
