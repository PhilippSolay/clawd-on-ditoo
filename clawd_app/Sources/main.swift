// Clawd — a menu-bar controller + settings UI for the Divoom Ditoo pixel pet.
//
// It owns the Python daemon (so macOS attributes the Bluetooth/Microphone TCC
// permissions to *this* app), shows live status, and edits every setting through
// the daemon's /config HTTP API (or the config file directly while it's stopped).
//
// Build with clawd_app/build.sh — produces Clawd.app (LSUIElement, menu-bar only).

import SwiftUI
import AppKit
import ServiceManagement

// MARK: - Menu-bar icon (vector Clawd silhouette, rendered as a template image so
// macOS tints it white on a dark menu bar and dark on a light one).

enum ClawdIcon {
    static let image: NSImage = make()

    private static func make() -> NSImage {
        let img = NSImage(size: NSSize(width: 22, height: 16), flipped: true) { _ in
            NSColor.black.setFill()  // color is ignored for template images; alpha is the shape
            // Body + side nubs + legs as one nonzero-wound path (clean union, no seams).
            let body = NSBezierPath()
            body.appendRoundedRect(NSRect(x: 3, y: 2, width: 16, height: 10), xRadius: 3, yRadius: 3)
            body.appendRoundedRect(NSRect(x: 0.5, y: 6.5, width: 3.2, height: 4), xRadius: 1.5, yRadius: 1.5)   // left nub
            body.appendRoundedRect(NSRect(x: 18.3, y: 6.5, width: 3.2, height: 4), xRadius: 1.5, yRadius: 1.5)  // right nub
            body.appendRoundedRect(NSRect(x: 7.3, y: 10.5, width: 2.2, height: 5), xRadius: 0.8, yRadius: 0.8)  // left leg
            body.appendRoundedRect(NSRect(x: 12.5, y: 10.5, width: 2.2, height: 5), xRadius: 0.8, yRadius: 0.8) // right leg
            body.windingRule = .nonZero
            body.fill()
            // Punch the two eyes out so the menu-bar background shows through.
            NSGraphicsContext.current?.compositingOperation = .clear
            NSBezierPath(roundedRect: NSRect(x: 7.6, y: 4.6, width: 1.8, height: 4), xRadius: 0.7, yRadius: 0.7).fill()
            NSBezierPath(roundedRect: NSRect(x: 12.6, y: 4.6, width: 1.8, height: 4), xRadius: 0.7, yRadius: 0.7).fill()
            return true
        }
        img.isTemplate = true
        return img
    }
}

extension NSBezierPath {
    func appendRoundedRect(_ rect: NSRect, xRadius: CGFloat, yRadius: CGFloat) {
        append(NSBezierPath(roundedRect: rect, xRadius: xRadius, yRadius: yRadius))
    }
}

// MARK: - Config model (mirrors ~/.clawd/config.json; snake_case <-> camelCase)

// NOTE: each struct has an explicit init(from:) using decodeIfPresent. Swift's
// *synthesized* Codable init does NOT fall back to a stored-property default for a
// missing JSON key — it throws keyNotFound — which (under the `try?` decode sites)
// would silently wipe the user's whole config the moment the daemon adds a new
// field (e.g. sounds.theme). decodeIfPresent makes every key optional-with-default.

struct DeviceCfg: Codable {
    var mac: String? = nil
    var channel = 2
    init() {}
    init(from d: Decoder) throws {
        let c = try d.container(keyedBy: CodingKeys.self)
        mac = try c.decodeIfPresent(String.self, forKey: .mac)
        channel = try c.decodeIfPresent(Int.self, forKey: .channel) ?? 2
    }
}

struct SoundsCfg: Codable {
    var enabled = true
    var volume = 0.6
    var audioDevice = "DitooPro"
    var theme = "bubbly"
    init() {}
    init(from d: Decoder) throws {
        let c = try d.container(keyedBy: CodingKeys.self)
        enabled = try c.decodeIfPresent(Bool.self, forKey: .enabled) ?? true
        volume = try c.decodeIfPresent(Double.self, forKey: .volume) ?? 0.6
        audioDevice = try c.decodeIfPresent(String.self, forKey: .audioDevice) ?? "DitooPro"
        theme = try c.decodeIfPresent(String.self, forKey: .theme) ?? "bubbly"
    }
}

struct VoiceCfg: Codable {
    var babble = true
    var spokenLines = true
    var ttsVoice: String? = nil
    init() {}
    init(from d: Decoder) throws {
        let c = try d.container(keyedBy: CodingKeys.self)
        babble = try c.decodeIfPresent(Bool.self, forKey: .babble) ?? true
        spokenLines = try c.decodeIfPresent(Bool.self, forKey: .spokenLines) ?? true
        ttsVoice = try c.decodeIfPresent(String.self, forKey: .ttsVoice)
    }
}

struct MicCfg: Codable {
    var enabled = true
    var clapFloor = 0.06
    var clapRise = 4.0
    var doubleWindow = 0.55
    init() {}
    init(from d: Decoder) throws {
        let c = try d.container(keyedBy: CodingKeys.self)
        enabled = try c.decodeIfPresent(Bool.self, forKey: .enabled) ?? true
        clapFloor = try c.decodeIfPresent(Double.self, forKey: .clapFloor) ?? 0.06
        clapRise = try c.decodeIfPresent(Double.self, forKey: .clapRise) ?? 4.0
        doubleWindow = try c.decodeIfPresent(Double.self, forKey: .doubleWindow) ?? 0.55
    }
}

struct AnimationsCfg: Codable {
    var brightness = 70
    var idleFidgets = true
    var fidgetFrequency = 1.0
    var blink = true
    init() {}
    init(from d: Decoder) throws {
        let c = try d.container(keyedBy: CodingKeys.self)
        brightness = try c.decodeIfPresent(Int.self, forKey: .brightness) ?? 70
        idleFidgets = try c.decodeIfPresent(Bool.self, forKey: .idleFidgets) ?? true
        fidgetFrequency = try c.decodeIfPresent(Double.self, forKey: .fidgetFrequency) ?? 1.0
        blink = try c.decodeIfPresent(Bool.self, forKey: .blink) ?? true
    }
}

struct SleepCfg: Codable {
    var idleToSleepSeconds = 240.0
    init() {}
    init(from d: Decoder) throws {
        let c = try d.container(keyedBy: CodingKeys.self)
        idleToSleepSeconds = try c.decodeIfPresent(Double.self, forKey: .idleToSleepSeconds) ?? 240.0
    }
}

struct ClawdConfig: Codable {
    var device = DeviceCfg()
    var sounds = SoundsCfg()
    var voice = VoiceCfg()
    var mic = MicCfg()
    var animations = AnimationsCfg()
    var sleep = SleepCfg()

    init() {}
    init(from d: Decoder) throws {
        let c = try d.container(keyedBy: CodingKeys.self)
        device = try c.decodeIfPresent(DeviceCfg.self, forKey: .device) ?? DeviceCfg()
        sounds = try c.decodeIfPresent(SoundsCfg.self, forKey: .sounds) ?? SoundsCfg()
        voice = try c.decodeIfPresent(VoiceCfg.self, forKey: .voice) ?? VoiceCfg()
        mic = try c.decodeIfPresent(MicCfg.self, forKey: .mic) ?? MicCfg()
        animations = try c.decodeIfPresent(AnimationsCfg.self, forKey: .animations) ?? AnimationsCfg()
        sleep = try c.decodeIfPresent(SleepCfg.self, forKey: .sleep) ?? SleepCfg()
    }

    static func decoder() -> JSONDecoder {
        let d = JSONDecoder(); d.keyDecodingStrategy = .convertFromSnakeCase; return d
    }
    static func encoder() -> JSONEncoder {
        let e = JSONEncoder(); e.keyEncodingStrategy = .convertToSnakeCase
        e.outputFormatting = [.prettyPrinted, .sortedKeys]; return e
    }
}

// MARK: - Controller: daemon lifecycle + status polling + config I/O

@MainActor
final class ClawdController: ObservableObject {
    @Published var config = ClawdConfig()
    @Published var running = false
    @Published var bridgeAlive = false
    @Published var state = "—"
    @Published var lastMessage = ""

    private let base = URL(string: "http://127.0.0.1:7878")!
    private var daemon: Process?
    private var pollTimer: Timer?

    /// Project root = two levels up from Clawd.app (it lives in <root>/clawd_app/).
    let projectRoot: URL = Bundle.main.bundleURL
        .deletingLastPathComponent()   // clawd_app/
        .deletingLastPathComponent()   // <root>/
    var clawdBin: URL { projectRoot.appendingPathComponent("bin/clawd") }
    var configFile: URL {
        FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".clawd/config.json")
    }

    init() {
        loadConfigFromFile()
        startPolling()
    }

    // ----- status polling -----

    func startPolling() {
        pollTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { [weak self] _ in
            Task { await self?.refresh() }
        }
        Task { await refresh() }
    }

    func refresh() async {
        guard let data = try? await get("/healthz"),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            running = false; bridgeAlive = false; state = "—"; return
        }
        running = true
        bridgeAlive = (obj["bridge_alive"] as? Bool) ?? false
        state = (obj["state"] as? String) ?? "—"
        if let cfgData = try? await get("/config"),
           let cfg = try? ClawdConfig.decoder().decode(ClawdConfig.self, from: cfgData) {
            config = cfg
        }
    }

    // ----- daemon control -----

    func start() {
        guard FileManager.default.isExecutableFile(atPath: clawdBin.path) else {
            lastMessage = "bin/clawd not found at \(clawdBin.path)"; return
        }
        guard let mac = config.device.mac, !mac.isEmpty else {
            lastMessage = "Set the Ditoo MAC in Settings first."; return
        }
        let p = Process()
        p.executableURL = clawdBin
        p.arguments = ["start", "--foreground", "--mac", mac]
        p.currentDirectoryURL = projectRoot
        do {
            try p.run()
            daemon = p
            lastMessage = "Starting Clawd…"
        } catch {
            lastMessage = "Failed to start: \(error.localizedDescription)"
        }
    }

    func stop() {
        Task { _ = try? await post("/shutdown", body: [:]) }
        daemon?.terminate()
        daemon = nil
        lastMessage = "Stopping Clawd…"
    }

    // ----- settings -----

    /// Apply the current config: live via /config when running, else write the file.
    func apply() {
        if running {
            if let body = try? ClawdConfig.encoder().encode(config),
               let dict = try? JSONSerialization.jsonObject(with: body) as? [String: Any] {
                Task {
                    if let resp = try? await post("/config", body: dict),
                       let obj = try? JSONSerialization.jsonObject(with: resp) as? [String: Any],
                       let needs = obj["needs_restart"] as? [String], !needs.isEmpty {
                        lastMessage = "Saved. Restart to apply: \(needs.joined(separator: ", "))"
                    } else {
                        lastMessage = "Settings applied."
                    }
                }
            }
        } else {
            writeConfigToFile()
            lastMessage = "Saved to file (applies when Clawd starts)."
        }
    }

    private func loadConfigFromFile() {
        guard let data = try? Data(contentsOf: configFile),
              let cfg = try? ClawdConfig.decoder().decode(ClawdConfig.self, from: data) else { return }
        config = cfg
    }

    private func writeConfigToFile() {
        guard let data = try? ClawdConfig.encoder().encode(config) else { return }
        try? FileManager.default.createDirectory(
            at: configFile.deletingLastPathComponent(), withIntermediateDirectories: true)
        try? data.write(to: configFile)
    }

    // ----- tiny HTTP helpers -----

    private func get(_ path: String) async throws -> Data {
        var req = URLRequest(url: base.appendingPathComponent(path))
        req.timeoutInterval = 1.0
        return try await URLSession.shared.data(for: req).0
    }

    private func post(_ path: String, body: [String: Any]) async throws -> Data {
        var req = URLRequest(url: base.appendingPathComponent(path))
        req.httpMethod = "POST"
        req.timeoutInterval = 2.0
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        return try await URLSession.shared.data(for: req).0
    }
}

// MARK: - Login item

enum LoginItem {
    static var enabled: Bool { SMAppService.mainApp.status == .enabled }
    static func toggle() {
        do {
            if enabled { try SMAppService.mainApp.unregister() }
            else { try SMAppService.mainApp.register() }
        } catch { NSLog("login item toggle failed: \(error)") }
    }
}

// MARK: - Settings window

struct SettingsView: View {
    @EnvironmentObject var ctl: ClawdController

    var body: some View {
        Form {
            Section("Device") {
                TextField("Ditoo MAC", text: Binding(
                    get: { ctl.config.device.mac ?? "" },
                    set: { ctl.config.device.mac = $0.isEmpty ? nil : $0 }))
                    .textFieldStyle(.roundedBorder)
                Stepper("RFCOMM channel: \(ctl.config.device.channel)",
                        value: $ctl.config.device.channel, in: 1...30)
            }
            Section("Display & Animations") {
                slider("Brightness", value: Binding(
                    get: { Double(ctl.config.animations.brightness) },
                    set: { ctl.config.animations.brightness = Int($0) }), 0, 100, "%.0f")
                Toggle("Idle fidgets (look / wave / bubble / stretch)", isOn: $ctl.config.animations.idleFidgets)
                slider("Fidget frequency", value: $ctl.config.animations.fidgetFrequency, 0, 3, "%.1f×")
                Toggle("Idle blinking", isOn: $ctl.config.animations.blink)
            }
            Section("Sounds") {
                Toggle("Sounds enabled", isOn: $ctl.config.sounds.enabled)
                Picker("Theme", selection: $ctl.config.sounds.theme) {
                    Text("Marimba (warm)").tag("marimba")
                    Text("Music box").tag("music_box")
                    Text("Bubbly").tag("bubbly")
                    Text("Chiptune (retro)").tag("chip")
                }
                slider("Volume", value: $ctl.config.sounds.volume, 0, 1, "%.2f")
                TextField("Output device", text: $ctl.config.sounds.audioDevice)
                    .textFieldStyle(.roundedBorder)
            }
            Section("Voice") {
                Toggle("Chiptune muttering (babble)", isOn: $ctl.config.voice.babble)
                Toggle("Spoken lines (TTS)", isOn: $ctl.config.voice.spokenLines)
                TextField("TTS voice (blank = auto)", text: Binding(
                    get: { ctl.config.voice.ttsVoice ?? "" },
                    set: { ctl.config.voice.ttsVoice = $0.isEmpty ? nil : $0 }))
                    .textFieldStyle(.roundedBorder)
            }
            Section("Microphone / Claps") {
                Toggle("Clap detection", isOn: $ctl.config.mic.enabled)
                slider("Clap floor", value: $ctl.config.mic.clapFloor, 0, 0.3, "%.3f")
                slider("Clap rise ×", value: $ctl.config.mic.clapRise, 1, 20, "%.1f")
                slider("Double-clap window (s)", value: $ctl.config.mic.doubleWindow, 0.2, 1.5, "%.2f")
            }
            Section("Sleep") {
                slider("Nap after idle (s)", value: $ctl.config.sleep.idleToSleepSeconds, 10, 1800, "%.0f")
            }
            Section {
                HStack {
                    Button("Apply") { ctl.apply() }.keyboardShortcut(.defaultAction)
                    Spacer()
                    Text(ctl.lastMessage).font(.caption).foregroundStyle(.secondary)
                }
            }
        }
        .formStyle(.grouped)
        .frame(width: 420, height: 560)
    }

    @ViewBuilder
    private func slider(_ label: String, value: Binding<Double>,
                        _ lo: Double, _ hi: Double, _ fmt: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack { Text(label); Spacer(); Text(String(format: fmt, value.wrappedValue)).foregroundStyle(.secondary) }
            Slider(value: value, in: lo...hi)
        }
    }
}

// MARK: - App

@main
struct ClawdApp: App {
    @StateObject private var ctl = ClawdController()
    @Environment(\.openWindow) private var openWindow

    var body: some Scene {
        MenuBarExtra {
            Text(ctl.running ? "Clawd — \(ctl.state)" : "Clawd — stopped")
            Text(ctl.bridgeAlive ? "● Ditoo connected" : "○ Ditoo not connected")
            Divider()
            if ctl.running {
                Button("Stop Clawd") { ctl.stop() }
            } else {
                Button("Start Clawd") { ctl.start() }
            }
            Button("Settings…") {
                openWindow(id: "settings")
                NSApp.activate(ignoringOtherApps: true)
            }
            Divider()
            Button(LoginItem.enabled ? "✓ Launch at Login" : "Launch at Login") { LoginItem.toggle() }
            if !ctl.lastMessage.isEmpty { Text(ctl.lastMessage).font(.caption) }
            Divider()
            Button("Quit Clawd") { ctl.stop(); NSApp.terminate(nil) }
                .keyboardShortcut("q")
        } label: {
            Image(nsImage: ClawdIcon.image)
        }

        Window("Clawd Settings", id: "settings") {
            SettingsView().environmentObject(ctl)
        }
        .windowResizability(.contentSize)
    }
}
